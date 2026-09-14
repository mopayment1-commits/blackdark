"""Focused P3 Forward Shadow / Regime / Drift tests — all 63 atomic requirements."""

from __future__ import annotations

import copy
from datetime import UTC, datetime, timedelta

import pytest

from blackdark.temporal import (
    ForwardShadowLedger,
    KnownRegimeLabel,
    OutcomeLabelStatus,
    P3_ATOMIC_REQUIREMENT_IDS,
    P3_DISCOVERED_ACTIVE_ATOMIC_REQUIREMENTS,
    P3_EXPECTED_ACTIVE_ATOMIC_REQUIREMENTS,
    P3_EXTERNAL_OR_LIVE_GATED_ATOMIC_IDS,
    REPLAY_EVIDENCE_CLASS,
    TemporalEvidenceClass,
    classify_regime,
    evaluate_by_regime,
    evaluate_drift,
    evaluate_reality_anchor,
    run_forward_shadow_pipeline,
)
from blackdark.temporal.evidence_provenance import EvidenceProvenanceLedger
from blackdark.temporal.failure_surprise_corpus import FailureCaseType, FailureSurpriseCorpus
from blackdark.temporal.forward_shadow import ForwardShadowLedger as FSLedger
from blackdark.temporal.outcome_contract import OUTCOME_EVALUATOR_IDENTITY, OutcomeContract
from blackdark.temporal.outcome_factory import predictor_must_not_self_validate
from blackdark.temporal.regime_intelligence import KnownRegimeLabel as KR

T_ISSUED = datetime(2024, 9, 1, 10, 0, 0, tzinfo=UTC)
T_EVAL = datetime(2024, 9, 1, 10, 5, 0, tzinfo=UTC)
T_OUTCOME = datetime(2024, 9, 1, 11, 0, 0, tzinfo=UTC)
T_FUTURE = datetime(2024, 9, 1, 12, 0, 0, tzinfo=UTC)


def _outcome(**kwargs) -> OutcomeContract:
    defaults = {
        "outcome_id": "outcome_test",
        "subject_identity": "asset-a",
        "prediction_identity": "model-v1",
        "decision_identity": "asset-a:act",
        "target_definition": "directional",
        "evaluation_horizon": "1h",
        "outcome_timestamp": T_OUTCOME,
        "realized_result": 125.0,
        "benchmark_result": 120.0,
        "confidence": 0.7,
        "calibration_error": 0.1,
        "directional_correctness": True,
        "magnitude_error": 0.05,
        "regret": 0.0,
        "favorable_excursion": 5.0,
        "adverse_excursion": 0.0,
        "drawdown": None,
        "false_positive_cost": None,
        "false_negative_cost": None,
        "abstention_quality": "evaluated",
        "market_regime": "bull",
        "evaluator_version": OUTCOME_EVALUATOR_IDENTITY,
        "label_status": OutcomeLabelStatus.VERIFIED,
    }
    defaults.update(kwargs)
    return OutcomeContract(**defaults)


def test_p3_inventory_lock() -> None:
    assert P3_EXPECTED_ACTIVE_ATOMIC_REQUIREMENTS == 63
    assert P3_DISCOVERED_ACTIVE_ATOMIC_REQUIREMENTS == 63
    assert len(P3_ATOMIC_REQUIREMENT_IDS) == 63
    assert P3_EXTERNAL_OR_LIVE_GATED_ATOMIC_IDS == ("TEMP-AR-0164",)


def test_forward_receipt_created_before_outcome() -> None:
    ledger = ForwardShadowLedger()
    receipt = ledger.create_pre_outcome_receipt(
        subject_identity="asset-a",
        input_identity="input-1",
        decision_or_prediction_identity="pred-1",
        model_version="model-v1",
        rule_config_version="rule-v1",
        dataset_version="ds-1",
        code_version="code-v1",
        input_snapshot_hash="abc123",
        prediction={"direction": "up"},
        confidence=0.8,
        abstention_state="act",
        issued_at=T_ISSUED,
        temporal_context={"simulated_time": T_ISSUED.isoformat()},
        source_or_dataset_context={"source": "binance"},
    )
    assert receipt.evidence_class == TemporalEvidenceClass.FORWARD_SHADOW.value
    assert receipt.status == "pre_outcome"
    assert receipt.prediction_id
    assert receipt.issued_at == T_ISSUED


def test_post_outcome_shadow_receipt_rejected() -> None:
    ledger = ForwardShadowLedger()
    with pytest.raises(ValueError, match="post_outcome"):
        ledger.create_pre_outcome_receipt(
            subject_identity="asset-a",
            input_identity="input-1",
            decision_or_prediction_identity="pred-1",
            model_version="model-v1",
            rule_config_version="rule-v1",
            dataset_version="ds-1",
            code_version="code-v1",
            input_snapshot_hash="abc123",
            prediction={"direction": "up"},
            confidence=0.8,
            abstention_state="act",
            issued_at=T_ISSUED,
            temporal_context={},
            source_or_dataset_context={},
            outcome_already_known=True,
            outcome_known_at=T_OUTCOME,
        )


