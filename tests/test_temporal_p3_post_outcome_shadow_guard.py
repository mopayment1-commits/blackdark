"""Focused P3 post-outcome shadow receipt canonical-truth enforcement tests."""

from __future__ import annotations

import inspect
from datetime import UTC, datetime, timedelta

import pytest

from blackdark.temporal.forward_shadow import (
    CALLER_FLAG_CAN_BYPASS_POST_OUTCOME_GUARD,
    DUPLICATE_OUTCOME_AUTHORITY,
    POST_OUTCOME_REJECTION_AUTHORITY,
    POST_OUTCOME_REJECTION_RUNTIME_PATH,
    POST_OUTCOME_REJECTION_USES_CANONICAL_TRUTH,
    POST_OUTCOME_SHADOW_RECEIPT_CREATION,
    SHADOW_EVIDENCE_CLASS_PRESERVED,
    TEMPORAL_TIMESTAMP_FABRICATION,
    ForwardShadowLedger,
    evaluate_post_outcome_receipt_admission,
)
from blackdark.temporal.outcome_contract import OUTCOME_EVALUATOR_IDENTITY, OutcomeContract, OutcomeLabelStatus
from blackdark.temporal.outcome_factory import OUTCOME_EVALUATOR_IDENTITY as FACTORY_EVALUATOR
from blackdark.temporal.p3_pipeline import run_forward_shadow_pipeline
from blackdark.temporal.evidence_class import TemporalEvidenceClass

T_ISSUED = datetime(2024, 9, 1, 10, 0, 0, tzinfo=UTC)
T_OUTCOME_PAST = datetime(2024, 9, 1, 9, 30, 0, tzinfo=UTC)
T_OUTCOME_FUTURE = datetime(2024, 9, 1, 11, 0, 0, tzinfo=UTC)


def _outcome(**kwargs) -> OutcomeContract:
    defaults = {
        "outcome_id": "outcome_test",
        "subject_identity": "asset-a",
        "prediction_identity": "model-v1",
        "decision_identity": "asset-a:act",
        "target_definition": "directional",
        "evaluation_horizon": "1h",
        "outcome_timestamp": T_OUTCOME_PAST,
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


def test_canonically_known_outcome_rejects_receipt() -> None:
    decision = evaluate_post_outcome_receipt_admission(
        issued_at=T_ISSUED,
        subject_identity="asset-a",
        canonical_outcome=_outcome(),
    )
    assert decision.admitted is False
    assert decision.rejection_reason == "post_outcome_shadow_receipt_creation_forbidden"
    assert decision.canonical_outcome_known_at_receipt_time is True

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
            canonical_outcome=_outcome(),
        )


def test_caller_false_unknown_claim_does_not_bypass_guard() -> None:
    """Canonical VERIFIED outcome rejects even when caller omits or misrepresents state."""
    known = _outcome()
    decision = evaluate_post_outcome_receipt_admission(
        issued_at=T_ISSUED,
        subject_identity="asset-a",
        canonical_outcome=known,
    )
    assert decision.admitted is False
    assert CALLER_FLAG_CAN_BYPASS_POST_OUTCOME_GUARD is False

    ledger = ForwardShadowLedger()
    sig = inspect.signature(ledger.create_pre_outcome_receipt)
    assert "outcome_already_known" not in sig.parameters

    with pytest.raises(ValueError, match="post_outcome"):
        ledger.create_pre_outcome_receipt(
            subject_identity="asset-a",
            input_identity="input-1",
            decision_or_prediction_identity="pred-1",
            model_version="model-v1",
            rule_config_version="rule-v1",
            dataset_version="ds-1",
            code_version="code-v1",
            input_snapshot_hash="hash",
            prediction={"direction": "up"},
            confidence=0.5,
            abstention_state="act",
            issued_at=T_ISSUED,
            temporal_context={"caller_claims_outcome_unknown": True},
            source_or_dataset_context={},
            canonical_outcome=known,
        )


