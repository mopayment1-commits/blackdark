"""P1_CANONICAL_EVENT_AND_REPLAY closure runtime/E2E tests."""

from __future__ import annotations

import inspect
import os
import socket
import uuid
from datetime import UTC, datetime

import pytest

from blackdark.temporal import (
    REPLAY_EVIDENCE_CLASS,
    ReplayRequest,
    TemporalCanonicalEventStore,
    TemporalEventStoreError,
    build_retention_descriptor,
    classify_storage_tier,
    run_deterministic_mass_replay,
)
from blackdark.temporal.event_contract import ProvenanceMetadata
from blackdark.temporal.event_store import TemporalCanonicalEventStore as EventStoreClass
from blackdark.temporal.normalization import build_observation_dict, build_provenance_dict, normalize_ingestion_to_canonical_event
from blackdark.temporal.persistence.postgres import PostgresEventStore
from blackdark.temporal.production_spine import ProductionSpineRequest, run_production_temporal_spine
from blackdark.temporal.replay import FORBIDDEN_EVIDENCE_CLASSES
from blackdark.temporal.retention_policy import StorageTier

POSTGRES_URL = os.getenv(
    "BLACKDARK_TEST_DATABASE_URL",
    "postgresql://blackdark:blackdark@127.0.0.1:5432/blackdark_clean",
)


def _postgres_reachable() -> bool:
    try:
        with socket.create_connection(("127.0.0.1", 5432), timeout=1.5):
            return True
    except OSError:
        return False


async def _reset_data_engine(monkeypatch, tmp_path) -> None:
    import asyncpg

    import config
    import blackdark.data.db as db_module

    monkeypatch.setattr(config, "DATABASE_URL", POSTGRES_URL)
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)

    db_module._engine = None
    db_module._session_factory = None
    db_module._schema_ready = False
    db_module._bootstrapped = False

    raw = await asyncpg.connect(POSTGRES_URL)
    await raw.execute("DROP SCHEMA IF EXISTS public CASCADE")
    await raw.execute("CREATE SCHEMA public")
    await raw.close()

    from blackdark.data.db import init_data_engine

    await init_data_engine()


def _ingestion_payload(simulated: str, available: str, *, suffix: str) -> dict:
    return {
        "entity_key": f"P1-{suffix}",
        "event_type": "market_tick",
        "payload": {"price": "100.0"},
        "observation": build_observation_dict(
            event_time=simulated,
            observed_time=simulated,
            available_at=available,
            ingested_at=available,
            effective_at=simulated,
            revised_at=available,
        ),
        "provenance": {
            **build_provenance_dict(
                source="binance",
                source_version="v1",
                dataset_version=f"ds-p1-{suffix}",
                rights_or_provenance={"permitted_purpose": "historical_evaluation"},
            ),
            "retention_policy_reference": "retain-raw-indefinite",
        },
    }


def test_temp_ar_0044_canonical_store_is_not_unstructured_file_archive() -> None:
    """TEMP-AR-0044: structured canonical store, not filesystem archive."""
    source = inspect.getsource(EventStoreClass)
    assert "open(" not in source
    assert "Path(" not in source
    store = TemporalCanonicalEventStore()
    assert hasattr(store, "_events")
    assert isinstance(store._events, list)


def test_temp_ar_0045_canonical_ingestion_path_modules_present() -> None:
    """TEMP-AR-0045: Raw → Normalized → Entity/Event canonical path."""
    from blackdark.temporal import normalization, production_spine

    assert callable(normalize_ingestion_to_canonical_event)
    assert callable(production_spine.run_production_temporal_spine)
    payload = _ingestion_payload("2026-02-01T02:00:00Z", "2026-02-01T01:00:00Z", suffix="path")
    event = normalize_ingestion_to_canonical_event(payload, strict=True)
    assert event.entity_key == "P1-path"
    assert event.event_type == "market_tick"


def test_temp_ar_0049_event_id_deduplication_fail_closed() -> None:
    """TEMP-AR-0049: duplicate event_id rejected at canonical store boundary."""
    from tests.test_temporal_p1_1_canonical_event_store import _event

    store = TemporalCanonicalEventStore()
    store.append_event(_event("evt-dup"))
    with pytest.raises(TemporalEventStoreError, match="already exists"):
        store.append_event(_event("evt-dup"))


def test_temp_ar_0054_retention_policy_reference_and_descriptor() -> None:
    """TEMP-AR-0054: retention policy metadata and lifecycle descriptor."""
    provenance = ProvenanceMetadata(
        source="binance",
        retention_policy_reference="retain-365d",
    )
    assert provenance.retention_policy_reference == "retain-365d"
    tier = classify_storage_tier(access_frequency="recent")
    descriptor = build_retention_descriptor(tier, rights_metadata={"retention_rights": "retain-365d"})
    meta = descriptor.to_metadata()
    assert meta["lifecycle_policies"] is True
    assert meta["rights_aware_retention"] is True


