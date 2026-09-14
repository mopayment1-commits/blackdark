"""Focused P4 Controlled Learning tests — TEMP-AR-0233..0240."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from blackdark.temporal.champion_challenger import ChampionChallengerEvaluator
from blackdark.temporal.controlled_learning import (
    AUTONOMOUS_MODEL_PROMOTION,
    AUTONOMOUS_PRODUCTION_MODEL_REPLACEMENT,
    CONTROLLED_LEARNING_EVALUATION_DETERMINISTIC,
    CONTROLLED_LEARNING_EVIDENCE_PROMOTION,
    CONTROLLED_LEARNING_HISTORY_MUTATION,
    CONTROLLED_LEARNING_PRODUCTION_MUTATION,
    EVALUATION_IMPLIES_DEPLOYMENT,
    LEARNING_RECOMMENDATION_IMPLIES_PROMOTION,
    UNCONTROLLED_PRODUCTION_SELF_MODIFICATION,
    CandidateArtifactType,
    ControlledLearningEngine,
    controlled_learning_preserves_champion_state,
    controlled_learning_preserves_corpus_case,
    controlled_learning_preserves_evidence_lineage,
)
from blackdark.temporal.evidence_class import TemporalEvidenceClass
from blackdark.temporal.evidence_provenance import EvidenceProvenanceLedger
from blackdark.temporal.failure_surprise_corpus import FailureSurpriseCorpus
from blackdark.temporal.learning_value import LearningStream, LearningValueEngine, LearningValueResult
from blackdark.temporal.outcome_contract import OUTCOME_EVALUATOR_IDENTITY, OutcomeContract, OutcomeLabelStatus
from blackdark.temporal.p4_controlled_learning_registry import P4_CONTROLLED_LEARNING_ATOMIC_REQUIREMENT_IDS

T_NOW = datetime(2024, 9, 1, 12, 0, 0, tzinfo=UTC)
CTX = {"available_at": T_NOW.isoformat()}
PROV = "prov-ref-1"


def _outcome(**kwargs) -> OutcomeContract:
    defaults = {
        "outcome_id": "outcome-1",
        "subject_identity": "asset-a",
        "prediction_identity": "model-v1",
        "decision_identity": "asset-a:act",
        "target_definition": "directional",
        "evaluation_horizon": "1h",
        "outcome_timestamp": T_NOW,
        "realized_result": 100.0,
        "benchmark_result": 99.0,
        "confidence": 0.9,
        "calibration_error": 0.1,
        "directional_correctness": False,
        "magnitude_error": 0.1,
        "regret": 0.1,
        "favorable_excursion": 1.0,
        "adverse_excursion": 0.0,
        "drawdown": None,
        "false_positive_cost": 1.0,
        "false_negative_cost": None,
        "abstention_quality": "evaluated",
        "market_regime": "bull",
        "evaluator_version": OUTCOME_EVALUATOR_IDENTITY,
        "label_status": OutcomeLabelStatus.VERIFIED,
    }
    defaults.update(kwargs)
    return OutcomeContract(**defaults)


def _evidence(ledger: EvidenceProvenanceLedger, evidence_class: str):
    return ledger.record_evidence(
        evidence_class=evidence_class,
        producer="test",
        source_provenance={"provenance_reference": PROV},
        temporal_context=CTX,
        versions={"model_version": "model-v1"},
        lineage=("line-1",),
        quality_state={"outcome_quality": "direct_observed", "label_confidence": 0.95},
        limitations=(),
        methodology="test",
        timestamps={"recorded_at": T_NOW.isoformat()},
        evaluator_identity=OUTCOME_EVALUATOR_IDENTITY,
        payload={},
    )


def _learning_value(outcome: OutcomeContract, record) -> LearningValueResult:
    return LearningValueEngine().evaluate_evidence(
        record,
        outcome=outcome,
        stream=LearningStream.HIGH_INFORMATION,
    )


def _fsa_case() -> FailureSurpriseCase:
    return FailureSurpriseCorpus().capture_high_confidence_wrong(
        case_id="fsa-1",
        prediction_identity="model-v1",
        decision_identity="decision-1",
        outcome=_outcome(),
        shadow_receipt_id="shadow-1",
        evidence_class=TemporalEvidenceClass.FORWARD_SHADOW.value,
        recorded_at=T_NOW,
        temporal_context=CTX,
        provenance_reference=PROV,
        confidence=0.95,
    )


def test_selected_atomic_requirement_ids() -> None:
    assert P4_CONTROLLED_LEARNING_ATOMIC_REQUIREMENT_IDS == (
        "TEMP-AR-0233",
        "TEMP-AR-0234",
        "TEMP-AR-0235",
        "TEMP-AR-0236",
        "TEMP-AR-0237",
        "TEMP-AR-0238",
        "TEMP-AR-0239",
        "TEMP-AR-0240",
    )


def test_eligible_evidence_creates_controlled_learning_request() -> None:
    engine = ControlledLearningEngine()
    ledger = EvidenceProvenanceLedger()
    record = _evidence(ledger, TemporalEvidenceClass.HISTORICAL_REPLAY.value)
    outcome = _outcome()
    lv = _learning_value(outcome, record)
    case = _fsa_case()
    assert case is not None

    request = engine.create_request(
        artifact_type=CandidateArtifactType.WEIGHTS,
        proposed_change={"weights_delta": {"layer_1": 0.01}},
        learning_value=lv,
        outcome=outcome,
        evidence_records=(record,),
        corpus_case=case,
    )

    assert request.eligible_for_learning is True
    assert request.learning_request_id.startswith("cl_req_")
    assert lv.subject_or_case_id in request.source_case_or_evidence_ids
    assert case.case_id in request.source_case_or_evidence_ids
    assert record.evidence_id in request.source_case_or_evidence_ids


def test_ineligible_unproven_evidence_rejected() -> None:
    engine = ControlledLearningEngine()
    ledger = EvidenceProvenanceLedger()
    record = ledger.record_evidence(
        evidence_class=TemporalEvidenceClass.HISTORICAL_REPLAY.value,
        producer="test",
        source_provenance={},
        temporal_context=CTX,
        versions={},
        lineage=(),
        quality_state={},
        limitations=(),
        methodology="test",
        timestamps={},
        evaluator_identity=OUTCOME_EVALUATOR_IDENTITY,
        payload={},
    )
    request = engine.create_request(
        artifact_type=CandidateArtifactType.MODEL,
        proposed_change={"model_variant": "candidate-v2"},
        evidence_records=(record,),
        outcome=_outcome(label_status=OutcomeLabelStatus.UNRESOLVED, realized_result=None),
    )
    assert request.eligible_for_learning is False
    assert request.approval_state == "ineligible"
    result = engine.evaluate_request(request)
    assert result.validation_state == "failed"
    assert result.deployed is False


def test_learning_value_context_preserved() -> None:
    engine = ControlledLearningEngine()
    ledger = EvidenceProvenanceLedger()
    record = _evidence(ledger, TemporalEvidenceClass.FORWARD_SHADOW.value)
    outcome = _outcome()
    lv = _learning_value(outcome, record)
    request = engine.create_request(
        artifact_type=CandidateArtifactType.THRESHOLDS,
        proposed_change={"threshold": 0.55},
        learning_value=lv,
        outcome=outcome,
        evidence_records=(record,),
    )
    assert request.learning_value_context["subject_or_case_id"] == lv.subject_or_case_id
    assert request.learning_value_context["learning_value"] == lv.learning_value


def test_fsa_lineage_preserved() -> None:
    case = _fsa_case()
    assert case is not None
    before = case.to_metadata()
    engine = ControlledLearningEngine()
    ledger = EvidenceProvenanceLedger()
    record = _evidence(ledger, TemporalEvidenceClass.FORWARD_SHADOW.value)
    request = engine.create_request(
        artifact_type=CandidateArtifactType.RULES,
        proposed_change={"rule_id": "abstain_threshold"},
        learning_value=_learning_value(_outcome(), record),
        outcome=_outcome(),
        evidence_records=(record,),
        corpus_case=case,
    )
    assert "fsa_lineage" in request.provenance
    assert controlled_learning_preserves_corpus_case(case, before_metadata=before)


def test_learning_recommendation_does_not_promote_model() -> None:
    engine = ControlledLearningEngine()
    ledger = EvidenceProvenanceLedger()
    record = _evidence(ledger, TemporalEvidenceClass.HISTORICAL_REPLAY.value)
    request = engine.create_request(
        artifact_type=CandidateArtifactType.CALIBRATION,
        proposed_change={"calibration_shift": 0.02},
        learning_value=_learning_value(_outcome(), record),
        outcome=_outcome(),
        evidence_records=(record,),
    )
    result = engine.evaluate_request(request)
    assert LEARNING_RECOMMENDATION_IMPLIES_PROMOTION is False
    assert AUTONOMOUS_MODEL_PROMOTION == 0
    assert result.promotion_gate_required is True
    with pytest.raises(ValueError, match="autonomous_model_promotion"):
        engine.attempt_autonomous_promotion(result)


def test_evaluation_does_not_deploy_model() -> None:
    engine = ControlledLearningEngine()
    ledger = EvidenceProvenanceLedger()
    record = _evidence(ledger, TemporalEvidenceClass.HISTORICAL_REPLAY.value)
    request = engine.create_request(
        artifact_type=CandidateArtifactType.MODEL,
        proposed_change={"model_variant": "candidate-v2"},
        learning_value=_learning_value(_outcome(), record),
        outcome=_outcome(),
        evidence_records=(record,),
    )
    result = engine.evaluate_request(request)
    assert EVALUATION_IMPLIES_DEPLOYMENT is False
    assert result.deployed is False
    with pytest.raises(ValueError, match="evaluation_implies_deployment"):
        engine.attempt_deploy(result)


def test_production_model_not_mutated() -> None:
    engine = ControlledLearningEngine(current_production_model_identity="prod-v1")
    ledger = EvidenceProvenanceLedger()
    record = _evidence(ledger, TemporalEvidenceClass.HISTORICAL_REPLAY.value)
    request = engine.create_request(
        artifact_type=CandidateArtifactType.WEIGHTS,
        proposed_change={"weights_delta": {"w": 0.1}},
        learning_value=_learning_value(_outcome(), record),
        outcome=_outcome(),
        evidence_records=(record,),
    )
    result = engine.evaluate_request(request)
    assert engine.current_production_model_identity == "prod-v1"
    assert UNCONTROLLED_PRODUCTION_SELF_MODIFICATION == 0
    assert CONTROLLED_LEARNING_PRODUCTION_MUTATION == 0
    with pytest.raises(ValueError, match="production_mutation"):
        engine.attempt_production_mutation(result)
    with pytest.raises(ValueError, match="production_model_replacement"):
        engine.attempt_production_replacement(result)


def test_historical_evidence_not_mutated() -> None:
    engine = ControlledLearningEngine()
    ledger = EvidenceProvenanceLedger()
    record = _evidence(ledger, TemporalEvidenceClass.HISTORICAL_REPLAY.value)
    before = tuple(r.to_metadata() for r in ledger.list_records())
    request = engine.create_request(
        artifact_type=CandidateArtifactType.WEIGHTS,
        proposed_change={"weights_delta": {"w": 0.1}},
        learning_value=_learning_value(_outcome(), record),
        outcome=_outcome(),
        evidence_records=(record,),
    )
    engine.evaluate_request(request)
    assert CONTROLLED_LEARNING_HISTORY_MUTATION == 0
    assert controlled_learning_preserves_evidence_lineage(ledger, before_snapshot=before)
    with pytest.raises(ValueError, match="history_mutation"):
        engine.attempt_history_mutation(ledger, evidence_id=record.evidence_id)


def test_evidence_class_preserved() -> None:
    engine = ControlledLearningEngine()
    ledger = EvidenceProvenanceLedger()
    record = _evidence(ledger, TemporalEvidenceClass.FORWARD_SHADOW.value)
    request = engine.create_request(
        artifact_type=CandidateArtifactType.MODEL,
        proposed_change={"model_variant": "candidate-v2"},
        learning_value=_learning_value(_outcome(), record),
        outcome=_outcome(),
        evidence_records=(record,),
    )
    assert TemporalEvidenceClass.FORWARD_SHADOW.value in request.evidence_classes
    result = engine.evaluate_request(request)
    assert result.evidence_classes == request.evidence_classes
    assert CONTROLLED_LEARNING_EVIDENCE_PROMOTION == 0
    with pytest.raises(ValueError, match="evidence_promotion"):
        engine.attempt_evidence_promotion(
            result,
            TemporalEvidenceClass.VERIFIED_PRODUCTION.value,
        )


def test_identical_evaluation_inputs_produce_identical_result() -> None:
    engine_a = ControlledLearningEngine()
    engine_b = ControlledLearningEngine()
    ledger = EvidenceProvenanceLedger()
    record = _evidence(ledger, TemporalEvidenceClass.HISTORICAL_REPLAY.value)
    outcome = _outcome()
    lv = _learning_value(outcome, record)
    kwargs = {
        "artifact_type": CandidateArtifactType.WEIGHTS,
        "proposed_change": {"weights_delta": {"layer_1": 0.01}},
        "learning_value": lv,
        "outcome": outcome,
        "evidence_records": (record,),
        "candidate_identity": "candidate-fixed-1",
    }
    req_a = engine_a.create_request(**kwargs)
    req_b = engine_b.create_request(**kwargs)
    res_a = engine_a.evaluate_request(req_a)
    res_b = engine_b.evaluate_request(req_b)
    assert req_a.to_metadata() == req_b.to_metadata()
    assert res_a.to_metadata() == res_b.to_metadata()
    assert CONTROLLED_LEARNING_EVALUATION_DETERMINISTIC is True


def test_champion_challenger_state_unchanged() -> None:
    cc = ChampionChallengerEvaluator(current_champion_identity="champion-v1")
    engine = ControlledLearningEngine()
    ledger = EvidenceProvenanceLedger()
    record = _evidence(ledger, TemporalEvidenceClass.HISTORICAL_REPLAY.value)
    request = engine.create_request(
        artifact_type=CandidateArtifactType.THRESHOLDS,
        proposed_change={"threshold": 0.6},
        learning_value=_learning_value(_outcome(), record),
        outcome=_outcome(),
        evidence_records=(record,),
    )
    engine.evaluate_request(request, champion_challenger=cc)
    assert controlled_learning_preserves_champion_state(cc, before_champion_identity="champion-v1")
    assert AUTONOMOUS_PRODUCTION_MODEL_REPLACEMENT == 0
