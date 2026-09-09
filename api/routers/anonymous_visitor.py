"""Anonymous Visitor & Public Intelligence API routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, Query, Request

from anonymous_visitor.account_gate import account_gate_status, evaluate_account_gate
from anonymous_visitor.allowlist import allowlist_export
from anonymous_visitor.analytics import analytics_status, record_public_analytics_event
from anonymous_visitor.consent import consent_status, update_consent
from anonymous_visitor.controls import av_control_matrix, evaluate_av_controls
from anonymous_visitor.evidence import collect_av_evidence
from anonymous_visitor.licensing import licensing_register_export
from anonymous_visitor.public_intelligence import (
    build_decision_truth_pulse,
    build_evidence_passport_summary,
    build_market_surface,
    build_methodology_page_payload,
    build_net_edge_proof,
    build_public_accuracy,
)
from anonymous_visitor.registry import registry_summary
from anonymous_visitor.seo import seo_policy_export, seo_policy_for_path
from anonymous_visitor.states import states_status
from anonymous_visitor.accessibility import accessibility_report
from api.openapi_responses import COMMON_ERROR_RESPONSES

router = APIRouter(prefix="/api/anonymous-visitor", tags=["anonymous-visitor"], responses=COMMON_ERROR_RESPONSES)


def _visitor_key(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for") or ""
    if forwarded:
        return forwarded.split(",")[0].strip()[:64]
    if request.client and request.client.host:
        return request.client.host[:64]
    return "anonymous"


@router.get("/status")
async def anonymous_visitor_status() -> dict[str, Any]:
    return {
        "ok": True,
        "product": "Anonymous Visitor & Public Intelligence",
        "auth_state": "ANONYMOUS",
        **registry_summary(),
    }


@router.get("/states")
async def anonymous_visitor_states() -> dict[str, Any]:
    return {"ok": True, **states_status()}


@router.get("/allowlist")
async def anonymous_visitor_allowlist() -> dict[str, Any]:
    return {"ok": True, "allowlist": allowlist_export(), "single_canonical_registry": True}


@router.get("/route-inventory")
async def anonymous_visitor_route_inventory(request: Request) -> dict[str, Any]:
    from anonymous_visitor.inventory import audit_route_inventory

    app = request.app
    return {"ok": True, **audit_route_inventory(app, client=None)}


@router.get("/matrix")
async def anonymous_visitor_matrix(head: str | None = Query(None)) -> dict[str, Any]:
    return {"ok": True, "matrix": av_control_matrix(head=head)}


@router.get("/evidence")
async def anonymous_visitor_evidence(head: str | None = Query(None)) -> dict[str, Any]:
    return {"ok": True, **collect_av_evidence(head=head)}


@router.get("/licensing/register")
async def anonymous_visitor_licensing_register() -> dict[str, Any]:
    return {"ok": True, "sources": licensing_register_export()}


@router.get("/public-intelligence/decision-truth-pulse")
async def public_decision_truth_pulse(symbol: str = Query("BTC")) -> dict[str, Any]:
    return await build_decision_truth_pulse(symbol=symbol)


@router.get("/public-intelligence/evidence-passport")
async def public_evidence_passport() -> dict[str, Any]:
    return await build_evidence_passport_summary()


@router.get("/public-intelligence/net-edge-proof")
async def public_net_edge_proof(symbol: str = Query("BTC")) -> dict[str, Any]:
    return await build_net_edge_proof(symbol=symbol)


@router.get("/public-intelligence/market-surface")
async def public_market_surface() -> dict[str, Any]:
    return await build_market_surface()


@router.get("/public-intelligence/accuracy")
async def public_accuracy() -> dict[str, Any]:
    return await build_public_accuracy()


@router.get("/public-intelligence/methodology")
async def public_methodology() -> dict[str, Any]:
    return build_methodology_page_payload()


@router.get("/consent/status")
async def public_consent_status(request: Request) -> dict[str, Any]:
    return consent_status(visitor_key=_visitor_key(request))


@router.post("/consent")
async def public_consent_update(request: Request, payload: dict[str, Any] = Body(default={})) -> dict[str, Any]:
    return update_consent(visitor_key=_visitor_key(request), payload=payload)


@router.post("/analytics/event")
async def public_analytics_event(request: Request, payload: dict[str, Any] = Body(default={})) -> dict[str, Any]:
    return record_public_analytics_event(
        visitor_key=_visitor_key(request),
        event=str(payload.get("event") or ""),
        metadata=payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {},
    )


@router.get("/analytics/status")
async def public_analytics_status() -> dict[str, Any]:
    return {"ok": True, **analytics_status()}


@router.get("/account-gate/status")
async def public_account_gate_status() -> dict[str, Any]:
    return {"ok": True, **account_gate_status()}


@router.post("/account-gate/evaluate")
async def public_account_gate_evaluate(payload: dict[str, Any] = Body(default={})) -> dict[str, Any]:
    return evaluate_account_gate(str(payload.get("action") or ""), auth_state=str(payload.get("auth_state") or "ANONYMOUS"))


@router.get("/seo/policy")
async def public_seo_policy(path: str = Query("/")) -> dict[str, Any]:
    return {"ok": True, "policy": seo_policy_for_path(path), "catalog": seo_policy_export()}


@router.get("/accessibility/report")
async def public_accessibility_report() -> dict[str, Any]:
    return {"ok": True, **accessibility_report()}


@router.get("/evaluate")
async def anonymous_visitor_evaluate(head: str | None = Query(None)) -> dict[str, Any]:
    return {"ok": True, "evaluation": evaluate_av_controls(head=head)}
