"""FastAPI routes for Wave 01 data engine."""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from blackdark.data.db import data_engine_available, ensure_data_engine_ready, get_session
from blackdark.data.ingestors.binance import ingest_funding, ingest_ohlcv, ingest_open_interest
from blackdark.data.ingestors.coingecko import ingest_markets
from blackdark.data.institutional import wave_01_institutional_status
from blackdark.data.circuit_breaker import is_open as circuit_is_open
from blackdark.data.provenance import get_provenance_by_record
from blackdark.data.response_metadata import dataset_response
from blackdark.data.repository import (
    data_engine_status,
    query_events,
    query_funding,
    query_ohlcv,
    query_open_interest,
    seed_data_sources,
)
from security_auth import require_admin

logger = logging.getLogger("BLACKDARK.DataEngine.API")

WAVE_01_VERSION = "1.0.0"

router = APIRouter(tags=["data-engine-v1"])
admin_router = APIRouter(prefix="/api/v1/admin", tags=["data-engine-admin"])


def _require_postgres() -> None:
    if not data_engine_available():
        raise HTTPException(
            status_code=503,
            detail="Wave 01 data engine requires PostgreSQL (DATABASE_URL=postgresql://...).",
        )


async def _ensure_ready() -> None:
    _require_postgres()
    try:
        await ensure_data_engine_ready()
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("data engine ensure failed")
        raise HTTPException(status_code=503, detail=f"data engine migration failed: {exc}") from exc


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid datetime: {value}") from exc


class IngestRequest(BaseModel):
    source: str
    symbols: list[str] = Field(default_factory=lambda: ["BTCUSDT"])
    intervals: list[str] = Field(default_factory=lambda: ["1h"])
    backfill_days: int = 1


class IngestResponse(BaseModel):
    run_id: str
    status: str
    estimated_records: int


async def _run_ingest_job(body: IngestRequest, triggered_by: str) -> dict[str, Any]:
    async with get_session() as session:
        if body.source == "binance":
            ohlcv = await ingest_ohlcv(
                session,
                symbols=body.symbols,
                intervals=body.intervals,
                limit=min(body.backfill_days * 24, 1000),
                triggered_by=triggered_by,
            )
            funding = await ingest_funding(session, symbols=body.symbols, triggered_by=triggered_by)
            oi = await ingest_open_interest(session, symbols=body.symbols, triggered_by=triggered_by)
            estimated = int(ohlcv.get("records_inserted", 0)) + int(
                funding.get("records_inserted", 0)
            ) + int(oi.get("records_inserted", 0))
            return {
                "run_id": ohlcv.get("run_id", ""),
                "status": "completed",
                "estimated_records": estimated,
            }
        if body.source == "coingecko":
            result = await ingest_markets(session, triggered_by=triggered_by)
            return {
                "run_id": result.get("run_id", ""),
                "status": result.get("status", "completed"),
                "estimated_records": int(result.get("records_inserted", 0)),
            }
        raise RuntimeError(f"Unsupported source: {body.source}")


@router.get("/api/v1/data/ohlcv")
async def get_ohlcv(
    symbol: str = Query(...),
    interval: str = Query(...),
    start_time: str | None = None,
    end_time: str | None = None,
    limit: int = Query(100, ge=1, le=1000),
    source: str | None = None,
    _: None = Depends(_ensure_ready),
):
    source_slug = source or "kraken"
    async with get_session() as session:
        rows = await query_ohlcv(
            session,
            symbol=symbol,
            interval=interval,
            start_time=_parse_dt(start_time),
            end_time=_parse_dt(end_time),
            limit=limit,
            source_slug=source,
        )
    upstream_unknown = not rows and circuit_is_open(source_slug)
    return dataset_response(
        count=len(rows),
        data=rows,
        dataset="ohlcv",
        symbol=symbol,
        interval=interval,
        latest_record_at=rows[0]["open_time"] if rows else None,
        upstream_unknown=upstream_unknown,
    )


