"""Focused FAILURE_SURPRISE_ABSTENTION tests — all 18 P3 atomics."""

from __future__ import annotations

import copy
from datetime import UTC, datetime

import pytest

from blackdark.temporal.evidence_class import TemporalEvidenceClass
from blackdark.temporal.evidence_provenance import EvidenceProvenanceLedger
from blackdark.temporal.failure_surprise_corpus import (
    ATOMIC_CASE_TYPE,
    CaptureCategory,
    FailureCaseType,
    FailureSurpriseCorpus,
    FSB_ATOMIC_IDS,
    FAILURE_SURPRISE_ABSTENTION_TOTAL,
)
from blackdark.temporal.outcome_contract import OUTCOME_EVALUATOR_IDENTITY, OutcomeContract, OutcomeLabelStatus

T_NOW = datetime(2024, 9, 1, 12, 0, 0, tzinfo=UTC)
CTX = {"available_at": T_NOW.isoformat(), "simulated_time": T_NOW.isoformat()}
PROV = "prov-ref-1"
EVIDENCE = TemporalEvidenceClass.FORWARD_SHADOW.value


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


def _corpus() -> FailureSurpriseCorpus:
    return FailureSurpriseCorpus()


# --- inventory ---

def test_fsb_inventory_total_18() -> None:
    assert FAILURE_SURPRISE_ABSTENTION_TOTAL == 18
    assert len(FSB_ATOMIC_IDS) == 18
    assert len(ATOMIC_CASE_TYPE) == 15


# --- TEMP-AR-0167 durable corpus ---

def test_temp_ar_0167_durable_append_only_corpus() -> None:
    corpus = _corpus()
    case = corpus.capture_high_confidence_wrong(
        case_id="c-0167",
        prediction_identity="model-v1",
        decision_identity="decision-1",
        outcome=_outcome(),
        shadow_receipt_id="shadow-1",
        evidence_class=EVIDENCE,
        recorded_at=T_NOW,
        temporal_context=CTX,
        provenance_reference=PROV,
        confidence=0.9,
    )
    assert case is not None
    assert len(corpus.list_cases()) == 1
    assert len(corpus.lineage_log()) >= 1


# --- TEMP-AR-0168..0170 abstention/failure captures ---

def test_temp_ar_0168_high_confidence_wrong() -> None:
    case = _corpus().capture_high_confidence_wrong(
        case_id="c-0168",
        prediction_identity="model-v1",
        decision_identity="decision-1",
        outcome=_outcome(directional_correctness=False),
        shadow_receipt_id="shadow-1",
        evidence_class=EVIDENCE,
        recorded_at=T_NOW,
        temporal_context=CTX,
        provenance_reference=PROV,
        confidence=0.95,
    )
    assert case is not None
    assert case.case_type == FailureCaseType.HIGH_CONFIDENCE_WRONG
    assert case.capture_category == CaptureCategory.FAILURE


def test_temp_ar_0169_failure_to_abstain() -> None:
    case = _corpus().capture_failure_to_abstain(
        case_id="c-0169",
        prediction_identity="model-v1",
        decision_identity="decision-1",
        outcome=_outcome(directional_correctness=True),
        shadow_receipt_id="shadow-1",
        evidence_class=EVIDENCE,
        recorded_at=T_NOW,
        temporal_context=CTX,
        provenance_reference=PROV,
        abstained=False,
        should_have_abstained=True,
    )
    assert case is not None
    assert case.capture_category == CaptureCategory.ABSTENTION


def test_temp_ar_0170_unnecessary_abstention() -> None:
    case = _corpus().capture_unnecessary_abstention(
        case_id="c-0170",
        prediction_identity="model-v1",
        decision_identity="decision-1",
        outcome=_outcome(directional_correctness=True),
        shadow_receipt_id="shadow-1",
        evidence_class=EVIDENCE,
        recorded_at=T_NOW,
        temporal_context=CTX,
        provenance_reference=PROV,
        abstained=True,
        should_have_abstained=False,
    )
    assert case is not None
    assert case.capture_category == CaptureCategory.ABSTENTION


# --- TEMP-AR-0171..0182 signal captures ---

