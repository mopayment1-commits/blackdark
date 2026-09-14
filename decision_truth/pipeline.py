"""Decision Truth Pipeline — delegates to canonical govern spine (P1)."""

from __future__ import annotations

from typing import Any

from decision_truth.contract import DecisionContract, DecisionState
from decision_truth.govern import govern_decision_payload, govern_stats

_PIPELINE_STATS = govern_stats()


def pipeline_status() -> dict[str, Any]:
    return {
        "package": "decision_truth",
        "methodology_version": "dts-p4-evidence-lifecycle-1.0",
        "stats": dict(_PIPELINE_STATS),
        "canonical_owner": "decision_truth/govern.py",
        "stages": [
            "source_ingestion",
            "data_integrity",
            "freshness",
            "quality",
            "evidence_class",
            "economic_reality",
            "execution_feasibility",
            "portfolio_risk",
            "risk_envelope",
            "pre_impact",
            "reverse_stress",
            "venue_health",
            "depeg_protection",
            "signal_admission_gate",
            "safety_floor",
            "decision_contract",
            "failure_integration",
            "user_agency",
            "compliance_guards",
        ],
    }


def evaluate_opportunity(
    opportunity: dict[str, Any],
    *,
    symbol: str | None = None,
    record: bool = True,
    context: str = "api",
) -> DecisionContract:
    """Run governed Decision Truth pipeline for one opportunity."""
    payload = dict(opportunity)
    if symbol:
        payload["symbol"] = symbol
    governed = govern_decision_payload(payload, context=context, record=record, run_data_governance=True)
    contract_dict = (governed.get("decision_truth") or {}).get("contract") or {}
    return DecisionContract(
        decision_state=DecisionState(contract_dict.get("decision_state", DecisionState.UNAVAILABLE.value)),
        symbol=str(contract_dict.get("symbol") or payload.get("symbol") or "BTC"),
        time_horizon=str(contract_dict.get("time_horizon") or "intraday"),
        net_edge=dict(contract_dict.get("net_edge") or {}),
        execution_feasibility=dict(contract_dict.get("execution_feasibility") or {}),
        risk=dict(contract_dict.get("risk") or {}),
        grade=str(contract_dict.get("grade") or "UNAVAILABLE"),
        evidence_class=str(contract_dict.get("evidence_class") or "UNAVAILABLE"),
        freshness=dict(contract_dict.get("freshness") or {}),
        uncertainty=dict(contract_dict.get("uncertainty") or {}),
        capacity=dict(contract_dict.get("capacity") or {}),
        why=list(contract_dict.get("why") or []),
        why_not=list(contract_dict.get("why_not") or []),
        invalidation_condition=str(contract_dict.get("invalidation_condition") or ""),
        methodology_version=str(contract_dict.get("methodology_version") or "dts-p1-spine-1.0"),
        assumptions=dict(contract_dict.get("assumptions") or {}),
        safety_floor=dict(contract_dict.get("safety_floor") or {}),
        provenance_context=dict(contract_dict.get("provenance_context") or {}),
        field_availability=dict(contract_dict.get("field_availability") or {}),
        user_agency=dict(governed.get("user_agency") or {}),
        failure_integration=dict(contract_dict.get("failure_integration") or {}),
    )


def evaluate_decision_truth(
    payload: dict[str, Any],
    *,
    lang: str = "en",
    previous_decision_state: str | None = None,
    record: bool = False,
    context: str = "oracle",
) -> dict[str, Any]:
    """Attach governed Decision Truth evaluation — no silent fallback."""
    return govern_decision_payload(
        payload,
        context=context,
        lang=lang,
        record=record,
        run_data_governance=not bool(payload.get("data_governance")),
        previous_decision_state=previous_decision_state,
    )
