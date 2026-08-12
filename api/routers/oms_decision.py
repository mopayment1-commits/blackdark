"""OMS + Decision Graph production API wiring."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from api.openapi_responses import COMMON_ERROR_RESPONSES
from api.routers.institutional import require_institutional_principal

router = APIRouter(
    prefix="/api/institutional",
    tags=["oms-decision"],
    responses=COMMON_ERROR_RESPONSES,
    dependencies=[Depends(require_institutional_principal)],
)


class OmsIntentBody(BaseModel):
    org_id: str
    venue: str
    symbol: str
    side: str
    quantity: float = Field(gt=0)
    order_type: str = "limit"
    limit_price: float | None = None
    idempotency_key: str
    actor: str = "api"


class OmsTransitionBody(BaseModel):
    new_state: str
    actor: str = "api"
    fill_qty: float = 0.0
    reason: str = ""
    venue_ack_id: str = ""


class DecisionBody(BaseModel):
    org_id: str = "default"
    symbol: str
    hypothesis: str
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    counter_evidence: list[dict[str, Any]] = Field(default_factory=list)
    action: str = "hold"
    confidence: float | None = None
    confidence_type: str = "heuristic_score"
    risk: dict[str, Any] = Field(default_factory=dict)
    execution_feasibility: dict[str, Any] = Field(default_factory=dict)
    invalidation: str = ""


@router.get("/oms/status")
async def oms_status_api(_: Annotated[dict, Depends(require_institutional_principal)]) -> dict[str, Any]:
    import oms

    return oms.oms_status()


@router.post("/oms/intents")
async def oms_create_intent(
    body: OmsIntentBody,
    _: Annotated[dict, Depends(require_institutional_principal)],
) -> dict[str, Any]:
    import oms

    try:
        return oms.create_intent(
            org_id=body.org_id,
            venue=body.venue,
            symbol=body.symbol,
            side=body.side,
            quantity=body.quantity,
            order_type=body.order_type,
            limit_price=body.limit_price,
            idempotency_key=body.idempotency_key,
            actor=body.actor,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/oms/orders/{order_id}/transition")
async def oms_transition(
    order_id: str,
    body: OmsTransitionBody,
    _: Annotated[dict, Depends(require_institutional_principal)],
) -> dict[str, Any]:
    import oms

    try:
        return oms.transition(
            order_id,
            body.new_state,
            actor=body.actor,
            fill_qty=body.fill_qty,
            reason=body.reason,
            venue_ack_id=body.venue_ack_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/oms/orders/{order_id}")
async def oms_get_order(
    order_id: str,
    _: Annotated[dict, Depends(require_institutional_principal)],
) -> dict[str, Any]:
    import oms

    row = oms.get_order(order_id)
    if not row:
        raise HTTPException(status_code=404, detail="order_not_found")
    return row


@router.get("/decision-graph/status")
async def decision_graph_status(
    _: Annotated[dict, Depends(require_institutional_principal)],
) -> dict[str, Any]:
    import decision_graph

    return decision_graph.graph_status()


@router.post("/decision-graph/decisions")
async def decision_graph_append(
    body: DecisionBody,
    _: Annotated[dict, Depends(require_institutional_principal)],
) -> dict[str, Any]:
    import decision_graph
    from confidence_truth import claim_heuristic, claim_insufficient

    if body.confidence is None:
        conf = claim_insufficient(label="decision_api").to_dict()
    else:
        conf = claim_heuristic(float(body.confidence), label=body.confidence_type).to_dict()
    return decision_graph.record_decision_bundle(
        market_state={"symbol": body.symbol, "org_id": body.org_id},
        evidence=body.evidence,
        contradictions=body.counter_evidence,
        hypothesis={"text": body.hypothesis},
        decision={"action": body.action, "invalidation": body.invalidation},
        risk=body.risk,
        execution_feasibility=body.execution_feasibility,
        action={"action": body.action},
        confidence=conf,
        actor="api",
    )


@router.get("/decision-intelligence/status")
async def decision_intel_status(
    _: Annotated[dict, Depends(require_institutional_principal)],
) -> dict[str, Any]:
    import decision_intelligence_engine

    return decision_intelligence_engine.engine_status()
