"""Outcome Quality and Label Confidence (P2) — read-only on canonical outcomes."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping

from blackdark.temporal.outcome_contract import OutcomeContract, OutcomeLabelStatus

UNKNOWN_OUTCOME_TREATED_AS_FALSE = False
LABEL_CONFIDENCE_PRESERVED = True


class OutcomeQualityTier(str, Enum):
    DIRECT_OBSERVED = "direct_observed"
    DERIVED = "derived"
    INFERRED = "inferred"
    IMPERFECT = "imperfect"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True, slots=True)
class OutcomeQualityAssessment:
    """TEMP-AR-0117..0123, TEMP-AR-0437."""

    outcome_id: str
    outcome_quality: OutcomeQualityTier
    label_confidence: float | None
    data_completeness: float
    evaluation_source: str
    evaluation_method: str
    known_limitations: tuple[str, ...]
    equivalent_to_direct_truth: bool

    def to_metadata(self) -> dict[str, Any]:
        return {
            "outcome_id": self.outcome_id,
            "outcome_quality": self.outcome_quality.value,
            "label_confidence": self.label_confidence,
            "data_completeness": self.data_completeness,
            "evaluation_source": self.evaluation_source,
            "evaluation_method": self.evaluation_method,
            "known_limitations": list(self.known_limitations),
            "equivalent_to_direct_truth": self.equivalent_to_direct_truth,
        }


def assess_outcome_quality(
    outcome: OutcomeContract,
    *,
    source_quality_score: float | None = None,
) -> OutcomeQualityAssessment:
    """
    Assess outcome quality without mutating the canonical outcome record.

    TEMP-AR-0123: derived/inferred outcomes must not be presented as direct truth.
    """
    if outcome.label_status == OutcomeLabelStatus.UNRESOLVED:
        tier = OutcomeQualityTier.UNAVAILABLE
        confidence = None
        completeness = 0.0
        limitations = ("outcome_not_yet_verifiable",)
        equivalent = False
    elif outcome.label_status == OutcomeLabelStatus.VERIFIED and outcome.realized_result is not None:
        tier = OutcomeQualityTier.DIRECT_OBSERVED
        confidence = 0.95 if source_quality_score is None else min(0.99, source_quality_score)
        completeness = 1.0
        limitations = ()
        equivalent = True
    elif outcome.label_status == OutcomeLabelStatus.PROVISIONAL:
        tier = OutcomeQualityTier.DERIVED
        confidence = 0.5
        completeness = 0.6
        limitations = ("provisional_label",)
        equivalent = False
    elif outcome.label_status == OutcomeLabelStatus.LOW_CONFIDENCE:
        tier = OutcomeQualityTier.IMPERFECT
        confidence = 0.3
        completeness = 0.4
        limitations = ("low_confidence_label",)
        equivalent = False
    else:
        tier = OutcomeQualityTier.INFERRED
        confidence = None
        completeness = 0.2
        limitations = (outcome.label_status.value,)
        equivalent = False

    return OutcomeQualityAssessment(
        outcome_id=outcome.outcome_id,
        outcome_quality=tier,
        label_confidence=confidence,
        data_completeness=completeness,
        evaluation_source="independent_outcome_evaluator",
        evaluation_method="pit_observable_comparison",
        known_limitations=limitations,
        equivalent_to_direct_truth=equivalent,
    )


def outcome_quality_does_not_mutate_canonical(
    before: Mapping[str, Any],
    after: Mapping[str, Any],
) -> bool:
    return before == after
