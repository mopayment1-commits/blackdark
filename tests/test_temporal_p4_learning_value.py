"""Focused P4 Learning Value / Learning Priority tests — TEMP-AR-0184..0190."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from blackdark.temporal.evidence_class import TemporalEvidenceClass
from blackdark.temporal.evidence_provenance import EvidenceProvenanceLedger
from blackdark.temporal.failure_surprise_corpus import CaptureCategory, FailureSurpriseCorpus
from blackdark.temporal.learning_value import (
    LEARNING_VALUE_AUTO_MODEL_MUTATION,
    LEARNING_VALUE_AUTO_MODEL_PROMOTION,
    LEARNING_VALUE_DETERMINISTIC,
    LEARNING_VALUE_EVIDENCE_PROMOTION,
    RETENTION_EQUALS_LEARNING_PRIORITY,
    LearningStream,
    LearningValueEngine,
    learning_value_preserves_corpus_cases,
    learning_value_preserves_evidence_lineage,
)
from blackdark.temporal.outcome_contract import OUTCOME_EVALUATOR_IDENTITY, OutcomeContract, OutcomeLabelStatus
from blackdark.temporal.p4_learning_value_registry import P4_LEARNING_VALUE_ATOMIC_REQUIREMENT_IDS
from blackdark.temporal.retention_policy import build_retention_descriptor, classify_storage_tier

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


def _evidence_record(
    ledger: EvidenceProvenanceLedger,
    *,
    evidence_class: str = TemporalEvidenceClass.HISTORICAL_REPLAY.value,
    quality_state: dict | None = None,
    payload: dict | None = None,
):
    return ledger.record_evidence(
        evidence_class=evidence_class,
        producer="test",
        source_provenance={"provenance_reference": PROV},
        temporal_context=CTX,
        versions={},
        lineage=("line-1",),
        quality_state=quality_state or {
            "outcome_quality": "direct_observed",
            "label_confidence": 0.95,
        },
        limitations=(),
        methodology="test",
        timestamps={"recorded_at": T_NOW.isoformat()},
        evaluator_identity=OUTCOME_EVALUATOR_IDENTITY,
        payload=payload or {},
    )


def test_selected_atomic_requirement_ids() -> None:
    assert P4_LEARNING_VALUE_ATOMIC_REQUIREMENT_IDS == (
        "TEMP-AR-0184",
        "TEMP-AR-0185",
        "TEMP-AR-0186",
        "TEMP-AR-0187",
        "TEMP-AR-0188",
        "TEMP-AR-0189",
        "TEMP-AR-0190",
    )


def test_retained_evidence_can_have_low_learning_priority() -> None:
    engine = LearningValueEngine()
    ledger = EvidenceProvenanceLedger()
    record = _evidence_record(ledger)
    result = engine.evaluate_evidence(record, stream=LearningStream.REPRESENTATIVE)
    retention = engine.retention_vs_priority(result, access_frequency="recent")

    assert result.learning_value <= 0.35
    assert result.priority == "low"
    assert retention["RETENTION_EQUALS_LEARNING_PRIORITY"] is False
    assert retention["delete_raw_for_low_learning_value"] is False
    assert RETENTION_EQUALS_LEARNING_PRIORITY is False


def test_fsa_case_receives_explicit_learning_value() -> None:
    corpus = FailureSurpriseCorpus()
    case = corpus.capture_high_confidence_wrong(
        case_id="lv-case-1",
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
    assert case is not None
    engine = LearningValueEngine()
    result = engine.evaluate_corpus_case(case, outcome=_outcome())

    assert result.subject_or_case_id == "lv-case-1"
    assert result.learning_value > 0.35
    assert "failure_surprise_abstention_case" in result.reason_codes
    assert result.failure_surprise_abstention_context["case_type"] == case.case_type.value
    assert result.failure_surprise_abstention_context["capture_category"] == CaptureCategory.FAILURE.value


def test_unknown_quality_not_trusted_for_learning() -> None:
    engine = LearningValueEngine()
    ledger = EvidenceProvenanceLedger()
    record = _evidence_record(
        ledger,
        quality_state={"outcome_quality": "unavailable"},
    )
    result = engine.evaluate_evidence(
        record,
        outcome=_outcome(label_status=OutcomeLabelStatus.UNRESOLVED, realized_result=None),
    )

    assert result.eligible_for_learning is False
    assert result.quality_or_confidence is None
    assert "outcome_unresolved" in result.ineligibility_reasons or "outcome_quality_unavailable" in result.ineligibility_reasons


def test_evidence_class_preserved() -> None:
    engine = LearningValueEngine()
    ledger = EvidenceProvenanceLedger()
    for evidence_class in (
        TemporalEvidenceClass.HISTORICAL_REPLAY.value,
        TemporalEvidenceClass.FORWARD_SHADOW.value,
        TemporalEvidenceClass.SIMULATED.value,
        TemporalEvidenceClass.VERIFIED_PRODUCTION.value,
    ):
        record = _evidence_record(ledger, evidence_class=evidence_class)
        result = engine.evaluate_evidence(record, outcome=_outcome())
        assert result.evidence_class == evidence_class
        assert record.evidence_class == evidence_class


def test_learning_value_does_not_mutate_models() -> None:
    engine = LearningValueEngine()
    result = engine.evaluate_corpus_case(
        FailureSurpriseCorpus()
        .capture_high_confidence_wrong(
            case_id="mut-1",
            prediction_identity="model-v1",
            decision_identity="decision-1",
            outcome=_outcome(),
            shadow_receipt_id="shadow-1",
            evidence_class=TemporalEvidenceClass.FORWARD_SHADOW.value,
            recorded_at=T_NOW,
            temporal_context=CTX,
            provenance_reference=PROV,
            confidence=0.9,
        ),
        outcome=_outcome(),
    )
    assert LEARNING_VALUE_AUTO_MODEL_MUTATION == 0
    with pytest.raises(ValueError, match="model_mutation"):
        engine.attempt_model_mutation(result)


def test_learning_value_does_not_promote_models() -> None:
    engine = LearningValueEngine()
    result = engine.evaluate_corpus_case(
        FailureSurpriseCorpus()
        .capture_high_confidence_wrong(
            case_id="prom-1",
            prediction_identity="model-v1",
            decision_identity="decision-1",
            outcome=_outcome(),
            shadow_receipt_id="shadow-1",
            evidence_class=TemporalEvidenceClass.FORWARD_SHADOW.value,
            recorded_at=T_NOW,
            temporal_context=CTX,
            provenance_reference=PROV,
            confidence=0.9,
        ),
        outcome=_outcome(),
    )
    assert LEARNING_VALUE_AUTO_MODEL_PROMOTION == 0
    with pytest.raises(ValueError, match="model_promotion"):
        engine.attempt_model_promotion(result)


def test_learning_value_does_not_promote_evidence_class() -> None:
    engine = LearningValueEngine()
    ledger = EvidenceProvenanceLedger()
    record = _evidence_record(
        ledger,
        evidence_class=TemporalEvidenceClass.FORWARD_SHADOW.value,
    )
    result = engine.evaluate_evidence(record, outcome=_outcome())
    assert LEARNING_VALUE_EVIDENCE_PROMOTION == 0
    with pytest.raises(ValueError, match="evidence_promotion"):
        engine.attempt_evidence_promotion(
            result,
            TemporalEvidenceClass.VERIFIED_PRODUCTION.value,
        )


def test_identical_inputs_produce_identical_results() -> None:
    engine = LearningValueEngine()
    ledger = EvidenceProvenanceLedger()
    record = _evidence_record(ledger)
    outcome = _outcome()
    first = engine.evaluate_evidence(record, outcome=outcome)
    second = engine.evaluate_evidence(record, outcome=outcome)
    assert first.to_metadata() == second.to_metadata()
    assert LEARNING_VALUE_DETERMINISTIC is True


def test_representative_stream_preserved_with_high_information() -> None:
    engine = LearningValueEngine()
    ledger = EvidenceProvenanceLedger()
    record = _evidence_record(ledger)
    prioritized = engine.prioritize(evidence_records=(record,), outcomes={record.evidence_id: _outcome()})
    streams = {r.sampling_stream for r in prioritized}
    assert LearningStream.REPRESENTATIVE.value in streams
    assert LearningStream.HIGH_INFORMATION.value in streams
    assert len(prioritized) == 2


def test_p2_evidence_lineage_remains_intact() -> None:
    engine = LearningValueEngine()
    ledger = EvidenceProvenanceLedger()
    record = _evidence_record(ledger)
    before = tuple(r.to_metadata() for r in ledger.list_records())
    engine.prioritize(evidence_records=(record,), outcomes={record.evidence_id: _outcome()})
    assert learning_value_preserves_evidence_lineage(ledger, before_snapshot=before)


def test_p3_corpus_records_remain_immutable() -> None:
    corpus = FailureSurpriseCorpus()
    case = corpus.capture_high_confidence_wrong(
        case_id="imm-1",
        prediction_identity="model-v1",
        decision_identity="decision-1",
        outcome=_outcome(),
        shadow_receipt_id="shadow-1",
        evidence_class=TemporalEvidenceClass.FORWARD_SHADOW.value,
        recorded_at=T_NOW,
        temporal_context=CTX,
        provenance_reference=PROV,
        confidence=0.9,
    )
    assert case is not None
    before = tuple(c.to_metadata() for c in corpus.list_cases())
    engine = LearningValueEngine()
    engine.prioritize(corpus_cases=(case,), outcomes={case.outcome_id: _outcome()})
    assert learning_value_preserves_corpus_cases(corpus, before_snapshot=before)


def test_retention_descriptor_independent_of_learning_priority() -> None:
    tier = classify_storage_tier(access_frequency="recent")
    descriptor = build_retention_descriptor(tier)
    engine = LearningValueEngine()
    ledger = EvidenceProvenanceLedger()
    low = engine.evaluate_evidence(
        _evidence_record(ledger),
        stream=LearningStream.REPRESENTATIVE,
    )
    assert low.priority == "low"
    assert descriptor.delete_raw_for_low_learning_value is False
