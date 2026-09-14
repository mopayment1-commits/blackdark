"""Focused P1.2 Deterministic Mass Replay tests."""

from __future__ import annotations

import copy
from datetime import UTC, datetime

from blackdark.temporal import (
    CanonicalTemporalEvent,
    ProvenanceMetadata,
    REPLAY_EVIDENCE_CLASS,
    ReplayRequest,
    TemporalCanonicalEventStore,
    TemporalObservation,
    TemporalSemanticField,
    TemporalTimestamp,
    run_deterministic_mass_replay,
)

T_START = datetime(2024, 8, 1, 9, 0, 0, tzinfo=UTC)
T_MID = datetime(2024, 8, 1, 11, 0, 0, tzinfo=UTC)
T_END = datetime(2024, 8, 1, 14, 0, 0, tzinfo=UTC)
T_EARLY = datetime(2024, 8, 1, 9, 30, 0, tzinfo=UTC)
T_LATE_AVAIL = datetime(2024, 8, 1, 13, 0, 0, tzinfo=UTC)
T_SCHEDULE_EARLY = datetime(2024, 8, 1, 10, 0, 0, tzinfo=UTC)
T_SCHEDULE_LATE = datetime(2024, 8, 1, 12, 0, 0, tzinfo=UTC)


def _ts(field: TemporalSemanticField, value: datetime) -> TemporalTimestamp:
    return TemporalTimestamp.direct(field, value)


def _unknown(field: TemporalSemanticField) -> TemporalTimestamp:
    return TemporalTimestamp.unknown(field)


