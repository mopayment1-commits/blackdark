"""Point-in-Time Reconstruction boundary (P0.2) — built on P0.1 truth primitives."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Mapping, Sequence

from blackdark.temporal.accessibility import PitAccessibilityDecision, evaluate_pit_accessibility
from blackdark.temporal.truth import TemporalObservation, TemporalSemanticField, parse_temporal_instant


@dataclass(frozen=True, slots=True)
class TemporalRecord:
    """One reconstructable datum with explicit Temporal observation semantics."""

    record_id: str
    entity_key: str
    observation: TemporalObservation
    payload: Mapping[str, Any] | None = None
    version: str | int | None = None

    def to_metadata(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "entity_key": self.entity_key,
            "version": self.version,
            "observation": self.observation.to_metadata(),
            "payload": dict(self.payload) if self.payload is not None else None,
        }


@dataclass(frozen=True, slots=True)
class PitReconstructionExclusion:
    """Explicit exclusion from reconstructed state at simulated_time."""

    record: TemporalRecord
    reason: str
    accessibility_decision: PitAccessibilityDecision | None = None

    def to_metadata(self) -> dict[str, Any]:
        return {
            "record_id": self.record.record_id,
            "entity_key": self.record.entity_key,
            "version": self.record.version,
            "reason": self.reason,
            "accessibility_decision": (
                self.accessibility_decision.to_metadata() if self.accessibility_decision is not None else None
            ),
            "observation": self.record.observation.to_metadata(),
        }


@dataclass(frozen=True, slots=True)
class PitReconstructionResult:
    """Reconstructed legitimately observable state at simulated_time."""

    simulated_time: datetime
    strict: bool
    included: tuple[TemporalRecord, ...]
    excluded: tuple[PitReconstructionExclusion, ...]
    state_by_entity: dict[str, TemporalRecord]

    def to_metadata(self) -> dict[str, Any]:
        return {
            "simulated_time": self.simulated_time.isoformat(),
            "strict": self.strict,
            "included_count": len(self.included),
            "excluded_count": len(self.excluded),
            "entity_count": len(self.state_by_entity),
            "included": [record.to_metadata() for record in self.included],
            "excluded": [item.to_metadata() for item in self.excluded],
            "state_by_entity": {key: record.to_metadata() for key, record in self.state_by_entity.items()},
        }


def _revision_sort_key(record: TemporalRecord) -> tuple[datetime, str, str]:
    revised = record.observation.revised_at
    if revised.is_known() and revised.value is not None:
        revised_at = revised.value
    else:
        revised_at = datetime.min.replace(tzinfo=UTC)
    return (revised_at, str(record.version or ""), record.record_id)


def _is_temporally_valid_at_simulated_time(
    record: TemporalRecord,
    simulated_time: datetime,
    *,
    strict: bool,
) -> tuple[bool, str]:
    observation = record.observation
    for field_ts in (observation.effective_at, observation.revised_at):
        if strict and not field_ts.is_known():
            return False, f"unknown_{field_ts.field.value}_fail_closed"
        if field_ts.is_known():
            assert field_ts.value is not None
            if field_ts.value > simulated_time:
                if field_ts.field == TemporalSemanticField.REVISED_AT:
                    return False, "revision_not_yet_occurred"
                return False, "effective_at_after_simulated_time"
    return True, "temporally_valid_at_simulated_time"


def reconstruct_point_in_time(
    records: Sequence[TemporalRecord],
    simulated_time: datetime | str,
    *,
    strict: bool = True,
) -> PitReconstructionResult:
    """
    Reconstruct only state legitimately observable and available at simulated_time.

    Uses P0.1 evaluate_pit_accessibility for availability gating. Applies deterministic
    revision selection so later knowledge cannot replace historically valid state.
    """
    sim = parse_temporal_instant(simulated_time)
    included: list[TemporalRecord] = []
    excluded: list[PitReconstructionExclusion] = []
    accessible_by_entity: dict[str, list[TemporalRecord]] = {}

    for record in records:
        decision = evaluate_pit_accessibility(record.observation.available_at, sim, strict=strict)
        if not decision.accessible:
            excluded.append(
                PitReconstructionExclusion(
                    record=record,
                    reason=decision.reason,
                    accessibility_decision=decision,
                )
            )
            continue

        valid, reason = _is_temporally_valid_at_simulated_time(record, sim, strict=strict)
        if not valid:
            excluded.append(PitReconstructionExclusion(record=record, reason=reason))
            continue

        included.append(record)
        accessible_by_entity.setdefault(record.entity_key, []).append(record)

    state_by_entity: dict[str, TemporalRecord] = {}
    for entity_key, candidates in accessible_by_entity.items():
        winner = max(candidates, key=lambda candidate: _revision_sort_key(candidate))
        state_by_entity[entity_key] = winner
        for candidate in candidates:
            if candidate.record_id == winner.record_id:
                continue
            excluded.append(
                PitReconstructionExclusion(
                    record=candidate,
                    reason="superseded_by_historically_valid_revision",
                )
            )

    return PitReconstructionResult(
        simulated_time=sim,
        strict=strict,
        included=tuple(included),
        excluded=tuple(excluded),
        state_by_entity=state_by_entity,
    )
