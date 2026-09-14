"""Focused P0.3 Temporal Leakage Firewall tests."""

from __future__ import annotations

from datetime import UTC, datetime

from blackdark.temporal import (
    LeakageClass,
    TemporalObservation,
    TemporalProcessingContext,
    TemporalRecord,
    TemporalSemanticField,
    TemporalTimestamp,
    evaluate_pit_accessibility,
    evaluate_temporal_leakage_firewall,
    extract_available_at_from_row,
    filter_point_in_time,
    reconstruct_point_in_time,
)
from temporal_leakage_firewall import evaluate_temporal_leakage_firewall as registry_evaluate_firewall

T0 = datetime(2024, 6, 1, 12, 0, 0, tzinfo=UTC)
T_EARLY = datetime(2024, 6, 1, 9, 0, 0, tzinfo=UTC)
T_MID = datetime(2024, 6, 1, 11, 0, 0, tzinfo=UTC)
T_LATE = datetime(2024, 6, 1, 14, 0, 0, tzinfo=UTC)
T_FUTURE_REV = datetime(2024, 6, 1, 15, 0, 0, tzinfo=UTC)


def _ts(field: TemporalSemanticField, value: datetime) -> TemporalTimestamp:
    return TemporalTimestamp.direct(field, value)


def _unknown(field: TemporalSemanticField) -> TemporalTimestamp:
    return TemporalTimestamp.unknown(field)


def _observation(
    *,
    available_at: datetime,
    revised_at: datetime,
    effective_at: datetime | None = None,
    event_time: datetime | None = None,
) -> TemporalObservation:
    eff = effective_at or revised_at
    evt = event_time or available_at
    return TemporalObservation.create(
        event_time=_ts(TemporalSemanticField.EVENT_TIME, evt),
        observed_time=_ts(TemporalSemanticField.OBSERVED_TIME, available_at),
        available_at=_ts(TemporalSemanticField.AVAILABLE_AT, available_at),
        ingested_at=_ts(TemporalSemanticField.INGESTED_AT, available_at),
        effective_at=_ts(TemporalSemanticField.EFFECTIVE_AT, eff),
        revised_at=_ts(TemporalSemanticField.REVISED_AT, revised_at),
    )


def _record(
    record_id: str,
    entity_key: str,
    *,
    available_at: datetime,
    revised_at: datetime,
    version: str,
    value: str,
    effective_at: datetime | None = None,
    event_time: datetime | None = None,
) -> TemporalRecord:
    return TemporalRecord(
        record_id=record_id,
        entity_key=entity_key,
        observation=_observation(
            available_at=available_at,
            revised_at=revised_at,
            effective_at=effective_at,
            event_time=event_time,
        ),
        payload={"value": value},
        version=version,
    )


def _context(strict: bool = True) -> TemporalProcessingContext:
    return TemporalProcessingContext(simulated_time=T0, strict_mode=strict)


def test_future_available_at_rejected() -> None:
    record = _record("r1", "entity-a", available_at=T_LATE, revised_at=T_LATE, version="1", value="future")
    decision = evaluate_temporal_leakage_firewall([record], _context())
    assert decision.allowed is False
    assert LeakageClass.FUTURE_AVAILABILITY.value in decision.reason_codes


def test_unknown_available_at_rejected_in_strict_mode() -> None:
    observation = TemporalObservation.create(
        event_time=_ts(TemporalSemanticField.EVENT_TIME, T_EARLY),
        observed_time=_unknown(TemporalSemanticField.OBSERVED_TIME),
        available_at=_unknown(TemporalSemanticField.AVAILABLE_AT),
        ingested_at=_unknown(TemporalSemanticField.INGESTED_AT),
        effective_at=_ts(TemporalSemanticField.EFFECTIVE_AT, T_EARLY),
        revised_at=_ts(TemporalSemanticField.REVISED_AT, T_EARLY),
    )
    record = TemporalRecord(record_id="r-unknown", entity_key="entity-a", observation=observation)
    decision = evaluate_temporal_leakage_firewall([record], _context(strict=True))
    assert decision.allowed is False
    assert LeakageClass.UNKNOWN_AVAILABILITY.value in decision.reason_codes


def test_future_revision_rejected() -> None:
    record = TemporalRecord(
        record_id="r-rev",
        entity_key="entity-a",
        observation=_observation(available_at=T_MID, revised_at=T_FUTURE_REV, effective_at=T_MID),
        payload={"value": "future-rev"},
        version="1",
    )
    decision = evaluate_temporal_leakage_firewall([record], _context())
    assert decision.allowed is False
    assert LeakageClass.FUTURE_REVISION.value in decision.reason_codes


