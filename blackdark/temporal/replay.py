"""Deterministic Mass Replay engine (P1.2)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Mapping, Sequence
from uuid import uuid4

from blackdark.temporal.event_contract import CanonicalTemporalEvent, deterministic_event_sort_key
from blackdark.temporal.event_store import TemporalCanonicalEventStore
from blackdark.temporal.firewall import TemporalProcessingContext, evaluate_temporal_leakage_firewall
from blackdark.temporal.reconstruction import PitReconstructionResult
from blackdark.temporal.truth import parse_temporal_instant

REPLAY_ENGINE_CONTRACT_VERSION = "p1.2.0"
REPLAY_EVIDENCE_CLASS = "HISTORICAL_REPLAY"
FORBIDDEN_EVIDENCE_CLASSES = frozenset(
    {"FORWARD_SHADOW", "VERIFIED_PRODUCTION", "INDEPENDENTLY_VERIFIED", "INDEPENDENT_ASSURANCE"}
)


class ReplayFailureReason(str, Enum):
    TEMPORAL_ADMISSION_REJECTED = "TEMPORAL_ADMISSION_REJECTED"
    UNPROVEN_REPLAY_ORDER = "UNPROVEN_REPLAY_ORDER"
    INVALID_REPLAY_WINDOW = "INVALID_REPLAY_WINDOW"
    MISSING_REQUIRED_TEMPORAL_TRUTH = "MISSING_REQUIRED_TEMPORAL_TRUTH"
    SOURCE_VERSION_CONTEXT_UNPROVEN = "SOURCE_VERSION_CONTEXT_UNPROVEN"


@dataclass(frozen=True, slots=True)
class ReplayRequest:
    """Canonical deterministic mass replay request."""

    event_source: TemporalCanonicalEventStore
    start_time: datetime | str
    end_time: datetime | str
    replay_clock_or_schedule: Sequence[datetime | str]
    strict_mode: bool = True
    replay_parameters: Mapping[str, Any] = field(default_factory=dict)
    dataset_or_source_version_context: Mapping[str, Any] = field(default_factory=dict)
    chunk_size: int | None = None

    def to_metadata(self) -> dict[str, Any]:
        return {
            "start_time": parse_temporal_instant(self.start_time).isoformat(),
            "end_time": parse_temporal_instant(self.end_time).isoformat(),
            "replay_clock_or_schedule": [parse_temporal_instant(t).isoformat() for t in self.replay_clock_or_schedule],
            "strict_mode": self.strict_mode,
            "replay_parameters": dict(self.replay_parameters),
            "dataset_or_source_version_context": dict(self.dataset_or_source_version_context),
            "chunk_size": self.chunk_size,
        }


@dataclass(frozen=True, slots=True)
class ReplayStepOutput:
    """Replay output for one simulated time step."""

    simulated_time: datetime
    admitted_event_ids: tuple[str, ...]
    state_by_entity: dict[str, str]
    reconstruction: Mapping[str, Any]

    def to_metadata(self) -> dict[str, Any]:
        return {
            "simulated_time": self.simulated_time.isoformat(),
            "admitted_event_ids": list(self.admitted_event_ids),
            "state_by_entity": dict(self.state_by_entity),
            "reconstruction": dict(self.reconstruction),
        }


@dataclass(frozen=True, slots=True)
class ReplayRejection:
    """Explicit replay rejection."""

    simulated_time: datetime | None
    event_id: str | None
    reason: str
    reason_code: str

    def to_metadata(self) -> dict[str, Any]:
        return {
            "simulated_time": self.simulated_time.isoformat() if self.simulated_time else None,
            "event_id": self.event_id,
            "reason": self.reason,
            "reason_code": self.reason_code,
        }


@dataclass(frozen=True, slots=True)
class ReplayResult:
    """Structured deterministic mass replay result."""

    replay_id: str
    start_time: datetime
    end_time: datetime
    processed_event_count: int
    admitted_event_count: int
    rejected_event_count: int
    simulated_time_sequence: tuple[datetime, ...]
    replay_outputs: tuple[ReplayStepOutput, ...]
    rejections: tuple[ReplayRejection, ...]
    replay_manifest: Mapping[str, Any]
    evidence_class: str
    determinism_fingerprint: str
    success: bool
    failure_reasons: tuple[str, ...]

    def to_metadata(self) -> dict[str, Any]:
        return {
            "replay_id": self.replay_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "processed_event_count": self.processed_event_count,
            "admitted_event_count": self.admitted_event_count,
            "rejected_event_count": self.rejected_event_count,
            "simulated_time_sequence": [t.isoformat() for t in self.simulated_time_sequence],
            "replay_outputs": [step.to_metadata() for step in self.replay_outputs],
            "rejections": [rejection.to_metadata() for rejection in self.rejections],
            "replay_manifest": dict(self.replay_manifest),
            "evidence_class": self.evidence_class,
            "determinism_fingerprint": self.determinism_fingerprint,
            "success": self.success,
            "failure_reasons": list(self.failure_reasons),
        }


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def compute_determinism_fingerprint(manifest: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(manifest).encode("utf-8")).hexdigest()


def _event_in_window(event: CanonicalTemporalEvent, start: datetime, end: datetime) -> bool:
    event_time = event.observation.event_time
    if not event_time.is_known() or event_time.value is None:
        return False
    return start <= event_time.value <= end


def _events_eligible_at(event: CanonicalTemporalEvent, simulated_time: datetime) -> bool:
    event_time = event.observation.event_time
    available_at = event.observation.available_at
    if not event_time.is_known() or event_time.value is None:
        return False
    if not available_at.is_known() or available_at.value is None:
        return False
    return event_time.value <= simulated_time and available_at.value <= simulated_time


def _validate_source_version_context(
    request: ReplayRequest,
    window_events: Sequence[CanonicalTemporalEvent],
) -> ReplayRejection | None:
    required_source = request.dataset_or_source_version_context.get("required_source")
    required_source_version = request.dataset_or_source_version_context.get("required_source_version")
    required_dataset_version = request.dataset_or_source_version_context.get("required_dataset_version")
    if not request.strict_mode:
        return None
    if required_source_version and required_source_version == "UNKNOWN":
        return ReplayRejection(
            simulated_time=None,
            event_id=None,
            reason="required source_version is unproven",
            reason_code=ReplayFailureReason.SOURCE_VERSION_CONTEXT_UNPROVEN.value,
        )
    if required_dataset_version and required_dataset_version == "UNKNOWN":
        return ReplayRejection(
            simulated_time=None,
            event_id=None,
            reason="required dataset_version is unproven",
            reason_code=ReplayFailureReason.SOURCE_VERSION_CONTEXT_UNPROVEN.value,
        )
    if required_source:
        for event in window_events:
            if event.provenance.source != required_source:
                continue
            if required_source_version and event.provenance.source_version != required_source_version:
                if event.provenance.source_version is None:
                    return ReplayRejection(
                        simulated_time=None,
                        event_id=event.event_id,
                        reason="event source_version unproven for required context",
                        reason_code=ReplayFailureReason.SOURCE_VERSION_CONTEXT_UNPROVEN.value,
                    )
    return None


def _temporal_replay_order_key(event: CanonicalTemporalEvent) -> tuple[Any, ...]:
    return deterministic_event_sort_key(event)[:-1]


def _verify_replay_order(window_events: Sequence[CanonicalTemporalEvent]) -> ReplayRejection | None:
    seen: set[tuple[Any, ...]] = set()
    for event in window_events:
        key = _temporal_replay_order_key(event)
        if key in seen:
            return ReplayRejection(
                simulated_time=None,
                event_id=event.event_id,
                reason="replay ordering cannot be proven from Temporal semantics",
                reason_code=ReplayFailureReason.UNPROVEN_REPLAY_ORDER.value,
            )
        seen.add(key)
    return None


def _lookahead_rejections(
    window_events: Sequence[CanonicalTemporalEvent],
    schedule: Sequence[datetime],
) -> list[ReplayRejection]:
    rejections: list[ReplayRejection] = []
    for simulated_time in schedule:
        for event in window_events:
            event_time = event.observation.event_time
            available_at = event.observation.available_at
            if not event_time.is_known() or event_time.value is None:
                continue
            if event_time.value > simulated_time:
                continue
            if not available_at.is_known() or available_at.value is None:
                continue
            if available_at.value > simulated_time:
                rejections.append(
                    ReplayRejection(
                        simulated_time=simulated_time,
                        event_id=event.event_id,
                        reason="available_at_after_simulated_time",
                        reason_code=ReplayFailureReason.TEMPORAL_ADMISSION_REJECTED.value,
                    )
                )
    return rejections


def _build_manifest(
    *,
    request: ReplayRequest,
    window_events: Sequence[CanonicalTemporalEvent],
    simulated_time_sequence: Sequence[datetime],
) -> dict[str, Any]:
    return {
        "engine_version_or_contract_version": REPLAY_ENGINE_CONTRACT_VERSION,
        "start_time": parse_temporal_instant(request.start_time).isoformat(),
        "end_time": parse_temporal_instant(request.end_time).isoformat(),
        "simulated_time_sequence": [t.isoformat() for t in simulated_time_sequence],
        "replay_parameters": dict(request.replay_parameters),
        "strict_mode": request.strict_mode,
        "input_event_identity_set": [event.event_id for event in window_events],
        "input_event_versions": {event.event_id: str(event.record_version) for event in window_events},
        "source_versions": {
            event.event_id: event.provenance.source_version for event in window_events
        },
        "dataset_versions": {
            event.event_id: event.provenance.dataset_version for event in window_events
        },
        "dataset_or_source_version_context": dict(request.dataset_or_source_version_context),
    }


def run_deterministic_mass_replay(request: ReplayRequest) -> ReplayResult:
    """
    Canonical deterministic mass replay entrypoint.

    Reuses P0 firewall and reconstruction semantics. Does not mutate canonical history
    or production state. Output evidence class is always HISTORICAL_REPLAY.
    """
    start = parse_temporal_instant(request.start_time)
    end = parse_temporal_instant(request.end_time)
    rejections: list[ReplayRejection] = []
    failure_reasons: list[str] = []

    if start > end:
        rejections.append(
            ReplayRejection(
                simulated_time=None,
                event_id=None,
                reason="start_time after end_time",
                reason_code=ReplayFailureReason.INVALID_REPLAY_WINDOW.value,
            )
        )
        failure_reasons.append(ReplayFailureReason.INVALID_REPLAY_WINDOW.value)
        manifest = _build_manifest(request=request, window_events=(), simulated_time_sequence=())
        fingerprint = compute_determinism_fingerprint(manifest)
        return ReplayResult(
            replay_id=f"replay_{fingerprint[:16]}",
            start_time=start,
            end_time=end,
            processed_event_count=0,
            admitted_event_count=0,
            rejected_event_count=len(rejections),
            simulated_time_sequence=(),
            replay_outputs=(),
            rejections=tuple(rejections),
            replay_manifest=manifest,
            evidence_class=REPLAY_EVIDENCE_CLASS,
            determinism_fingerprint=fingerprint,
            success=False,
            failure_reasons=tuple(failure_reasons),
        )

    schedule = tuple(sorted({parse_temporal_instant(t) for t in request.replay_clock_or_schedule}))
    for sim in schedule:
        if sim < start or sim > end:
            rejections.append(
                ReplayRejection(
                    simulated_time=sim,
                    event_id=None,
                    reason="simulated time outside replay window",
                    reason_code=ReplayFailureReason.INVALID_REPLAY_WINDOW.value,
                )
            )
    if rejections:
        failure_reasons.append(ReplayFailureReason.INVALID_REPLAY_WINDOW.value)

    window_events = tuple(
        sorted(
            [event for event in request.event_source.list_events() if _event_in_window(event, start, end)],
            key=deterministic_event_sort_key,
        )
    )

    if request.strict_mode:
        for event in window_events:
            if not event.observation.available_at.is_known():
                rejections.append(
                    ReplayRejection(
                        simulated_time=None,
                        event_id=event.event_id,
                        reason="missing required available_at",
                        reason_code=ReplayFailureReason.MISSING_REQUIRED_TEMPORAL_TRUTH.value,
                    )
                )
                failure_reasons.append(ReplayFailureReason.MISSING_REQUIRED_TEMPORAL_TRUTH.value)
        order_issue = _verify_replay_order(window_events)
        if order_issue is not None:
            rejections.append(order_issue)
            failure_reasons.append(ReplayFailureReason.UNPROVEN_REPLAY_ORDER.value)
        context_issue = _validate_source_version_context(request, window_events)
        if context_issue is not None:
            rejections.append(context_issue)
            failure_reasons.append(ReplayFailureReason.SOURCE_VERSION_CONTEXT_UNPROVEN.value)

    lookahead = _lookahead_rejections(window_events, schedule)
    if lookahead:
        rejections.extend(lookahead)
        failure_reasons.append(ReplayFailureReason.TEMPORAL_ADMISSION_REJECTED.value)

    manifest = _build_manifest(
        request=request,
        window_events=window_events,
        simulated_time_sequence=schedule,
    )
    fingerprint = compute_determinism_fingerprint(manifest)
    replay_id = f"replay_{fingerprint[:16]}"
    manifest = {**manifest, "chunk_size": request.chunk_size, "replay_id": replay_id}

    if failure_reasons:
        return ReplayResult(
            replay_id=replay_id,
            start_time=start,
            end_time=end,
            processed_event_count=len(window_events),
            admitted_event_count=0,
            rejected_event_count=len(rejections),
            simulated_time_sequence=schedule,
            replay_outputs=(),
            rejections=tuple(rejections),
            replay_manifest={**manifest, "determinism_fingerprint": fingerprint},
            evidence_class=REPLAY_EVIDENCE_CLASS,
            determinism_fingerprint=fingerprint,
            success=False,
            failure_reasons=tuple(sorted(set(failure_reasons))),
        )

    replay_outputs: list[ReplayStepOutput] = []
    admitted_ids: set[str] = set()
    rejected_count = 0

    for simulated_time in schedule:
        eligible = [event for event in window_events if _events_eligible_at(event, simulated_time)]
        records = [event.to_temporal_record() for event in eligible]
        firewall = evaluate_temporal_leakage_firewall(
            records,
            TemporalProcessingContext(
                simulated_time=simulated_time,
                strict_mode=request.strict_mode,
                operation="deterministic_mass_replay",
            ),
        )
        reconstruction: PitReconstructionResult = firewall.reconstruction
        if not firewall.allowed:
            rejected_count += len(firewall.rejections)
            for rejection in firewall.rejections:
                rejections.append(
                    ReplayRejection(
                        simulated_time=simulated_time,
                        event_id=rejection.record_id,
                        reason=rejection.reason,
                        reason_code=ReplayFailureReason.TEMPORAL_ADMISSION_REJECTED.value,
                    )
                )
            failure_reasons.append(ReplayFailureReason.TEMPORAL_ADMISSION_REJECTED.value)
            continue

        step_admitted = tuple(sorted(event.event_id for event in eligible))
        admitted_ids.update(step_admitted)
        replay_outputs.append(
            ReplayStepOutput(
                simulated_time=simulated_time,
                admitted_event_ids=step_admitted,
                state_by_entity={
                    entity: record.record_id for entity, record in reconstruction.state_by_entity.items()
                },
                reconstruction=reconstruction.to_metadata(),
            )
        )

    success = len(failure_reasons) == 0
    return ReplayResult(
        replay_id=replay_id,
        start_time=start,
        end_time=end,
        processed_event_count=len(window_events),
        admitted_event_count=len(admitted_ids),
        rejected_event_count=rejected_count,
        simulated_time_sequence=schedule,
        replay_outputs=tuple(replay_outputs),
        rejections=tuple(rejections),
        replay_manifest={**manifest, "replay_id": replay_id, "determinism_fingerprint": fingerprint},
        evidence_class=REPLAY_EVIDENCE_CLASS,
        determinism_fingerprint=fingerprint,
        success=success,
        failure_reasons=tuple(sorted(set(failure_reasons))),
    )


def new_replay_id() -> str:
    return f"replay_{uuid4().hex[:16]}"
