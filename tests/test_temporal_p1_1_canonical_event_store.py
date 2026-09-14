"""Focused P1.1 Canonical Temporal Historical/Event Store tests."""

from __future__ import annotations

from datetime import UTC, datetime

from blackdark.temporal import (
    CanonicalTemporalEvent,
    ProvenanceMetadata,
    TemporalCanonicalEventStore,
    TemporalEventQuery,
    TemporalObservation,
    TemporalProcessingContext,
    TemporalSemanticField,
    TemporalTimestamp,
    evaluate_temporal_leakage_firewall,
    reconstruct_point_in_time,
)

T0 = datetime(2024, 7, 1, 12, 0, 0, tzinfo=UTC)
T_EARLY = datetime(2024, 7, 1, 9, 0, 0, tzinfo=UTC)
T_LATE = datetime(2024, 7, 1, 14, 0, 0, tzinfo=UTC)


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


def _event(
    event_id: str,
    *,
    entity_key: str = "entity-a",
    event_type: str = "market.tick",
    available_at: datetime = T_EARLY,
    revised_at: datetime = T_EARLY,
    source: str | None = "binance",
    source_version: str | None = "v1",
    dataset_version: str | None = "ds-1",
    record_version: str = "1",
    payload: dict | None = None,
    rights: dict | None = None,
    prior_event_id: str | None = None,
    conflict_metadata: dict | None = None,
) -> CanonicalTemporalEvent:
    return CanonicalTemporalEvent(
        event_id=event_id,
        entity_key=entity_key,
        event_type=event_type,
        payload=payload or {"price": "100"},
        observation=_observation(available_at=available_at, revised_at=revised_at),
        provenance=ProvenanceMetadata(
            source=source,
            source_version=source_version,
            dataset_version=dataset_version,
            rights_or_provenance=rights,
            provenance_reference="prov-ref-1" if source else None,
        ),
        record_version=record_version,
        correction_or_revision_reference=prior_event_id,
        conflict_metadata=conflict_metadata,
    )


def test_canonical_event_persists_without_semantic_field_substitution() -> None:
    store = TemporalCanonicalEventStore()
    event = _event("evt-1")
    store.append_event(event)
    retrieved = store.get_event("evt-1")
    assert retrieved is not None
    meta = retrieved.observation.to_metadata()
    assert meta["available_at"]["field"] == "available_at"
    assert meta["event_time"]["field"] == "event_time"
    assert meta["ingested_at"]["field"] == "ingested_at"


def test_unknown_metadata_remains_unknown() -> None:
    observation = TemporalObservation.create(
        event_time=_ts(TemporalSemanticField.EVENT_TIME, T_EARLY),
        observed_time=_unknown(TemporalSemanticField.OBSERVED_TIME),
        available_at=_ts(TemporalSemanticField.AVAILABLE_AT, T_EARLY),
        ingested_at=_unknown(TemporalSemanticField.INGESTED_AT),
        effective_at=_unknown(TemporalSemanticField.EFFECTIVE_AT),
        revised_at=_ts(TemporalSemanticField.REVISED_AT, T_EARLY),
    )
    event = CanonicalTemporalEvent(
        event_id="evt-unknown",
        entity_key="entity-a",
        event_type="market.tick",
        payload={"price": "100"},
        observation=observation,
        provenance=ProvenanceMetadata(),
        record_version="1",
    )
    store = TemporalCanonicalEventStore()
    store.append_event(event)
    retrieved = store.get_event("evt-unknown")
    assert retrieved is not None
    assert retrieved.observation.ingested_at.to_metadata()["provenance"] == "UNKNOWN"
    assert retrieved.provenance.to_metadata()["source_known"] is False


def test_later_revision_preserves_prior_historical_version() -> None:
    store = TemporalCanonicalEventStore()
    v1 = _event("evt-v1", record_version="1", payload={"price": "100"})
    v2 = _event("evt-v2", record_version="2", payload={"price": "101"})
    store.append_event(v1)
    store.append_revision(v2, prior_event_id="evt-v1")
    assert store.get_event("evt-v1") is not None
    assert store.get_event("evt-v2") is not None
    assert store.event_count == 2


def test_prior_historical_version_remains_retrievable() -> None:
    store = TemporalCanonicalEventStore()
    v1 = _event("evt-v1", record_version="1", payload={"price": "100"})
    v2 = _event("evt-v2", record_version="2", payload={"price": "101"})
    store.append_event(v1)
    store.append_revision(v2, prior_event_id="evt-v1")
    prior = store.retrieve(TemporalEventQuery(record_version="1"))
    assert len(prior) == 1
    assert prior[0].payload["price"] == "100"


