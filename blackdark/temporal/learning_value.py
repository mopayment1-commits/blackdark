"""Learning Value Engine — prioritization without retention or authority duplication (P4)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Sequence

from blackdark.temporal.evidence_class import (
    TemporalEvidenceClass,
    assert_no_automatic_promotion,
    validate_evidence_class_assignment,
)
from blackdark.temporal.evidence_provenance import EvidenceProvenanceLedger, EvidenceRecord
from blackdark.temporal.failure_surprise_corpus import (
    CaptureCategory,
    FailureCaseType,
    FailureSurpriseCase,
    FailureSurpriseCorpus,
)
from blackdark.temporal.outcome_contract import OutcomeContract, OutcomeLabelStatus
from blackdark.temporal.outcome_quality import OutcomeQualityAssessment, OutcomeQualityTier, assess_outcome_quality
from blackdark.temporal.retention_policy import build_retention_descriptor, classify_storage_tier

LEARNING_VALUE_CONTRACT_VERSION = "p4.learning_value.1.0"
RETENTION_EQUALS_LEARNING_PRIORITY = False
LEARNING_VALUE_DETERMINISTIC = True
LEARNING_VALUE_AUTO_MODEL_MUTATION = 0
LEARNING_VALUE_AUTO_MODEL_PROMOTION = 0
LEARNING_VALUE_EVIDENCE_PROMOTION = 0
DUPLICATE_OUTCOME_FACTORY = 0
DUPLICATE_EVIDENCE_LEDGER = 0
DUPLICATE_FAILURE_SURPRISE_CORPUS = 0

_REPRESENTATIVE_BASELINE_SCORE = 0.25
_HIGH_INFORMATION_FSA_BOOST: dict[FailureCaseType, float] = {
    FailureCaseType.HIGH_CONFIDENCE_WRONG: 0.35,
    FailureCaseType.FAILURE_TO_ABSTAIN: 0.30,
    FailureCaseType.UNNECESSARY_ABSTENTION: 0.20,
    FailureCaseType.MISSED_MAJOR_EVENT: 0.40,
    FailureCaseType.MODEL_DISAGREEMENT: 0.30,
    FailureCaseType.UNEXPECTED_REGIME_SHIFT: 0.28,
    FailureCaseType.CORRELATION_BREAKDOWN: 0.25,
    FailureCaseType.STALE_SOURCE: 0.22,
    FailureCaseType.CONFLICTING_SOURCES: 0.24,
    FailureCaseType.MISSING_SOURCE: 0.26,
    FailureCaseType.TAIL_EVENT: 0.38,
    FailureCaseType.CALIBRATION_COLLAPSE: 0.32,
    FailureCaseType.PREDICTION_INSTABILITY: 0.27,
    FailureCaseType.SOURCE_REVISION: 0.21,
    FailureCaseType.MODEL_REGRESSION: 0.33,
}
_UNTRUSTED_QUALITY_TIERS = frozenset(
    {
        OutcomeQualityTier.UNAVAILABLE,
        OutcomeQualityTier.IMPERFECT,
    }
)


class LearningStream(str, Enum):
    """TEMP-AR-0185..0187 complementary sampling streams."""

    REPRESENTATIVE = "representative"
    HIGH_INFORMATION = "high_information"


class LearningPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True, slots=True)
class LearningValueResult:
    """Structured learning-value evaluation output."""

    subject_or_case_id: str
    learning_value: float
    priority: str
    reason_codes: tuple[str, ...]
    evidence_class: str
    quality_or_confidence: float | None
    failure_surprise_abstention_context: Mapping[str, Any]
    provenance_reference: str
    eligible_for_learning: bool
    ineligibility_reasons: tuple[str, ...]
    sampling_stream: str
    policy_version: str

    def to_metadata(self) -> dict[str, Any]:
        return {
            "subject_or_case_id": self.subject_or_case_id,
            "learning_value": self.learning_value,
            "priority": self.priority,
            "reason_codes": list(self.reason_codes),
            "evidence_class": self.evidence_class,
            "quality_or_confidence": self.quality_or_confidence,
            "failure_surprise_abstention_context": dict(self.failure_surprise_abstention_context),
            "provenance_reference": self.provenance_reference,
            "eligible_for_learning": self.eligible_for_learning,
            "ineligibility_reasons": list(self.ineligibility_reasons),
            "sampling_stream": self.sampling_stream,
            "policy_version": self.policy_version,
        }


def _deterministic_score(seed_payload: Mapping[str, Any], base: float) -> float:
    digest = hashlib.sha256(
        json.dumps(seed_payload, sort_keys=True, default=str).encode()
    ).hexdigest()
    jitter = int(digest[:8], 16) / 0xFFFFFFFF * 0.05
    return min(1.0, max(0.0, round(base + jitter, 6)))


def _priority_from_score(score: float) -> str:
    if score >= 0.75:
        return LearningPriority.CRITICAL.value
    if score >= 0.55:
        return LearningPriority.HIGH.value
    if score >= 0.35:
        return LearningPriority.MEDIUM.value
    return LearningPriority.LOW.value


def _quality_from_record(record: EvidenceRecord) -> tuple[float | None, tuple[str, ...]]:
    quality_state = dict(record.quality_state)
    confidence = quality_state.get("label_confidence")
    if confidence is not None:
        try:
            return float(confidence), ()
        except (TypeError, ValueError):
            return None, ("quality_confidence_unparseable",)
    tier = quality_state.get("outcome_quality")
    if tier == OutcomeQualityTier.UNAVAILABLE.value:
        return None, ("outcome_quality_unavailable",)
    if tier in (OutcomeQualityTier.IMPERFECT.value, OutcomeQualityTier.INFERRED.value):
        return None, (f"outcome_quality_{tier}",)
    return None, ("quality_unknown",)


def _eligibility_from_quality(
    *,
    quality_confidence: float | None,
    quality_assessment: OutcomeQualityAssessment | None,
    outcome_unresolved: bool,
) -> tuple[bool, tuple[str, ...]]:
    reasons: list[str] = []
    if outcome_unresolved:
        reasons.append("outcome_unresolved")
    if quality_assessment is not None:
        if quality_assessment.outcome_quality in _UNTRUSTED_QUALITY_TIERS:
            reasons.append(f"outcome_quality_{quality_assessment.outcome_quality.value}")
        if not quality_assessment.equivalent_to_direct_truth:
            reasons.append("not_equivalent_to_direct_truth")
    elif quality_confidence is None:
        reasons.append("quality_unproven")
    if reasons:
        return False, tuple(reasons)
    return True, ()


def evaluate_learning_value_for_evidence(
    record: EvidenceRecord,
    *,
    outcome: OutcomeContract | None = None,
    policy_version: str = LEARNING_VALUE_CONTRACT_VERSION,
    stream: LearningStream = LearningStream.HIGH_INFORMATION,
) -> LearningValueResult:
    """
    TEMP-AR-0184, 0188, 0190: score evidence for learning priority without retention coupling.

    Evidence class and ledger record are read-only inputs.
    """
    validate_evidence_class_assignment(record.evidence_class)
    quality_assessment = assess_outcome_quality(outcome) if outcome is not None else None
    quality_confidence, quality_reasons = _quality_from_record(record)
    if quality_assessment is not None:
        quality_confidence = quality_assessment.label_confidence
        quality_reasons = ()

    outcome_unresolved = (
        outcome is not None and outcome.label_status == OutcomeLabelStatus.UNRESOLVED
    )
    eligible, ineligibility = _eligibility_from_quality(
        quality_confidence=quality_confidence,
        quality_assessment=quality_assessment,
        outcome_unresolved=outcome_unresolved,
    )
    if quality_reasons:
        eligible = False
        ineligibility = tuple(sorted(set(ineligibility + quality_reasons)))

    reason_codes: list[str] = ["evidence_record"]
    base_score = _REPRESENTATIVE_BASELINE_SCORE
    if stream == LearningStream.REPRESENTATIVE:
        reason_codes.append("representative_sampling_stream")
    else:
        reason_codes.append("high_information_stream")
        payload = dict(record.payload)
        if payload.get("failure_case_type"):
            reason_codes.append("failure_surprise_abstention_signal")
            base_score += 0.20
        if record.evidence_class == TemporalEvidenceClass.FORWARD_SHADOW.value:
            reason_codes.append("forward_shadow_material")
            base_score += 0.10
        elif record.evidence_class == TemporalEvidenceClass.HISTORICAL_REPLAY.value:
            reason_codes.append("historical_replay_coverage")
            base_score += 0.05

    if not eligible:
        base_score = min(base_score, _REPRESENTATIVE_BASELINE_SCORE)

    learning_value = _deterministic_score(
        {
            "subject": record.evidence_id,
            "stream": stream.value,
            "policy_version": policy_version,
            "evidence_class": record.evidence_class,
            "base": base_score,
        },
        base_score,
    )

    provenance_ref = str(
        record.source_provenance.get("provenance_reference")
        or record.source_provenance.get("provenance")
        or record.evidence_id
    )

    return LearningValueResult(
        subject_or_case_id=record.evidence_id,
        learning_value=learning_value,
        priority=_priority_from_score(learning_value),
        reason_codes=tuple(reason_codes),
        evidence_class=record.evidence_class,
        quality_or_confidence=quality_confidence,
        failure_surprise_abstention_context={},
        provenance_reference=provenance_ref,
        eligible_for_learning=eligible,
        ineligibility_reasons=ineligibility,
        sampling_stream=stream.value,
        policy_version=policy_version,
    )


def evaluate_learning_value_for_corpus_case(
    case: FailureSurpriseCase,
    *,
    outcome: OutcomeContract | None = None,
    policy_version: str = LEARNING_VALUE_CONTRACT_VERSION,
) -> LearningValueResult:
    """
    TEMP-AR-0187: prioritize failure/surprise/abstention corpus cases explicitly.

    Corpus case records remain immutable; scoring is read-only.
    """
    validate_evidence_class_assignment(case.evidence_class)
    quality_assessment = assess_outcome_quality(outcome) if outcome is not None else None
    eligible, ineligibility = _eligibility_from_quality(
        quality_confidence=quality_assessment.label_confidence if quality_assessment else None,
        quality_assessment=quality_assessment,
        outcome_unresolved=case.outcome_unresolved,
    )

    boost = _HIGH_INFORMATION_FSA_BOOST.get(case.case_type, 0.15)
    base_score = _REPRESENTATIVE_BASELINE_SCORE + boost
    reason_codes = [
        "high_information_stream",
        "failure_surprise_abstention_case",
        f"case_type:{case.case_type.value}",
        f"capture_category:{case.capture_category.value}",
    ]
    if case.capture_category == CaptureCategory.ABSTENTION:
        reason_codes.append("abstention_learning_signal")
    if case.capture_category == CaptureCategory.SURPRISE:
        reason_codes.append("surprise_learning_signal")
    if case.capture_category == CaptureCategory.FAILURE:
        reason_codes.append("failure_learning_signal")

    if not eligible:
        base_score = min(base_score, _REPRESENTATIVE_BASELINE_SCORE)

    learning_value = _deterministic_score(
        {
            "subject": case.case_id,
            "policy_version": policy_version,
            "case_type": case.case_type.value,
            "base": base_score,
        },
        base_score,
    )

    return LearningValueResult(
        subject_or_case_id=case.case_id,
        learning_value=learning_value,
        priority=_priority_from_score(learning_value),
        reason_codes=tuple(reason_codes),
        evidence_class=case.evidence_class,
        quality_or_confidence=quality_assessment.label_confidence if quality_assessment else None,
        failure_surprise_abstention_context={
            "case_type": case.case_type.value,
            "capture_category": case.capture_category.value,
            "outcome_unresolved": case.outcome_unresolved,
            "root_cause": case.root_cause,
        },
        provenance_reference=case.provenance_reference,
        eligible_for_learning=eligible,
        ineligibility_reasons=ineligibility,
        sampling_stream=LearningStream.HIGH_INFORMATION.value,
        policy_version=policy_version,
    )


@dataclass
class LearningValueEngine:
    """TEMP-AR-0185..0189: dual-stream learning value prioritization."""

    policy_version: str = LEARNING_VALUE_CONTRACT_VERSION

    def evaluate_evidence(
        self,
        record: EvidenceRecord,
        *,
        outcome: OutcomeContract | None = None,
        stream: LearningStream = LearningStream.HIGH_INFORMATION,
    ) -> LearningValueResult:
        return evaluate_learning_value_for_evidence(
            record,
            outcome=outcome,
            policy_version=self.policy_version,
            stream=stream,
        )

    def evaluate_corpus_case(
        self,
        case: FailureSurpriseCase,
        *,
        outcome: OutcomeContract | None = None,
    ) -> LearningValueResult:
        return evaluate_learning_value_for_corpus_case(
            case,
            outcome=outcome,
            policy_version=self.policy_version,
        )

    def prioritize(
        self,
        *,
        evidence_records: Sequence[EvidenceRecord] = (),
        corpus_cases: Sequence[FailureSurpriseCase] = (),
        outcomes: Mapping[str, OutcomeContract] | None = None,
    ) -> tuple[LearningValueResult, ...]:
        """
        TEMP-AR-0189: representative stream preserved alongside high-information scores.

        Returns both streams for every subject; learning value score does not replace
        representative coverage.
        """
        outcomes = outcomes or {}
        results: list[LearningValueResult] = []
        for record in evidence_records:
            outcome = outcomes.get(record.evidence_id)
            results.append(
                self.evaluate_evidence(
                    record,
                    outcome=outcome,
                    stream=LearningStream.REPRESENTATIVE,
                )
            )
            results.append(
                self.evaluate_evidence(
                    record,
                    outcome=outcome,
                    stream=LearningStream.HIGH_INFORMATION,
                )
            )
        for case in corpus_cases:
            outcome = outcomes.get(case.outcome_id or "")
            results.append(self.evaluate_corpus_case(case, outcome=outcome))
        return tuple(sorted(results, key=lambda r: (-r.learning_value, r.subject_or_case_id)))

    def retention_vs_priority(
        self,
        result: LearningValueResult,
        *,
        access_frequency: str = "recent",
    ) -> dict[str, Any]:
        """TEMP-AR-0190: learning priority independent from retention policy."""
        tier = classify_storage_tier(access_frequency=access_frequency)
        descriptor = build_retention_descriptor(tier)
        return {
            "RETENTION_EQUALS_LEARNING_PRIORITY": RETENTION_EQUALS_LEARNING_PRIORITY,
            "learning_priority": result.priority,
            "learning_value": result.learning_value,
            "retention_tier": descriptor.tier.value,
            "delete_raw_for_low_learning_value": descriptor.delete_raw_for_low_learning_value,
            "retention_authority": "RETENTION_POLICY",
            "learning_priority_authority": "LEARNING_VALUE",
        }

    def attempt_model_mutation(self, result: LearningValueResult) -> None:
        raise ValueError("learning_value_auto_model_mutation_forbidden")

    def attempt_model_promotion(self, result: LearningValueResult) -> None:
        raise ValueError("learning_value_auto_model_promotion_forbidden")

    def attempt_evidence_promotion(self, result: LearningValueResult, to_class: str) -> None:
        if result.evidence_class != to_class:
            try:
                assert_no_automatic_promotion(result.evidence_class, to_class)
            except ValueError:
                pass
            raise ValueError(
                f"learning_value_evidence_promotion_forbidden: "
                f"{result.evidence_class} -> {to_class}"
            )


def learning_value_preserves_evidence_lineage(
    ledger: EvidenceProvenanceLedger,
    *,
    before_snapshot: tuple[Mapping[str, Any], ...],
) -> bool:
    """Verify P2 evidence ledger records remain unchanged after learning-value evaluation."""
    after = tuple(record.to_metadata() for record in ledger.list_records())
    return after == before_snapshot


def learning_value_preserves_corpus_cases(
    corpus: FailureSurpriseCorpus,
    *,
    before_snapshot: tuple[Mapping[str, Any], ...],
) -> bool:
    """Verify P3 corpus cases remain unchanged after learning-value evaluation."""
    after = tuple(case.to_metadata() for case in corpus.list_cases())
    return after == before_snapshot
