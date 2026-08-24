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
INTERVAL_MINUTES = {"1h": 60, "30m": 30}


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
    delta = timedelta(minutes=INTERVAL_MINUTES.get(interval, 60))
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
    kraken_interval = INTERVAL_MINUTES.get(interval, 60)
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
        "source": "kraken",
    }
