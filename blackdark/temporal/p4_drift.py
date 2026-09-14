"""P4 learning/evaluation drift monitoring (TEMP-AR-0306..0314)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping

P4_DRIFT_CONTRACT_VERSION = "p4.drift.1.0"
HISTORICAL_SCALE_DOES_NOT_OVERRIDE_INVALIDATION = True


class P4DriftDimension(str, Enum):
    FEATURE_DRIFT = "feature_drift"
    TARGET_DRIFT = "target_drift"
    CALIBRATION_DRIFT = "calibration_drift"
    RELATIONSHIP_DRIFT = "relationship_drift"
    STRUCTURAL_BREAK = "structural_break"
    REPRESENTATIVENESS_INVALIDATION = "representativeness_invalidation"
    SOURCE_DRIFT = "source_drift"
    REGIME_DRIFT = "regime_drift"
    LATENCY_DRIFT = "latency_drift"


@dataclass(frozen=True, slots=True)
class P4DriftSignal:
    dimension: P4DriftDimension
    detected: bool
    confidence: float | None
    proven: bool
    invalidates_representativeness: bool
    evidence: Mapping[str, Any]

    def to_metadata(self) -> dict[str, Any]:
        return {
            "dimension": self.dimension.value,
            "detected": self.detected,
            "confidence": self.confidence,
            "proven": self.proven,
            "invalidates_representativeness": self.invalidates_representativeness,
            "evidence": dict(self.evidence),
        }


@dataclass(frozen=True, slots=True)
class P4DriftResult:
    signals: tuple[P4DriftSignal, ...]
    representativeness_invalidated: bool
    historical_scale_override_attempted: bool = False

    def to_metadata(self) -> dict[str, Any]:
        return {
            "signals": [s.to_metadata() for s in self.signals],
            "representativeness_invalidated": self.representativeness_invalidated,
            "historical_scale_override_attempted": self.historical_scale_override_attempted,
        }


def evaluate_p4_drift(
    *,
    baseline: Mapping[str, Any],
    current: Mapping[str, Any],
    sufficient_evidence: bool = True,
    historical_sample_scale: int = 0,
) -> P4DriftResult:
    """Monitor P4 drift dimensions; historical scale cannot override invalidation."""
    signals: list[P4DriftSignal] = []
    representativeness_invalidated = False

    for dimension in P4DriftDimension:
        base_val = baseline.get(dimension.value)
        cur_val = current.get(dimension.value)
        if not sufficient_evidence:
            signals.append(
                P4DriftSignal(
                    dimension=dimension,
                    detected=False,
                    confidence=None,
                    proven=False,
                    invalidates_representativeness=False,
                    evidence={"reason": "insufficient_evidence"},
                )
            )
            continue
        detected = base_val != cur_val and base_val is not None and cur_val is not None
        invalidates = (
            detected
            and dimension
            in {
                P4DriftDimension.REPRESENTATIVENESS_INVALIDATION,
                P4DriftDimension.STRUCTURAL_BREAK,
            }
        )
        if invalidates:
            representativeness_invalidated = True
        signals.append(
            P4DriftSignal(
                dimension=dimension,
                detected=detected,
                confidence=0.85 if detected else 0.0,
                proven=sufficient_evidence,
                invalidates_representativeness=invalidates,
                evidence={"baseline": base_val, "current": cur_val},
            )
        )

    override_attempted = representativeness_invalidated and historical_sample_scale > 1_000_000
    if override_attempted and HISTORICAL_SCALE_DOES_NOT_OVERRIDE_INVALIDATION:
        representativeness_invalidated = True

    return P4DriftResult(
        signals=tuple(signals),
        representativeness_invalidated=representativeness_invalidated,
        historical_scale_override_attempted=override_attempted,
    )