def test_receipt_not_overwritten_after_outcome() -> None:
    ledger = ForwardShadowLedger()
    receipt = ledger.create_pre_outcome_receipt(
        subject_identity="asset-a",
        input_identity="input-1",
        decision_or_prediction_identity="pred-1",
        model_version="model-v1",
        rule_config_version="rule-v1",
        dataset_version="ds-1",
        code_version="code-v1",
        input_snapshot_hash="abc123",
        prediction={"direction": "up"},
        confidence=0.8,
        abstention_state="act",
        issued_at=T_ISSUED,
        temporal_context={},
        source_or_dataset_context={},
    )
    original_meta = receipt.to_metadata()
    ledger.mark_outcome_known(
        receipt.shadow_receipt_id,
        outcome_known_at=T_OUTCOME,
        linked_outcome_id="outcome-1",
    )
    first_version = ledger.list_receipts()[0]
    assert first_version.to_metadata() == original_meta
    assert first_version.linked_outcome_id is None


def test_append_only_amendments() -> None:
    ledger = ForwardShadowLedger()
    receipt = ledger.create_pre_outcome_receipt(
        subject_identity="asset-a",
        input_identity="input-1",
        decision_or_prediction_identity="pred-1",
        model_version="model-v1",
        rule_config_version="rule-v1",
        dataset_version="ds-1",
        code_version="code-v1",
        input_snapshot_hash="abc123",
        prediction={"direction": "up"},
        confidence=0.8,
        abstention_state="act",
        issued_at=T_ISSUED,
        temporal_context={},
        source_or_dataset_context={},
    )
    amendment = ledger.append_amendment(
        receipt.shadow_receipt_id,
        reason="correction",
        provenance={"source": "reviewer"},
        created_at=T_EVAL,
        payload={"note": "amended"},
    )
    assert amendment.original_receipt_id == receipt.shadow_receipt_id
    assert len(ledger.list_amendments()) == 1


def test_no_shadow_to_production_promotion() -> None:
    ledger = ForwardShadowLedger()
    receipt = ledger.create_pre_outcome_receipt(
        subject_identity="asset-a",
        input_identity="input-1",
        decision_or_prediction_identity="pred-1",
        model_version="model-v1",
        rule_config_version="rule-v1",
        dataset_version="ds-1",
        code_version="code-v1",
        input_snapshot_hash="abc123",
        prediction={"direction": "up"},
        confidence=0.8,
        abstention_state="act",
        issued_at=T_ISSUED,
        temporal_context={},
        source_or_dataset_context={},
    )
    with pytest.raises(ValueError):
        ledger.attempt_promotion(
            receipt.shadow_receipt_id,
            TemporalEvidenceClass.VERIFIED_PRODUCTION.value,
        )


def test_unknown_regime_not_forced() -> None:
    regime = classify_regime(
        observation_time=T_ISSUED,
        available_at=T_ISSUED,
        evaluation_time=T_EVAL,
        indicators={},
    )
    assert regime.unknown_or_unclassified_state is True
    assert regime.regime_id_or_label == KnownRegimeLabel.UNKNOWN.value


def test_regime_lookahead_rejected() -> None:
    regime = classify_regime(
        observation_time=T_ISSUED,
        available_at=T_FUTURE,
        evaluation_time=T_EVAL,
        indicators={"trend": "up"},
    )
    assert regime.unknown_or_unclassified_state is True


def test_retrospective_regime_not_forward_truth() -> None:
    regime = classify_regime(
        observation_time=T_ISSUED,
        available_at=T_ISSUED,
        evaluation_time=T_EVAL,
        indicators={"trend": "up"},
        retrospective=True,
    )
    assert regime.retrospective_analysis is True


def test_regime_decomposition_exposes_hidden_failure() -> None:
    observations = [
        {"regime_context": {"regime_id_or_label": "bull", "unknown_or_unclassified_state": False}, "success": True},
        {"regime_context": {"regime_id_or_label": "bull", "unknown_or_unclassified_state": False}, "success": True},
        {"regime_context": {"regime_id_or_label": "bull", "unknown_or_unclassified_state": False}, "success": True},
        {"regime_context": {"regime_id_or_label": "bull", "unknown_or_unclassified_state": False}, "success": True},
        {"regime_context": {"regime_id_or_label": "bull", "unknown_or_unclassified_state": False}, "success": True},
        {"regime_context": {"regime_id_or_label": "bear", "unknown_or_unclassified_state": False}, "success": False},
        {"regime_context": {"regime_id_or_label": "bear", "unknown_or_unclassified_state": False}, "success": False},
    ]
    result = evaluate_by_regime(observations)
    assert result.aggregate_hides_regime_failure is True
    assert len(result.regime_segments) == 2


