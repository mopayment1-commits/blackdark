"""CoinGecko market snapshot ingestion."""

from __future__ import annotations

import logging
import os
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
    insert_market_snapshot_row,
    insert_ohlcv_row,
    log_ingestion_error,
)

logger = logging.getLogger("BLACKDARK.DataEngine.CoinGecko")

MARKETS_URL = (
    "https://api.coingecko.com/api/v3/coins/markets"
    "?vs_currency=usd&order=market_cap_desc&per_page=250&page=1&sparkline=false"
)

INTERVAL_SECONDS = {"30m": 1800, "1h": 3600, "4h": 14400}


def _client_headers() -> dict[str, str]:
    headers = {
        "User-Agent": "BLACKDARK-DataEngine/1.0 (+https://blackdark.io)",
        "Accept": "application/json",
    }
    api_key = os.getenv("COINGECKO_API_KEY", "").strip()
    if api_key:
        headers["x-cg-demo-api-key"] = api_key
    return headers


def _ms_to_dt(ms: int) -> datetime:
    return datetime.fromtimestamp(ms / 1000.0, tz=UTC)


def parse_ohlc(
    symbol: str,
    interval: str,
    rows: list[Any],
    *,
    quote_asset: str = "USD",
) -> list[dict[str, Any]]:
    pair = symbol.upper()
    delta = timedelta(seconds=INTERVAL_SECONDS.get(interval, 1800))
    parsed: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, list) or len(row) < 5:
            continue
        open_time = _ms_to_dt(int(row[0]))
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
                "volume": Decimal("0"),
            }
        )
    return parsed


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)
    except ValueError:
        return None


