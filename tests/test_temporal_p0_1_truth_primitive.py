"""Focused P0.1 Temporal truth primitive tests."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from blackdark.temporal import (
    PitAccessibilityDecision,
    TemporalObservation,
    TemporalSemanticField,
    TemporalTimestamp,
    TimestampProvenanceKind,
    evaluate_pit_accessibility,
    extract_available_at_from_row,
    filter_point_in_time,
)
from temporal_leakage_firewall import filter_point_in_time as registry_filter_point_in_time

T0 = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
T_BEFORE = datetime(2024, 1, 1, 11, 0, 0, tzinfo=UTC)
T_AFTER = datetime(2024, 1, 1, 13, 0, 0, tzinfo=UTC)


def _available_at(value: datetime, *, provenance: str = "DIRECT", basis: str | None = None) -> TemporalTimestamp:
    if provenance == "DIRECT":
        return TemporalTimestamp.direct(TemporalSemanticField.AVAILABLE_AT, value)
    if provenance == "DERIVED":
        assert basis is not None
        return TemporalTimestamp.derived(
            TemporalSemanticField.AVAILABLE_AT,
            value,
            derivation_basis=basis,
        )
    return TemporalTimestamp.unknown(TemporalSemanticField.AVAILABLE_AT)


def test_known_available_at_before_simulated_time_is_accessible() -> None:
    decision = evaluate_pit_accessibility(_available_at(T_BEFORE), T0)
    assert decision.accessible is True
    assert decision.reason == "available_at_lte_simulated_time"


def test_known_available_at_equal_simulated_time_is_accessible() -> None:
    decision = evaluate_pit_accessibility(_available_at(T0), T0)
    assert decision.accessible is True
    assert decision.reason == "available_at_lte_simulated_time"


def test_known_available_at_after_simulated_time_is_inaccessible() -> None:
    decision = evaluate_pit_accessibility(_available_at(T_AFTER), T0)
    assert decision.accessible is False
    assert decision.reason == "available_at_after_simulated_time"


def test_unknown_available_at_strict_pit_fails_closed() -> None:
    decision = evaluate_pit_accessibility(
        TemporalTimestamp.unknown(TemporalSemanticField.AVAILABLE_AT),
        T0,
        strict=True,
    )
    assert decision.accessible is False
    assert decision.reason == "unknown_available_at_fail_closed"
    assert decision.available_at_provenance == TimestampProvenanceKind.UNKNOWN


def test_no_fallback_from_freshness_or_ingested_at_to_available_at() -> None:
    row = {
        "event_time": T_BEFORE.isoformat(),
        "ingested_at": T_BEFORE.isoformat(),
        "freshness_seconds": 0,
        "sla_deadline": T_BEFORE.isoformat(),
        "latest_record_at": T_BEFORE.isoformat(),
    }
    assert extract_available_at_from_row(row, time_field="available_at") is None
    assert filter_point_in_time([row], cutoff=T0, time_field="available_at", strict=True) == []


def test_provenance_direct_derived_unknown_retained() -> None:
    direct = TemporalTimestamp.direct(TemporalSemanticField.EVENT_TIME, T0)
    derived = TemporalTimestamp.derived(
        TemporalSemanticField.OBSERVED_TIME,
        T0,
        derivation_basis="exchange_ack_timestamp",
    )
    unknown = TemporalTimestamp.unknown(TemporalSemanticField.AVAILABLE_AT)

    assert direct.to_metadata()["provenance"] == "DIRECT"
    assert derived.to_metadata()["provenance"] == "DERIVED"
    assert derived.to_metadata()["derivation_basis"] == "exchange_ack_timestamp"
    assert unknown.to_metadata()["provenance"] == "UNKNOWN"
    assert unknown.to_metadata()["known"] is False

    with pytest.raises(ValueError, match="must not carry derivation_basis"):
        TemporalTimestamp(
            field=TemporalSemanticField.AVAILABLE_AT,
            provenance=TimestampProvenanceKind.DIRECT,
            value=T0,
            derivation_basis="illegal_promotion",
        )


def test_event_time_cannot_substitute_for_available_at() -> None:
    row = {"event_time": T_BEFORE.isoformat(), "available_at": None}
    assert extract_available_at_from_row(row, time_field="available_at") is None

    row_only_event = {"event_time": T_BEFORE.isoformat()}
    filtered = filter_point_in_time([row_only_event], cutoff=T0, time_field="available_at", strict=True)
    assert filtered == []


def test_temporal_observation_preserves_non_interchangeable_fields() -> None:
    observation = TemporalObservation.create(
        event_time=TemporalTimestamp.direct(TemporalSemanticField.EVENT_TIME, T_BEFORE),
        observed_time=TemporalTimestamp.unknown(TemporalSemanticField.OBSERVED_TIME),
        available_at=TemporalTimestamp.direct(TemporalSemanticField.AVAILABLE_AT, T0),
        ingested_at=TemporalTimestamp.direct(TemporalSemanticField.INGESTED_AT, T_AFTER),
        effective_at=TemporalTimestamp.unknown(TemporalSemanticField.EFFECTIVE_AT),
        revised_at=TemporalTimestamp.unknown(TemporalSemanticField.REVISED_AT),
    )
    meta = observation.to_metadata()
    assert meta["event_time"]["field"] == "event_time"
    assert meta["available_at"]["field"] == "available_at"
    assert meta["ingested_at"]["value"] != meta["available_at"]["value"]


def test_registry_entrypoint_matches_canonical_filter() -> None:
    rows = [
        {"dataset_id": "d1", "available_time": T_BEFORE.isoformat()},
        {"dataset_id": "d1", "available_time": T_AFTER.isoformat()},
        {"dataset_id": "d1", "event_time": T_BEFORE.isoformat()},
    ]
    canonical = filter_point_in_time(rows, cutoff=T0, time_field="available_time", strict=True)
    registry = registry_filter_point_in_time(rows, cutoff=T0, time_field="available_time", strict=True)
    assert canonical == registry == [rows[0]]


def test_derived_available_at_without_basis_treated_as_unknown_for_filter() -> None:
    row = {
        "available_at": T_BEFORE.isoformat(),
        "meta": {"available_at_provenance": "DERIVED"},
    }
    assert filter_point_in_time([row], cutoff=T0, time_field="available_at", strict=True) == []


def test_derived_available_at_with_basis_can_be_accessible() -> None:
    row = {
        "available_at": T_BEFORE.isoformat(),
        "meta": {
            "available_at_provenance": "DERIVED",
            "available_at_derivation_basis": "source_publication_log",
        },
    }
    assert filter_point_in_time([row], cutoff=T0, time_field="available_at", strict=True) == [row]