def test_unresolved_canonical_outcome_allows_receipt() -> None:
    unresolved = _outcome(
        outcome_timestamp=None,
        realized_result=None,
        label_status=OutcomeLabelStatus.UNRESOLVED,
        directional_correctness=None,
    )
    decision = evaluate_post_outcome_receipt_admission(
        issued_at=T_ISSUED,
        subject_identity="asset-a",
        canonical_outcome=unresolved,
    )
    assert decision.admitted is True

    ledger = ForwardShadowLedger()
    receipt = ledger.create_pre_outcome_receipt(
        subject_identity="asset-a",
        input_identity="input-1",
        decision_or_prediction_identity="pred-1",
        model_version="model-v1",
        rule_config_version="rule-v1",
        dataset_version="ds-1",
        code_version="code-v1",
        input_snapshot_hash="hash",
        prediction={"direction": "up"},
        confidence=0.5,
        abstention_state="act",
        issued_at=T_ISSUED,
        temporal_context={},
        source_or_dataset_context={},
        canonical_outcome=unresolved,
    )
    assert receipt.evidence_class == TemporalEvidenceClass.FORWARD_SHADOW.value
    assert receipt.status == "pre_outcome"


def test_future_outcome_does_not_block_pre_outcome_receipt() -> None:
    future = _outcome(
        outcome_timestamp=T_OUTCOME_FUTURE,
        label_status=OutcomeLabelStatus.VERIFIED,
    )
    decision = evaluate_post_outcome_receipt_admission(
        issued_at=T_ISSUED,
        subject_identity="asset-a",
        canonical_outcome=future,
    )
    assert decision.admitted is True
    assert decision.canonical_outcome_known_at_receipt_time is False

    result = run_forward_shadow_pipeline(
        subject_identity="asset-a",
        input_identity="input-1",
        prediction={"direction": "up"},
        confidence=0.7,
        abstention_state="act",
        issued_at=T_ISSUED,
        evaluation_time=T_ISSUED + timedelta(minutes=5),
        temporal_context={},
        source_context={},
        outcome=future,
        outcome_known_at=T_OUTCOME_FUTURE,
    )
    assert result.shadow_receipt.issued_at == T_ISSUED
    assert result.evidence_class == TemporalEvidenceClass.FORWARD_SHADOW.value


def test_no_duplicate_outcome_authority_introduced() -> None:
    import blackdark.temporal.forward_shadow as fs_module
    import blackdark.temporal.outcome_factory as factory_module

    assert DUPLICATE_OUTCOME_AUTHORITY == 0
    assert not hasattr(fs_module, "generate_outcome_contract")
    assert not hasattr(fs_module, "OutcomeFactory")
    assert evaluate_post_outcome_receipt_admission.__module__ == "blackdark.temporal.forward_shadow"
    assert FACTORY_EVALUATOR == OUTCOME_EVALUATOR_IDENTITY
    assert factory_module.OUTCOME_EVALUATOR_IDENTITY == OUTCOME_EVALUATOR_IDENTITY


def test_required_assertions_metadata() -> None:
    assert POST_OUTCOME_REJECTION_USES_CANONICAL_TRUTH is True
    assert POST_OUTCOME_SHADOW_RECEIPT_CREATION == 0
    assert CALLER_FLAG_CAN_BYPASS_POST_OUTCOME_GUARD is False
    assert DUPLICATE_OUTCOME_AUTHORITY == 0
    assert TEMPORAL_TIMESTAMP_FABRICATION == 0
    assert SHADOW_EVIDENCE_CLASS_PRESERVED is True
    assert POST_OUTCOME_REJECTION_AUTHORITY == "p2_outcome_contract+p0_pit_outcome_timestamp"
    assert POST_OUTCOME_REJECTION_RUNTIME_PATH == (
        "forward_shadow.evaluate_post_outcome_receipt_admission"
    )
