"""Champion/Challenger evaluation runtime — compare without auto-promotion (P4)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping

from blackdark.temporal.evidence_class import (
    TemporalEvidenceClass,
    assert_no_automatic_promotion,
    validate_evidence_class_assignment,
)
from blackdark.temporal.evidence_provenance import EvidenceProvenanceLedger, EvidenceRecord
from blackdark.temporal.forward_shadow import ForwardShadowReceipt
from blackdark.temporal.learning_value import LearningValueResult
from blackdark.temporal.outcome_contract import OutcomeContract
from blackdark.temporal.outcome_quality import assess_outcome_quality
from blackdark.temporal.replay_coverage import ReplayComparisonResult, compare_replay_runs

CHAMPION_CHALLENGER_CONTRACT_VERSION = "p4.champion_challenger.1.0"
UNPROVEN_CHAMPION_CHALLENGER_COMPARISON_FAILS_CLOSED = True
CHALLENGER_EVIDENCE_CLASS_COLLAPSE = 0
INSUFFICIENT_EVIDENCE_FORCES_WINNER = False
CHALLENGER_AUTO_PROMOTION = 0
CHAMPION_AUTO_REPLACEMENT = 0
PRODUCTION_MODEL_MUTATION = 0
CHAMPION_CHALLENGER_EVALUATION_DETERMINISTIC = True
DUPLICATE_OUTCOME_FACTORY = 0
DUPLICATE_EVIDENCE_LEDGER = 0
DUPLICATE_REPLAY_ENGINE = 0

_PROMOTION_PIPELINE_STAGES: tuple[str, ...] = (
    "outcome",
    "candidate_learning",
    "challenger",
    "historical_evaluation",
    "walk_forward",
    "regime_validation",
    "forward_shadow",
    "stability_review",
    "promotion_decision",
    "champion",
)

_REQUIRED_CONTEXT_KEYS: frozenset[str] = frozenset(
    {
        "evaluation_window",
        "input_identity_context",
        "dataset_or_source_versions",
        "parameters",
    }
)

_PRODUCTION_EVIDENCE_CLASSES: frozenset[str] = frozenset(
    {
        TemporalEvidenceClass.VERIFIED_PRODUCTION.value,
        TemporalEvidenceClass.INDEPENDENTLY_VERIFIED.value,
    }
)


class ComparisonStatus(str, Enum):
    COMPLETED = "COMPLETED"
    INCONCLUSIVE = "INCONCLUSIVE"
    REJECTED = "REJECTED"


class PromotionRecommendation(str, Enum):
    NONE = "none"
    REVIEW_REQUIRED = "review_required"
    REJECT_CHALLENGER = "reject_challenger"


@dataclass(frozen=True, slots=True)
class ChampionChallengerComparisonContext:
    """Proven comparison context required before champion/challenger evaluation."""

    champion_identity: str
    challenger_identity: str
    model_or_engine_versions: Mapping[str, str]
    evaluation_window: Mapping[str, str]
    input_identity_context: Mapping[str, Any]
    dataset_or_source_versions: Mapping[str, str]
    parameters: Mapping[str, Any]
    champion_evidence_class: str
    challenger_evidence_class: str
    policy_version: str = CHAMPION_CHALLENGER_CONTRACT_VERSION

    def to_metadata(self) -> dict[str, Any]:
        return {
            "champion_identity": self.champion_identity,
            "challenger_identity": self.challenger_identity,
            "model_or_engine_versions": dict(self.model_or_engine_versions),
            "evaluation_window": dict(self.evaluation_window),
            "input_identity_context": dict(self.input_identity_context),
            "dataset_or_source_versions": dict(self.dataset_or_source_versions),
            "parameters": dict(self.parameters),
            "champion_evidence_class": self.champion_evidence_class,
            "challenger_evidence_class": self.challenger_evidence_class,
            "policy_version": self.policy_version,
        }


@dataclass(frozen=True, slots=True)
class ChampionChallengerEvaluationResult:
    """Structured champion/challenger evaluation output."""

    evaluation_id: str
    champion_identity: str
    challenger_identity: str
    model_or_engine_versions: Mapping[str, str]
    evaluation_window: Mapping[str, str]
    input_identity_context: Mapping[str, Any]
    dataset_or_source_versions: Mapping[str, str]
    parameters: Mapping[str, Any]
    evidence_class: str
    champion_evidence_class: str
    challenger_evidence_class: str
    outcome_quality: Mapping[str, Any] | None
    comparison_metrics: Mapping[str, Any]
    comparison_status: str
    reason_codes: tuple[str, ...]
    promotion_pipeline_stages_completed: tuple[str, ...]
    promotion_recommendation: str
    promotion_recommendation_reviewable: bool
    evidence_lineage: tuple[str, ...]
    learning_value_metadata: Mapping[str, Any] | None
    replay_comparison: Mapping[str, Any] | None
    policy_version: str

    def to_metadata(self) -> dict[str, Any]:
        return {
            "evaluation_id": self.evaluation_id,
            "champion_identity": self.champion_identity,
            "challenger_identity": self.challenger_identity,
            "model_or_engine_versions": dict(self.model_or_engine_versions),
            "evaluation_window": dict(self.evaluation_window),
            "input_identity_context": dict(self.input_identity_context),
            "dataset_or_source_versions": dict(self.dataset_or_source_versions),
            "parameters": dict(self.parameters),
            "evidence_class": self.evidence_class,
            "champion_evidence_class": self.champion_evidence_class,
            "challenger_evidence_class": self.challenger_evidence_class,
            "outcome_quality": dict(self.outcome_quality or {}),
            "comparison_metrics": dict(self.comparison_metrics),
            "comparison_status": self.comparison_status,
            "reason_codes": list(self.reason_codes),
            "promotion_pipeline_stages_completed": list(self.promotion_pipeline_stages_completed),
            "promotion_recommendation": self.promotion_recommendation,
            "promotion_recommendation_reviewable": self.promotion_recommendation_reviewable,
            "evidence_lineage": list(self.evidence_lineage),
            "learning_value_metadata": dict(self.learning_value_metadata or {}),
            "replay_comparison": dict(self.replay_comparison or {}),
            "policy_version": self.policy_version,
        }


def _deterministic_evaluation_id(payload: Mapping[str, Any]) -> str:
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, default=str).encode()
    ).hexdigest()[:16]
    return f"cc_eval_{digest}"


def _validate_context_provenance(context: ChampionChallengerComparisonContext) -> tuple[str, ...]:
    reason_codes: list[str] = []
    for key in sorted(_REQUIRED_CONTEXT_KEYS):
        value = getattr(context, key, None)
        if not value:
            reason_codes.append(f"MISSING_CONTEXT:{key}")
    validate_evidence_class_assignment(context.champion_evidence_class)
    validate_evidence_class_assignment(context.challenger_evidence_class)
    if context.champion_evidence_class != context.challenger_evidence_class:
        if (
            context.champion_evidence_class in _PRODUCTION_EVIDENCE_CLASSES
            and context.challenger_evidence_class == TemporalEvidenceClass.HISTORICAL_REPLAY.value
        ) or (
            context.challenger_evidence_class in _PRODUCTION_EVIDENCE_CLASSES
            and context.champion_evidence_class == TemporalEvidenceClass.HISTORICAL_REPLAY.value
        ):
            reason_codes.append("EVIDENCE_CLASS_AUTHORITY_MISMATCH")
    if context.champion_evidence_class == context.challenger_evidence_class:
        pass
    elif (
        context.champion_evidence_class == TemporalEvidenceClass.HISTORICAL_REPLAY.value
        and context.challenger_evidence_class == TemporalEvidenceClass.FORWARD_SHADOW.value
    ) or (
        context.challenger_evidence_class == TemporalEvidenceClass.HISTORICAL_REPLAY.value
        and context.champion_evidence_class == TemporalEvidenceClass.FORWARD_SHADOW.value
    ):
        reason_codes.append("CROSS_CLASS_COMPARISON_REQUIRES_EXPLICIT_PIPELINE")
    return tuple(sorted(set(reason_codes)))


def _evidence_class_collapse_detected(
    context: ChampionChallengerComparisonContext,
    *,
    champion_record: EvidenceRecord | None,
    challenger_record: EvidenceRecord | None,
) -> bool:
    if champion_record is not None and champion_record.evidence_class != context.champion_evidence_class:
        return True
    if challenger_record is not None and challenger_record.evidence_class != context.challenger_evidence_class:
        return True
    collapsed = context.champion_evidence_class
    if (
        collapsed == TemporalEvidenceClass.HISTORICAL_REPLAY.value
        and context.challenger_evidence_class in _PRODUCTION_EVIDENCE_CLASSES
    ):
        return True
    return False


def _completed_pipeline_stages(
    *,
    outcome: OutcomeContract | None,
    replay_comparison: ReplayComparisonResult | None,
    forward_shadow_receipt: ForwardShadowReceipt | None,
    stability_review_passed: bool,
) -> tuple[str, ...]:
    stages: list[str] = ["challenger"]
    if outcome is not None:
        stages.append("outcome")
    if replay_comparison is not None and replay_comparison.comparable:
        stages.extend(["historical_evaluation", "walk_forward", "regime_validation"])
    if forward_shadow_receipt is not None:
        stages.append("forward_shadow")
    if stability_review_passed:
        stages.append("stability_review")
    if len(stages) >= 7:
        stages.append("promotion_decision")
    return tuple(stages)


@dataclass
class ChampionChallengerEvaluator:
    """
    TEMP-AR-0230..0232: evaluate champion/challenger without autonomous promotion.

    Reuses P1 replay comparability; reads P2 evidence/outcome quality; accepts P3
    forward-shadow receipts and optional P4 learning-value metadata as inputs only.
    """

    policy_version: str = CHAMPION_CHALLENGER_CONTRACT_VERSION
    current_champion_identity: str = "champion-default"
    _evaluations: list[ChampionChallengerEvaluationResult] = field(default_factory=list)

    def evaluate(
        self,
        context: ChampionChallengerComparisonContext,
        *,
        outcome: OutcomeContract | None = None,
        champion_evidence: EvidenceRecord | None = None,
        challenger_evidence: EvidenceRecord | None = None,
        baseline_replay_result: Mapping[str, Any] | None = None,
        challenger_replay_result: Mapping[str, Any] | None = None,
        forward_shadow_receipt: ForwardShadowReceipt | None = None,
        learning_value: LearningValueResult | None = None,
        stability_review_passed: bool = False,
        proven_replay_context_keys: frozenset[str] | None = None,
    ) -> ChampionChallengerEvaluationResult:
        reason_codes = list(_validate_context_provenance(context))
        comparison_status = ComparisonStatus.REJECTED
        promotion_recommendation = PromotionRecommendation.NONE.value
        comparison_metrics: dict[str, Any] = {}
        replay_comparison_meta: dict[str, Any] | None = None
        replay_comparison: ReplayComparisonResult | None = None

        if _evidence_class_collapse_detected(
            context,
            champion_record=champion_evidence,
            challenger_record=challenger_evidence,
        ):
            reason_codes.append("EVIDENCE_CLASS_COLLAPSE")

        outcome_quality_meta: dict[str, Any] | None = None
        if outcome is not None:
            quality = assess_outcome_quality(outcome)
            outcome_quality_meta = quality.to_metadata()
            if not quality.equivalent_to_direct_truth:
                reason_codes.append("OUTCOME_QUALITY_UNPROVEN")

        lineage: list[str] = []
        if champion_evidence is not None:
            lineage.extend(champion_evidence.lineage)
            if champion_evidence.evidence_class != context.champion_evidence_class:
                reason_codes.append("CHAMPION_EVIDENCE_CLASS_DRIFT")
        if challenger_evidence is not None:
            lineage.extend(challenger_evidence.lineage)
            if challenger_evidence.evidence_class != context.challenger_evidence_class:
                reason_codes.append("CHALLENGER_EVIDENCE_CLASS_DRIFT")

        if baseline_replay_result is not None and challenger_replay_result is not None:
            replay_comparison = compare_replay_runs(
                baseline_replay_result,
                challenger_replay_result,
                baseline_run_id=context.champion_identity,
                challenger_run_id=context.challenger_identity,
                proven_context_keys=proven_replay_context_keys,
            )
            replay_comparison_meta = {
                "comparable": replay_comparison.comparable,
                "reason_codes": list(replay_comparison.reason_codes),
                "context_differences": list(replay_comparison.context_differences),
                "comparison_outputs": dict(replay_comparison.comparison_outputs),
                "evidence_class": replay_comparison.evidence_class,
            }
            if not replay_comparison.comparable:
                reason_codes.extend(replay_comparison.reason_codes)
                reason_codes.append("UNPROVEN_COMPARISON_CONTEXT")
            else:
                comparison_metrics.update(dict(replay_comparison.comparison_outputs))
                comparison_metrics["replay_evidence_class"] = replay_comparison.evidence_class
        elif baseline_replay_result is not None or challenger_replay_result is not None:
            reason_codes.append("INCOMPLETE_REPLAY_PAIR")
            reason_codes.append("INSUFFICIENT_EVIDENCE")

        if forward_shadow_receipt is not None:
            if forward_shadow_receipt.evidence_class != TemporalEvidenceClass.FORWARD_SHADOW.value:
                reason_codes.append("FORWARD_SHADOW_CLASS_VIOLATION")

        stages = _completed_pipeline_stages(
            outcome=outcome,
            replay_comparison=replay_comparison,
            forward_shadow_receipt=forward_shadow_receipt,
            stability_review_passed=stability_review_passed,
        )

        final_reason_codes = sorted(set(reason_codes))
        reject_codes = {
            "CONTEXT_MISMATCH",
            "UNPROVEN_CONTEXT",
            "UNPROVEN_COMPARISON_CONTEXT",
            "EVIDENCE_CLASS_COLLAPSE",
            "CHAMPION_EVIDENCE_CLASS_DRIFT",
            "CHALLENGER_EVIDENCE_CLASS_DRIFT",
            "FORWARD_SHADOW_CLASS_VIOLATION",
            "EVIDENCE_CLASS_AUTHORITY_MISMATCH",
        }
        if final_reason_codes:
            if any(code in final_reason_codes for code in reject_codes):
                comparison_status = ComparisonStatus.REJECTED
            else:
                comparison_status = ComparisonStatus.INCONCLUSIVE
        elif replay_comparison is None and forward_shadow_receipt is None:
            comparison_status = ComparisonStatus.INCONCLUSIVE
            final_reason_codes = ["INSUFFICIENT_EVIDENCE"]
        else:
            comparison_status = ComparisonStatus.COMPLETED
            challenger_better = bool(
                comparison_metrics.get("fingerprints_match") is False
                and comparison_metrics.get("challenger_admitted_count", 0)
                >= comparison_metrics.get("baseline_admitted_count", 0)
            )
            only_historical = (
                context.champion_evidence_class == TemporalEvidenceClass.HISTORICAL_REPLAY.value
                and context.challenger_evidence_class == TemporalEvidenceClass.HISTORICAL_REPLAY.value
            )
            if challenger_better and only_historical:
                final_reason_codes = ["HISTORICAL_REPLAY_NOT_PRODUCTION_SUPERIORITY"]
                comparison_status = ComparisonStatus.INCONCLUSIVE
                promotion_recommendation = PromotionRecommendation.NONE.value
            elif challenger_better and "forward_shadow" in stages and stability_review_passed:
                promotion_recommendation = PromotionRecommendation.REVIEW_REQUIRED.value
            elif challenger_better:
                comparison_status = ComparisonStatus.INCONCLUSIVE
                promotion_recommendation = PromotionRecommendation.NONE.value
                final_reason_codes = ["INSUFFICIENT_PIPELINE_FOR_PROMOTION"]
            else:
                promotion_recommendation = PromotionRecommendation.REJECT_CHALLENGER.value

        primary_evidence_class = context.challenger_evidence_class
        evaluation_id = _deterministic_evaluation_id(
            {
                "context": context.to_metadata(),
                "comparison_status": comparison_status.value,
                "reason_codes": final_reason_codes,
                "policy_version": self.policy_version,
            }
        )

        result = ChampionChallengerEvaluationResult(
            evaluation_id=evaluation_id,
            champion_identity=context.champion_identity,
            challenger_identity=context.challenger_identity,
            model_or_engine_versions=dict(context.model_or_engine_versions),
            evaluation_window=dict(context.evaluation_window),
            input_identity_context=dict(context.input_identity_context),
            dataset_or_source_versions=dict(context.dataset_or_source_versions),
            parameters=dict(context.parameters),
            evidence_class=primary_evidence_class,
            champion_evidence_class=context.champion_evidence_class,
            challenger_evidence_class=context.challenger_evidence_class,
            outcome_quality=outcome_quality_meta,
            comparison_metrics=comparison_metrics,
            comparison_status=comparison_status.value,
            reason_codes=tuple(final_reason_codes),
            promotion_pipeline_stages_completed=stages,
            promotion_recommendation=promotion_recommendation,
            promotion_recommendation_reviewable=(
                promotion_recommendation == PromotionRecommendation.REVIEW_REQUIRED.value
            ),
            evidence_lineage=tuple(sorted(set(lineage))),
            learning_value_metadata=learning_value.to_metadata() if learning_value else None,
            replay_comparison=replay_comparison_meta,
            policy_version=self.policy_version,
        )
        self._evaluations.append(result)
        return result

    def list_evaluations(self) -> tuple[ChampionChallengerEvaluationResult, ...]:
        return tuple(self._evaluations)

    def attempt_auto_promote_challenger(self, result: ChampionChallengerEvaluationResult) -> None:
        raise ValueError("challenger_auto_promotion_forbidden")

    def attempt_replace_champion(self, result: ChampionChallengerEvaluationResult) -> None:
        raise ValueError("champion_auto_replacement_forbidden")

    def attempt_production_model_mutation(self, result: ChampionChallengerEvaluationResult) -> None:
        raise ValueError("production_model_mutation_forbidden")

    def attempt_evidence_class_promotion(
        self,
        result: ChampionChallengerEvaluationResult,
        to_class: str,
    ) -> None:
        assert_no_automatic_promotion(result.champion_evidence_class, to_class)
        assert_no_automatic_promotion(result.challenger_evidence_class, to_class)
        raise ValueError(
            f"champion_challenger_evidence_promotion_forbidden: "
            f"{result.challenger_evidence_class} -> {to_class}"
        )


def champion_challenger_preserves_evidence_lineage(
    ledger: EvidenceProvenanceLedger,
    *,
    before_snapshot: tuple[Mapping[str, Any], ...],
) -> bool:
    after = tuple(record.to_metadata() for record in ledger.list_records())
    return after == before_snapshot


def promotion_pipeline_stages() -> tuple[str, ...]:
    return _PROMOTION_PIPELINE_STAGES
