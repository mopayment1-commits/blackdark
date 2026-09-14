"""Decision Truth contract types (DTS-002, DTS-018)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

from decision_truth.field_state import field_value


class DecisionState(str, Enum):
    AVAILABLE = "AVAILABLE"
    DEGRADED = "DEGRADED"
    ABSTAINED = "ABSTAINED"
    REJECTED = "REJECTED"
    UNAVAILABLE = "UNAVAILABLE"
    ADMITTED = "ADMITTED"


@dataclass
class DecisionContract:
    """Machine-readable decision contract per DTS-018."""

    decision_state: DecisionState
    symbol: str
    time_horizon: str
    net_edge: dict[str, Any]
    execution_feasibility: dict[str, Any]
    risk: dict[str, Any]
    grade: str
    evidence_class: str
    freshness: dict[str, Any]
    uncertainty: dict[str, Any]
    capacity: dict[str, Any]
    why: list[str] = field(default_factory=list)
    why_not: list[str] = field(default_factory=list)
    invalidation_condition: str = ""
    methodology_version: str = "dts-p3-portfolio-preimpact-1.0"
    assumptions: dict[str, Any] = field(default_factory=dict)
    safety_floor: dict[str, Any] = field(default_factory=dict)
    provenance_context: dict[str, Any] = field(default_factory=dict)
    field_availability: dict[str, Any] = field(default_factory=dict)
    user_agency: dict[str, Any] = field(default_factory=dict)
    failure_integration: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["decision_state"] = self.decision_state.value
        return payload


def build_field_availability(
    inputs_missing: tuple[str, ...],
    *,
    grade_present: bool,
    capacity_available: bool = False,
    capacity_not_applicable: bool = False,
    portfolio_impact_available: bool = False,
    portfolio_impact_not_applicable: bool = False,
) -> dict[str, Any]:
    return {
        "grade": field_value(None, available=grade_present, not_applicable=not grade_present, reason="p3_not_implemented"),
        "capacity": field_value(
            None,
            available=capacity_available,
            not_applicable=capacity_not_applicable,
            reason=None if capacity_available or capacity_not_applicable else "capacity_unavailable",
        ),
        "simulation": field_value(None, available=False, not_applicable=True, reason="p3_not_implemented"),
        "calibration": field_value(None, available=False, not_applicable=True, reason="p3_not_implemented"),
        "portfolio_impact": field_value(
            None,
            available=portfolio_impact_available,
            not_applicable=portfolio_impact_not_applicable,
            reason=None if portfolio_impact_available or portfolio_impact_not_applicable else "portfolio_pre_impact_unavailable",
        ),
        "missing_critical_inputs": list(inputs_missing),
    }