def parse_markets(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    parsed: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        parsed.append(
            {
                "coin_id": row.get("id"),
                "symbol": str(row.get("symbol", "")).upper(),
                "name": row.get("name"),
                "current_price": Decimal(str(row["current_price"])) if row.get("current_price") is not None else None,
                "market_cap": Decimal(str(row["market_cap"])) if row.get("market_cap") is not None else None,
                "total_volume": Decimal(str(row["total_volume"])) if row.get("total_volume") is not None else None,
                "price_change_24h": Decimal(str(row["price_change_24h"]))
                if row.get("price_change_24h") is not None
                else None,
                "price_change_pct_24h": Decimal(str(row["price_change_percentage_24h"]))
                if row.get("price_change_percentage_24h") is not None
                else None,
                "circulating_supply": Decimal(str(row["circulating_supply"]))
                if row.get("circulating_supply") is not None
                else None,
                "total_supply": Decimal(str(row["total_supply"])) if row.get("total_supply") is not None else None,
                "max_supply": Decimal(str(row["max_supply"])) if row.get("max_supply") is not None else None,
                "ath": Decimal(str(row["ath"])) if row.get("ath") is not None else None,
                "ath_change_pct": Decimal(str(row["ath_change_percentage"]))
                if row.get("ath_change_percentage") is not None
                else None,
                "ath_date": _parse_dt(row.get("ath_date")),
                "atl": Decimal(str(row["atl"])) if row.get("atl") is not None else None,
                "atl_change_pct": Decimal(str(row["atl_change_percentage"]))
                if row.get("atl_change_percentage") is not None
                else None,
                "atl_date": _parse_dt(row.get("atl_date")),
                "last_updated": _parse_dt(row.get("last_updated")),
            }
        )
    return parsed


async def ingest_ohlcv(
    session: AsyncSession,
    *,
    coin_id: str = "bitcoin",
    symbol: str = "BTCUSDT",
    days: int = 1,
    interval: str = "30m",
    quote_asset: str = "USD",
    triggered_by: str = "system",
) -> dict[str, Any]:
    source = await get_source_by_slug(session, "coingecko")
    if not source:
        raise RuntimeError("coingecko data source not seeded")
    endpoint = (
        f"https://api.coingecko.com/api/v3/coins/{coin_id}/ohlc"
        f"?vs_currency=usd&days={days}"
    )
    run_id = await create_ingestion_run(
        session,
        source_id=source["id"],
        run_type="ohlcv",
        params={"coin_id": coin_id, "symbol": symbol, "days": days, "interval": interval},
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

            payload = json.loads(raw) if status == 200 else []
            if status != 200 or not isinstance(payload, list):
                errors += 1
                await log_ingestion_error(
                    session,
                    ingestion_run_id=run_id,
                    source_id=source["id"],
                    error_type="http_error",
                    error_message=f"status={status}",
                    endpoint=endpoint,
                )
            else:
                fetched = len(payload)
                prov_hash = hash_payload(raw)
                for row in parse_ohlc(symbol, interval, payload, quote_asset=quote_asset):
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
            logger.exception("CoinGecko OHLCV ingest failed | %s", coin_id)
            await log_ingestion_error(
                session,
                ingestion_run_id=run_id,
                source_id=source["id"],
                error_type="exception",
                error_message=str(exc),
                endpoint=endpoint,
            )
    status = "failed" if errors and not inserted else ("partial" if errors else "completed")
    await finish_ingestion_run(
        session,
        run_id,
        status=status,
        records_fetched=fetched,
        records_inserted=inserted,
        records_deduped=deduped,
        errors_count=errors,
    )
    return {
        "run_id": str(run_id),
        "status": status,
        "records_fetched": fetched,
        "records_inserted": inserted,
        "records_deduped": deduped,
        "errors_count": errors,
        "source": "coingecko",
    }


async def ingest_markets(session: AsyncSession, *, triggered_by: str = "system") -> dict[str, Any]:
    source = await get_source_by_slug(session, "coingecko")
    if not source:
        raise RuntimeError("coingecko data source not seeded")
    run_id = await create_ingestion_run(
        session,
        source_id=source["id"],
        run_type="market_snapshot",
        params={"per_page": 250},
        triggered_by=triggered_by,
    )
    fetched = inserted = deduped = errors = 0
    timeout = aiohttp.ClientTimeout(total=60)
    async with aiohttp.ClientSession(timeout=timeout, headers=_client_headers()) as http:
        try:
            async with http.get(MARKETS_URL) as resp:
                raw = await resp.text()
                status = resp.status
            import json

            payload = json.loads(raw) if status == 200 else []
            if status != 200 or not isinstance(payload, list):
                errors += 1
                await log_ingestion_error(
                    session,
                    ingestion_run_id=run_id,
                    source_id=source["id"],
                    error_type="http_error",
                    error_message=f"status={status}",
                    endpoint=MARKETS_URL,
                )
            else:
                fetched = len(payload)
                for row in parse_markets(payload):
                    record_id = await insert_market_snapshot_row(
                        session,
                        source_id=source["id"],
                        ingestion_run_id=run_id,
                        row=row,
                    )
                    if record_id:
                        inserted += 1
                        await record_provenance(
                            session,
                            ingestion_run_id=run_id,
                            target_table="market_snapshots",
                            target_record_id=record_id,
                            source_endpoint=MARKETS_URL,
                            raw_body=raw,
                            response_status=status,
                        )
                    else:
                        deduped += 1
        except Exception as exc:
            errors += 1
            logger.exception("CoinGecko market ingest failed")
            await log_ingestion_error(
                session,
                ingestion_run_id=run_id,
                source_id=source["id"],
                error_type="exception",
                error_message=str(exc),
                endpoint=MARKETS_URL,
            )
    status = "failed" if errors and not inserted else ("partial" if errors else "completed")
    await finish_ingestion_run(
        session,
        run_id,
        status=status,
        records_fetched=fetched,
        records_inserted=inserted,
        records_deduped=deduped,
        errors_count=errors,
    )
    return {"run_id": str(run_id), "status": status, "records_inserted": inserted}
