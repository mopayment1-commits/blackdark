"""Walk-forward evaluation engine (TEAS-REQ-030..033 / TEMP-AR-0086..0095)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any, Callable, Mapping, Sequence
from uuid import uuid4

from blackdark.temporal.contamination_registry import (
    ContaminationPurpose,
    ContaminationRegistry,
    EvaluationContaminationError,
)
from blackdark.temporal.truth import parse_temporal_instant

TRAIN_ON_ALL_HISTORY_PROHIBITED = True


class WalkForwardControl(str, Enum):
    PURGE = "purge"
    EMBARGO = "embargo"
    NO_FUTURE_FEATURE_LEAKAGE = "no_future_feature_leakage"
    IMMUTABLE_EVALUATION_WINDOWS = "immutable_evaluation_windows"
    MODEL_VERSION_FREEZE = "model_version_freeze"
    DATASET_VERSION_FREEZE = "dataset_version_freeze"
    CONFIGURATION_FREEZE = "configuration_freeze"


@dataclass(frozen=True, slots=True)
class WalkForwardWindow:
    dataset_id: str
    train_start: datetime
    train_end: datetime
    eval_start: datetime
    eval_end: datetime
    purge_gap_seconds: int = 0
    embargo_gap_seconds: int = 0

    def to_metadata(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "train_start": self.train_start.isoformat(),
            "train_end": self.train_end.isoformat(),
            "eval_start": self.eval_start.isoformat(),
            "eval_end": self.eval_end.isoformat(),
            "purge_gap_seconds": self.purge_gap_seconds,
            "embargo_gap_seconds": self.embargo_gap_seconds,
        }


@dataclass(frozen=True, slots=True)
class WalkForwardFreezeContext:
    model_version: str
    dataset_version: str
    config_version: str
    controls: tuple[WalkForwardControl, ...]

    def to_metadata(self) -> dict[str, Any]:
        return {
            "model_version": self.model_version,
            "dataset_version": self.dataset_version,
            "config_version": self.config_version,
            "controls": [c.value for c in self.controls],
        }


@dataclass(frozen=True, slots=True)
class WalkForwardFoldResult:
    run_id: str
    window: WalkForwardWindow
    freeze: WalkForwardFreezeContext
    train_sample_count: int
    eval_sample_count: int
    metrics: Mapping[str, Any]
    contamination_checked: bool
    provenance: Mapping[str, Any]

    def to_metadata(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "window": self.window.to_metadata(),
            "freeze": self.freeze.to_metadata(),
            "train_sample_count": self.train_sample_count,
            "eval_sample_count": self.eval_sample_count,
            "metrics": dict(self.metrics),
            "contamination_checked": self.contamination_checked,
            "provenance": dict(self.provenance),
        }


@dataclass(frozen=True, slots=True)
class WalkForwardEvaluationResult:
    dataset_id: str
    folds: tuple[WalkForwardFoldResult, ...]
    controls_applied: tuple[WalkForwardControl, ...]
    train_on_all_history_used: bool

    def to_metadata(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "fold_count": len(self.folds),
            "folds": [f.to_metadata() for f in self.folds],
            "controls_applied": [c.value for c in self.controls_applied],
            "train_on_all_history_used": self.train_on_all_history_used,
        }


def _apply_purge_embargo(window: WalkForwardWindow) -> WalkForwardWindow:
    if window.purge_gap_seconds > 0:
        train_end = window.train_end
        eval_start = train_end + timedelta(seconds=window.purge_gap_seconds)
        if eval_start > window.eval_start:
            return WalkForwardWindow(
                dataset_id=window.dataset_id,
                train_start=window.train_start,
                train_end=train_end,
                eval_start=eval_start,
                eval_end=window.eval_end,
                purge_gap_seconds=window.purge_gap_seconds,
                embargo_gap_seconds=window.embargo_gap_seconds,
            )
    if window.embargo_gap_seconds > 0:
        eval_start = window.eval_start + timedelta(seconds=window.embargo_gap_seconds)
        if eval_start >= window.eval_end:
            raise ValueError("embargo_gap eliminates evaluation window")
        return WalkForwardWindow(
            dataset_id=window.dataset_id,
            train_start=window.train_start,
            train_end=window.train_end,
            eval_start=eval_start,
            eval_end=window.eval_end,
            purge_gap_seconds=window.purge_gap_seconds,
            embargo_gap_seconds=window.embargo_gap_seconds,
        )
    return window


def generate_walk_forward_windows(
    *,
    dataset_id: str,
    series_start: datetime | str,
    series_end: datetime | str,
    train_duration: timedelta,
    eval_duration: timedelta,
    step: timedelta,
    purge_gap_seconds: int = 0,
    embargo_gap_seconds: int = 0,
) -> tuple[WalkForwardWindow, ...]:
    start = parse_temporal_instant(series_start)
    end = parse_temporal_instant(series_end)
    windows: list[WalkForwardWindow] = []
    train_start = start
    while True:
        train_end = train_start + train_duration
        eval_start = train_end
        eval_end = eval_start + eval_duration
        if eval_end > end:
            break
        window = WalkForwardWindow(
            dataset_id=dataset_id,
            train_start=train_start,
            train_end=train_end,
            eval_start=eval_start,
            eval_end=eval_end,
            purge_gap_seconds=purge_gap_seconds,
            embargo_gap_seconds=embargo_gap_seconds,
        )
        windows.append(_apply_purge_embargo(window))
        train_start = train_start + step
    return tuple(windows)


def _partition_samples(
    samples: Sequence[Mapping[str, Any]],
    window: WalkForwardWindow,
    *,
    time_field: str = "event_time",
) -> tuple[tuple[Mapping[str, Any], ...], tuple[Mapping[str, Any], ...]]:
    train: list[Mapping[str, Any]] = []
    eval_samples: list[Mapping[str, Any]] = []
    for sample in samples:
        ts = parse_temporal_instant(sample[time_field])
        if window.train_start <= ts < window.train_end:
            train.append(sample)
        elif window.eval_start <= ts < window.eval_end:
            eval_samples.append(sample)
    return tuple(train), tuple(eval_samples)


def run_walk_forward_evaluation(
    *,
    dataset_id: str,
    samples: Sequence[Mapping[str, Any]],
    windows: Sequence[WalkForwardWindow],
    freeze: WalkForwardFreezeContext,
    contamination_registry: ContaminationRegistry,
    evaluate_fold: Callable[[tuple[Mapping[str, Any], ...], tuple[Mapping[str, Any], ...], WalkForwardFreezeContext], Mapping[str, Any]],
    time_field: str = "event_time",
    fail_closed_on_contamination: bool = True,
) -> WalkForwardEvaluationResult:
    if TRAIN_ON_ALL_HISTORY_PROHIBITED and len(windows) == 0:
        raise ValueError("walk-forward requires at least one train/eval window")

    controls = tuple(sorted(set(freeze.controls), key=lambda c: c.value))
    folds: list[WalkForwardFoldResult] = []

    for window in windows:
        adjusted = _apply_purge_embargo(window)
        train, eval_set = _partition_samples(samples, adjusted, time_field=time_field)

        gate = contamination_registry.check_evaluation_admission(
            dataset_id=dataset_id,
            window_start=adjusted.eval_start,
            window_end=adjusted.eval_end,
            model_version=freeze.model_version,
            config_version=freeze.config_version,
            dataset_version=freeze.dataset_version,
            fail_closed=fail_closed_on_contamination,
        )
        if not gate.admitted:
            raise EvaluationContaminationError(gate.rejection_reason or "evaluation_contamination")

        metrics = evaluate_fold(train, eval_set, freeze)
        run_id = f"wf_{uuid4().hex[:16]}"
        contamination_registry.record_exposure(
            dataset_id=dataset_id,
            window_start=adjusted.eval_start,
            window_end=adjusted.eval_end,
            purpose=ContaminationPurpose.EVALUATION,
            model_version=freeze.model_version,
            config_version=freeze.config_version,
            dataset_version=freeze.dataset_version,
            metadata={"run_id": run_id, "controls": [c.value for c in controls]},
        )
        folds.append(
            WalkForwardFoldResult(
                run_id=run_id,
                window=adjusted,
                freeze=freeze,
                train_sample_count=len(train),
                eval_sample_count=len(eval_set),
                metrics=metrics,
                contamination_checked=True,
                provenance={
                    "controls": [c.value for c in controls],
                    "model_version": freeze.model_version,
                    "dataset_version": freeze.dataset_version,
                    "config_version": freeze.config_version,
                    "generated_at": datetime.now(UTC).isoformat(),
                },
            )
        )

    return WalkForwardEvaluationResult(
        dataset_id=dataset_id,
        folds=tuple(folds),
        controls_applied=controls,
        train_on_all_history_used=False,
    )


def record_tuning_contamination(
    *,
    registry: ContaminationRegistry,
    dataset_id: str,
    window_start: datetime,
    window_end: datetime,
    model_version: str,
    config_version: str,
    dataset_version: str,
    metadata: Mapping[str, Any] | None = None,
) -> None:
    """TEMP-AR-0095: repeated tuning against same window tracked as contamination."""
    registry.record_exposure(
        dataset_id=dataset_id,
        window_start=window_start,
        window_end=window_end,
        purpose=ContaminationPurpose.TUNING,
        model_version=model_version,
        config_version=config_version,
        dataset_version=dataset_version,
        metadata=metadata or {},
    )
