"""Data Governance API routes."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Body, Query, Request

from api.openapi_responses import COMMON_ERROR_RESPONSES
from data_governance.decision_surface import build_decision_surface
from data_governance.observability import observability_dashboard
from data_governance.pipeline import data_governance_status, evaluate_data_governance
from data_governance.registry import canonical_source_registry, registry_summary
from i18n_service import resolve_request_lang
from log_safety import sanitize_log_value

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/data-governance", tags=["data-governance"], responses=COMMON_ERROR_RESPONSES)

_DG_EVALUATE_ERROR = "data_governance_evaluate_unavailable"
_DG_SURFACE_ERROR = "data_governance_surface_unavailable"


def _public_dg_payload(result: dict[str, Any]) -> dict[str, Any]:
    """Client-safe slice — no raw exception text from governance pipeline."""
    return {
        "data_governance_state": result.get("data_governance_state"),
        "data_governance_failed_gates": result.get("data_governance_failed_gates"),
        "data_governance": result.get("data_governance"),
        "todays_decision_surface": result.get("todays_decision_surface"),
        "user_facing_provenance": result.get("user_facing_provenance"),
        "raw_evidence_id": result.get("raw_evidence_id"),
    }


@router.post("/evaluate")
async def data_governance_evaluate(
    request: Request,
    payload: dict[str, Any] = Body(default={}),
) -> dict[str, Any]:
    lang = resolve_request_lang(request)
    symbol = str(payload.get("symbol") or payload.get("asset") or "BTC")
    try:
        result = evaluate_data_governance(payload, symbol=symbol, lang=lang)
    except Exception as exc:
        logger.warning(
            "data_governance_evaluate failed symbol=%s detail=%s",
            sanitize_log_value(symbol, field_name="symbol").replace("\r", " ").replace("\n", " "),
            sanitize_log_value(exc).replace("\r", " ").replace("\n", " "),
        )
        return {
            "ok": False,
            "error": _DG_EVALUATE_ERROR,
            "message": "Data governance evaluation is temporarily unavailable.",
        }
    return {
        "ok": True,
        "data_governance_state": result.get("data_governance_state"),
        "payload": _public_dg_payload(result),
    }


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
    try:
        enriched = evaluate_data_governance(payload, lang=lang)
        surface = build_decision_surface(enriched, lang=lang)
    except Exception as exc:
        logger.warning(
            "data_governance_decision_surface failed detail=%s",
            sanitize_log_value(exc),
        )
        return {
            "ok": False,
            "error": _DG_SURFACE_ERROR,
            "message": "Decision surface is temporarily unavailable.",
        }
    return {"ok": True, "surface": surface}
