"""Signal admission gate (DTS-017) — fail-closed on missing critical inputs."""

from __future__ import annotations

from decision_truth.contract import DecisionState
from decision_truth.inputs import AdmissionInputs


def evaluate_admission(inputs: AdmissionInputs) -> tuple[DecisionState, list[str]]:
    why_not: list[str] = []

    if inputs.failure_state in {"STALE", "PARTIAL", "UNAVAILABLE", "INDETERMINATE", "DEGRADED"}:
        why_not.append(f"failure_state_{inputs.failure_state.lower()}")
    if inputs.data_governance_state in {"REJECTED", "ABSTAINED", "UNAVAILABLE", "INDETERMINATE"}:
        why_not.append(f"data_governance_{str(inputs.data_governance_state).lower()}")
    if inputs.data_governance_failed_gates:
        why_not.extend([f"data_governance_{g}" for g in inputs.data_governance_failed_gates])

    for missing in inputs.missing_critical:
        why_not.append(f"missing_{missing}")

    if inputs.freshness_ok is False:
        why_not.append("freshness_gate_failed")
    elif inputs.freshness_ok is None:
        why_not.append("freshness_unverified")

    if inputs.data_quality_score is None:
        why_not.append("data_quality_unavailable")
    elif inputs.data_quality_score < 40.0:
        why_not.append("data_quality_below_floor")

    if not inputs.evidence_class_available:
        why_not.append("evidence_class_unavailable")
    elif inputs.evidence_class in {"UNVERIFIED", "MOCK", "STUB", "UNAVAILABLE"}:
        why_not.append("evidence_class_insufficient")

    if inputs.liquidity_ok is False:
        why_not.append("liquidity_gate_failed")
    elif inputs.liquidity_ok is None:
        why_not.append("liquidity_unverified")

    if not inputs.execution_available:
        why_not.append("execution_feasibility_unavailable")
    elif inputs.execution_score is not None and inputs.execution_score < 35.0:
        why_not.append("execution_feasibility_low")

    if inputs.net_edge_reject:
        why_not.append("net_edge_truth_reject")
    elif not inputs.net_edge_available:
        why_not.append("net_edge_unavailable")
    if inputs.net_edge_available and not inputs.capacity_available:
        why_not.append("capacity_unavailable")
    if inputs.net_edge_available and not inputs.half_life_available:
        why_not.append("half_life_unavailable")

    if inputs.pre_impact_breach:
        why_not.append("pre_impact_material_breach")
    if inputs.portfolio_risk_impact == "reject":
        why_not.append("portfolio_risk_reject")
    elif inputs.portfolio_risk_impact == "abstain":
        why_not.append("portfolio_risk_abstain")
    if inputs.venue_health_impact == "reject":
        why_not.append("venue_health_critical")
    elif inputs.venue_health_impact == "abstain":
        why_not.append("venue_health_abstain")
    if inputs.depeg_material and inputs.depeg_impact == "reject":
        why_not.append("depeg_risk_critical")
    elif inputs.depeg_impact in {"abstain", "reject"} and inputs.depeg_impact:
        why_not.append("depeg_risk_material")

    if inputs.risk_ok is False:
        why_not.append("risk_gate_failed")
    elif inputs.risk_ok is None:
        why_not.append("risk_context_unverified")

    if inputs.calibration_weak:
        why_not.append("calibration_weak")
    if not inputs.cherry_picking_allowed:
        why_not.append("cherry_picking_violation")

    if inputs.uncertainty_high:
        why_not.append("uncertainty_too_high")
    elif not inputs.uncertainty_available:
        why_not.append("uncertainty_unavailable")

    if not why_not:
        return DecisionState.ADMITTED, []

    hard_reject = {
        "net_edge_truth_reject",
        "risk_gate_failed",
        "data_governance_rejected",
        "failure_state_unavailable",
        "failure_state_indeterminate",
        "portfolio_risk_reject",
        "venue_health_critical",
        "depeg_risk_critical",
        "pre_impact_material_breach",
    }
    if any(r in why_not for r in hard_reject) or "net_edge_truth_reject" in why_not:
        return DecisionState.REJECTED, why_not
    if any("abstain" in r or "unavailable" in r or "unverified" in r or "conflict" in r for r in why_not):
        if len(why_not) >= 2 or "freshness_gate_failed" in why_not or inputs.data_quality_state == "CONFLICTING":
            return DecisionState.ABSTAINED, why_not
    if len(why_not) >= 3:
        return DecisionState.ABSTAINED, why_not
    return DecisionState.DEGRADED, why_not
