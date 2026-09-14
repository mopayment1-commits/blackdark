"""P5 User Behavioral Learning tests — TEMP-AR-0352..0360."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from blackdark.temporal.p5_requirement_registry import P5_ATOMIC_REQUIREMENT_IDS
from blackdark.temporal.user_behavioral_learning import (
    BehavioralLearningPurpose,
    BehavioralConsentRecord,
    USER_BEHAVIOR_NOT_FINANCIAL_TRUTH,
    USER_ACTION_NOT_OUTCOME_PROOF,
    build_behavioral_learning_state,
    delete_user_behavioral_data,
    evaluate_user_action_as_outcome_proof,
    record_behavioral_signal,
)

T_NOW = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)


def _consent() -> BehavioralConsentRecord:
    return BehavioralConsentRecord(
        user_key="user-1",
        purpose=BehavioralLearningPurpose.DISCIPLINE_COACHING,
        legal_basis="explicit_consent",
        consented_at=T_NOW,
        minimized_fields=("action_type", "followed_system"),
    )


def test_temp_ar_0352_user_behavior_not_financial_truth() -> None:
    assert USER_BEHAVIOR_NOT_FINANCIAL_TRUTH is True
    signal = record_behavioral_signal(
        user_key="user-1",
        action_type="follow",
        asset="BTC",
        followed_system=True,
        consent=_consent(),
    )
    assert signal.is_outcome_truth is False


def test_temp_ar_0353_explicit_purpose_required() -> None:
    state = build_behavioral_learning_state(
        user_key="user-1",
        purpose=BehavioralLearningPurpose.PERSONALIZATION,
        consent=None,
    )
    assert state.eligible_for_adaptation is False
    assert state.abstention_reason == "consent_required"


def test_temp_ar_0354_consent_legal_basis() -> None:
    consent = _consent()
    assert consent.legal_basis == "explicit_consent"
    state = build_behavioral_learning_state(
        user_key="user-1",
        purpose=BehavioralLearningPurpose.DISCIPLINE_COACHING,
        consent=consent,
    )
    assert state.consent is not None


def test_temp_ar_0355_minimization() -> None:
    consent = _consent()
    assert "action_type" in consent.minimized_fields
    signal = record_behavioral_signal(
        user_key="user-1",
        action_type="ignore",
        consent=consent,
    )
    assert signal.metadata.get("minimized") is True


def test_temp_ar_0356_retention_rules() -> None:
    signal = record_behavioral_signal(
        user_key="user-1",
        action_type="follow",
        consent=_consent(),
    )
    state = build_behavioral_learning_state(
        user_key="user-1",
        purpose=BehavioralLearningPurpose.DISCIPLINE_COACHING,
        signals=(signal,),
        consent=_consent(),
        retention_days=30,
    )
    assert state.retention_days == 30


def test_temp_ar_0357_deletion_rights() -> None:
    signal = record_behavioral_signal(
        user_key="user-1",
        action_type="follow",
        consent=_consent(),
    )
    state = build_behavioral_learning_state(
        user_key="user-1",
        purpose=BehavioralLearningPurpose.DISCIPLINE_COACHING,
        signals=(signal,),
        consent=_consent(),
    )
    deleted = delete_user_behavioral_data(state, user_key="user-1")
    assert deleted.signals == ()
    assert deleted.abstention_reason == "data_deleted"


def test_temp_ar_0358_separation_from_objective_outcomes() -> None:
    state = build_behavioral_learning_state(
        user_key="user-1",
        purpose=BehavioralLearningPurpose.UX_ADAPTATION,
        consent=_consent(),
    )
    assert state.separated_from_objective_outcomes is True


def test_temp_ar_0359_anti_manipulation_controls() -> None:
    state = build_behavioral_learning_state(
        user_key="user-1",
        purpose=BehavioralLearningPurpose.PERSONALIZATION,
        consent=_consent(),
    )
    assert state.anti_manipulation_enabled is True


def test_temp_ar_0360_buy_click_not_outcome_proof() -> None:
    assert USER_ACTION_NOT_OUTCOME_PROOF is True
    result = evaluate_user_action_as_outcome_proof("buy")
    assert result["treated_as_outcome_proof"] is False
    assert result["prohibited_as_automatic_proof"] is True
    assert "TEMP-AR-0360" in P5_ATOMIC_REQUIREMENT_IDS or "TEMP-AR-0360" in P5_ATOMIC_REQUIREMENT_IDS
