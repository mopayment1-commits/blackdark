"""Methodology version registry for Decision Truth calculations."""

from __future__ import annotations

METHODOLOGY_VERSIONS: dict[str, str] = {
    "net_edge": "net_edge_v2.0",
    "cost_autopsy": "cost_autopsy_v1.0",
    "execution_feasibility": "execution_feasibility_v1.0",
    "capacity": "capacity_v1.0",
    "half_life": "half_life_v1.0",
    "risk_budget": "risk_budget_v1.0",
    "pre_impact": "pre_impact_v1.0",
    "reverse_stress": "reverse_stress_v1.0",
    "evidence_grade": "evidence_grade_v1.0",
    "admission_gate": "admission_gate_v1.0",
    "decision_contract": "decision_contract_v1.0",
    "simulation": "simulation_v1.0",
    "calibration": "calibration_v1.0",
    "outcome_ledger": "outcome_ledger_v1.0",
    "change_detector": "change_detector_v1.0",
}


def methodology_versions() -> dict[str, str]:
    return dict(METHODOLOGY_VERSIONS)