def test_lineage_between_revision_and_prior_version_preserved() -> None:
    store = TemporalCanonicalEventStore()
    v1 = _event("evt-v1", record_version="1")
    v2 = _event("evt-v2", record_version="2")
    store.append_event(v1)
    store.append_revision(v2, prior_event_id="evt-v1")
    lineage = store.retrieve_lineage("evt-v2")
    assert [event.event_id for event in lineage] == ["evt-v1", "evt-v2"]
    assert lineage[-1].correction_or_revision_reference == "evt-v1"


def test_conflicting_source_records_not_silently_collapsed() -> None:
    store = TemporalCanonicalEventStore()
    a = _event("evt-a", source="binance", payload={"price": "100"})
    b = _event(
        "evt-b",
        source="kraken",
        payload={"price": "101"},
        conflict_metadata={"conflict_group": "cg-1", "reason": "source_value_mismatch"},
    )
    store.append_event(a)
    store.append_conflicting_event(b, conflict_metadata=b.conflict_metadata or {})
    results = store.retrieve(TemporalEventQuery(entity_key="entity-a"))
    assert len(results) == 2
    assert {event.provenance.source for event in results} == {"binance", "kraken"}


def test_deterministic_retrieval_ordering() -> None:
    store = TemporalCanonicalEventStore()
    events = [
        _event("evt-c", available_at=T_EARLY, source="binance", event_type="market.tick"),
        _event("evt-a", available_at=T_EARLY, source="binance", event_type="market.tick"),
        _event("evt-b", available_at=T_EARLY, source="binance", event_type="market.tick"),
    ]
    for event in events:
        store.append_event(event)
    first = store.retrieve(TemporalEventQuery(entity_key="entity-a"))
    second = store.retrieve(TemporalEventQuery(entity_key="entity-a"))
    assert [event.event_id for event in first] == [event.event_id for event in second]
    assert [event.event_id for event in first] == sorted(event.event_id for event in events)


def test_future_available_stored_records_rejected_by_p0_firewall() -> None:
    store = TemporalCanonicalEventStore()
    future = _event("evt-future", available_at=T_LATE, revised_at=T_LATE)
    store.append_event(future)
    stored = store.get_event("evt-future")
    assert stored is not None
    decision = evaluate_temporal_leakage_firewall(
        [stored.to_temporal_record()],
        TemporalProcessingContext(simulated_time=T0, strict_mode=True),
    )
    assert decision.allowed is False


def test_provenance_metadata_survives_store_retrieve() -> None:
    store = TemporalCanonicalEventStore()
    event = _event(
        "evt-prov",
        rights={"license_class": "internal_analysis_only"},
        source="binance",
        source_version="v2",
        dataset_version="ds-9",
    )
    store.append_event(event)
    retrieved = store.get_event("evt-prov")
    assert retrieved is not None
    assert retrieved.provenance.rights_or_provenance == {"license_class": "internal_analysis_only"}
    assert retrieved.provenance.source_version == "v2"
    assert retrieved.provenance.dataset_version == "ds-9"


def test_source_version_dataset_metadata_remain_distinct() -> None:
    event = _event("evt-meta", source="binance", source_version="v1", dataset_version="ds-1")
    meta = event.provenance.to_metadata()
    assert meta["source"] == "binance"
    assert meta["source_version"] == "v1"
    assert meta["dataset_version"] == "ds-1"
    assert meta["source"] != meta["source_version"]


def test_no_timestamp_fabrication_for_unknown_fields() -> None:
    event = _event("evt-no-fab")
    event = CanonicalTemporalEvent(
        event_id=event.event_id,
        entity_key=event.entity_key,
        event_type=event.event_type,
        payload=event.payload,
        observation=TemporalObservation.create(
            event_time=_ts(TemporalSemanticField.EVENT_TIME, T_EARLY),
            observed_time=_unknown(TemporalSemanticField.OBSERVED_TIME),
            available_at=_ts(TemporalSemanticField.AVAILABLE_AT, T_EARLY),
            ingested_at=_unknown(TemporalSemanticField.INGESTED_AT),
            effective_at=_unknown(TemporalSemanticField.EFFECTIVE_AT),
            revised_at=_ts(TemporalSemanticField.REVISED_AT, T_EARLY),
        ),
        provenance=ProvenanceMetadata(),
        record_version="1",
    )
    assert event.observation.ingested_at.is_known() is False
    assert event.observation.observed_time.is_known() is False


def test_p0_reconstruction_and_firewall_behavior_unchanged() -> None:
    store = TemporalCanonicalEventStore()
    ok = _event("evt-ok", available_at=T_EARLY, revised_at=T_EARLY)
    store.append_event(ok)
    reconstruction = reconstruct_point_in_time([ok.to_temporal_record()], T0)
    assert reconstruction.state_by_entity["entity-a"].record_id == "evt-ok"
    decision = evaluate_temporal_leakage_firewall(
        [ok.to_temporal_record()],
        TemporalProcessingContext(simulated_time=T0, strict_mode=True),
    )
    assert decision.allowed is True
