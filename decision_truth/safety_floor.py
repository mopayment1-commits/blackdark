"""Unified Safety Floor gate (DTS-024)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from decision_truth.inputs import AdmissionInputs


@dataclass(frozen=True, slots=True)
class SafetyFloorResult:
    passed: bool
    failures: tuple[str, ...]
    context: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {"passed": self.passed, "failures": list(self.failures), "context": self.context}


def evaluate_safety_floor(inputs: AdmissionInputs, contract_context: dict[str, Any]) -> SafetyFloorResult:
    failures: list[str] = []
    context: dict[str, Any] = {
        "freshness": inputs.freshness_meta,
        "data_quality_state": inputs.data_quality_state,
        "evidence_class": inputs.evidence_class,
        "uncertainty_available": inputs.uncertainty_available,
        "execution_available": inputs.execution_available,
        "limitations": contract_context.get("limitations") or [],
        "invalidation_condition": contract_context.get("invalidation_condition"),
    }

    if inputs.freshness_ok is not True:
        failures.append("freshness_floor_failed")
    if inputs.data_quality_score is None:
        failures.append("data_quality_unavailable")
    elif inputs.data_quality_score < 40.0:
        failures.append("data_quality_below_floor")
    if not inputs.evidence_class_available:
        failures.append("evidence_context_unavailable")
    if inputs.evidence_class in {"UNVERIFIED", "MOCK", "STUB", "UNAVAILABLE"}:
        failures.append("evidence_class_insufficient")
    economics_required = bool(contract_context.get("economics_required", True))
    if economics_required and not inputs.net_edge_available:
        failures.append("net_edge_economics_unavailable")
    if economics_required and inputs.net_edge_reject:
        failures.append("net_edge_below_floor")
    if not inputs.execution_available:
        failures.append("execution_feasibility_unavailable")
    elif inputs.execution_score is not None and inputs.execution_score < 35.0:
        failures.append("execution_feasibility_below_floor")
    if not inputs.uncertainty_available:
        failures.append("uncertainty_context_unavailable")
    elif inputs.uncertainty_state == "UNCERTAINTY_UNAVAILABLE":
        failures.append("net_edge_uncertainty_unavailable")
    if economics_required and not inputs.capacity_available:
        failures.append("capacity_evidence_unavailable")
    if contract_context.get("half_life_material") and not inputs.half_life_available:
        failures.append("half_life_unavailable")
    portfolio_risk = contract_context.get("portfolio_risk") or {}
    if inputs.pre_impact_breach:
        failures.append("pre_impact_material_breach")
    if inputs.venue_health_impact in {"reject", "abstain"}:
        failures.append(f"venue_health_{inputs.venue_health_impact}")
    if inputs.depeg_material:
        failures.append("depeg_risk_material")
    if portfolio_risk.get("decision_impact") == "reject":
        failures.append("portfolio_risk_reject")
    if not contract_context.get("invalidation_condition"):
        failures.append("invalidation_context_missing")

    if inputs.failure_state in {"STALE", "PARTIAL", "UNAVAILABLE", "INDETERMINATE"}:
        failures.append(f"failure_state_{inputs.failure_state.lower()}")
    if inputs.data_quality_state in {"CONFLICTING", "INSUFFICIENT"}:
        failures.append(f"quality_state_{inputs.data_quality_state.lower()}")

    return SafetyFloorResult(passed=not failures, failures=tuple(failures), context=context)
