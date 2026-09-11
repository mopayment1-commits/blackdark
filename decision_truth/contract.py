"""Decision Truth contract types (DTS-002, DTS-018)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


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
    methodology_version: str = "dts-mvp-1.0"
    assumptions: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["decision_state"] = self.decision_state.value
        return payload