@pytest.mark.parametrize(
    "atomic_id,signal_key,capability",
    [
        ("TEMP-AR-0171", "missed_major_event", "event_detection"),
        ("TEMP-AR-0172", "model_disagreement", "ensemble"),
        ("TEMP-AR-0173", "unexpected_regime_shift", "regime"),
        ("TEMP-AR-0174", "correlation_breakdown", "correlation"),
        ("TEMP-AR-0175", "stale_source", "source_quality"),
        ("TEMP-AR-0176", "conflicting_sources", "source_quality"),
        ("TEMP-AR-0177", "missing_source", "source_quality"),
        ("TEMP-AR-0178", "tail_event", "risk"),
        ("TEMP-AR-0179", "calibration_collapse", "calibration"),
        ("TEMP-AR-0180", "prediction_instability", "prediction"),
        ("TEMP-AR-0181", "source_revision", "provenance"),
        ("TEMP-AR-0182", "model_regression", "model_quality"),
    ],
)
def test_temp_ar_signal_captures(atomic_id: str, signal_key: str, capability: str) -> None:
    case = _corpus().capture_signal_case(
        atomic_id=atomic_id,
        case_id=f"c-{atomic_id[-4:]}",
        prediction_identity="model-v1",
        decision_identity="decision-1",
        outcome=_outcome(directional_correctness=True),
        shadow_receipt_id="shadow-1",
        evidence_class=EVIDENCE,
        recorded_at=T_NOW,
        temporal_context=CTX,
        provenance_reference=PROV,
        signal_active=True,
        root_cause=signal_key,
        affected_capability=capability,
    )
    assert case is not None
    assert case.case_type == ATOMIC_CASE_TYPE[atomic_id]
    assert case.prediction_identity == "model-v1"
    assert case.decision_identity == "decision-1"


# --- TEMP-AR-0183 traceability ---

def test_temp_ar_0183_case_traceability_chain() -> None:
    case = _corpus().capture_high_confidence_wrong(
        case_id="c-0183",
        prediction_identity="model-v1",
        decision_identity="decision-1",
        outcome=_outcome(),
        shadow_receipt_id="shadow-1",
        evidence_class=EVIDENCE,
        recorded_at=T_NOW,
        temporal_context=CTX,
        provenance_reference=PROV,
        confidence=0.9,
    )
    assert case is not None
    trace = case.traceability.to_metadata()
    assert trace["case"] == "c-0183"
    assert trace["root_cause"]
    assert trace["affected_capability"]
    assert trace["model_rule_version"]


# --- TEMP-AR-0453 governing objective ---

def test_temp_ar_0453_strategic_proprietary_asset() -> None:
    corpus = _corpus()
    assert corpus.governance.strategic_proprietary_asset is True
    assert corpus.governance.contract_version


# --- negative cases ---

def test_unresolved_outcome_does_not_create_false_failure() -> None:
    corpus = _corpus()
    unresolved = _outcome(
        label_status=OutcomeLabelStatus.UNRESOLVED,
        realized_result=None,
        directional_correctness=None,
    )
    case = corpus.capture_high_confidence_wrong(
        case_id="neg-unresolved",
        prediction_identity="model-v1",
        decision_identity="decision-1",
        outcome=unresolved,
        shadow_receipt_id="shadow-1",
        evidence_class=EVIDENCE,
        recorded_at=T_NOW,
        temporal_context=CTX,
        provenance_reference=PROV,
        confidence=0.99,
    )
    assert case is None
    assert len(corpus.list_cases()) == 0


def test_abstention_distinguishable_from_failure() -> None:
    corpus = _corpus()
    failure = corpus.capture_failure_to_abstain(
        case_id="abst-fail",
        prediction_identity="model-v1",
        decision_identity="decision-1",
        outcome=_outcome(),
        shadow_receipt_id="shadow-1",
        evidence_class=EVIDENCE,
        recorded_at=T_NOW,
        temporal_context=CTX,
        provenance_reference=PROV,
        abstained=False,
        should_have_abstained=True,
    )
    surprise = corpus.capture_signal_case(
        atomic_id="TEMP-AR-0178",
        case_id="surprise-tail",
        prediction_identity="model-v1",
        decision_identity="decision-1",
        outcome=_outcome(),
        shadow_receipt_id="shadow-1",
        evidence_class=EVIDENCE,
        recorded_at=T_NOW,
        temporal_context=CTX,
        provenance_reference=PROV,
        signal_active=True,
        root_cause="tail_event",
        affected_capability="risk",
        capture_category=CaptureCategory.SURPRISE,
    )
    assert failure is not None and surprise is not None
    assert failure.capture_category == CaptureCategory.ABSTENTION
    assert surprise.capture_category == CaptureCategory.SURPRISE


