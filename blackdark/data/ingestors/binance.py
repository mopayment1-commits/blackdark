"""Binance spot/futures ingestion."""

from __future__ import annotations

import logging
import os
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

import aiohttp
from sqlalchemy.ext.asyncio import AsyncSession

from blackdark.data.provenance import hash_payload, record_provenance
from blackdark.data.repository import (
    create_ingestion_run,
    finish_ingestion_run,
    get_source_by_slug,
    insert_funding_row,
    insert_ohlcv_row,
    insert_open_interest_row,
    log_ingestion_error,
)

logger = logging.getLogger("BLACKDARK.DataEngine.Binance")

SPOT_BASE = "https://api.binance.com"
FUTURES_BASE = "https://fapi.binance.com"

DEFAULT_SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT")
DEFAULT_INTERVALS = ("1m", "1h")


def _client_headers() -> dict[str, str]:
    return {
        "User-Agent": "BLACKDARK-DataEngine/1.0 (+https://blackdark.io)",
        "Accept": "application/json",
    }


def _ms_to_dt(ms: int) -> datetime:
    return datetime.fromtimestamp(ms / 1000.0, tz=UTC)


def _split_symbol(symbol: str) -> tuple[str, str]:
    sym = symbol.upper()
    for quote in ("USDT", "USDC", "BUSD", "BTC", "ETH"):
        if sym.endswith(quote) and len(sym) > len(quote):
            return sym[: -len(quote)], quote
    return sym, "USDT"


def parse_klines(symbol: str, interval: str, rows: list[Any]) -> list[dict[str, Any]]:
    pair = symbol.upper()
    _, quote = _split_symbol(pair)
    parsed: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, list) or len(row) < 11:
            continue
        parsed.append(
            {
                "symbol": pair,
                "quote_asset": quote,
                "interval": interval,
                "open_time": _ms_to_dt(int(row[0])),
                "close_time": _ms_to_dt(int(row[6])),
                "open": Decimal(row[1]),
                "high": Decimal(row[2]),
                "low": Decimal(row[3]),
                "close": Decimal(row[4]),
                "volume": Decimal(row[5]),
                "quote_volume": Decimal(row[7]) if row[7] is not None else None,
                "trades_count": int(row[8]) if row[8] is not None else None,
                "taker_buy_base_volume": Decimal(row[9]) if row[9] is not None else None,
                "taker_buy_quote_volume": Decimal(row[10]) if row[10] is not None else None,
            }
        )
    return parsed