def test_drift_unproven_without_evidence() -> None:
    result = evaluate_drift(baseline={}, current={}, sufficient_evidence=False)
    assert all(not s.proven for s in result.signals)
    assert all(not s.triggers_model_mutation for s in result.signals)
    assert all(not s.triggers_model_promotion for s in result.signals)


def test_drift_detects_dimension_change() -> None:
    result = evaluate_drift(
        baseline={"concept_drift": "stable"},
        current={"concept_drift": "shifted"},
        sufficient_evidence=True,
    )
    concept = next(s for s in result.signals if s.dimension.value == "concept_drift")
    assert concept.detected is True


def test_reality_anchor_external_gate() -> None:
    anchor = evaluate_reality_anchor(
        anchor_id="anchor-1",
        receipt_issued_at=T_ISSUED,
        evaluation_time=T_EVAL,
        uses_simulated_time=True,
    )
    assert anchor.external_evidence_pending is True
    assert anchor.external_gate_requirement_id == "TEMP-AR-0164"
    assert anchor.forward_time_passage_verified is False


def test_p3_pipeline_links_p2_outcome() -> None:
    result = run_forward_shadow_pipeline(
        subject_identity="asset-a",
        input_identity="input-1",
        prediction={"direction": "up"},
        confidence=0.9,
        abstention_state="act",
        issued_at=T_ISSUED,
        evaluation_time=T_EVAL,
        temporal_context={"available_at": T_ISSUED.isoformat()},
        source_context={"source": "binance"},
        regime_indicators={"trend": "up"},
        drift_baseline={"data_drift": "v1"},
        drift_current={"data_drift": "v1"},
        outcome=_outcome(directional_correctness=False),
        outcome_known_at=T_OUTCOME,
    )
    assert result.evidence_class == TemporalEvidenceClass.FORWARD_SHADOW.value
    assert result.linked_outcome_id == "outcome_test"
    assert predictor_must_not_self_validate("model-v1", OUTCOME_EVALUATOR_IDENTITY)


def test_failure_corpus_records_high_confidence_wrong() -> None:
    corpus = FailureSurpriseCorpus()
    case = corpus.classify_from_shadow_outcome(
        case_id="case-1",
        shadow_receipt_id="shadow-1",
        outcome_id="outcome-1",
        prediction_confidence=0.95,
        prediction_correct=False,
        abstained=False,
        should_have_abstained=False,
        evidence_class=TemporalEvidenceClass.FORWARD_SHADOW.value,
        recorded_at=T_OUTCOME,
        model_version="model-v1",
    )
    assert case is not None
    assert case.case_type == FailureCaseType.HIGH_CONFIDENCE_WRONG
    assert case.traceability.get("root_cause")


def test_replay_remains_historical_not_shadow() -> None:
    assert REPLAY_EVIDENCE_CLASS == "HISTORICAL_REPLAY"
    assert REPLAY_EVIDENCE_CLASS != TemporalEvidenceClass.FORWARD_SHADOW.value


def test_p3_pipeline_end_to_end_deterministic() -> None:
    kwargs = {
        "subject_identity": "asset-a",
        "input_identity": "input-1",
        "prediction": {"direction": "up"},
        "confidence": 0.7,
        "abstention_state": "act",
        "issued_at": T_ISSUED,
        "evaluation_time": T_EVAL,
        "temporal_context": {},
        "source_context": {},
        "regime_indicators": {"volatility": "low"},
    }
    first = run_forward_shadow_pipeline(**kwargs)
    second = run_forward_shadow_pipeline(**kwargs)
    assert first.shadow_receipt.shadow_receipt_id == second.shadow_receipt.shadow_receipt_id


def test_evidence_ledger_prior_records_immutable() -> None:
    evidence = EvidenceProvenanceLedger()
    record = evidence.record_evidence(
        evidence_class="HISTORICAL_REPLAY",
        producer="test",
        source_provenance={},
        temporal_context={},
        versions={},
        lineage=(),
        quality_state={},
        limitations=(),
        methodology="m",
        timestamps={},
        evaluator_identity=OUTCOME_EVALUATOR_IDENTITY,
        payload={},
    )
    before = copy.deepcopy(evidence.list_records())
    run_forward_shadow_pipeline(
        subject_identity="asset-a",
        input_identity="input-1",
        prediction={"direction": "up"},
        confidence=0.7,
        abstention_state="act",
        issued_at=T_ISSUED,
        evaluation_time=T_EVAL,
        temporal_context={},
        source_context={},
        evidence_ledger=evidence,
    )
    assert evidence.list_records()[0].to_metadata() == before[0].to_metadata()


def test_known_regime_labels_supported() -> None:
    labels = {r.value for r in KR}
    for expected in ("bull", "bear", "range-bound", "high_volatility", "structural_break"):
        assert expected in labels