def _observation(
    *,
    available_at: datetime,
    revised_at: datetime,
    event_time: datetime | None = None,
    effective_at: datetime | None = None,
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


def _event(
    event_id: str,
    *,
    entity_key: str = "entity-a",
    event_type: str = "market.tick",
    available_at: datetime = T_EARLY,
    revised_at: datetime = T_EARLY,
    event_time: datetime | None = None,
    record_version: str = "1",
    source: str = "binance",
    source_version: str | None = "v1",
    dataset_version: str | None = "ds-1",
    payload: dict | None = None,
) -> CanonicalTemporalEvent:
    return CanonicalTemporalEvent(
        event_id=event_id,
        entity_key=entity_key,
        event_type=event_type,
        payload=payload or {"price": event_id},
        observation=_observation(
            available_at=available_at,
            revised_at=revised_at,
            event_time=event_time or available_at,
        ),
        provenance=ProvenanceMetadata(
            source=source,
            source_version=source_version,
            dataset_version=dataset_version,
        ),
        record_version=record_version,
    )


def _request(
    store: TemporalCanonicalEventStore,
    *,
    schedule: list[datetime] | None = None,
    strict: bool = True,
    replay_parameters: dict | None = None,
    version_context: dict | None = None,
    chunk_size: int | None = None,
) -> ReplayRequest:
    return ReplayRequest(
        event_source=store,
        start_time=T_START,
        end_time=T_END,
        replay_clock_or_schedule=schedule or [T_SCHEDULE_EARLY, T_SCHEDULE_LATE],
        strict_mode=strict,
        replay_parameters=replay_parameters or {},
        dataset_or_source_version_context=version_context or {},
        chunk_size=chunk_size,
    )


def test_identical_inputs_produce_identical_replay_result() -> None:
    store = TemporalCanonicalEventStore([_event("evt-a"), _event("evt-b", event_time=T_MID, available_at=T_MID, revised_at=T_MID)])
    first = run_deterministic_mass_replay(_request(store))
    second = run_deterministic_mass_replay(_request(store))
    assert first.to_metadata() == second.to_metadata()


def test_replay_fingerprint_identical_across_repeated_runs() -> None:
    store = TemporalCanonicalEventStore([_event("evt-a")])
    fingerprints = {run_deterministic_mass_replay(_request(store)).determinism_fingerprint for _ in range(3)}
    assert len(fingerprints) == 1


def test_future_available_event_cannot_enter_replay_state() -> None:
    store = TemporalCanonicalEventStore(
        [_event("evt-future", event_time=T_EARLY, available_at=T_LATE_AVAIL, revised_at=T_LATE_AVAIL)]
    )
    result = run_deterministic_mass_replay(_request(store, schedule=[T_SCHEDULE_EARLY]))
    assert result.success is False
    assert any(rejection.reason_code == "TEMPORAL_ADMISSION_REJECTED" for rejection in result.rejections)


def test_unknown_available_at_fails_closed() -> None:
    observation = TemporalObservation.create(
        event_time=_ts(TemporalSemanticField.EVENT_TIME, T_EARLY),
        observed_time=_unknown(TemporalSemanticField.OBSERVED_TIME),
        available_at=_unknown(TemporalSemanticField.AVAILABLE_AT),
        ingested_at=_unknown(TemporalSemanticField.INGESTED_AT),
        effective_at=_ts(TemporalSemanticField.EFFECTIVE_AT, T_EARLY),
        revised_at=_ts(TemporalSemanticField.REVISED_AT, T_EARLY),
    )
    event = CanonicalTemporalEvent(
        event_id="evt-unknown",
        entity_key="entity-a",
        event_type="market.tick",
        payload={"price": "1"},
        observation=observation,
        provenance=ProvenanceMetadata(source="binance"),
        record_version="1",
    )
    store = TemporalCanonicalEventStore([event])
    result = run_deterministic_mass_replay(_request(store))
    assert result.success is False
    assert "MISSING_REQUIRED_TEMPORAL_TRUTH" in result.failure_reasons


def test_later_revision_cannot_contaminate_earlier_replay_state() -> None:
    store = TemporalCanonicalEventStore()
    v1 = _event("evt-v1", record_version="1", payload={"price": "100"})
    v2 = _event(
        "evt-v2",
        record_version="2",
        event_time=T_MID,
        available_at=T_MID,
        revised_at=T_MID,
        payload={"price": "200"},
    )
    store.append_event(v1)
    store.append_revision(v2, prior_event_id="evt-v1")
    early = run_deterministic_mass_replay(_request(store, schedule=[T_SCHEDULE_EARLY]))
    late = run_deterministic_mass_replay(_request(store, schedule=[T_SCHEDULE_LATE]))
    assert early.success is True
    assert late.success is True
    early_state = early.replay_outputs[0].state_by_entity["entity-a"]
    late_state = late.replay_outputs[0].state_by_entity["entity-a"]
    assert early_state == "evt-v1"
    assert late_state == "evt-v2"


def test_unproven_replay_ordering_fails_closed() -> None:
    same_time = T_EARLY
    a = _event("evt-a", event_time=same_time, available_at=same_time, revised_at=same_time, record_version="1")
    b = _event("evt-b", event_time=same_time, available_at=same_time, revised_at=same_time, record_version="1")
    store = TemporalCanonicalEventStore([a, b])
    result = run_deterministic_mass_replay(_request(store))
    assert result.success is False
    assert "UNPROVEN_REPLAY_ORDER" in result.failure_reasons


def test_valid_chronological_events_replay_deterministically() -> None:
    store = TemporalCanonicalEventStore(
        [
            _event("evt-a", event_time=T_EARLY, available_at=T_EARLY, revised_at=T_EARLY),
            _event("evt-b", event_time=T_MID, available_at=T_MID, revised_at=T_MID),
        ]
    )
    result = run_deterministic_mass_replay(_request(store))
    assert result.success is True
    assert result.processed_event_count == 2
    assert result.evidence_class == REPLAY_EVIDENCE_CLASS


def test_replay_manifest_preserves_version_context_without_fabrication() -> None:
    store = TemporalCanonicalEventStore([_event("evt-a", source_version="v1", dataset_version="ds-1")])
    result = run_deterministic_mass_replay(_request(store))
    manifest = result.replay_manifest
    assert manifest["source_versions"]["evt-a"] == "v1"
    assert manifest["dataset_versions"]["evt-a"] == "ds-1"
    assert manifest["engine_version_or_contract_version"]


def test_replay_does_not_mutate_canonical_event_history() -> None:
    store = TemporalCanonicalEventStore([_event("evt-a")])
    before = copy.deepcopy(store.list_events())
    run_deterministic_mass_replay(_request(store))
    after = store.list_events()
    assert [event.to_metadata() for event in before] == [event.to_metadata() for event in after]


def test_replay_does_not_mutate_production_state() -> None:
    production_state = {"decisions": []}
    before = copy.deepcopy(production_state)
    store = TemporalCanonicalEventStore([_event("evt-a")])
    run_deterministic_mass_replay(_request(store))
    assert production_state == before


def test_evidence_class_is_historical_replay_only() -> None:
    store = TemporalCanonicalEventStore([_event("evt-a")])
    result = run_deterministic_mass_replay(_request(store))
    assert result.evidence_class == "HISTORICAL_REPLAY"


def test_replay_cannot_self_promote_evidence_class() -> None:
    store = TemporalCanonicalEventStore([_event("evt-a")])
    result = run_deterministic_mass_replay(_request(store))
    metadata = result.to_metadata()
    assert metadata["evidence_class"] == "HISTORICAL_REPLAY"
    assert "FORWARD_SHADOW" not in str(metadata)
    assert "VERIFIED_PRODUCTION" not in str(metadata)


def test_p0_firewall_effective_inside_replay() -> None:
    store = TemporalCanonicalEventStore(
        [_event("evt-future", event_time=T_EARLY, available_at=T_LATE_AVAIL, revised_at=T_LATE_AVAIL)]
    )
    result = run_deterministic_mass_replay(_request(store, schedule=[T_SCHEDULE_EARLY]))
    assert result.success is False
    assert result.rejected_event_count >= 1


def test_p1_1_lineage_unchanged_after_replay() -> None:
    store = TemporalCanonicalEventStore()
    v1 = _event("evt-v1", record_version="1")
    v2 = _event("evt-v2", record_version="2", event_time=T_MID, available_at=T_MID, revised_at=T_MID)
    store.append_event(v1)
    store.append_revision(v2, prior_event_id="evt-v1")
    lineage_before = store.retrieve_lineage("evt-v2")
    run_deterministic_mass_replay(_request(store))
    lineage_after = store.retrieve_lineage("evt-v2")
    assert [event.event_id for event in lineage_before] == [event.event_id for event in lineage_after]


def test_invalid_replay_window_fails_explicitly() -> None:
    store = TemporalCanonicalEventStore([_event("evt-a")])
    result = run_deterministic_mass_replay(
        ReplayRequest(
            event_source=store,
            start_time=T_END,
            end_time=T_START,
            replay_clock_or_schedule=[T_SCHEDULE_EARLY],
            strict_mode=True,
        )
    )
    assert result.success is False
    assert "INVALID_REPLAY_WINDOW" in result.failure_reasons


def test_chunk_size_does_not_change_replay_semantics() -> None:
    store = TemporalCanonicalEventStore(
        [
            _event("evt-a", event_time=T_EARLY, available_at=T_EARLY, revised_at=T_EARLY),
            _event("evt-b", event_time=T_MID, available_at=T_MID, revised_at=T_MID),
        ]
    )
    baseline = run_deterministic_mass_replay(_request(store))
    chunked = run_deterministic_mass_replay(_request(store, chunk_size=1))
    assert baseline.determinism_fingerprint == chunked.determinism_fingerprint
    assert baseline.replay_outputs == chunked.replay_outputs
    assert baseline.success == chunked.success
