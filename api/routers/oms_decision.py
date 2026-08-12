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


class OmsSubmitBody(BaseModel):
    actor: str = "api"
    dry_run: bool = True


@router.post("/oms/orders/{order_id}/submit")
async def oms_submit_venue(
    order_id: str,
    body: OmsSubmitBody,
    _: Annotated[dict, Depends(require_institutional_principal)],
) -> dict[str, Any]:
    import oms

    try:
        return await oms.submit_to_venue(order_id, actor=body.actor, dry_run=body.dry_run)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


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


class DecisionEvaluateBody(BaseModel):
    market_state: dict[str, Any]
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    contradictions: list[dict[str, Any]] = Field(default_factory=list)
    hypothesis: dict[str, Any] = Field(default_factory=dict)
    decision: dict[str, Any] = Field(default_factory=dict)
    risk_reports: list[dict[str, Any]] = Field(default_factory=list)
    confidence: float | dict[str, Any] | None = None
    actor: str = "api"


@router.post("/decision-intelligence/evaluate")
async def decision_intel_evaluate(
    body: DecisionEvaluateBody,
    _: Annotated[dict, Depends(require_institutional_principal)],
) -> dict[str, Any]:
    from decision_intelligence_engine import evaluate_decision

    try:
        return evaluate_decision(
            market_state=body.market_state,
            evidence=body.evidence,
            contradictions=body.contradictions,
            hypothesis=body.hypothesis or {"text": "unspecified"},
            decision=body.decision or {"action": "hold", "wants_action": False},
            risk_reports=body.risk_reports,
            confidence=body.confidence,
            actor=body.actor,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


class DecisionCloseLoopBody(BaseModel):
    graph_id: str
    decision_node_id: str
    predicted: dict[str, Any]
    actual: dict[str, Any]
    decision_ts: str
    outcome_ts: str
    actor: str = "api"


@router.post("/decision-intelligence/close-loop")
async def decision_intel_close_loop(
    body: DecisionCloseLoopBody,
    _: Annotated[dict, Depends(require_institutional_principal)],
) -> dict[str, Any]:
    from decision_intelligence_engine import close_decision_loop

    try:
        return close_decision_loop(
            graph_id=body.graph_id,
            decision_node_id=body.decision_node_id,
            predicted=body.predicted,
            actual=body.actual,
            decision_ts=body.decision_ts,
            outcome_ts=body.outcome_ts,
            actor=body.actor,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/super-terminal")
async def super_terminal_api(
    _: Annotated[dict, Depends(require_institutional_principal)],
    symbol: str = "BTC/USDT",
    org_id: str = "default",
) -> dict[str, Any]:
    from super_terminal import build_super_terminal

    return build_super_terminal(symbol=symbol, org_id=org_id)


class PortfolioAnalyzeBody(BaseModel):
    positions: list[dict[str, Any]] = Field(default_factory=list)


@router.post("/portfolio/analyze")
async def portfolio_analyze_api(
    body: PortfolioAnalyzeBody,
    _: Annotated[dict, Depends(require_institutional_principal)],
) -> dict[str, Any]:
    from portfolio_intelligence import analyze_portfolio

    return analyze_portfolio(body.positions)


@router.get("/portfolio/status")
async def portfolio_status_api(
    _: Annotated[dict, Depends(require_institutional_principal)],
) -> dict[str, Any]:
    from portfolio_intelligence import portfolio_status

    return portfolio_status()


@router.get("/risk/status")
async def risk_status_api(
    _: Annotated[dict, Depends(require_institutional_principal)],
) -> dict[str, Any]:
    from risk_intelligence import risk_intelligence_status

    return risk_intelligence_status()


class RiskAggregateBody(BaseModel):
    reports: list[dict[str, Any]] = Field(default_factory=list)


@router.post("/risk/aggregate")
async def risk_aggregate_api(
    body: RiskAggregateBody,
    _: Annotated[dict, Depends(require_institutional_principal)],
) -> dict[str, Any]:
    from risk_intelligence import aggregate_risk_gate

    return aggregate_risk_gate(body.reports)


@router.get("/memory/query")
async def memory_query_api(
    _: Annotated[dict, Depends(require_institutional_principal)],
    kind: str | None = None,
    graph_id: str | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    from institutional_memory import memory_status, query

    return {"status": memory_status(), "rows": query(kind=kind, graph_id=graph_id, limit=limit)}


@router.get("/learning/status")
async def learning_status_api(
    _: Annotated[dict, Depends(require_institutional_principal)],
) -> dict[str, Any]:
    from continuous_learning import calibrate_from_history, learning_status

    return {**learning_status(), "calibration": calibrate_from_history(min_samples=30)}


class B2BReportBody(BaseModel):
    org_id: str
    title: str
    evidence_pack: dict[str, Any] = Field(default_factory=dict)
    actor: str = "api"


@router.post("/b2b/committee-report")
async def b2b_committee_report_api(
    body: B2BReportBody,
    _: Annotated[dict, Depends(require_institutional_principal)],
) -> dict[str, Any]:
    from b2b_institutional_ops import generate_committee_report

    return generate_committee_report(
        org_id=body.org_id,
        title=body.title,
        evidence_pack=body.evidence_pack,
        actor=body.actor,
    )


class B2BAlertBody(BaseModel):
    org_id: str
    severity: str
    channel: str
    message: str
    dedupe_key: str


@router.post("/b2b/alerts")
async def b2b_alert_api(
    body: B2BAlertBody,
    _: Annotated[dict, Depends(require_institutional_principal)],
) -> dict[str, Any]:
    from b2b_institutional_ops import orchestrate_alert

    try:
        return orchestrate_alert(
            org_id=body.org_id,
            severity=body.severity,
            channel=body.channel,
            message=body.message,
            dedupe_key=body.dedupe_key,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/b2b/status")
async def b2b_status_api(
    _: Annotated[dict, Depends(require_institutional_principal)],
) -> dict[str, Any]:
    from b2b_institutional_ops import b2b_status

    return b2b_status()


class OmsReconcileBody(BaseModel):
    actor: str = "api"
    venue_filled_qty: float | None = None
    venue_ack_id: str = ""


@router.post("/oms/orders/{order_id}/reconcile")
async def oms_reconcile_api(
    order_id: str,
    body: OmsReconcileBody,
    _: Annotated[dict, Depends(require_institutional_principal)],
) -> dict[str, Any]:
    import oms

    try:
        return oms.reconcile(
            order_id,
            actor=body.actor,
            venue_filled_qty=body.venue_filled_qty,
            venue_ack_id=body.venue_ack_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/canonical/status")
async def canonical_status_api(
    _: Annotated[dict, Depends(require_institutional_principal)],
) -> dict[str, Any]:
    from canonical_adoption import adoption_status
    from canonical_data_layer import layer_status
    from canonical_truth_bus import bus_status, refresh_live_truth
    from live_data_truth_probe import probe_binance_public_book, probe_status, prove_multi_venue_live
    from streaming_institutional import streaming_status

    live = await probe_binance_public_book("BTCUSDT")
    multi = await prove_multi_venue_live()
    bus = await refresh_live_truth()
    return {
        "canonical_data_layer": layer_status(),
        "canonical_adoption": adoption_status(),
        "streaming": streaming_status(),
        "live_public_probe": live,
        "live_multi_venue_proof": multi,
        "live_probe_status": probe_status(),
        "canonical_truth_bus": {**bus_status(), "refresh": bus},
    }


@router.post("/venue-fill-proof")
async def venue_fill_proof_api(
    _: Annotated[dict, Depends(require_institutional_principal)],
    org_id: str = "proof",
    prefer_testnet: bool = False,
) -> dict[str, Any]:
    from venue_fill_proof import prove_fill_lifecycle

    return await prove_fill_lifecycle(org_id=org_id, prefer_testnet=prefer_testnet)


@router.post("/decision-e2e")
async def decision_e2e_api(
    _: Annotated[dict, Depends(require_institutional_principal)],
    symbol: str = "BTC/USDT",
    org_id: str = "default",
    notional: float = 25_000.0,
) -> dict[str, Any]:
    from decision_e2e import run_decision_e2e

    return run_decision_e2e(symbol=symbol, org_id=org_id, notional=notional)


@router.get("/ops/recovery")
async def ops_recovery_api(
    _: Annotated[dict, Depends(require_institutional_principal)],
) -> dict[str, Any]:
    from ops_recovery import ops_status

    return ops_status()


@router.get("/store/status")
async def institutional_store_api(
    _: Annotated[dict, Depends(require_institutional_principal)],
) -> dict[str, Any]:
    from institutional_store import store_status

    return store_status()


@router.post("/ingestion/prove")
async def institutional_ingestion_prove_api(
    _: Annotated[dict, Depends(require_institutional_principal)],
    symbol: str = "BTC/USDT",
) -> dict[str, Any]:
    from institutional_ingestion_proof import prove_durable_ingestion

    return await prove_durable_ingestion(symbol=symbol)


@router.post("/ingestion/scheduler-prove")
async def institutional_scheduler_prove_api(
    _: Annotated[dict, Depends(require_institutional_principal)],
) -> dict[str, Any]:
    from institutional_scheduler_proof import prove_scheduler_continuum

    return await prove_scheduler_continuum()


@router.get("/jupiter/quote-proof")
async def jupiter_quote_proof_api(
    _: Annotated[dict, Depends(require_institutional_principal)],
) -> dict[str, Any]:
    from jupiter_dex_adapter import prove_jupiter_live_quote

    return await prove_jupiter_live_quote()


@router.post("/jupiter/submit-proof")
async def jupiter_submit_proof_api(
    _: Annotated[dict, Depends(require_institutional_principal)],
) -> dict[str, Any]:
    from jupiter_dex_adapter import prove_jupiter_submit_path

    return await prove_jupiter_submit_path()


class WhiteLabelBrandBody(BaseModel):
    product_name: str
    primary_color: str = "#0B1F33"
    logo_url: str = ""
    support_email: str = ""
    custom_domain: str = ""
    report_footer: str = ""
    api_title: str = ""


class WhiteLabelExportBody(BaseModel):
    payload: dict[str, Any] = Field(default_factory=dict)


@router.get("/orgs/{org_id}/brand")
async def white_label_get_brand_api(
    org_id: str,
    _: Annotated[dict, Depends(require_institutional_principal)],
) -> dict[str, Any]:
    from white_label import get_brand

    brand = get_brand(org_id)
    if not brand:
        raise HTTPException(status_code=404, detail="white_label_not_configured")
    return brand


@router.put("/orgs/{org_id}/brand")
async def white_label_put_brand_api(
    org_id: str,
    body: WhiteLabelBrandBody,
    _: Annotated[dict, Depends(require_institutional_principal)],
) -> dict[str, Any]:
    from white_label import configure_brand

    try:
        return configure_brand(
            org_id,
            product_name=body.product_name,
            primary_color=body.primary_color,
            logo_url=body.logo_url,
            support_email=body.support_email,
            custom_domain=body.custom_domain,
            report_footer=body.report_footer,
            api_title=body.api_title,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/orgs/{org_id}/brand/export")
async def white_label_export_api(
    org_id: str,
    body: WhiteLabelExportBody,
    _: Annotated[dict, Depends(require_institutional_principal)],
) -> dict[str, Any]:
    from white_label import apply_brand_to_surface, branded_report_export

    try:
        export = branded_report_export(org_id, body.payload or {})
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    surface = apply_brand_to_surface(org_id, {"surface": "export", "payload_keys": list((body.payload or {}).keys())})
    return {**export, "served_surface": surface}


@router.get("/white-label/status")
async def white_label_status_api(
    _: Annotated[dict, Depends(require_institutional_principal)],
) -> dict[str, Any]:
    from white_label import white_label_status

    return white_label_status()


@router.post("/white-label/prove")
async def white_label_prove_api(
    _: Annotated[dict, Depends(require_institutional_principal)],
    org_id: str = "wl_proof_org",
    product_name: str = "Desk Alpha",
) -> dict[str, Any]:
    from white_label import prove_white_label_surface

    return prove_white_label_surface(org_id, product_name=product_name)


@router.post("/ops/postgres-product-path")
async def postgres_product_path_api(
    _: Annotated[dict, Depends(require_institutional_principal)],
) -> dict[str, Any]:
    from ops_recovery import prove_postgres_product_path

    return await prove_postgres_product_path()


@router.post("/ops/postgres-ha-rpo-rto")
async def postgres_ha_rpo_rto_api(
    _: Annotated[dict, Depends(require_institutional_principal)],
) -> dict[str, Any]:
    from ops_recovery import prove_postgres_streaming_ha_rpo_rto

    return prove_postgres_streaming_ha_rpo_rto()
