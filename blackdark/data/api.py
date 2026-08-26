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


@router.get("/api/v1/data/provenance-lineage/status")
async def provenance_lineage_status_route():
    """#1003 Data Provenance & Lineage Layer — cross-cutting mandatory infrastructure."""
    from blackdark.data.provenance_lineage import provenance_lineage_status

    return provenance_lineage_status()


@router.get("/api/v1/data/provenance-lineage/metrics")
async def provenance_lineage_metrics_route():
    from blackdark.data.provenance_lineage import list_registered_metrics

    return list_registered_metrics()


@router.get("/api/v1/data/provenance-lineage/lineage/{metric_id}")
async def provenance_lineage_detail_route(metric_id: str):
    from blackdark.data.provenance_lineage import get_metric_lineage

    result = get_metric_lineage(metric_id)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/api/v1/data/provenance-lineage/audit/{metric_id}")
async def provenance_lineage_audit_route(metric_id: str):
    """#1003 Audit API — programmatic lineage for third-party verification."""
    from blackdark.data.provenance_lineage import audit_lineage

    result = audit_lineage(metric_id)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/api/v1/data/provenance-lineage/recompute/{metric_id}")
async def provenance_lineage_recompute_route(
    metric_id: str,
    schema_version: str | None = Query(None),
    transformation_version: str | None = Query(None),
):
    from blackdark.data.provenance_lineage import recompute_historical

    result = recompute_historical(
        metric_id,
        as_of_schema_version=schema_version,
        as_of_transformation_version=transformation_version,
    )
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


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
        from blackdark.data.order_book_liquidity import order_book_liquidity_status

        status["order_book_liquidity_269"] = {
            "merged": True,
            "standalone": False,
            "dashboard_deferred": "Sprint 2",
            "summary": order_book_liquidity_status(),
        }
        from blackdark.data.spot_metrics_venue_quality import spot_metrics_status

        status["spot_metrics_295"] = {
            "merged": True,
            "standalone": False,
            "dashboard_deferred": "Sprint 2",
            "summary": spot_metrics_status(),
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


@router.get("/api/v1/data/instrument-master/derivatives-contracts")
async def list_derivatives_contract_mappings_route(limit: int = Query(50, ge=1, le=500)):
    """#325 Derivatives Asset Class Expansion — absorbed into #268 Instrument Master."""
    from blackdark.data.instrument_master import list_derivatives_contract_mappings

    return list_derivatives_contract_mappings(limit=limit)


@router.get("/api/v1/data/order-book-liquidity/status")
async def get_order_book_liquidity_status():
    """#269 Order Book & Liquidity Data Layer — no standalone, no UI."""
    from blackdark.data.order_book_liquidity import order_book_liquidity_status

    return order_book_liquidity_status()


@router.get("/api/v1/data/order-book-liquidity/gaps")
async def list_order_book_gaps_route(
    venue: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
):
    from blackdark.data.order_book_liquidity import list_gaps

    return list_gaps(venue=venue, limit=limit)


@router.get("/api/v1/data/order-book-liquidity/replay-tests")
async def list_replay_tests_route(
    passed_only: bool = Query(False),
    limit: int = Query(50, ge=1, le=200),
):
    from blackdark.data.order_book_liquidity import list_replay_tests

    return list_replay_tests(passed_only=passed_only, limit=limit)


@router.get("/api/v1/data/order-book-liquidity/sequence-gaps")
async def list_sequence_gaps_route(
    venue: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
):
    """#277 sequence gap detection — L2/L3 order book update integrity."""
    from blackdark.data.order_book_liquidity import list_sequence_gaps

    return list_sequence_gaps(venue=venue, limit=limit)


@router.get("/api/v1/data/order-book-liquidity/sequence-replay-tests")
async def list_sequence_replay_tests_route(
    passed_only: bool = Query(False),
    limit: int = Query(50, ge=1, le=200),
):
    """#277 sequence replay QA — daily batch."""
    from blackdark.data.order_book_liquidity import list_sequence_replay_tests

    return list_sequence_replay_tests(passed_only=passed_only, limit=limit)


@router.get("/api/v1/data/order-book-liquidity/market-depth")
async def market_depth_panel_route(
    pair: str = Query("BTC/USDT"),
    venue: str | None = Query(None),
):
    """#277 market depth panel — depth/spread/imbalance/slippage, heatmap deferred."""
    from blackdark.data.order_book_liquidity import build_market_depth_panel

    result = build_market_depth_panel(pair=pair, venue=venue)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/api/v1/data/spot-metrics/status")
async def spot_metrics_status_route():
    """#295 Spot Metrics & Venue Quality Layer — #294 absorbed, no separate pipeline."""
    from blackdark.data.spot_metrics_venue_quality import spot_metrics_status

    return spot_metrics_status()


@router.get("/api/v1/data/spot-metrics")
async def spot_metrics_panel_route(symbol: str = Query("BTC/USDT")):
    """#295 spot metrics panel — cross-venue aggregation, outlier/stale filtered."""
    from blackdark.data.spot_metrics_venue_quality import build_spot_metrics_panel

    result = build_spot_metrics_panel(symbol)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/api/v1/data/venue-quality/rankings")
async def venue_quality_rankings_route(limit: int = Query(50, ge=1, le=50)):
    """#295 venue quality rankings — top 50 venues, documented quality scores."""
    from blackdark.data.spot_metrics_venue_quality import list_venue_quality_rankings

    return list_venue_quality_rankings(limit=limit)


@router.get("/api/v1/data/liquidity-intelligence/status")
async def liquidity_intelligence_status_route():
    """#280 Liquidity Intelligence Engine — absorbs #277+#278+#279, layer not dashboard."""
    from blackdark.data.liquidity_intelligence_engine import liquidity_intelligence_status

    return liquidity_intelligence_status()


@router.get("/api/v1/data/liquidity-intelligence/panel")
async def liquidity_intelligence_panel_route(
    pair: str = Query("BTC/USDT"),
    venue: str | None = Query(None),
):
    """#280 Order Book Intelligence panel — depth, imbalance, warnings, UI deferred."""
    from blackdark.data.liquidity_intelligence_engine import build_intelligence_panel

    result = build_intelligence_panel(pair=pair, venue=venue)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/api/v1/data/liquidity-intelligence/warnings")
async def liquidity_intelligence_warnings_route(
    pair: str | None = Query(None),
    severity: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
):
    """#280 liquidity warnings — backend output for asset page / Screener."""
    from blackdark.data.liquidity_intelligence_engine import list_liquidity_warnings

    return list_liquidity_warnings(pair=pair, severity=severity, limit=limit)


@router.get("/api/v1/data/historical-vault/status")
async def historical_data_vault_status_route():
    """#738 Historical Data Vault — Sprint 0 infrastructure."""
    from blackdark.data.historical_data_vault import historical_data_vault_status

    return historical_data_vault_status()


@router.get("/api/v1/data/historical-vault/datasets/{dataset_id}")
async def historical_data_vault_dataset_route(
    dataset_id: str,
    version: int | None = Query(None),
):
    """#738 versioned dataset with SHA-256 checksum."""
    from blackdark.data.historical_data_vault import get_dataset

    result = get_dataset(dataset_id, version=version)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/api/v1/data/historical-vault/query/{query_id}")
async def historical_data_vault_query_route(
    query_id: str,
    as_of_date: str | None = Query(None),
    tier: str = Query("free"),
):
    """#738 reproducible historical query."""
    from blackdark.data.historical_data_vault import run_reproducible_query

    result = run_reproducible_query(query_id, as_of_date=as_of_date, tier=tier)  # type: ignore[arg-type]
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "not_found")
    return result


@router.get("/api/v1/data/market-pairs/status")
async def get_market_pair_view_status():
    """#270 archived — frontend requirement for Market Radar Sprint 2."""
    from blackdark.data.market_pair_view import market_pair_view_status

    return market_pair_view_status()


@router.get("/api/v1/data/market-pairs")
async def list_market_pairs_route(
    base: str | None = Query(None),
    venue: str | None = Query(None),
    include_stale: bool = Query(True),
    limit: int = Query(50, ge=1, le=200),
):
    """#270 pair view over #268 — no separate pipeline."""
    from blackdark.data.market_pair_view import list_pair_views

    return list_pair_views(
        base=base,
        venue=venue,
        include_stale=include_stale,
        limit=limit,
    )


@router.get("/api/v1/data/market-pairs/compare/{base}")
async def compare_market_pairs_route(
    base: str,
    quote: str = Query("USDT"),
):
    from blackdark.data.market_pair_view import compare_pairs_across_venues

    return compare_pairs_across_venues(base, quote=quote)


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
