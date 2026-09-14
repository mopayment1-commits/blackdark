"""Walk-forward evaluation engine tests (TEMP-PR-0030..0033)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from blackdark.temporal.contamination_registry import ContaminationPurpose, ContaminationRegistry
from blackdark.temporal.walk_forward import (
    WalkForwardControl,
    WalkForwardFreezeContext,
    generate_walk_forward_windows,
    record_tuning_contamination,
    run_walk_forward_evaluation,
)


def _sample(ts: str, value: float) -> dict:
    return {"event_time": ts, "value": value}


def test_generate_walk_forward_windows() -> None:
    windows = generate_walk_forward_windows(
        dataset_id="ds-1",
        series_start="2026-01-01T00:00:00Z",
        series_end="2026-01-01T12:00:00Z",
        train_duration=timedelta(hours=2),
        eval_duration=timedelta(hours=1),
        step=timedelta(hours=1),
        purge_gap_seconds=60,
    )
    assert len(windows) >= 1
    assert windows[0].eval_start >= windows[0].train_end


def test_walk_forward_prohibits_train_on_all_history() -> None:
    with pytest.raises(ValueError):
        run_walk_forward_evaluation(
            dataset_id="ds-1",
            samples=[_sample("2026-01-01T01:00:00Z", 1.0)],
            windows=(),
            freeze=WalkForwardFreezeContext(
                model_version="m1",
                dataset_version="d1",
                config_version="c1",
                controls=(WalkForwardControl.PURGE,),
            ),
            contamination_registry=ContaminationRegistry(),
            evaluate_fold=lambda t, e, f: {"ok": True},
        )


def test_walk_forward_runs_with_controls_and_contamination_tracking() -> None:
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
        dataset_id="ds-1",
        series_start="2026-01-01T00:00:00Z",
        series_end="2026-01-01T08:00:00Z",
        train_duration=timedelta(hours=2),
        eval_duration=timedelta(hours=1),
        step=timedelta(hours=1),
    )
    result = run_walk_forward_evaluation(
        dataset_id="ds-1",
        samples=samples,
        windows=windows,
        freeze=WalkForwardFreezeContext(
            model_version="m1",
            dataset_version="d1",
            config_version="c1",
            controls=(
                WalkForwardControl.PURGE,
                WalkForwardControl.EMBARGO,
                WalkForwardControl.NO_FUTURE_FEATURE_LEAKAGE,
                WalkForwardControl.IMMUTABLE_EVALUATION_WINDOWS,
                WalkForwardControl.MODEL_VERSION_FREEZE,
                WalkForwardControl.DATASET_VERSION_FREEZE,
                WalkForwardControl.CONFIGURATION_FREEZE,
            ),
        ),
        contamination_registry=registry,
        evaluate_fold=lambda train, eval_set, freeze: {
            "train": len(train),
            "eval": len(eval_set),
        },
        fail_closed_on_contamination=False,
    )
    assert result.train_on_all_history_used is False
    assert len(result.folds) >= 1
    record_tuning_contamination(
        registry=registry,
        dataset_id="ds-1",
        window_start=windows[0].eval_start,
        window_end=windows[0].eval_end,
        model_version="m1",
        config_version="c1",
        dataset_version="d1",
    )
    exposures = registry.query_exposures(dataset_id="ds-1", purpose=ContaminationPurpose.TUNING)
    assert exposures
