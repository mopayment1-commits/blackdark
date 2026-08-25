"""FastAPI routes for Wave 01 data engine."""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from blackdark.data.db import data_engine_available, get_session
from blackdark.data.ingestors.binance import ingest_funding, ingest_ohlcv, ingest_open_interest
from blackdark.data.ingestors.coingecko import ingest_markets
from blackdark.data.provenance import get_provenance_by_record
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
):
    _require_postgres()
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
    return {"symbol": symbol.upper(), "interval": interval, "count": len(rows), "data": rows}


@router.get("/api/v1/data/funding")
async def get_funding(
    symbol: str = Query(...),
    start_time: str | None = None,
    end_time: str | None = None,
    limit: int = Query(100, ge=1, le=1000),
    source: str | None = None,
):
    _require_postgres()
    async with get_session() as session:
        rows = await query_funding(
            session,
            symbol=symbol,
            start_time=_parse_dt(start_time),
            end_time=_parse_dt(end_time),
            limit=limit,
            source_slug=source,
        )
    return {"symbol": symbol.upper(), "count": len(rows), "data": rows}


@router.get("/api/v1/data/open-interest")
async def get_open_interest(
    symbol: str = Query(...),
    start_time: str | None = None,
    end_time: str | None = None,
    limit: int = Query(100, ge=1, le=1000),
    source: str | None = None,
):
    _require_postgres()
    async with get_session() as session:
        rows = await query_open_interest(
            session,
            symbol=symbol,
            start_time=_parse_dt(start_time),
            end_time=_parse_dt(end_time),
            limit=limit,
            source_slug=source,
        )
    return {"symbol": symbol.upper(), "count": len(rows), "data": rows}


@router.get("/api/v1/data/provenance/{record_id}")
async def get_provenance(record_id: UUID):
    _require_postgres()
    async with get_session() as session:
        row = await get_provenance_by_record(session, record_id)
    if not row:
        raise HTTPException(status_code=404, detail="provenance record not found")
    return row


@router.get("/api/v1/data/status")
async def get_data_status():
    _require_postgres()
    async with get_session() as session:
        status = await data_engine_status(session)
    try:
        from blackdark.data.instrument_master import instrument_master_status

        status["instrument_master_268"] = {
            "merged": True,
            "standalone": False,
            "summary": instrument_master_status(),
        }
    except Exception:
        logger.debug("instrument master status enrich failed", exc_info=True)
    return status


@router.get("/api/v1/data/instrument-master/status")
async def get_instrument_master_status():
    """#268 Instrument Master merged into Wave 01 Data Engine — no standalone."""
    from blackdark.data.instrument_master import instrument_master_status

    return instrument_master_status()


@router.get("/api/v1/data/instrument-master/mappings")
async def list_instrument_mappings_route(
    tier: str | None = Query(None, description="hot | warm | cold"),
    asset_class: str | None = Query(None, description="spot | perp | option"),
    venue_type: str | None = Query(None, description="CEX | DEX | Derivatives"),
    limit: int = Query(50, ge=1, le=500),
):
    from blackdark.data.instrument_master import list_instrument_mappings

    return list_instrument_mappings(
        tier=tier,  # type: ignore[arg-type]
        asset_class=asset_class,  # type: ignore[arg-type]
        venue_type=venue_type,  # type: ignore[arg-type]
        limit=limit,
    )


@router.get("/api/v1/data/instrument-master/mappings/{instrument_id}")
async def get_instrument_mapping_route(instrument_id: str):
    from blackdark.data.instrument_master import get_instrument_mapping

    result = get_instrument_mapping(instrument_id)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.post("/api/v1/data/ingest", status_code=202)
async def trigger_ingest(body: IngestRequest, _: None = Depends(require_admin)):
    _require_postgres()

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
):
    _require_postgres()
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
    return {"count": len(events), "events": events}


@admin_router.post("/seed-sources")
async def seed_sources(_: None = Depends(require_admin)):
    _require_postgres()
    async with get_session() as session:
        result = await seed_data_sources(session)
    return {"ok": True, **result}
