"""Point-in-time accessibility guard — canonical Temporal leakage firewall primitive (P0.1)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping

from blackdark.temporal.truth import (
    AVAILABLE_AT_FIELD_ALIASES,
    TemporalSemanticField,
    TemporalTimestamp,
    TimestampProvenanceKind,
    parse_temporal_instant,
)


@dataclass(frozen=True, slots=True)
class PitAccessibilityDecision:
    """Result of a point-in-time accessibility evaluation."""

    accessible: bool
    reason: str
    simulated_time: datetime
    available_at: datetime | None
    available_at_provenance: TimestampProvenanceKind | None
    strict: bool

    def to_metadata(self) -> dict[str, Any]:
        return {
            "accessible": self.accessible,
            "reason": self.reason,
            "simulated_time": self.simulated_time.isoformat(),
            "available_at": self.available_at.isoformat() if self.available_at is not None else None,
            "available_at_provenance": (
                self.available_at_provenance.value if self.available_at_provenance is not None else None
            ),
            "strict": self.strict,
        }


def evaluate_pit_accessibility(
    available_at: TemporalTimestamp,
    simulated_time: datetime | str,
    *,
    strict: bool = True,
) -> PitAccessibilityDecision:
    """
    Canonical accessibility primitive.

    Semantics:
    - known available_at <= simulated_time -> accessible
    - known available_at > simulated_time -> inaccessible
    - unknown/unproven available_at under strict PIT -> inaccessible (fail closed)
    """
    if available_at.field != TemporalSemanticField.AVAILABLE_AT:
        raise ValueError("evaluate_pit_accessibility requires available_at semantics")

    sim = parse_temporal_instant(simulated_time)

    if not available_at.is_known():
        return PitAccessibilityDecision(
            accessible=False,
            reason="unknown_available_at_fail_closed",
            simulated_time=sim,
            available_at=None,
            available_at_provenance=TimestampProvenanceKind.UNKNOWN,
            strict=strict,
        )

    assert available_at.value is not None
    if available_at.value > sim:
        return PitAccessibilityDecision(
            accessible=False,
            reason="available_at_after_simulated_time",
            simulated_time=sim,
            available_at=available_at.value,
            available_at_provenance=available_at.provenance,
            strict=strict,
        )

    return PitAccessibilityDecision(
        accessible=True,
        reason="available_at_lte_simulated_time",
        simulated_time=sim,
        available_at=available_at.value,
        available_at_provenance=available_at.provenance,
        strict=strict,
    )


def extract_available_at_from_row(
    row: Mapping[str, Any],
    *,
    time_field: str = "available_at",
) -> TemporalTimestamp | None:
    """
    Extract available_at semantics from a row without cross-field substitution.

    Returns None when the requested field is absent. Does not fall back to event_time,
    ingested_at, freshness, SLA, or other non-available_at fields.
    """
    if time_field not in AVAILABLE_AT_FIELD_ALIASES:
        raise ValueError(f"Unsupported available_at field alias: {time_field}")

    raw = row.get(time_field)
    if raw is None or raw == "":
        return None

    meta = row.get("meta") if isinstance(row.get("meta"), dict) else {}
    provenance_raw = meta.get("available_at_provenance") or row.get("available_at_provenance")
    basis = meta.get("available_at_derivation_basis") or row.get("available_at_derivation_basis")

    if provenance_raw == TimestampProvenanceKind.DERIVED.value:
        if not basis:
            return TemporalTimestamp.unknown(TemporalSemanticField.AVAILABLE_AT)
        return TemporalTimestamp.derived(
            TemporalSemanticField.AVAILABLE_AT,
            raw,
            derivation_basis=str(basis),
        )
    if provenance_raw == TimestampProvenanceKind.UNKNOWN.value:
        return TemporalTimestamp.unknown(TemporalSemanticField.AVAILABLE_AT)

    return TemporalTimestamp.direct(TemporalSemanticField.AVAILABLE_AT, raw)


def filter_point_in_time(
    rows: list[dict[str, Any]],
    *,
    cutoff: datetime | str,
    time_field: str = "available_at",
    strict: bool = True,
) -> list[dict[str, Any]]:
    """
    Filter rows to those accessible at simulated decision time.

    Uses only the requested available_at semantic field; never substitutes event_time or
    other Temporal fields when available_at is missing.
    """
    accessible_rows: list[dict[str, Any]] = []
    for row in rows:
        available_at = extract_available_at_from_row(row, time_field=time_field)
        if available_at is None:
            if strict:
                continue
            raise ValueError("missing_available_at_under_non_strict_mode")
        decision = evaluate_pit_accessibility(available_at, cutoff, strict=strict)
        if decision.accessible:
            accessible_rows.append(row)
    return accessible_rows
