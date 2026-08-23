"""Historical backfill CLI for Wave 01 data engine."""

from __future__ import annotations

import argparse
import asyncio
import logging
from datetime import UTC, datetime, timedelta

from blackdark.data.db import get_session, init_data_engine
from blackdark.data.ingestors.binance import ingest_funding, ingest_ohlcv, ingest_open_interest
from blackdark.data.repository import seed_data_sources

logger = logging.getLogger("BLACKDARK.DataEngine.Backfill")


async def backfill_binance_ohlcv(
    *,
    symbol: str,
    interval: str,
    days: int,
    batch_size: int,
) -> dict:
    end = datetime.now(UTC)
    start = end - timedelta(days=days)
    start_ms = int(start.timestamp() * 1000)
    end_ms = int(end.timestamp() * 1000)
    total_inserted = 0
    total_fetched = 0
    cursor = start_ms
    while cursor < end_ms:
        async with get_session() as session:
            result = await ingest_ohlcv(
                session,
                symbols=[symbol],
                intervals=[interval],
                limit=batch_size,
                start_time_ms=cursor,
                end_time_ms=end_ms,
                triggered_by="cli:backfill",
            )
        batch_fetched = int(result.get("records_fetched") or 0)
        total_inserted += int(result.get("records_inserted") or 0)
        total_fetched += batch_fetched
        if batch_fetched <= 0:
            break
        interval_ms = {
            "1m": 60_000,
            "1h": 3_600_000,
            "4h": 14_400_000,
            "1d": 86_400_000,
        }.get(interval, 3_600_000)
        cursor += batch_fetched * interval_ms
        if batch_fetched < batch_size:
            break
    return {
        "symbol": symbol,
        "interval": interval,
        "days": days,
        "records_fetched": total_fetched,
        "records_inserted": total_inserted,
    }


async def run_backfill(args: argparse.Namespace) -> dict:
    await init_data_engine()
    async with get_session() as session:
        await seed_data_sources(session)
    if args.source == "binance":
        if not args.symbol or not args.interval:
            raise SystemExit("--symbol and --interval required for binance backfill")
        return await backfill_binance_ohlcv(
            symbol=args.symbol,
            interval=args.interval,
            days=args.days,
            batch_size=args.batch_size,
        )
    raise SystemExit(f"Unsupported source: {args.source}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="BLACKDARK Wave 01 data backfill")
    parser.add_argument("command", choices=["backfill"])
    parser.add_argument("--source", required=True)
    parser.add_argument("--symbol")
    parser.add_argument("--interval", default="1h")
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--batch-size", type=int, default=1000)
    args = parser.parse_args(argv)
    if args.command == "backfill":
        result = asyncio.run(run_backfill(args))
        print(result)
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
