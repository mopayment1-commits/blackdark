"""Temporal Leakage Firewall (P0.3) — canonical admissibility boundary."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Mapping, Sequence

from blackdark.temporal.reconstruction import (
    PitReconstructionResult,
    TemporalRecord,
    reconstruct_point_in_time,
)
from blackdark.temporal.truth import parse_temporal_instant


class LeakageClass(str, Enum):
    FUTURE_AVAILABILITY = "FUTURE_AVAILABILITY"
    UNKNOWN_AVAILABILITY = "UNKNOWN_AVAILABILITY"
    FUTURE_REVISION = "FUTURE_REVISION"
    UNPROVEN_REVISION_ORDER = "UNPROVEN_REVISION_ORDER"
    FUTURE_EFFECTIVITY = "FUTURE_EFFECTIVITY"
    TEMPORAL_PROVENANCE_UNPROVEN = "TEMPORAL_PROVENANCE_UNPROVEN"
    CROSS_TIME_STATE_CONTAMINATION = "CROSS_TIME_STATE_CONTAMINATION"


LEAKAGE_REASON_MAP: dict[str, LeakageClass] = {
    "available_at_after_simulated_time": LeakageClass.FUTURE_AVAILABILITY,
    "unknown_available_at_fail_closed": LeakageClass.UNKNOWN_AVAILABILITY,
    "revision_not_yet_occurred": LeakageClass.FUTURE_REVISION,
    "unproven_revision_order_fail_closed": LeakageClass.UNPROVEN_REVISION_ORDER,
    "effective_at_after_simulated_time": LeakageClass.FUTURE_EFFECTIVITY,
    "unknown_effective_at_fail_closed": LeakageClass.TEMPORAL_PROVENANCE_UNPROVEN,
    "unknown_revised_at_fail_closed": LeakageClass.TEMPORAL_PROVENANCE_UNPROVEN,
}

NON_LEAKAGE_REASONS = frozenset({"superseded_by_historically_valid_revision", "temporally_valid_at_simulated_time"})


@dataclass(frozen=True, slots=True)
class TemporalProcessingContext:
    """Temporal processing admission context."""

    simulated_time: datetime | str
    strict_mode: bool = True
    operation: str = "temporal_admission"

    def to_metadata(self) -> dict[str, Any]:
        return {
            "simulated_time": parse_temporal_instant(self.simulated_time).isoformat(),
            "strict_mode": self.strict_mode,
            "operation": self.operation,
        }


@dataclass(frozen=True, slots=True)
class TemporalLeakageRejection:
    """One rejected record with explicit leakage classification."""

    record_id: str
    entity_key: str
    reason: str
    leakage_class: LeakageClass
    observation: Mapping[str, Any]

    def to_metadata(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "entity_key": self.entity_key,
            "reason": self.reason,
            "leakage_class": self.leakage_class.value,
            "observation": dict(self.observation),
        }


@dataclass(frozen=True, slots=True)
class TemporalLeakageFirewallDecision:
    """Machine-readable Temporal Leakage Firewall decision."""

    allowed: bool
    reason_codes: tuple[str, ...]
    simulated_time: datetime
    evaluated_record_count: int
    rejected_record_count: int
    provenance: Mapping[str, Any]
    strict_mode: bool
    reconstruction: PitReconstructionResult
    rejections: tuple[TemporalLeakageRejection, ...]
    admitted_state_by_entity: Mapping[str, TemporalRecord]

    def to_metadata(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "reason_codes": list(self.reason_codes),
            "simulated_time": self.simulated_time.isoformat(),
            "evaluated_record_count": self.evaluated_record_count,
            "rejected_record_count": self.rejected_record_count,
            "provenance": dict(self.provenance),
            "strict_mode": self.strict_mode,
            "reconstruction": self.reconstruction.to_metadata(),
            "rejections": [rejection.to_metadata() for rejection in self.rejections],
            "admitted_state_by_entity": {
                key: record.to_metadata() for key, record in self.admitted_state_by_entity.items()
            },
        }


def _classify_exclusion_reason(reason: str) -> LeakageClass | None:
    if reason in NON_LEAKAGE_REASONS:
        return None
    if reason in LEAKAGE_REASON_MAP:
        return LEAKAGE_REASON_MAP[reason]
    if reason.startswith("unknown_") and reason.endswith("_fail_closed"):
        return LeakageClass.TEMPORAL_PROVENANCE_UNPROVEN
    return LeakageClass.CROSS_TIME_STATE_CONTAMINATION


def _detect_cross_time_contamination(record: TemporalRecord, simulated_time: datetime) -> LeakageClass | None:
    event_time = record.observation.event_time
    available_at = record.observation.available_at
    if not event_time.is_known() or not available_at.is_known():
        return None
    assert event_time.value is not None and available_at.value is not None
    if event_time.value <= simulated_time and available_at.value > simulated_time:
        return LeakageClass.CROSS_TIME_STATE_CONTAMINATION
    if event_time.value > simulated_time and available_at.value <= simulated_time:
        return LeakageClass.CROSS_TIME_STATE_CONTAMINATION
    return None


def evaluate_temporal_leakage_firewall(
    records: Sequence[TemporalRecord],
    context: TemporalProcessingContext,
) -> TemporalLeakageFirewallDecision:
    """
    Canonical Temporal Leakage Firewall entrypoint.

    Uses P0.2 reconstruct_point_in_time (which delegates availability to P0.1) without
    independently recalculating point-in-time accessibility.
    """
    sim = parse_temporal_instant(context.simulated_time)
    reconstruction = reconstruct_point_in_time(records, sim, strict=context.strict_mode)

    rejections: list[TemporalLeakageRejection] = []
    reason_codes: set[str] = set()

    for exclusion in reconstruction.excluded:
        leakage_class = _classify_exclusion_reason(exclusion.reason)
        if leakage_class is None:
            continue
        reason_codes.add(leakage_class.value)
        rejections.append(
            TemporalLeakageRejection(
                record_id=exclusion.record.record_id,
                entity_key=exclusion.record.entity_key,
                reason=exclusion.reason,
                leakage_class=leakage_class,
                observation=exclusion.record.observation.to_metadata(),
            )
        )

    for record in records:
        contamination = _detect_cross_time_contamination(record, sim)
        if contamination is None:
            continue
        if any(rejection.record_id == record.record_id for rejection in rejections):
            continue
        reason_codes.add(contamination.value)
        rejections.append(
            TemporalLeakageRejection(
                record_id=record.record_id,
                entity_key=record.entity_key,
                reason="cross_time_state_contamination",
                leakage_class=contamination,
                observation=record.observation.to_metadata(),
            )
        )

    rejected_record_count = len(rejections)
    allowed = rejected_record_count == 0

    provenance = {
        "firewall": "TEMPORAL_LEAKAGE_FIREWALL",
        "p0_1_primitive": "evaluate_pit_accessibility",
        "p0_2_primitive": "reconstruct_point_in_time",
        "authority": "TEMPORAL_LEAKAGE_FIREWALL",
        "upstream_provenance_mutated": False,
        "invalidated_for_current_operation": not allowed,
    }

    return TemporalLeakageFirewallDecision(
        allowed=allowed,
        reason_codes=tuple(sorted(reason_codes)),
        simulated_time=sim,
        evaluated_record_count=len(records),
        rejected_record_count=rejected_record_count,
        provenance=provenance,
        strict_mode=context.strict_mode,
        reconstruction=reconstruction,
        rejections=tuple(rejections),
        admitted_state_by_entity=dict(reconstruction.state_by_entity),
    )