def test_temp_ar_0056_raw_not_discarded_for_low_learning_priority() -> None:
    """TEMP-AR-0056: retention descriptor forbids low-priority raw deletion."""
    descriptor = build_retention_descriptor(StorageTier.COLD)
    assert descriptor.delete_raw_for_low_learning_value is False


def test_temp_ar_0072_replay_evidence_class_not_live_forward_proof() -> None:
    """TEMP-AR-0072: replay evidence is historical evaluation only."""
    from tests.test_temporal_p1_1_canonical_event_store import T_EARLY, _event

    store = TemporalCanonicalEventStore()
    store.append_event(_event("evt-r", available_at=T_EARLY, revised_at=T_EARLY))
    result = run_deterministic_mass_replay(
        ReplayRequest(
            event_source=store,
            start_time=T_EARLY,
            end_time=T_EARLY,
            replay_clock_or_schedule=(T_EARLY,),
            strict_mode=True,
            replay_parameters={"model_version": "m1"},
            dataset_or_source_version_context={"dataset_version": "ds-1"},
        )
    )
    assert result.evidence_class == REPLAY_EVIDENCE_CLASS
    assert result.evidence_class not in FORBIDDEN_EVIDENCE_CLASSES
    assert result.evidence_class != "VERIFIED_PRODUCTION"


@pytest.mark.asyncio
@pytest.mark.skipif(not _postgres_reachable(), reason="Postgres test DB unavailable")
async def test_temp_ar_postgres_hydrate_replay_round_trip(monkeypatch, tmp_path) -> None:
    """Postgres-backed event store hydrate + deterministic replay round-trip."""
    from blackdark.data.db import get_session

    await _reset_data_engine(monkeypatch, tmp_path)
    suffix = uuid.uuid4().hex[:8]
    simulated = "2026-03-01T02:00:00Z"
    available = "2026-03-01T01:00:00Z"
    sim_dt = datetime.fromisoformat("2026-03-01T02:00:00+00:00")

    async with get_session() as session:
        result = await run_production_temporal_spine(
            session,
            ProductionSpineRequest(
                ingestion_payload=_ingestion_payload(simulated, available, suffix=suffix),
                simulated_time=sim_dt,
                prediction={"direction": "hold"},
                confidence=0.5,
                abstention_state="abstain",
                subject_identity=f"P1-{suffix}",
                input_identity=f"input-{suffix}",
                idempotency_key=f"p1-replay-{suffix}",
            ),
        )
    assert result.status == "completed"
    assert result.event_id

    replay_stages = [
        stage
        for stage in result.observability.get("stages", [])
        if stage.get("stage") == "replay"
    ]
    assert replay_stages
    assert replay_stages[-1].get("status") == "completed"
    assert replay_stages[-1].get("replay_id")

    async with get_session() as session:
        store = PostgresEventStore(session)
        await store.hydrate()
        assert store.event_count >= 1
        replay = run_deterministic_mass_replay(
            ReplayRequest(
                event_source=store,
                start_time=sim_dt,
                end_time=sim_dt,
                replay_clock_or_schedule=(sim_dt,),
                strict_mode=True,
                replay_parameters={"model_version": "model-v1"},
                dataset_or_source_version_context={"dataset_version": f"ds-p1-{suffix}"},
            )
        )
    assert replay.processed_event_count >= 1
    assert replay.replay_manifest
    assert replay.determinism_fingerprint
    assert replay.evidence_class == REPLAY_EVIDENCE_CLASS
    assert "input_event_identity_set" in replay.replay_manifest


@pytest.mark.asyncio
@pytest.mark.skipif(not _postgres_reachable(), reason="Postgres test DB unavailable")
async def test_temp_ar_0049_spine_idempotency_deduplication(monkeypatch, tmp_path) -> None:
    """TEMP-AR-0049: spine idempotency key deduplicates ingestion."""
    from blackdark.data.db import get_session

    await _reset_data_engine(monkeypatch, tmp_path)
    suffix = uuid.uuid4().hex[:8]
    req = ProductionSpineRequest(
        ingestion_payload=_ingestion_payload("2026-03-02T02:00:00Z", "2026-03-02T01:00:00Z", suffix=suffix),
        simulated_time=datetime.fromisoformat("2026-03-02T02:00:00+00:00"),
        prediction={"direction": "hold"},
        confidence=0.5,
        abstention_state="abstain",
        subject_identity=f"P1-{suffix}",
        input_identity=f"input-{suffix}",
        idempotency_key=f"p1-dedup-{suffix}",
    )
    async with get_session() as session:
        first = await run_production_temporal_spine(session, req)
    async with get_session() as session:
        second = await run_production_temporal_spine(session, req)
    assert first.event_id == second.event_id

    import asyncpg

    raw = await asyncpg.connect(POSTGRES_URL)
    count = await raw.fetchval(
        "SELECT COUNT(*) FROM te_canonical_events WHERE idempotency_key=$1",
        f"p1-dedup-{suffix}",
    )
    await raw.close()
    assert count == 1
