"""Observability + due diligence API router."""

from __future__ import annotations

from fastapi import APIRouter, Response

router = APIRouter(tags=["observability"])


@router.get("/metrics")
async def prometheus_metrics():
    from observability import prometheus_metrics_text

    return Response(content=prometheus_metrics_text(), media_type="text/plain; version=0.0.4")


@router.get("/api/observability/status")
async def observability_status_api():
    from observability import observability_status

    return observability_status()


@router.get("/api/due-diligence/bundle")
async def due_diligence_bundle():
    from due_diligence_bundle import build_full_due_diligence_bundle

    return await build_full_due_diligence_bundle()


@router.get("/api/due-diligence/technical")
async def technical_due_diligence_api(probe_production: bool = True):
    from technical_due_diligence import build_technical_due_diligence_report

    return await build_technical_due_diligence_report(probe_production=probe_production)


@router.get("/api/diagnostics/price/{symbol}")
async def price_source_diagnostics(symbol: str):
    from market_context import probe_price_sources

    return await probe_price_sources(symbol)
