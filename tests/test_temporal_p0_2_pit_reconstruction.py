"""Focused P0.2 Point-in-Time Reconstruction boundary tests."""

from __future__ import annotations

from datetime import UTC, datetime

from blackdark.temporal import TemporalObservation, TemporalSemanticField, TemporalTimestamp
from blackdark.temporal.reconstruction import TemporalRecord, reconstruct_point_in_time

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
) -> TemporalRecord:
    return TemporalRecord(
        record_id=record_id,
        entity_key=entity_key,
        observation=_observation(available_at=available_at, revised_at=revised_at),
        payload={"value": value},
        version=version,
    )


def test_accessible_records_included_in_reconstruction() -> None:
    record = _record("r1", "entity-a", available_at=T_EARLY, revised_at=T_EARLY, version="1", value="alpha")
    result = reconstruct_point_in_time([record], T0)
    assert result.state_by_entity["entity-a"].record_id == "r1"
    assert len(result.included) == 1
    assert result.excluded == ()


def test_future_available_at_records_excluded() -> None:
    record = _record("r-future", "entity-a", available_at=T_LATE, revised_at=T_LATE, version="2", value="future")
    result = reconstruct_point_in_time([record], T0)
    assert "entity-a" not in result.state_by_entity
    assert result.excluded[0].reason == "available_at_after_simulated_time"


def test_unknown_available_at_strict_mode_excluded() -> None:
    observation = TemporalObservation.create(
        event_time=_ts(TemporalSemanticField.EVENT_TIME, T_EARLY),
        observed_time=_unknown(TemporalSemanticField.OBSERVED_TIME),
        available_at=_unknown(TemporalSemanticField.AVAILABLE_AT),
        ingested_at=_unknown(TemporalSemanticField.INGESTED_AT),
        effective_at=_ts(TemporalSemanticField.EFFECTIVE_AT, T_EARLY),
        revised_at=_ts(TemporalSemanticField.REVISED_AT, T_EARLY),
    )
    record = TemporalRecord(record_id="r-unknown", entity_key="entity-a", observation=observation)
    result = reconstruct_point_in_time([record], T0, strict=True)
    assert result.state_by_entity == {}
    assert result.excluded[0].reason == "unknown_available_at_fail_closed"


def test_revision_not_visible_until_available_at() -> None:
    v1 = _record("r-v1", "entity-a", available_at=T_EARLY, revised_at=T_EARLY, version="1", value="v1")
    v2 = _record("r-v2", "entity-a", available_at=T_LATE, revised_at=T_LATE, version="2", value="v2")
    result = reconstruct_point_in_time([v1, v2], T0)
    assert result.state_by_entity["entity-a"].payload == {"value": "v1"}
    reasons = {item.reason for item in result.excluded}
    assert "available_at_after_simulated_time" in reasons


def test_later_valid_revision_supersedes_earlier_state() -> None:
    v1 = _record("r-v1", "entity-a", available_at=T_EARLY, revised_at=T_EARLY, version="1", value="v1")
    v2 = _record("r-v2", "entity-a", available_at=T_MID, revised_at=T_MID, version="2", value="v2")
    result = reconstruct_point_in_time([v1, v2], T0)
    assert result.state_by_entity["entity-a"].record_id == "r-v2"
    assert any(item.reason == "superseded_by_historically_valid_revision" for item in result.excluded)


def test_revision_with_future_revised_at_excluded_prevents_revision_leakage() -> None:
    v1 = _record("r-v1", "entity-a", available_at=T_EARLY, revised_at=T_EARLY, version="1", value="v1")
    leaked = TemporalRecord(
        record_id="r-leak",
        entity_key="entity-a",
        observation=_observation(
            available_at=T_MID,
            revised_at=T_FUTURE_REV,
            effective_at=T_MID,
        ),
        payload={"value": "leaked"},
        version="3",
    )
    result = reconstruct_point_in_time([v1, leaked], T0)
    assert result.state_by_entity["entity-a"].record_id == "r-v1"
    assert any(item.reason == "revision_not_yet_occurred" for item in result.excluded)


def test_temporal_provenance_preserved_in_reconstruction_result() -> None:
    record = _record("r1", "entity-a", available_at=T_EARLY, revised_at=T_EARLY, version="1", value="alpha")
    meta = reconstruct_point_in_time([record], T0).to_metadata()
    included_meta = meta["included"][0]["observation"]["available_at"]
    assert included_meta["provenance"] == "DIRECT"
    assert included_meta["field"] == "available_at"


def test_reconstruction_uses_p0_1_accessibility_without_duplication() -> None:
    accessible = reconstruct_point_in_time(
        [_record("r1", "entity-a", available_at=T_EARLY, revised_at=T_EARLY, version="1", value="alpha")],
        T0,
    )
    inaccessible = reconstruct_point_in_time(
        [_record("r2", "entity-b", available_at=T_LATE, revised_at=T_LATE, version="1", value="beta")],
        T0,
    )
    assert accessible.excluded == ()
    assert inaccessible.excluded[0].accessibility_decision is not None
    assert inaccessible.excluded[0].accessibility_decision.reason == "available_at_after_simulated_time"
