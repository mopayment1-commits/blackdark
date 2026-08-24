"""Historical backfill CLI for Wave 01 data engine."""

from __future__ import annotations

import argparse
import asyncio
import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from blackdark.data.db import get_session, init_data_engine
from blackdark.data.ingestors.binance import ingest_ohlcv as binance_ingest_ohlcv
from blackdark.data.ingestors.kraken import backfill_ohlcv as kraken_backfill_ohlcv
from blackdark.data.repository import seed_data_sources

logger = logging.getLogger("BLACKDARK.DataEngine.Backfill")

INTERVAL_MS = {
    "1m": 60_000,
    "1h": 3_600_000,
    "4h": 14_400_000,
    "1d": 86_400_000,
}

KRAKEN_PAIR_MAP = {
    "BTCUSDT": "XBTUSDT",
    "ETHUSDT": "ETHUSDT",
    "SOLUSDT": "SOLUSDT",
}


async def backfill_binance_ohlcv(
    *,
    symbol: str,
    interval: str,
    days: int,
    batch_size: int,
) -> dict[str, Any]:
    end = datetime.now(UTC)
    start = end - timedelta(days=days)
    start_ms = int(start.timestamp() * 1000)
    end_ms = int(end.timestamp() * 1000)
    total_inserted = 0
    total_fetched = 0
    cursor = start_ms
    interval_step = INTERVAL_MS.get(interval, 3_600_000)

    while cursor < end_ms:
        async with get_session() as session:
            result = await binance_ingest_ohlcv(
                session,
                symbols=[symbol],
                intervals=[interval],
                limit=min(batch_size, 1000),
                start_time_ms=cursor,
                end_time_ms=end_ms,
                triggered_by="cli:backfill:binance",
            )
        batch_fetched = int(result.get("records_fetched") or 0)
        total_inserted += int(result.get("records_inserted") or 0)
        total_fetched += batch_fetched
        if batch_fetched <= 0:
            break
        cursor += batch_fetched * interval_step
        if batch_fetched < min(batch_size, 1000):
            break

    return {
        "symbol": symbol,
        "interval": interval,
        "days": days,
        "source": "binance",
        "records_fetched": total_fetched,
        "records_inserted": total_inserted,
    }


async def backfill_kraken_ohlcv(
    *,
    symbol: str,
    interval: str,
    days: int,
) -> dict[str, Any]:
    end = datetime.now(UTC)
    start = end - timedelta(days=days)
    pair = KRAKEN_PAIR_MAP.get(symbol.upper(), symbol.upper())
    async with get_session() as session:
        result = await kraken_backfill_ohlcv(
            session,
            pair=pair,
            symbol=symbol.upper(),
            interval=interval,
            start_time=start,
            end_time=end,
            triggered_by="cli:backfill:kraken",
        )
    return {
        "symbol": symbol.upper(),
        "interval": interval,
        "days": days,
        "source": "kraken",
        "records_fetched": int(result.get("records_fetched") or 0),
        "records_inserted": int(result.get("records_inserted") or 0),
        "run_id": result.get("run_id"),
        "status": result.get("status"),
    }


async def backfill_ohlcv(
    *,
    symbol: str,
    interval: str,
    days: int,
    batch_size: int,
) -> dict[str, Any]:
    """Try Binance; fall back to Kraken when geo-blocked or empty."""
    binance_result = await backfill_binance_ohlcv(
        symbol=symbol,
        interval=interval,
        days=days,
        batch_size=batch_size,
    )
    if int(binance_result.get("records_fetched") or 0) > 0:
        return binance_result

    logger.warning(
        "Binance backfill returned 0 rows for %s %s — falling back to Kraken",
        symbol,
        interval,
    )
    kraken_result = await backfill_kraken_ohlcv(symbol=symbol, interval=interval, days=days)
    kraken_result["binance_fallback_reason"] = "records_fetched_zero"
    return kraken_result


async def run_backfill(args: argparse.Namespace) -> dict[str, Any]:
    await init_data_engine()
    async with get_session() as session:
        await seed_data_sources(session)
    if args.source == "binance":
        if not args.symbol or not args.interval:
            raise SystemExit("--symbol and --interval required for binance backfill")
        return await backfill_ohlcv(
            symbol=args.symbol,
            interval=args.interval,
            days=args.days,
            batch_size=args.batch_size,
        )
    if args.source == "kraken":
        if not args.symbol or not args.interval:
            raise SystemExit("--symbol and --interval required for kraken backfill")
        return await backfill_kraken_ohlcv(
            symbol=args.symbol,
            interval=args.interval,
            days=args.days,
        )
    raise SystemExit(f"Unsupported source: {args.source}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="BLACKDARK Wave 01 data backfill")
    parser.add_argument("command", choices=["backfill"])
    parser.add_argument("--source", required=True, choices=["binance", "kraken"])
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