def parse_funding(symbol: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    pair = symbol.upper()
    parsed: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        parsed.append(
            {
                "symbol": pair,
                "funding_time": _ms_to_dt(int(row["fundingTime"])),
                "funding_rate": Decimal(str(row["fundingRate"])),
                "mark_price": Decimal(str(row["markPrice"])) if row.get("markPrice") is not None else None,
                "index_price": None,
                "realized_rate": None,
            }
        )
    return parsed


def parse_open_interest_hist(symbol: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    pair = symbol.upper()
    parsed: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        parsed.append(
            {
                "symbol": pair,
                "oi_time": _ms_to_dt(int(row["timestamp"])),
                "open_interest": Decimal(str(row["sumOpenInterest"])),
                "open_interest_value": Decimal(str(row["sumOpenInterestValue"]))
                if row.get("sumOpenInterestValue") is not None
                else None,
            }
        )
    return parsed


async def _fetch_json(session: aiohttp.ClientSession, url: str) -> tuple[int, str, Any]:
    import json

    async with session.get(url) as resp:
        text = await resp.text()
        try:
            payload = json.loads(text)
        except Exception:
            payload = None
        return resp.status, text, payload


async def ingest_ohlcv(
    session: AsyncSession,
    *,
    symbols: list[str] | None = None,
    intervals: list[str] | None = None,
    limit: int = 500,
    start_time_ms: int | None = None,
    end_time_ms: int | None = None,
    triggered_by: str = "system",
) -> dict[str, Any]:
    source = await get_source_by_slug(session, "binance")
    if not source:
        raise RuntimeError("binance data source not seeded")
    symbols = symbols or list(DEFAULT_SYMBOLS)
    intervals = intervals or list(DEFAULT_INTERVALS)
    run_id = await create_ingestion_run(
        session,
        source_id=source["id"],
        run_type="ohlcv",
        params={"symbols": symbols, "intervals": intervals, "limit": limit},
        triggered_by=triggered_by,
    )
    fetched = inserted = deduped = errors = 0
    timeout = aiohttp.ClientTimeout(total=60)
    async with aiohttp.ClientSession(timeout=timeout, headers=_client_headers()) as http:
        for symbol in symbols:
            pair = symbol.upper()
            for interval in intervals:
                params = [f"symbol={pair}", f"interval={interval}", f"limit={min(limit, 1000)}"]
                if start_time_ms:
                    params.append(f"startTime={start_time_ms}")
                if end_time_ms:
                    params.append(f"endTime={end_time_ms}")
                endpoint = f"{SPOT_BASE}/api/v3/klines?{'&'.join(params)}"
                try:
                    status, raw, payload = await _fetch_json(http, endpoint)
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
                        continue
                    fetched += len(payload)
                    prov_hash = hash_payload(raw)
                    for row in parse_klines(pair, interval, payload):
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
                    logger.exception("Binance OHLCV ingest failed | %s %s", pair, interval)
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
    }


async def ingest_funding(
    session: AsyncSession,
    *,
    symbols: list[str] | None = None,
    limit: int = 100,
    triggered_by: str = "system",
) -> dict[str, Any]:
    source = await get_source_by_slug(session, "binance")
    if not source:
        raise RuntimeError("binance data source not seeded")
    symbols = symbols or list(DEFAULT_SYMBOLS)
    run_id = await create_ingestion_run(
        session,
        source_id=source["id"],
        run_type="funding",
        params={"symbols": symbols, "limit": limit},
        triggered_by=triggered_by,
    )
    fetched = inserted = deduped = errors = 0
    timeout = aiohttp.ClientTimeout(total=60)
    async with aiohttp.ClientSession(timeout=timeout, headers=_client_headers()) as http:
        for symbol in symbols:
            pair = symbol.upper()
            endpoint = f"{FUTURES_BASE}/fapi/v1/fundingRate?symbol={pair}&limit={min(limit, 1000)}"
            try:
                status, raw, payload = await _fetch_json(http, endpoint)
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
                    continue
                fetched += len(payload)
                for row in parse_funding(pair, payload):
                    record_id = await insert_funding_row(
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
                            target_table="de_funding_rates",
                            target_record_id=record_id,
                            source_endpoint=endpoint,
                            raw_body=raw,
                            response_status=status,
                        )
                    else:
                        deduped += 1
            except Exception as exc:
                errors += 1
                logger.exception("Binance funding ingest failed | %s", pair)
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
    return {"run_id": str(run_id), "status": status, "records_inserted": inserted}


async def ingest_open_interest(
    session: AsyncSession,
    *,
    symbols: list[str] | None = None,
    period: str = "1h",
    limit: int = 100,
    triggered_by: str = "system",
) -> dict[str, Any]:
    source = await get_source_by_slug(session, "binance")
    if not source:
        raise RuntimeError("binance data source not seeded")
    symbols = symbols or list(DEFAULT_SYMBOLS)
    run_id = await create_ingestion_run(
        session,
        source_id=source["id"],
        run_type="open_interest",
        params={"symbols": symbols, "period": period, "limit": limit},
        triggered_by=triggered_by,
    )
    fetched = inserted = deduped = errors = 0
    timeout = aiohttp.ClientTimeout(total=60)
    async with aiohttp.ClientSession(timeout=timeout, headers=_client_headers()) as http:
        for symbol in symbols:
            pair = symbol.upper()
            endpoint = (
                f"{FUTURES_BASE}/futures/data/openInterestHist"
                f"?symbol={pair}&period={period}&limit={min(limit, 500)}"
            )
            try:
                status, raw, payload = await _fetch_json(http, endpoint)
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
                    continue
                fetched += len(payload)
                for row in parse_open_interest_hist(pair, payload):
                    record_id = await insert_open_interest_row(
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
                            target_table="open_interest",
                            target_record_id=record_id,
                            source_endpoint=endpoint,
                            raw_body=raw,
                            response_status=status,
                        )
                    else:
                        deduped += 1
            except Exception as exc:
                errors += 1
                logger.exception("Binance OI ingest failed | %s", pair)
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
    return {"run_id": str(run_id), "status": status, "records_inserted": inserted}
