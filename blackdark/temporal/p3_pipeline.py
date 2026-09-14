"""P3 orchestration: forward shadow → regime → drift → failure corpus."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping

from blackdark.temporal.drift_monitoring import DriftMonitorResult, evaluate_drift
from blackdark.temporal.evidence_class import TemporalEvidenceClass
from blackdark.temporal.evidence_provenance import EvidenceProvenanceLedger
from blackdark.temporal.failure_surprise_corpus import FailureSurpriseCorpus
from blackdark.temporal.forward_shadow import ForwardShadowLedger, ForwardShadowReceipt
from blackdark.temporal.outcome_contract import OutcomeContract
from blackdark.temporal.regime_intelligence import (
    RegimeContext,
    RegimeDecomposedEvaluation,
    classify_regime,
    evaluate_by_regime,
)
from blackdark.temporal.reality_anchor import RealityAnchorStatus, evaluate_reality_anchor

DUPLICATE_OUTCOME_FACTORY = 0
DUPLICATE_EVIDENCE_LEDGER = 0


@dataclass(frozen=True, slots=True)
class P3PipelineResult:
    shadow_receipt: ForwardShadowReceipt
    regime_context: RegimeContext
    drift_result: DriftMonitorResult
    reality_anchor: RealityAnchorStatus
    regime_evaluation: RegimeDecomposedEvaluation | None
    failure_cases: tuple[Any, ...]
    linked_outcome_id: str | None
    evidence_class: str

    def to_metadata(self) -> dict[str, Any]:
        return {
            "shadow_receipt": self.shadow_receipt.to_metadata(),
            "regime_context": self.regime_context.to_metadata(),
            "drift_result": self.drift_result.to_metadata(),
            "reality_anchor": self.reality_anchor.to_metadata(),
            "regime_evaluation": (
                self.regime_evaluation.to_metadata() if self.regime_evaluation else None
            ),
            "failure_cases": [c.to_metadata() for c in self.failure_cases],
            "linked_outcome_id": self.linked_outcome_id,
            "evidence_class": self.evidence_class,
        }


def run_forward_shadow_pipeline(
    *,
    subject_identity: str,
    input_identity: str,
    prediction: Any,
    confidence: float,
    abstention_state: str,
    issued_at: datetime,
    evaluation_time: datetime,
    temporal_context: Mapping[str, Any],
    source_context: Mapping[str, Any],
    model_version: str = "model-v1",
    rule_config_version: str = "rule-v1",
    dataset_version: str = "ds-1",
    code_version: str = "code-v1",
    input_snapshot_hash: str = "hash-0",
    regime_indicators: Mapping[str, Any] | None = None,
    drift_baseline: Mapping[str, Any] | None = None,
    drift_current: Mapping[str, Any] | None = None,
    outcome: OutcomeContract | None = None,
    outcome_known_at: datetime | None = None,
    shadow_ledger: ForwardShadowLedger | None = None,
    failure_corpus: FailureSurpriseCorpus | None = None,
    evidence_ledger: EvidenceProvenanceLedger | None = None,
    uses_simulated_time: bool = True,
) -> P3PipelineResult:
    """Execute canonical P3 forward-shadow path reusing P2 boundaries."""
    ledger = shadow_ledger or ForwardShadowLedger()
    corpus = failure_corpus or FailureSurpriseCorpus()
    evidence = evidence_ledger or EvidenceProvenanceLedger()

    receipt = ledger.create_pre_outcome_receipt(
        subject_identity=subject_identity,
        input_identity=input_identity,
        decision_or_prediction_identity=f"pred:{subject_identity}",
        model_version=model_version,
        rule_config_version=rule_config_version,
        dataset_version=dataset_version,
        code_version=code_version,
        input_snapshot_hash=input_snapshot_hash,
        prediction=prediction,
        confidence=confidence,
        abstention_state=abstention_state,
        issued_at=issued_at,
        temporal_context=temporal_context,
        source_or_dataset_context=source_context,
        canonical_outcome=outcome,
    )

    regime = classify_regime(
        observation_time=issued_at,
        available_at=issued_at,
        evaluation_time=evaluation_time,
        indicators=dict(regime_indicators or {}),
    )

    drift = evaluate_drift(
        baseline=dict(drift_baseline or {}),
        current=dict(drift_current or {}),
        sufficient_evidence=bool(drift_baseline and drift_current),
    )

    anchor = evaluate_reality_anchor(
        anchor_id=receipt.shadow_receipt_id,
        receipt_issued_at=issued_at,
        evaluation_time=evaluation_time,
        uses_simulated_time=uses_simulated_time,
    )

    linked_outcome_id: str | None = None
    failure_cases: list = []

    if outcome is not None and outcome_known_at is not None:
        linked = ledger.mark_outcome_known(
            receipt.shadow_receipt_id,
            outcome_known_at=outcome_known_at,
            linked_outcome_id=outcome.outcome_id,
        )
        linked_outcome_id = linked.linked_outcome_id
        case = corpus.classify_from_shadow_outcome(
            case_id=f"case_{receipt.shadow_receipt_id}",
            shadow_receipt_id=receipt.shadow_receipt_id,
            outcome_id=outcome.outcome_id,
            prediction_confidence=confidence or 0.0,
            prediction_correct=outcome.directional_correctness,
            abstained=abstention_state == "abstain",
            should_have_abstained=outcome.realized_result is None,
            evidence_class=TemporalEvidenceClass.FORWARD_SHADOW.value,
            recorded_at=outcome_known_at,
            model_version=model_version,
            outcome=outcome,
            temporal_context=dict(temporal_context),
            provenance_reference=receipt.provenance_reference,
        )
        if case is not None:
            failure_cases.append(case)

        evidence.record_evidence(
            evidence_class=TemporalEvidenceClass.FORWARD_SHADOW.value,
            producer="p3_forward_shadow_pipeline",
            source_provenance=dict(source_context),
            temporal_context=dict(temporal_context),
            versions={"model_version": model_version, "evaluator_version": outcome.evaluator_version},
            lineage=(receipt.shadow_receipt_id, outcome.outcome_id),
            quality_state={"label_status": outcome.label_status.value},
            limitations=(),
            methodology="forward_shadow_outcome_linkage",
            timestamps={"issued_at": issued_at.isoformat(), "outcome_at": outcome_known_at.isoformat()},
            evaluator_identity=outcome.evaluator_version,
            payload={
                "receipt": receipt.to_metadata(),
                "outcome": outcome.to_metadata(),
            },
        )

    regime_eval: RegimeDecomposedEvaluation | None = None
    if outcome is not None:
        regime_eval = evaluate_by_regime(
            [
                {
                    "regime_context": regime.to_metadata(),
                    "success": outcome.directional_correctness,
                }
            ]
        )

    return P3PipelineResult(
        shadow_receipt=receipt,
        regime_context=regime,
        drift_result=drift,
        reality_anchor=anchor,
        regime_evaluation=regime_eval,
        failure_cases=tuple(failure_cases),
        linked_outcome_id=linked_outcome_id,
        evidence_class=TemporalEvidenceClass.FORWARD_SHADOW.value,
    )
