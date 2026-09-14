"""Controlled Learning runtime — candidates without autonomous production change (P4)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Sequence

from blackdark.temporal.champion_challenger import ChampionChallengerEvaluator
from blackdark.temporal.evidence_class import (
    TemporalEvidenceClass,
    assert_no_automatic_promotion,
    validate_evidence_class_assignment,
)
from blackdark.temporal.evidence_provenance import EvidenceProvenanceLedger, EvidenceRecord
from blackdark.temporal.failure_surprise_corpus import FailureSurpriseCase
from blackdark.temporal.learning_value import LearningValueResult
from blackdark.temporal.outcome_contract import OutcomeContract, OutcomeLabelStatus
from blackdark.temporal.outcome_quality import assess_outcome_quality

CONTROLLED_LEARNING_CONTRACT_VERSION = "p4.controlled_learning.1.0"
UNCONTROLLED_PRODUCTION_SELF_MODIFICATION = 0
AUTONOMOUS_MODEL_PROMOTION = 0
AUTONOMOUS_PRODUCTION_MODEL_REPLACEMENT = 0
LEARNING_RECOMMENDATION_IMPLIES_PROMOTION = False
EVALUATION_IMPLIES_DEPLOYMENT = False
CONTROLLED_LEARNING_PRODUCTION_MUTATION = 0
CONTROLLED_LEARNING_HISTORY_MUTATION = 0
CONTROLLED_LEARNING_EVIDENCE_PROMOTION = 0
CONTROLLED_LEARNING_EVALUATION_DETERMINISTIC = True
ADAPTIVE_ONLINE_PRODUCTION_LEARNING_ENABLED = False
DUPLICATE_OUTCOME_FACTORY = 0
DUPLICATE_EVIDENCE_LEDGER = 0
DUPLICATE_LEARNING_VALUE_ENGINE = 0
DUPLICATE_CHAMPION_CHALLENGER = 0

_PROMOTION_GATE_REQUIRED = True


class CandidateArtifactType(str, Enum):
    """TEMP-AR-0234..0238 candidate artifact kinds."""

    WEIGHTS = "candidate_weights"
    MODEL = "candidate_model"
    RULES = "candidate_rules"
    CALIBRATION = "candidate_calibration_changes"
    THRESHOLDS = "candidate_thresholds"


class ApprovalState(str, Enum):
    PENDING = "pending"
    APPROVED_FOR_EVALUATION = "approved_for_evaluation"
    REJECTED = "rejected"
    INELIGIBLE = "ineligible"


class ValidationState(str, Enum):
    UNVALIDATED = "unvalidated"
    VALIDATED = "validated"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class ControlledLearningRequest:
    """Controlled learning request derived from proven upstream evidence."""

    learning_request_id: str
    source_case_or_evidence_ids: tuple[str, ...]
    learning_value_context: Mapping[str, Any]
    evidence_classes: tuple[str, ...]
    outcome_quality: Mapping[str, Any] | None
    current_model_identity: str
    candidate_identity: str
    proposed_change: Mapping[str, Any]
    approval_state: str
    validation_state: str
    reason_codes: tuple[str, ...]
    provenance: Mapping[str, Any]
    version: str
    artifact_type: str
    eligible_for_learning: bool

    def to_metadata(self) -> dict[str, Any]:
        return {
            "learning_request_id": self.learning_request_id,
            "source_case_or_evidence_ids": list(self.source_case_or_evidence_ids),
            "learning_value_context": dict(self.learning_value_context),
            "evidence_classes": list(self.evidence_classes),
            "outcome_quality": dict(self.outcome_quality or {}),
            "current_model_identity": self.current_model_identity,
            "candidate_identity": self.candidate_identity,
            "proposed_change": dict(self.proposed_change),
            "approval_state": self.approval_state,
            "validation_state": self.validation_state,
            "reason_codes": list(self.reason_codes),
            "provenance": dict(self.provenance),
            "version": self.version,
            "artifact_type": self.artifact_type,
            "eligible_for_learning": self.eligible_for_learning,
        }


@dataclass(frozen=True, slots=True)
class ControlledLearningEvaluationResult:
    """Deterministic controlled-learning evaluation without deployment."""

    learning_request_id: str
    candidate_identity: str
    current_model_identity: str
    evaluation_id: str
    recommendation: str
    approval_state: str
    validation_state: str
    reason_codes: tuple[str, ...]
    evidence_classes: tuple[str, ...]
    outcome_quality: Mapping[str, Any] | None
    learning_value_context: Mapping[str, Any]
    provenance: Mapping[str, Any]
    version: str
    promotion_gate_required: bool
    deployed: bool

    def to_metadata(self) -> dict[str, Any]:
        return {
            "learning_request_id": self.learning_request_id,
            "candidate_identity": self.candidate_identity,
            "current_model_identity": self.current_model_identity,
            "evaluation_id": self.evaluation_id,
            "recommendation": self.recommendation,
            "approval_state": self.approval_state,
            "validation_state": self.validation_state,
            "reason_codes": list(self.reason_codes),
            "evidence_classes": list(self.evidence_classes),
            "outcome_quality": dict(self.outcome_quality or {}),
            "learning_value_context": dict(self.learning_value_context),
            "provenance": dict(self.provenance),
            "version": self.version,
            "promotion_gate_required": self.promotion_gate_required,
            "deployed": self.deployed,
        }


def _deterministic_id(prefix: str, payload: Mapping[str, Any]) -> str:
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, default=str).encode()
    ).hexdigest()[:16]
    return f"{prefix}_{digest}"


def _eligibility_reasons(
    *,
    learning_value: LearningValueResult | None,
    outcome: OutcomeContract | None,
    evidence_records: Sequence[EvidenceRecord],
) -> tuple[bool, tuple[str, ...]]:
    reasons: list[str] = []
    if learning_value is not None and not learning_value.eligible_for_learning:
        reasons.extend(learning_value.ineligibility_reasons)
    if outcome is not None:
        quality = assess_outcome_quality(outcome)
        if not quality.equivalent_to_direct_truth:
            reasons.append("outcome_quality_unproven")
        if outcome.label_status == OutcomeLabelStatus.UNRESOLVED:
            reasons.append("outcome_unresolved")
    for record in evidence_records:
        validate_evidence_class_assignment(record.evidence_class)
        if not record.quality_state:
            reasons.append(f"evidence_quality_unproven:{record.evidence_id}")
    if reasons:
        return False, tuple(sorted(set(reasons)))
    if learning_value is None and outcome is None and not evidence_records:
        return False, ("no_proven_learning_inputs",)
    return True, ()


@dataclass
class ControlledLearningEngine:
    """
    TEMP-AR-0233..0240: generate controlled learning candidates without production mutation.

    Reuses P2 evidence/outcome quality, P3 FSA corpus lineage, P4 learning value, and
    reads champion/challenger state without mutating it.
    """

    policy_version: str = CONTROLLED_LEARNING_CONTRACT_VERSION
    current_production_model_identity: str = "production-model-v1"
    _requests: list[ControlledLearningRequest] = field(default_factory=list)
    _evaluations: list[ControlledLearningEvaluationResult] = field(default_factory=list)

    def create_request(
        self,
        *,
        artifact_type: CandidateArtifactType,
        proposed_change: Mapping[str, Any],
        learning_value: LearningValueResult | None = None,
        outcome: OutcomeContract | None = None,
        evidence_records: Sequence[EvidenceRecord] = (),
        corpus_case: FailureSurpriseCase | None = None,
        candidate_identity: str | None = None,
    ) -> ControlledLearningRequest:
        eligible, ineligibility = _eligibility_reasons(
            learning_value=learning_value,
            outcome=outcome,
            evidence_records=evidence_records,
        )
        source_ids: list[str] = [record.evidence_id for record in evidence_records]
        if corpus_case is not None:
            source_ids.append(corpus_case.case_id)
        if learning_value is not None:
            source_ids.append(learning_value.subject_or_case_id)

        evidence_classes = tuple(
            sorted(
                {
                    *(record.evidence_class for record in evidence_records),
                    *( [learning_value.evidence_class] if learning_value else [] ),
                    *( [corpus_case.evidence_class] if corpus_case else [] ),
                }
            )
        )

        outcome_quality_meta = (
            assess_outcome_quality(outcome).to_metadata() if outcome is not None else None
        )
        learning_value_context = (
            learning_value.to_metadata() if learning_value is not None else {}
        )

        provenance: dict[str, Any] = {
            "policy_version": self.policy_version,
            "promotion_gate_required": _PROMOTION_GATE_REQUIRED,
        }
        if corpus_case is not None:
            provenance["fsa_lineage"] = list(corpus_case.lineage)
            provenance["fsa_traceability"] = corpus_case.traceability.to_metadata()

        candidate_id = candidate_identity or _deterministic_id(
            "candidate",
            {
                "artifact_type": artifact_type.value,
                "current_model": self.current_production_model_identity,
                "proposed_change": dict(proposed_change),
                "source_ids": source_ids,
            },
        )

        approval_state = (
            ApprovalState.PENDING.value
            if eligible
            else ApprovalState.INELIGIBLE.value
        )
        reason_codes = () if eligible else ineligibility

        request_id = _deterministic_id(
            "cl_req",
            {
                "candidate_id": candidate_id,
                "artifact_type": artifact_type.value,
                "source_ids": source_ids,
                "policy_version": self.policy_version,
            },
        )

        request = ControlledLearningRequest(
            learning_request_id=request_id,
            source_case_or_evidence_ids=tuple(sorted(set(source_ids))),
            learning_value_context=learning_value_context,
            evidence_classes=evidence_classes,
            outcome_quality=outcome_quality_meta,
            current_model_identity=self.current_production_model_identity,
            candidate_identity=candidate_id,
            proposed_change=dict(proposed_change),
            approval_state=approval_state,
            validation_state=ValidationState.UNVALIDATED.value,
            reason_codes=reason_codes,
            provenance=provenance,
            version=self.policy_version,
            artifact_type=artifact_type.value,
            eligible_for_learning=eligible,
        )
        self._requests.append(request)
        return request

    def evaluate_request(
        self,
        request: ControlledLearningRequest,
        *,
        champion_challenger: ChampionChallengerEvaluator | None = None,
    ) -> ControlledLearningEvaluationResult:
        """Evaluate candidate deterministically; does not deploy or promote."""
        if champion_challenger is not None:
            _ = champion_challenger.current_champion_identity

        if not request.eligible_for_learning:
            result = ControlledLearningEvaluationResult(
                learning_request_id=request.learning_request_id,
                candidate_identity=request.candidate_identity,
                current_model_identity=self.current_production_model_identity,
                evaluation_id=_deterministic_id(
                    "cl_eval",
                    {
                        "request_id": request.learning_request_id,
                        "state": "ineligible",
                        "policy_version": self.policy_version,
                    },
                ),
                recommendation="reject_candidate",
                approval_state=ApprovalState.INELIGIBLE.value,
                validation_state=ValidationState.FAILED.value,
                reason_codes=request.reason_codes,
                evidence_classes=request.evidence_classes,
                outcome_quality=request.outcome_quality,
                learning_value_context=request.learning_value_context,
                provenance=request.provenance,
                version=self.policy_version,
                promotion_gate_required=_PROMOTION_GATE_REQUIRED,
                deployed=False,
            )
            self._evaluations.append(result)
            return result

        recommendation = "review_for_champion_challenger"
        validation_state = ValidationState.VALIDATED.value
        approval_state = ApprovalState.APPROVED_FOR_EVALUATION.value
        reason_codes: tuple[str, ...] = ("controlled_learning_candidate_validated",)

        if ADAPTIVE_ONLINE_PRODUCTION_LEARNING_ENABLED:
            reason_codes = tuple(
                sorted(
                    set(
                        list(reason_codes)
                        + ["adaptive_online_production_learning_restricted"]
                    )
                )
            )
            recommendation = "reject_candidate"
            validation_state = ValidationState.FAILED.value
            approval_state = ApprovalState.REJECTED.value

        evaluation_id = _deterministic_id(
            "cl_eval",
            {
                "request_id": request.learning_request_id,
                "recommendation": recommendation,
                "validation_state": validation_state,
                "policy_version": self.policy_version,
            },
        )

        result = ControlledLearningEvaluationResult(
            learning_request_id=request.learning_request_id,
            candidate_identity=request.candidate_identity,
            current_model_identity=self.current_production_model_identity,
            evaluation_id=evaluation_id,
            recommendation=recommendation,
            approval_state=approval_state,
            validation_state=validation_state,
            reason_codes=reason_codes,
            evidence_classes=request.evidence_classes,
            outcome_quality=request.outcome_quality,
            learning_value_context=request.learning_value_context,
            provenance=request.provenance,
            version=self.policy_version,
            promotion_gate_required=_PROMOTION_GATE_REQUIRED,
            deployed=False,
        )
        self._evaluations.append(result)
        return result

    def list_requests(self) -> tuple[ControlledLearningRequest, ...]:
        return tuple(self._requests)

    def list_evaluations(self) -> tuple[ControlledLearningEvaluationResult, ...]:
        return tuple(self._evaluations)

    def attempt_autonomous_promotion(self, result: ControlledLearningEvaluationResult) -> None:
        raise ValueError("autonomous_model_promotion_forbidden")

    def attempt_production_replacement(self, result: ControlledLearningEvaluationResult) -> None:
        raise ValueError("autonomous_production_model_replacement_forbidden")

    def attempt_production_mutation(self, result: ControlledLearningEvaluationResult) -> None:
        raise ValueError("controlled_learning_production_mutation_forbidden")

    def attempt_history_mutation(
        self,
        ledger: EvidenceProvenanceLedger,
        *,
        evidence_id: str,
    ) -> None:
        raise ValueError("controlled_learning_history_mutation_forbidden")

    def attempt_evidence_promotion(
        self,
        result: ControlledLearningEvaluationResult,
        to_class: str,
    ) -> None:
        for evidence_class in result.evidence_classes:
            if evidence_class != to_class:
                try:
                    assert_no_automatic_promotion(evidence_class, to_class)
                except ValueError:
                    pass
        raise ValueError(
            f"controlled_learning_evidence_promotion_forbidden: -> {to_class}"
        )

    def attempt_deploy(self, result: ControlledLearningEvaluationResult) -> None:
        raise ValueError("evaluation_implies_deployment_forbidden")


def controlled_learning_preserves_evidence_lineage(
    ledger: EvidenceProvenanceLedger,
    *,
    before_snapshot: tuple[Mapping[str, Any], ...],
) -> bool:
    after = tuple(record.to_metadata() for record in ledger.list_records())
    return after == before_snapshot


def controlled_learning_preserves_corpus_case(
    case: FailureSurpriseCase,
    *,
    before_metadata: Mapping[str, Any],
) -> bool:
    return case.to_metadata() == before_metadata


def controlled_learning_preserves_champion_state(
    evaluator: ChampionChallengerEvaluator,
    *,
    before_champion_identity: str,
) -> bool:
    return evaluator.current_champion_identity == before_champion_identity
