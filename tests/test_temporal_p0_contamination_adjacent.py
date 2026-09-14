"""Regression: adjacent walk-forward eval windows must not false-positive contamination."""

from __future__ import annotations

from datetime import timedelta

from blackdark.temporal.contamination_registry import ContaminationPurpose, ContaminationRegistry
from blackdark.temporal.walk_forward import (
    WalkForwardControl,
    WalkForwardFreezeContext,
    generate_walk_forward_windows,
    run_walk_forward_evaluation,
)


def _sample(ts: str, value: float) -> dict:
    return {"event_time": ts, "value": value}


def test_adjacent_eval_windows_do_not_false_positive_on_admission() -> None:
    registry = ContaminationRegistry()
    registry.record_exposure(
        dataset_id="ds-adj",
        window_start="2026-01-01T02:00:00Z",
        window_end="2026-01-01T03:00:00Z",
        purpose=ContaminationPurpose.EVALUATION,
        model_version="m1",
        config_version="c1",
        dataset_version="d1",
    )
    decision = registry.check_evaluation_admission(
        dataset_id="ds-adj",
        window_start="2026-01-01T03:00:00Z",
        window_end="2026-01-01T04:00:00Z",
        model_version="m1",
        config_version="c1",
        dataset_version="d1",
        fail_closed=True,
    )
    assert decision.admitted is True


def test_overlapping_eval_window_still_rejected() -> None:
    registry = ContaminationRegistry()
    registry.record_exposure(
        dataset_id="ds-overlap",
        window_start="2026-01-01T02:00:00Z",
        window_end="2026-01-01T04:00:00Z",
        purpose=ContaminationPurpose.EVALUATION,
    )
    decision = registry.check_evaluation_admission(
        dataset_id="ds-overlap",
        window_start="2026-01-01T02:00:00Z",
        window_end="2026-01-01T04:00:00Z",
        fail_closed=True,
    )
    assert decision.admitted is False
    assert decision.rejection_reason == "repeated_evaluation_window_reuse"


def test_walk_forward_multi_fold_fail_closed_succeeds() -> None:
    registry = ContaminationRegistry()
    samples = [
        _sample("2026-01-01T00:30:00Z", 1.0),
        _sample("2026-01-01T01:30:00Z", 2.0),
        _sample("2026-01-01T02:30:00Z", 3.0),
        _sample("2026-01-01T03:30:00Z", 4.0),
        _sample("2026-01-01T04:30:00Z", 5.0),
        _sample("2026-01-01T05:30:00Z", 6.0),
    ]
    windows = generate_walk_forward_windows(
        dataset_id="ds-wf-multi",
        series_start="2026-01-01T00:00:00Z",
        series_end="2026-01-01T08:00:00Z",
        train_duration=timedelta(hours=2),
        eval_duration=timedelta(hours=1),
        step=timedelta(hours=1),
    )
    result = run_walk_forward_evaluation(
        dataset_id="ds-wf-multi",
        samples=samples,
        windows=windows,
        freeze=WalkForwardFreezeContext(
            model_version="m1",
            dataset_version="d1",
            config_version="c1",
            controls=(WalkForwardControl.PURGE,),
        ),
        contamination_registry=registry,
        evaluate_fold=lambda train, eval_set, freeze: {"train": len(train), "eval": len(eval_set)},
        fail_closed_on_contamination=True,
    )
    assert len(result.folds) == len(windows)