def test_unproven_revision_ordering_rejected() -> None:
    same_revision = T_MID
    records = [
        _record("r1", "entity-a", available_at=T_EARLY, revised_at=same_revision, version="1", value="a"),
        _record("r2", "entity-a", available_at=T_EARLY, revised_at=same_revision, version="2", value="b"),
    ]
    decision = evaluate_temporal_leakage_firewall(records, _context())
    assert decision.allowed is False
    assert LeakageClass.UNPROVEN_REVISION_ORDER.value in decision.reason_codes


def test_future_effective_at_rejected() -> None:
    record = TemporalRecord(
        record_id="r-eff",
        entity_key="entity-a",
        observation=_observation(available_at=T_EARLY, revised_at=T_EARLY, effective_at=T_LATE),
        payload={"value": "future-effective"},
        version="1",
    )
    decision = evaluate_temporal_leakage_firewall([record], _context())
    assert decision.allowed is False
    assert LeakageClass.FUTURE_EFFECTIVITY.value in decision.reason_codes


def test_valid_historical_record_allowed() -> None:
    record = _record("r1", "entity-a", available_at=T_EARLY, revised_at=T_EARLY, version="1", value="ok")
    decision = evaluate_temporal_leakage_firewall([record], _context())
    assert decision.allowed is True
    assert decision.reason_codes == ()
    assert decision.admitted_state_by_entity["entity-a"].record_id == "r1"


def test_event_time_cannot_bypass_availability() -> None:
    row = {"event_time": T_EARLY.isoformat(), "available_at": None, "freshness_seconds": 0}
    assert extract_available_at_from_row(row, time_field="available_at") is None
    assert filter_point_in_time([row], cutoff=T0, time_field="available_at", strict=True) == []


def test_freshness_cannot_substitute_for_availability() -> None:
    row = {
        "event_time": T_EARLY.isoformat(),
        "freshness_seconds": 0,
        "sla_deadline": T_EARLY.isoformat(),
        "latest_record_at": T_EARLY.isoformat(),
    }
    assert extract_available_at_from_row(row, time_field="available_at") is None


def test_provenance_classification_preserved() -> None:
    record = _record("r1", "entity-a", available_at=T_EARLY, revised_at=T_EARLY, version="1", value="ok")
    decision = evaluate_temporal_leakage_firewall([record], _context())
    admitted = decision.admitted_state_by_entity["entity-a"]
    assert admitted.observation.available_at.to_metadata()["provenance"] == "DIRECT"


def test_repeated_identical_evaluation_produces_identical_decision() -> None:
    record = _record("r1", "entity-a", available_at=T_EARLY, revised_at=T_EARLY, version="1", value="ok")
    first = evaluate_temporal_leakage_firewall([record], _context())
    second = evaluate_temporal_leakage_firewall([record], _context())
    assert first.to_metadata() == second.to_metadata()


def test_leakage_reason_codes_are_explicit() -> None:
    record = _record("r1", "entity-a", available_at=T_LATE, revised_at=T_LATE, version="1", value="future")
    decision = evaluate_temporal_leakage_firewall([record], _context())
    assert decision.rejections[0].leakage_class == LeakageClass.FUTURE_AVAILABILITY
    assert decision.rejections[0].reason == "available_at_after_simulated_time"


def test_p0_1_accessibility_semantics_unchanged() -> None:
    available = evaluate_pit_accessibility(
        _ts(TemporalSemanticField.AVAILABLE_AT, T_EARLY),
        T0,
        strict=True,
    )
    unavailable = evaluate_pit_accessibility(
        _ts(TemporalSemanticField.AVAILABLE_AT, T_LATE),
        T0,
        strict=True,
    )
    assert available.accessible is True
    assert unavailable.accessible is False
    assert unavailable.reason == "available_at_after_simulated_time"


def test_p0_2_reconstruction_semantics_unchanged() -> None:
    record = _record("r1", "entity-a", available_at=T_EARLY, revised_at=T_EARLY, version="1", value="ok")
    reconstruction = reconstruct_point_in_time([record], T0)
    assert reconstruction.state_by_entity["entity-a"].record_id == "r1"


def test_cross_time_state_contamination_rejected() -> None:
    record = TemporalRecord(
        record_id="r-cross",
        entity_key="entity-a",
        observation=_observation(
            available_at=T_EARLY,
            revised_at=T_EARLY,
            effective_at=T_EARLY,
            event_time=T_LATE,
        ),
        payload={"value": "cross-time"},
        version="1",
    )
    decision = evaluate_temporal_leakage_firewall([record], _context())
    assert decision.allowed is False
    assert LeakageClass.CROSS_TIME_STATE_CONTAMINATION.value in decision.reason_codes


def test_registry_entrypoint_matches_canonical_firewall() -> None:
    record = _record("r1", "entity-a", available_at=T_EARLY, revised_at=T_EARLY, version="1", value="ok")
    canonical = evaluate_temporal_leakage_firewall([record], _context())
    registry = registry_evaluate_firewall([record], simulated_time=T0, strict_mode=True)
    assert canonical.to_metadata() == registry.to_metadata()
