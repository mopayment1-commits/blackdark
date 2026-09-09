"""Decision safety and evidence context (ERR-013, ERR-039)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from failure.freshness import FreshnessState
from failure.quality import DataQualityState


class DecisionSafetyState(StrEnum):
    AVAILABLE = "AVAILABLE"
    DEGRADED = "DEGRADED"
    ABSTAINED = "ABSTAINED"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(slots=True)
class EvidenceContext:
    evidence_state: str
    source_count: int
    freshness_state: str
    conflict_state: str
    quality_state: str
    decision_state: DecisionSafetyState

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_state": self.evidence_state,
            "source_count": self.source_count,
            "freshness_state": self.freshness_state,
            "conflict_state": self.conflict_state,
            "quality_state": self.quality_state,
            "decision_state": self.decision_state.value,
        }


def evaluate_decision_safety(
    *,
    freshness: FreshnessState | str,
    quality: DataQualityState | str,
    source_count: int = 0,
    conflicting: bool = False,
) -> EvidenceContext:
    fval = freshness.value if isinstance(freshness, FreshnessState) else str(freshness)
    qval = quality.value if isinstance(quality, DataQualityState) else str(quality)
    conflict_state = "CONFLICTING" if conflicting else "NONE"

    if qval in {DataQualityState.INSUFFICIENT.value, DataQualityState.CONFLICTING.value} or conflicting:
        decision = DecisionSafetyState.ABSTAINED
        evidence_state = "insufficient"
    elif fval in {FreshnessState.STALE.value, FreshnessState.UNKNOWN.value}:
        decision = DecisionSafetyState.DEGRADED
        evidence_state = "stale_or_unknown"
    elif qval in {DataQualityState.PARTIAL.value, DataQualityState.SUSPECT.value, DataQualityState.UNVERIFIED.value}:
        decision = DecisionSafetyState.DEGRADED
        evidence_state = "degraded_quality"
    elif source_count <= 0:
        decision = DecisionSafetyState.UNAVAILABLE
        evidence_state = "no_sources"
    else:
        decision = DecisionSafetyState.AVAILABLE
        evidence_state = "sufficient"

    return EvidenceContext(
        evidence_state=evidence_state,
        source_count=source_count,
        freshness_state=fval,
        conflict_state=conflict_state,
        quality_state=qval,
        decision_state=decision,
    )