def test_surprise_preserves_prediction_decision_linkage() -> None:
    case = _corpus().capture_signal_case(
        atomic_id="TEMP-AR-0172",
        case_id="link-0172",
        prediction_identity="model-v2",
        decision_identity="decision-xyz",
        outcome=_outcome(),
        shadow_receipt_id="shadow-9",
        evidence_class=EVIDENCE,
        recorded_at=T_NOW,
        temporal_context=CTX,
        provenance_reference=PROV,
        signal_active=True,
        root_cause="model_disagreement",
        affected_capability="ensemble",
    )
    assert case is not None
    assert case.prediction_identity == "model-v2"
    assert case.decision_identity == "decision-xyz"
    assert "model-v2" in case.lineage


def test_corpus_does_not_mutate_prior_cases() -> None:
    corpus = _corpus()
    first = corpus.capture_high_confidence_wrong(
        case_id="immutable-1",
        prediction_identity="model-v1",
        decision_identity="decision-1",
        outcome=_outcome(),
        shadow_receipt_id="shadow-1",
        evidence_class=EVIDENCE,
        recorded_at=T_NOW,
        temporal_context=CTX,
        provenance_reference=PROV,
        confidence=0.9,
    )
    before = copy.deepcopy(first.to_metadata())
    corpus.capture_signal_case(
        atomic_id="TEMP-AR-0175",
        case_id="immutable-2",
        prediction_identity="model-v1",
        decision_identity="decision-1",
        outcome=_outcome(),
        shadow_receipt_id="shadow-1",
        evidence_class=EVIDENCE,
        recorded_at=T_NOW,
        temporal_context=CTX,
        provenance_reference=PROV,
        signal_active=True,
        root_cause="stale_source",
        affected_capability="source_quality",
    )
    assert corpus.list_cases()[0].to_metadata() == before


def test_corpus_cannot_auto_promote_evidence() -> None:
    corpus = _corpus()
    case = corpus.capture_high_confidence_wrong(
        case_id="promo",
        prediction_identity="model-v1",
        decision_identity="decision-1",
        outcome=_outcome(),
        shadow_receipt_id="shadow-1",
        evidence_class=EVIDENCE,
        recorded_at=T_NOW,
        temporal_context=CTX,
        provenance_reference=PROV,
        confidence=0.9,
    )
    assert case is not None
    with pytest.raises(ValueError):
        corpus.attempt_evidence_promotion(case, TemporalEvidenceClass.VERIFIED_PRODUCTION.value)


def test_corpus_cannot_auto_mutate_or_promote_models() -> None:
    corpus = _corpus()
    case = corpus.capture_high_confidence_wrong(
        case_id="mut",
        prediction_identity="model-v1",
        decision_identity="decision-1",
        outcome=_outcome(),
        shadow_receipt_id="shadow-1",
        evidence_class=EVIDENCE,
        recorded_at=T_NOW,
        temporal_context=CTX,
        provenance_reference=PROV,
        confidence=0.9,
    )
    assert case is not None
    with pytest.raises(ValueError):
        corpus.attempt_model_mutation(case)
    with pytest.raises(ValueError):
        corpus.attempt_model_promotion(case)


def test_p2_evidence_ledger_reuse_without_duplicate_authority() -> None:
    corpus = _corpus()
    ledger = EvidenceProvenanceLedger()
    case = corpus.capture_high_confidence_wrong(
        case_id="ledger",
        prediction_identity="model-v1",
        decision_identity="decision-1",
        outcome=_outcome(),
        shadow_receipt_id="shadow-1",
        evidence_class=EVIDENCE,
        recorded_at=T_NOW,
        temporal_context=CTX,
        provenance_reference=PROV,
        confidence=0.9,
    )
    assert case is not None
    evidence_id = corpus.record_in_evidence_ledger(case, ledger=ledger, outcome=_outcome())
    assert evidence_id
    assert ledger.list_records()[0].evidence_class == EVIDENCE
    assert case.temporal_context == CTX
    assert case.evidence_class == EVIDENCE
