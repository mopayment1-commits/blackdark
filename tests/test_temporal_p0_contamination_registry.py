"""Evaluation contamination registry tests (TEMP-PR-0096..0097)."""

from __future__ import annotations

import pytest

from blackdark.temporal.contamination_registry import (
    ContaminationPurpose,
    ContaminationRegistry,
    ContaminationState,
    EvaluationContaminationError,
)


def test_track_all_usage_purposes() -> None:
    registry = ContaminationRegistry()
    purposes = [
        ContaminationPurpose.TRAINING,
        ContaminationPurpose.TUNING,
        ContaminationPurpose.FEATURE_DESIGN,
        ContaminationPurpose.THRESHOLD_SELECTION,
        ContaminationPurpose.HYPERPARAMETER_SELECTION,
        ContaminationPurpose.EVALUATION,
        ContaminationPurpose.POST_HOC_INVESTIGATION,
    ]
    for purpose in purposes:
        registry.record_exposure(
            dataset_id="ds-1",
            window_start="2026-01-01T00:00:00Z",
            window_end="2026-01-01T01:00:00Z",
            purpose=purpose,
            model_version="m1",
            config_version="c1",
            dataset_version="d1",
        )
    assert len(registry.list_entries()) == len(purposes)


def test_repeated_evaluation_reuse_visible_and_fail_closed() -> None:
    registry = ContaminationRegistry()
    registry.record_exposure(
        dataset_id="ds-1",
        window_start="2026-01-01T00:00:00Z",
        window_end="2026-01-01T01:00:00Z",
        purpose=ContaminationPurpose.EVALUATION,
        model_version="m1",
        config_version="c1",
        dataset_version="d1",
    )
    decision = registry.check_evaluation_admission(
        dataset_id="ds-1",
        window_start="2026-01-01T00:00:00Z",
        window_end="2026-01-01T01:00:00Z",
        model_version="m1",
        config_version="c1",
        dataset_version="d1",
        fail_closed=True,
    )
    assert decision.admitted is False
    assert decision.contamination_state == ContaminationState.REUSE_VISIBLE


def test_repeated_reuse_reduces_claim_strength() -> None:
    registry = ContaminationRegistry()
    registry.record_exposure(
        dataset_id="ds-1",
        window_start="2026-01-01T00:00:00Z",
        window_end="2026-01-01T01:00:00Z",
        purpose=ContaminationPurpose.EVALUATION,
    )
    registry.record_exposure(
        dataset_id="ds-1",
        window_start="2026-01-01T00:00:00Z",
        window_end="2026-01-01T01:00:00Z",
        purpose=ContaminationPurpose.EVALUATION,
    )
    decision = registry.check_evaluation_admission(
        dataset_id="ds-1",
        window_start="2026-01-01T00:00:00Z",
        window_end="2026-01-01T01:00:00Z",
        fail_closed=False,
    )
    assert decision.claim_strength_reduction > 0
