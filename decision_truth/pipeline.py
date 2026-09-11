"""Decision Truth Pipeline — single orchestrated path (BGS-009 §2)."""

from __future__ import annotations

import time
from typing import Any

from decision_truth.admission import evaluate_admission
from decision_truth.contract import DecisionContract, DecisionState
from decision_truth.ledger import record_outcome

_PIPELINE_STATS = {"evaluated": 0, "admitted": 0, "rejected": 0, "abstained": 0, "degraded": 0}


def pipeline_status() -> dict[str, Any]:
    return {
        "package": "decision_truth",
        "methodology_version": "dts-mvp-1.0",
        "stats": dict(_PIPELINE_STATS),
        "stages": [
            "source_ingestion",
            "data_integrity",
            "freshness",
            "quality",
            "evidence_class",
            "economic_reality",
            "execution_feasibility",
            "signal_admission_gate",
            "decision_contract",
            "outcome_ledger",
        ],
    }


def _freshness_gate(opportunity: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    age_ms = float(opportunity.get("quote_age_ms") or opportunity.get("age_ms") or 0)
    max_age = float(opportunity.get("max_quote_age_ms") or 2500.0)
    ok = age_ms <= max_age if age_ms > 0 else True
    return ok, {"quote_age_ms": age_ms, "max_quote_age_ms": max_age, "ok": ok}


def _economic_reality(opportunity: dict[str, Any]) -> dict[str, Any]:
    try:
        from net_edge_truth import compute_net_edge_truth

        truth = compute_net_edge_truth(opportunity)
        return truth
    except Exception as exc:  # noqa: BLE001 — pipeline must degrade, not crash
        return {"reject": True, "truth_score": 0.0, "error": str(exc), "reason": "net_edge_unavailable"}


def evaluate_opportunity(
    opportunity: dict[str, Any],
    *,
    symbol: str | None = None,
    record: bool = True,
) -> DecisionContract:
    """Run full Decision Truth pipeline for one opportunity."""
    _PIPELINE_STATS["evaluated"] += 1
    sym = str(symbol or opportunity.get("symbol") or opportunity.get("asset") or "BTC")
    freshness_ok, freshness = _freshness_gate(opportunity)
    net_edge = _economic_reality(opportunity)
    net_edge_reject = bool(net_edge.get("reject"))

    dq = float(opportunity.get("data_quality_score") or opportunity.get("provenance_score") or 70.0)
    evidence_class = str(opportunity.get("evidence_class") or "VERIFIED_LOCAL")
    execution_score = float(opportunity.get("execution_feasibility_score") or 60.0)
    liquidity_ok = bool(opportunity.get("liquidity_ok", True))
    risk_ok = bool(opportunity.get("risk_ok", True))
    uncertainty_high = bool(opportunity.get("uncertainty_high", False))

    admission_state, why_not = evaluate_admission(
        freshness_ok=freshness_ok,
        data_quality_score=dq,
        evidence_class=evidence_class,
        liquidity_ok=liquidity_ok,
        execution_score=execution_score,
        net_edge_reject=net_edge_reject,
        risk_ok=risk_ok,
        uncertainty_high=uncertainty_high,
    )

    if admission_state == DecisionState.ADMITTED:
        final_state = DecisionState.AVAILABLE
        _PIPELINE_STATS["admitted"] += 1
        why: list[str] = ["all_mandatory_gates_passed"]
    elif admission_state == DecisionState.REJECTED:
        final_state = DecisionState.REJECTED
        _PIPELINE_STATS["rejected"] += 1
        why = []
    elif admission_state == DecisionState.ABSTAINED:
        final_state = DecisionState.ABSTAINED
        _PIPELINE_STATS["abstained"] += 1
        why = []
    else:
        final_state = DecisionState.DEGRADED
        _PIPELINE_STATS["degraded"] += 1
        why = ["partial_gate_failure"]

    contract = DecisionContract(
        decision_state=final_state,
        symbol=sym,
        time_horizon=str(opportunity.get("time_horizon") or "intraday"),
        net_edge=net_edge,
        execution_feasibility={"score": execution_score, "liquidity_ok": liquidity_ok},
        risk={"ok": risk_ok},
        grade=str(opportunity.get("grade") or "B"),
        evidence_class=evidence_class,
        freshness=freshness,
        uncertainty={"high": uncertainty_high},
        capacity={"usd": opportunity.get("capacity_usd")},
        why=why,
        why_not=why_not,
        invalidation_condition=str(opportunity.get("invalidation") or "net_edge_or_freshness_breach"),
        assumptions={"source": opportunity.get("source"), "timestamp": time.time()},
    )

    if record:
        record_outcome(contract)
    return contract
