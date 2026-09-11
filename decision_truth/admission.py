"""Signal admission gate (DTS-017)."""

from __future__ import annotations

from typing import Any

from decision_truth.contract import DecisionState


def evaluate_admission(
    *,
    freshness_ok: bool,
    data_quality_score: float,
    evidence_class: str,
    liquidity_ok: bool,
    execution_score: float,
    net_edge_reject: bool,
    risk_ok: bool,
    uncertainty_high: bool,
) -> tuple[DecisionState, list[str]]:
    why_not: list[str] = []
    if not freshness_ok:
        why_not.append("freshness_gate_failed")
    if data_quality_score < 40.0:
        why_not.append("data_quality_below_floor")
    if evidence_class in {"UNVERIFIED", "MOCK", "STUB"}:
        why_not.append("evidence_class_insufficient")
    if not liquidity_ok:
        why_not.append("liquidity_gate_failed")
    if execution_score < 35.0:
        why_not.append("execution_feasibility_low")
    if net_edge_reject:
        why_not.append("net_edge_truth_reject")
    if not risk_ok:
        why_not.append("risk_gate_failed")
    if uncertainty_high:
        why_not.append("uncertainty_too_high")

    if why_not:
        if "net_edge_truth_reject" in why_not or "risk_gate_failed" in why_not:
            return DecisionState.REJECTED, why_not
        if len(why_not) >= 3:
            return DecisionState.ABSTAINED, why_not
        return DecisionState.DEGRADED, why_not
    return DecisionState.ADMITTED, []
