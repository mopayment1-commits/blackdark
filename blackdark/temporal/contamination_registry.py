"""Evaluation contamination registry (TEAS-REQ-096..097 / TEMP-AR-0315..0323)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Mapping, Sequence
from uuid import uuid4

from blackdark.temporal.truth import parse_temporal_instant

CONTAMINATION_REGISTRY_CONTRACT_VERSION = "p0.contamination.1.0"


class ContaminationPurpose(str, Enum):
    TRAINING = "training"
    TUNING = "tuning"
    FEATURE_DESIGN = "feature_design"
    THRESHOLD_SELECTION = "threshold_selection"
    HYPERPARAMETER_SELECTION = "hyperparameter_selection"
    EVALUATION = "evaluation"
    POST_HOC_INVESTIGATION = "post_hoc_investigation"


class ContaminationState(str, Enum):
    CLEAN = "clean"
    EXPOSED = "exposed"
    CONTAMINATED = "contaminated"
    REUSE_VISIBLE = "reuse_visible"


class EvaluationContaminationError(ValueError):
    """Fail-closed when evaluation evidence cannot be proven uncontaminated."""


@dataclass(frozen=True, slots=True)
class ContaminationEntry:
    entry_id: str
    dataset_id: str
    window_start: datetime
    window_end: datetime
    usage_purpose: ContaminationPurpose
    model_version: str | None
    config_version: str | None
    dataset_version: str | None
    exposure_count: int
    contamination_state: ContaminationState
    metadata: Mapping[str, Any]

    def to_metadata(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "dataset_id": self.dataset_id,
            "window_start": self.window_start.isoformat(),
            "window_end": self.window_end.isoformat(),
            "usage_purpose": self.usage_purpose.value,
            "model_version": self.model_version,
            "config_version": self.config_version,
            "dataset_version": self.dataset_version,
            "exposure_count": self.exposure_count,
            "contamination_state": self.contamination_state.value,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class EvaluationAdmissionDecision:
    admitted: bool
    rejection_reason: str | None
    prior_exposures: int
    contamination_state: ContaminationState
    claim_strength_reduction: float

    def to_metadata(self) -> dict[str, Any]:
        return {
            "admitted": self.admitted,
            "rejection_reason": self.rejection_reason,
            "prior_exposures": self.prior_exposures,
            "contamination_state": self.contamination_state.value,
            "claim_strength_reduction": self.claim_strength_reduction,
        }


def _entry_key(
    *,
    dataset_id: str,
    window_start: datetime,
    window_end: datetime,
    purpose: ContaminationPurpose,
    model_version: str | None,
    config_version: str | None,
    dataset_version: str | None,
) -> str:
    return "|".join(
        [
            dataset_id,
            window_start.isoformat(),
            window_end.isoformat(),
            purpose.value,
            model_version or "",
            config_version or "",
            dataset_version or "",
        ]
    )


@dataclass
class ContaminationRegistry:
    """In-memory registry; Postgres persistence via repository adapter."""

    _entries: dict[str, ContaminationEntry] = field(default_factory=dict)

    def list_entries(self) -> tuple[ContaminationEntry, ...]:
        return tuple(self._entries.values())

    def record_exposure(
        self,
        *,
        dataset_id: str,
        window_start: datetime | str,
        window_end: datetime | str,
        purpose: ContaminationPurpose,
        model_version: str | None = None,
        config_version: str | None = None,
        dataset_version: str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> ContaminationEntry:
        ws = parse_temporal_instant(window_start)
        we = parse_temporal_instant(window_end)
        key = _entry_key(
            dataset_id=dataset_id,
            window_start=ws,
            window_end=we,
            purpose=purpose,
            model_version=model_version,
            config_version=config_version,
            dataset_version=dataset_version,
        )
        existing = self._entries.get(key)
        if existing:
            updated = ContaminationEntry(
                entry_id=existing.entry_id,
                dataset_id=dataset_id,
                window_start=ws,
                window_end=we,
                usage_purpose=purpose,
                model_version=model_version,
                config_version=config_version,
                dataset_version=dataset_version,
                exposure_count=existing.exposure_count + 1,
                contamination_state=(
                    ContaminationState.REUSE_VISIBLE
                    if purpose == ContaminationPurpose.EVALUATION and existing.exposure_count >= 1
                    else ContaminationState.CONTAMINATED
                    if existing.exposure_count >= 1
                    else ContaminationState.EXPOSED
                ),
                metadata={**dict(existing.metadata), **dict(metadata or {})},
            )
            self._entries[key] = updated
            return updated

        entry = ContaminationEntry(
            entry_id=f"ctr_{uuid4().hex[:16]}",
            dataset_id=dataset_id,
            window_start=ws,
            window_end=we,
            usage_purpose=purpose,
            model_version=model_version,
            config_version=config_version,
            dataset_version=dataset_version,
            exposure_count=1,
            contamination_state=ContaminationState.CLEAN,
            metadata=dict(metadata or {}),
        )
        self._entries[key] = entry
        return entry

    def query_exposures(
        self,
        *,
        dataset_id: str,
        window_start: datetime | str | None = None,
        window_end: datetime | str | None = None,
        purpose: ContaminationPurpose | None = None,
    ) -> tuple[ContaminationEntry, ...]:
        ws = parse_temporal_instant(window_start) if window_start else None
        we = parse_temporal_instant(window_end) if window_end else None
        results: list[ContaminationEntry] = []
        for entry in self._entries.values():
            if entry.dataset_id != dataset_id:
                continue
            if purpose is not None and entry.usage_purpose != purpose:
                continue
            if ws and entry.window_end < ws:
                continue
            if we and entry.window_start > we:
                continue
            results.append(entry)
        return tuple(results)

    def check_evaluation_admission(
        self,
        *,
        dataset_id: str,
        window_start: datetime | str,
        window_end: datetime | str,
        model_version: str | None = None,
        config_version: str | None = None,
        dataset_version: str | None = None,
        fail_closed: bool = True,
    ) -> EvaluationAdmissionDecision:
        eval_exposures = self.query_exposures(
            dataset_id=dataset_id,
            window_start=window_start,
            window_end=window_end,
            purpose=ContaminationPurpose.EVALUATION,
        )
        tuning_exposures = self.query_exposures(
            dataset_id=dataset_id,
            window_start=window_start,
            window_end=window_end,
            purpose=ContaminationPurpose.TUNING,
        )
        prior = len(eval_exposures) + len(tuning_exposures)
        if prior == 0:
            return EvaluationAdmissionDecision(
                admitted=True,
                rejection_reason=None,
                prior_exposures=0,
                contamination_state=ContaminationState.CLEAN,
                claim_strength_reduction=0.0,
            )

        reduction = min(1.0, 0.25 * prior)
        state = ContaminationState.REUSE_VISIBLE if eval_exposures else ContaminationState.CONTAMINATED
        if fail_closed and eval_exposures:
            return EvaluationAdmissionDecision(
                admitted=False,
                rejection_reason="repeated_evaluation_window_reuse",
                prior_exposures=prior,
                contamination_state=state,
                claim_strength_reduction=reduction,
            )
        return EvaluationAdmissionDecision(
            admitted=True,
            rejection_reason=None,
            prior_exposures=prior,
            contamination_state=state,
            claim_strength_reduction=reduction,
        )

    def load_entries(self, entries: Sequence[ContaminationEntry]) -> None:
        for entry in entries:
            key = _entry_key(
                dataset_id=entry.dataset_id,
                window_start=entry.window_start,
                window_end=entry.window_end,
                purpose=entry.usage_purpose,
                model_version=entry.model_version,
                config_version=entry.config_version,
                dataset_version=entry.dataset_version,
            )
            self._entries[key] = entry
