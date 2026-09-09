"""Data Governance API routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, Query, Request

from api.openapi_responses import COMMON_ERROR_RESPONSES
from data_governance.decision_surface import build_decision_surface
from data_governance.observability import observability_dashboard
from data_governance.pipeline import data_governance_status, evaluate_data_governance
from data_governance.registry import canonical_source_registry, registry_summary
from i18n_service import resolve_request_lang

router = APIRouter(prefix="/api/data-governance", tags=["data-governance"], responses=COMMON_ERROR_RESPONSES)


@router.post("/evaluate")
async def data_governance_evaluate(
    request: Request,
    payload: dict[str, Any] = Body(default={}),
) -> dict[str, Any]:
    lang = resolve_request_lang(request)
    symbol = str(payload.get("symbol") or payload.get("asset") or "BTC")
    result = evaluate_data_governance(payload, symbol=symbol, lang=lang)
    return {"ok": True, "data_governance_state": result.get("data_governance_state"), "payload": result}


@router.get("/status")
async def data_governance_system_status() -> dict[str, Any]:
    return {"ok": True, **data_governance_status()}


@router.get("/registry")
async def data_governance_registry(limit: int = Query(50, ge=1, le=200)) -> dict[str, Any]:
    entries = canonical_source_registry()[:limit]
    return {
        "ok": True,
        "summary": registry_summary(),
        "sources": [
            {
                "source_id": e.source_id,
                "provider_name": e.provider_name,
                "source_class": e.source_class.value,
                "tier": e.tier.value,
                "l1": e.l1,
                "l2": e.l2,
                "l3": e.l3,
                "auth_model": e.auth_model,
            }
            for e in entries
        ],
    }


@router.get("/observability")
async def data_governance_observability() -> dict[str, Any]:
    return {"ok": True, **observability_dashboard()}


@router.post("/decision-surface")
async def data_governance_decision_surface(
    request: Request,
    payload: dict[str, Any] = Body(default={}),
) -> dict[str, Any]:
    lang = resolve_request_lang(request)
    enriched = evaluate_data_governance(payload, lang=lang)
    return {"ok": True, "surface": build_decision_surface(enriched, lang=lang)}
