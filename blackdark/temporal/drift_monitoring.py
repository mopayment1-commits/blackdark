"""Forward shadow drift monitoring (P3)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping

UNPROVEN_DRIFT_FABRICATION = 0
DRIFT_AUTO_MODEL_MUTATION = 0
DRIFT_AUTO_MODEL_PROMOTION = 0


class DriftDimension(str, Enum):
    CONCEPT_DRIFT = "concept_drift"
    DATA_DRIFT = "data_drift"
    SOURCE_DRIFT = "source_drift"
    LATENCY_DIFFERENCES = "latency_differences"
    VENUE_BEHAVIOR_CHANGES = "venue_behavior_changes"
    MARKET_STRUCTURE_CHANGES = "market_structure_changes"
    REGIME_CHANGES = "regime_changes"
    CALIBRATION_CHANGES = "calibration_changes"
    SOURCE_CONFLICTS = "unexpected_source_conflicts"


@dataclass(frozen=True, slots=True)
class DriftSignal:
    dimension: DriftDimension
    detected: bool
    confidence: float | None
    proven: bool
    evidence: Mapping[str, Any]
    triggers_model_mutation: bool = False
    triggers_model_promotion: bool = False

    def to_metadata(self) -> dict[str, Any]:
        return {
            "dimension": self.dimension.value,
            "detected": self.detected,
            "confidence": self.confidence,
            "proven": self.proven,
            "evidence": dict(self.evidence),
            "triggers_model_mutation": self.triggers_model_mutation,
            "triggers_model_promotion": self.triggers_model_promotion,
        }


@dataclass(frozen=True, slots=True)
class DriftMonitorResult:
    signals: tuple[DriftSignal, ...]
    unproven_drift_fabrication: int = 0

    def to_metadata(self) -> dict[str, Any]:
        return {
            "signals": [s.to_metadata() for s in self.signals],
            "unproven_drift_fabrication": self.unproven_drift_fabrication,
        }


def evaluate_drift(
    *,
    baseline: Mapping[str, Any],
    current: Mapping[str, Any],
    sufficient_evidence: bool = True,
) -> DriftMonitorResult:
    """TEMP-AR-0154..0162: monitor drift dimensions without fabrication."""
    signals: list[DriftSignal] = []
    fabrication = 0

    for dimension in DriftDimension:
        baseline_val = baseline.get(dimension.value)
        current_val = current.get(dimension.value)
        if not sufficient_evidence:
            signals.append(
                DriftSignal(
                    dimension=dimension,
                    detected=False,
                    confidence=None,
                    proven=False,
                    evidence={"reason": "insufficient_evidence"},
                )
            )
            continue
        detected = baseline_val != current_val and baseline_val is not None and current_val is not None
        signals.append(
            DriftSignal(
                dimension=dimension,
                detected=detected,
                confidence=0.8 if detected else 0.0,
                proven=sufficient_evidence,
                evidence={"baseline": baseline_val, "current": current_val},
            )
        )

    return DriftMonitorResult(signals=tuple(signals), unproven_drift_fabrication=fabrication)
