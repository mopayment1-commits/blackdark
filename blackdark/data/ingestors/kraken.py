"""Kraken public OHLC ingestion (geo-friendly fallback)."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import aiohttp
from sqlalchemy.ext.asyncio import AsyncSession

from blackdark.data.provenance import hash_payload, record_provenance
from blackdark.data.repository import (
    create_ingestion_run,
    finish_ingestion_run,
    get_source_by_slug,
    insert_ohlcv_row,
    log_ingestion_error,
)

logger = logging.getLogger("BLACKDARK.DataEngine.Kraken")

KRAKEN_BASE = "https://api.kraken.com"
# Kraken public OHLC interval minutes (API value)
KRAKEN_INTERVAL = {"1m": 1, "30m": 30, "1h": 60, "4h": 240, "1d": 1440}
INTERVAL_SECONDS = {"1m": 60, "30m": 1800, "1h": 3600, "4h": 14400, "1d": 86400}


def _client_headers() -> dict[str, str]:
    return {
        "User-Agent": "BLACKDARK-DataEngine/1.0 (+https://blackdark.io)",
        "Accept": "application/json",
    }


def _sec_to_dt(sec: int) -> datetime:
    return datetime.fromtimestamp(sec, tz=UTC)


def parse_ohlc(
    symbol: str,
    interval: str,
    rows: list[Any],
    *,
    quote_asset: str = "USDT",
) -> list[dict[str, Any]]:
    pair = symbol.upper()
    delta = timedelta(seconds=INTERVAL_SECONDS.get(interval, 3600))
    parsed: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, list) or len(row) < 7:
            continue
        open_time = _sec_to_dt(int(row[0]))
        parsed.append(
            {
                "symbol": pair,
                "quote_asset": quote_asset,
                "interval": interval,
                "open_time": open_time,
                "close_time": open_time + delta,
                "open": Decimal(str(row[1])),
                "high": Decimal(str(row[2])),
                "low": Decimal(str(row[3])),
                "close": Decimal(str(row[4])),
                "volume": Decimal(str(row[6])),
            }
        )
    return parsed


async def ingest_ohlcv(
    session: AsyncSession,
    *,
    pair: str = "XBTUSDT",
    symbol: str = "BTCUSDT",
    interval: str = "1h",
    triggered_by: str = "system",
) -> dict[str, Any]:
    source = await get_source_by_slug(session, "kraken")
    if not source:
        raise RuntimeError("kraken data source not seeded")
    kraken_interval = KRAKEN_INTERVAL.get(interval, 60)
    endpoint = f"{KRAKEN_BASE}/0/public/OHLC?pair={pair}&interval={kraken_interval}"
    run_id = await create_ingestion_run(
        session,
        source_id=source["id"],
        run_type="ohlcv",
        params={"pair": pair, "symbol": symbol, "interval": interval},
        triggered_by=triggered_by,
    )
    fetched = inserted = deduped = errors = 0
    timeout = aiohttp.ClientTimeout(total=60)
    async with aiohttp.ClientSession(timeout=timeout, headers=_client_headers()) as http:
        try:
            async with http.get(endpoint) as resp:
                raw = await resp.text()
                status = resp.status
            import json

            payload = json.loads(raw) if status == 200 else {}
            rows = []
            if isinstance(payload, dict) and not payload.get("error"):
                result = payload.get("result") or {}
                rows = result.get(pair) or next(iter(result.values()), [])
            if status != 200 or not isinstance(rows, list) or not rows:
                errors += 1
                await log_ingestion_error(
                    session,
                    ingestion_run_id=run_id,
                    source_id=source["id"],
                    error_type="http_error",
                    error_message=f"status={status} payload={raw[:200]}",
                    endpoint=endpoint,
                )
            else:
                fetched = len(rows)
                prov_hash = hash_payload(raw)
                for row in parse_ohlc(symbol, interval, rows):
                    record_id = await insert_ohlcv_row(
                        session,
                        source_id=source["id"],
                        ingestion_run_id=run_id,
                        row=row,
                        provenance_hash=prov_hash,
                    )
                    if record_id:
                        inserted += 1
                        await record_provenance(
                            session,
                            ingestion_run_id=run_id,
                            target_table="ohlcv_data",
                            target_record_id=record_id,
                            source_endpoint=endpoint,
                            raw_body=raw,
                            response_status=status,
                        )
                    else:
                        deduped += 1
        except Exception as exc:
            errors += 1
            logger.exception("Kraken OHLCV ingest failed | %s", pair)
            await log_ingestion_error(
                session,
                ingestion_run_id=run_id,
                source_id=source["id"],
                error_type="exception",
                error_message=str(exc),
                endpoint=endpoint,
            )
    run_status = "failed" if errors and not inserted else ("partial" if errors else "completed")
    await finish_ingestion_run(
        session,
        run_id,
        status=run_status,
        records_fetched=fetched,
        records_inserted=inserted,
        records_deduped=deduped,
        errors_count=errors,
    )
    return {
        "run_id": str(run_id),
        "status": run_status,
        "records_inserted": inserted,
        "records_fetched": fetched,
        "records_deduped": deduped,
        "source": "kraken",
    }


async def backfill_ohlcv(
    session: AsyncSession,
    *,
    pair: str = "XBTUSDT",
    symbol: str = "BTCUSDT",
    interval: str = "1h",
    start_time: datetime,
    end_time: datetime,
    triggered_by: str = "cli:backfill:kraken",
) -> dict[str, Any]:
    """Paginated Kraken OHLC backfill using the ``since`` parameter."""
    source = await get_source_by_slug(session, "kraken")
    if not source:
        raise RuntimeError("kraken data source not seeded")
    kraken_interval = KRAKEN_INTERVAL.get(interval, 60)
    since = int(start_time.timestamp())
    end_sec = int(end_time.timestamp())
    step_sec = INTERVAL_SECONDS.get(interval, 3600)

    run_id = await create_ingestion_run(
        session,
        source_id=source["id"],
        run_type="ohlcv_backfill",
        params={
            "pair": pair,
            "symbol": symbol,
            "interval": interval,
            "start": start_time.isoformat(),
            "end": end_time.isoformat(),
        },
        triggered_by=triggered_by,
    )
    total_fetched = total_inserted = total_deduped = errors = 0
    timeout = aiohttp.ClientTimeout(total=60)

    async with aiohttp.ClientSession(timeout=timeout, headers=_client_headers()) as http:
        while since < end_sec:
            endpoint = (
                f"{KRAKEN_BASE}/0/public/OHLC?pair={pair}"
                f"&interval={kraken_interval}&since={since}"
            )
            try:
                async with http.get(endpoint) as resp:
                    raw = await resp.text()
                    status = resp.status
                import json

                payload = json.loads(raw) if status == 200 else {}
                rows: list[Any] = []
                if isinstance(payload, dict) and not payload.get("error"):
                    result = payload.get("result") or {}
                    rows = result.get(pair) or []
                    if not rows and result:
                        for key, val in result.items():
                            if key != "last" and isinstance(val, list):
                                rows = val
                                break
                if status != 200 or not rows:
                    errors += 1
                    await log_ingestion_error(
                        session,
                        ingestion_run_id=run_id,
                        source_id=source["id"],
                        error_type="http_error",
                        error_message=f"status={status} since={since}",
                        endpoint=endpoint,
                    )
                    break

                prov_hash = hash_payload(raw)
                batch_last_ts = since
                for row in parse_ohlc(symbol, interval, rows):
                    if int(row["open_time"].timestamp()) > end_sec:
                        continue
                    record_id = await insert_ohlcv_row(
                        session,
                        source_id=source["id"],
                        ingestion_run_id=run_id,
                        row=row,
                        provenance_hash=prov_hash,
                    )
                    batch_last_ts = max(batch_last_ts, int(row["open_time"].timestamp()))
                    if record_id:
                        total_inserted += 1
                        await record_provenance(
                            session,
                            ingestion_run_id=run_id,
                            target_table="ohlcv_data",
                            target_record_id=record_id,
                            source_endpoint=endpoint,
                            raw_body=raw,
                            response_status=status,
                        )
                    else:
                        total_deduped += 1
                total_fetched += len(rows)
                next_since = batch_last_ts + step_sec
                if next_since <= since:
                    break
                since = next_since
            except Exception as exc:
                errors += 1
                logger.exception("Kraken backfill failed at since=%s", since)
                await log_ingestion_error(
                    session,
                    ingestion_run_id=run_id,
                    source_id=source["id"],
                    error_type="exception",
                    error_message=str(exc),
                    endpoint=endpoint,
                )
                break

    run_status = "failed" if errors and not total_inserted else ("partial" if errors else "completed")
    await finish_ingestion_run(
        session,
        run_id,
        status=run_status,
        records_fetched=total_fetched,
        records_inserted=total_inserted,
        records_deduped=total_deduped,
        errors_count=errors,
    )
    return {
        "run_id": str(run_id),
        "status": run_status,
        "records_fetched": total_fetched,
        "records_inserted": total_inserted,
        "records_deduped": total_deduped,
        "source": "kraken",
    }