@router.get("/api/v1/data/funding")
async def get_funding(
    symbol: str = Query(...),
    start_time: str | None = None,
    end_time: str | None = None,
    limit: int = Query(100, ge=1, le=1000),
    source: str | None = None,
    _: None = Depends(_ensure_ready),
):
    try:
        async with get_session() as session:
            rows = await query_funding(
                session,
                symbol=symbol,
                start_time=_parse_dt(start_time),
                end_time=_parse_dt(end_time),
                limit=limit,
                source_slug=source,
            )
    except Exception as exc:
        logger.exception("funding query failed")
        raise HTTPException(status_code=503, detail=f"funding query failed: {exc}") from exc
    return dataset_response(count=len(rows), data=rows, dataset="funding_rates", symbol=symbol)


@router.get("/api/v1/data/open-interest")
async def get_open_interest(
    symbol: str = Query(...),
    start_time: str | None = None,
    end_time: str | None = None,
    limit: int = Query(100, ge=1, le=1000),
    source: str | None = None,
    _: None = Depends(_ensure_ready),
):
    async with get_session() as session:
        rows = await query_open_interest(
            session,
            symbol=symbol,
            start_time=_parse_dt(start_time),
            end_time=_parse_dt(end_time),
            limit=limit,
            source_slug=source,
        )
    return dataset_response(count=len(rows), data=rows, dataset="open_interest", symbol=symbol)


@router.get("/api/v1/data/provenance/{record_id}")
async def get_provenance(record_id: UUID, _: None = Depends(_ensure_ready)):
    async with get_session() as session:
        row = await get_provenance_by_record(session, record_id)
    if not row:
        raise HTTPException(status_code=404, detail="provenance record not found")
    return row


@router.get("/api/v1/data/wave-01")
async def get_wave_01_institutional(_: None = Depends(_ensure_ready)):
    async with get_session() as session:
        return await wave_01_institutional_status(session)


@router.get("/api/v1/data/status")
async def get_data_status(_: None = Depends(_ensure_ready)):
    try:
        async with get_session() as session:
            return await data_engine_status(session)
    except Exception as exc:
        logger.exception("data status failed")
        raise HTTPException(status_code=503, detail=f"data engine unavailable: {exc}") from exc


@router.post("/api/v1/data/ingest", status_code=202)
async def trigger_ingest(body: IngestRequest, _: None = Depends(require_admin), __: None = Depends(_ensure_ready)):

    async def _bg() -> None:
        try:
            await _run_ingest_job(body, triggered_by="api:ingest")
        except Exception:
            logger.exception("Background ingest failed")

    asyncio.create_task(_bg())
    estimated = len(body.symbols) * len(body.intervals) * body.backfill_days * 24
    return IngestResponse(run_id="queued", status="queued", estimated_records=estimated)


@router.get("/api/v1/data/events")
async def get_events(
    event_type: str | None = None,
    severity: str | None = None,
    symbol: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    limit: int = Query(100, ge=1, le=1000),
    _: None = Depends(_ensure_ready),
):
    async with get_session() as session:
        events = await query_events(
            session,
            event_type=event_type,
            severity=severity,
            symbol=symbol,
            start_time=_parse_dt(start_time),
            end_time=_parse_dt(end_time),
            limit=limit,
        )
    return dataset_response(count=len(events), data=events, dataset="events", extra={"events": events})


@admin_router.post("/seed-sources")
async def seed_sources(_: None = Depends(require_admin), __: None = Depends(_ensure_ready)):
    async with get_session() as session:
        result = await seed_data_sources(session)
    return {"ok": True, **result}


@admin_router.post("/migrate-data-engine")
async def migrate_data_engine(_: None = Depends(require_admin)):
    _require_postgres()
    from blackdark.data.db import init_data_engine

    result = await init_data_engine()
    return result


@admin_router.post("/bootstrap-ingest")
async def bootstrap_ingest(_: None = Depends(require_admin), __: None = Depends(_ensure_ready)):
    from blackdark.data.jobs import run_bootstrap_ingest_once
    from blackdark.data.repository import count_ohlcv_rows

    async with get_session() as session:
        if await count_ohlcv_rows(session) > 0:
            return {"ok": True, "skipped": True, "reason": "ohlcv_data_not_empty"}
    return await run_bootstrap_ingest_once()
