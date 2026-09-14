"""Failure, Surprise & Abstention Corpus (P3)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Mapping, Sequence

FAILURE_CORPUS_CONTRACT_VERSION = "p3.0.0"


class FailureCaseType(str, Enum):
    HIGH_CONFIDENCE_WRONG = "high_confidence_wrong_prediction"
    FAILURE_TO_ABSTAIN = "failure_to_abstain"
    UNNECESSARY_ABSTENTION = "unnecessary_abstention"
    MISSED_MAJOR_EVENT = "missed_major_event"
    MODEL_DISAGREEMENT = "model_disagreement"
    UNEXPECTED_REGIME_SHIFT = "unexpected_regime_shift"
    CORRELATION_BREAKDOWN = "correlation_breakdown"
    STALE_SOURCE = "stale_source"
    CONFLICTING_SOURCES = "conflicting_sources"
    MISSING_SOURCE = "missing_source"
    TAIL_EVENT = "tail_event"
    CALIBRATION_COLLAPSE = "calibration_collapse"
    PREDICTION_INSTABILITY = "prediction_instability"
    SOURCE_REVISION = "source_revision"
    MODEL_REGRESSION = "model_regression"


@dataclass(frozen=True, slots=True)
class FailureSurpriseCase:
    """One high-learning-value failure/surprise case."""

    case_id: str
    case_type: FailureCaseType
    shadow_receipt_id: str | None
    outcome_id: str | None
    root_cause: str | None
    affected_capability: str | None
    model_rule_version: str | None
    evidence_class: str
    recorded_at: datetime
    traceability: Mapping[str, str] = field(default_factory=dict)

    def to_metadata(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "case_type": self.case_type.value,
            "shadow_receipt_id": self.shadow_receipt_id,
            "outcome_id": self.outcome_id,
            "root_cause": self.root_cause,
            "affected_capability": self.affected_capability,
            "model_rule_version": self.model_rule_version,
            "evidence_class": self.evidence_class,
            "recorded_at": self.recorded_at.isoformat(),
            "traceability": dict(self.traceability),
        }


@dataclass
class FailureSurpriseCorpus:
    """Durable append-only failure/surprise/abstention corpus."""

    _cases: list[FailureSurpriseCase]

    def __init__(self) -> None:
        self._cases = []

    def list_cases(self) -> tuple[FailureSurpriseCase, ...]:
        return tuple(self._cases)

    def record_case(
        self,
        *,
        case_id: str,
        case_type: FailureCaseType,
        shadow_receipt_id: str | None,
        outcome_id: str | None,
        root_cause: str | None,
        affected_capability: str | None,
        model_rule_version: str | None,
        evidence_class: str,
        recorded_at: datetime,
        traceability: Mapping[str, str] | None = None,
    ) -> FailureSurpriseCase:
        case = FailureSurpriseCase(
            case_id=case_id,
            case_type=case_type,
            shadow_receipt_id=shadow_receipt_id,
            outcome_id=outcome_id,
            root_cause=root_cause,
            affected_capability=affected_capability,
            model_rule_version=model_rule_version,
            evidence_class=evidence_class,
            recorded_at=recorded_at,
            traceability=dict(traceability or {}),
        )
        self._cases.append(case)
        return case

    def classify_from_shadow_outcome(
        self,
        *,
        case_id: str,
        shadow_receipt_id: str,
        outcome_id: str | None,
        prediction_confidence: float,
        prediction_correct: bool | None,
        abstained: bool,
        should_have_abstained: bool,
        evidence_class: str,
        recorded_at: datetime,
        model_version: str,
    ) -> FailureSurpriseCase | None:
        """Classify failure cases from shadow/outcome linkage."""
        if prediction_confidence >= 0.8 and prediction_correct is False:
            return self.record_case(
                case_id=case_id,
                case_type=FailureCaseType.HIGH_CONFIDENCE_WRONG,
                shadow_receipt_id=shadow_receipt_id,
                outcome_id=outcome_id,
                root_cause="overconfident_incorrect_prediction",
                affected_capability="prediction",
                model_rule_version=model_version,
                evidence_class=evidence_class,
                recorded_at=recorded_at,
                traceability={
                    "case": case_id,
                    "root_cause": "overconfident_incorrect_prediction",
                    "affected_capability": "prediction",
                    "model_version": model_version,
                },
            )
        if not abstained and should_have_abstained:
            return self.record_case(
                case_id=case_id,
                case_type=FailureCaseType.FAILURE_TO_ABSTAIN,
                shadow_receipt_id=shadow_receipt_id,
                outcome_id=outcome_id,
                root_cause="should_have_abstained",
                affected_capability="abstention",
                model_rule_version=model_version,
                evidence_class=evidence_class,
                recorded_at=recorded_at,
                traceability={"case": case_id, "root_cause": "should_have_abstained"},
            )
        if abstained and not should_have_abstained:
            return self.record_case(
                case_id=case_id,
                case_type=FailureCaseType.UNNECESSARY_ABSTENTION,
                shadow_receipt_id=shadow_receipt_id,
                outcome_id=outcome_id,
                root_cause="unnecessary_abstention",
                affected_capability="abstention",
                model_rule_version=model_version,
                evidence_class=evidence_class,
                recorded_at=recorded_at,
                traceability={"case": case_id, "root_cause": "unnecessary_abstention"},
            )
        return None
