"""Production temporal spine integration/E2E tests (P0-7)."""

from __future__ import annotations

import os
import socket
from datetime import UTC, datetime, timedelta

import pytest

from blackdark.temporal.normalization import build_observation_dict, build_provenance_dict
from blackdark.temporal.pit_contract import PitContractViolation
from blackdark.temporal.production_spine import ProductionSpineRequest, run_production_temporal_spine


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


def _ingestion_payload(simulated: str, available: str) -> dict:
    return {
        "entity_key": "BTCUSDT",
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
        "provenance": build_provenance_dict(
            source="binance",
            source_version="v1",
            dataset_version="ds-1",
            rights_or_provenance={"permitted_purpose": "historical_evaluation"},
        ),
    }


@pytest.mark.asyncio
@pytest.mark.skipif(not _postgres_reachable(), reason="Postgres test DB unavailable")
async def test_production_spine_e2e_persistence_and_restart(monkeypatch, tmp_path) -> None:
    from blackdark.data.db import get_session, init_data_engine

    await _reset_data_engine(monkeypatch, tmp_path)

    simulated = "2026-01-01T02:00:00Z"
    available = "2026-01-01T01:00:00Z"
    async with get_session() as session:
        result = await run_production_temporal_spine(
            session,
            ProductionSpineRequest(
                ingestion_payload=_ingestion_payload(simulated, available),
                simulated_time=datetime.fromisoformat("2026-01-01T02:00:00+00:00"),
                prediction={"direction": "buy"},
                confidence=0.7,
                abstention_state="act",
                subject_identity="BTCUSDT",
                input_identity="input-1",
                idempotency_key="e2e-test-1",
            ),
        )
    assert result.status == "completed"
    assert result.event_id
    assert result.receipt_id
    assert result.evidence_ids

    async with get_session() as session:
        from blackdark.data.temporal_repository import get_canonical_event, get_evidence_record

        event = await get_canonical_event(session, result.event_id)
        assert event is not None
        evidence = await get_evidence_record(session, result.evidence_ids[0])
        assert evidence is not None

    await init_data_engine()
    async with get_session() as session:
        from blackdark.data.temporal_repository import get_canonical_event

        event = await get_canonical_event(session, result.event_id)
        assert event is not None


@pytest.mark.asyncio
@pytest.mark.skipif(not _postgres_reachable(), reason="Postgres test DB unavailable")
async def test_production_spine_rejects_unavailable_at_simulated_time(monkeypatch, tmp_path) -> None:
    from blackdark.data.db import get_session

    await _reset_data_engine(monkeypatch, tmp_path)

    simulated = "2026-01-01T01:00:00Z"
    available = "2026-01-01T02:00:00Z"
    async with get_session() as session:
        result = await run_production_temporal_spine(
            session,
            ProductionSpineRequest(
                ingestion_payload=_ingestion_payload(simulated, available),
                simulated_time=datetime.fromisoformat("2026-01-01T01:00:00+00:00"),
                prediction={"direction": "buy"},
                confidence=0.7,
                abstention_state="act",
                subject_identity="BTCUSDT",
                input_identity="input-1",
            ),
        )
    assert result.status == "failed"
    assert result.error_code in {"PIT_RECONSTRUCTION_EMPTY", "TEMPORAL_LEAKAGE_REJECTED"}


@pytest.mark.asyncio
@pytest.mark.skipif(not _postgres_reachable(), reason="Postgres test DB unavailable")
async def test_production_spine_idempotent_ingestion(monkeypatch, tmp_path) -> None:
    from blackdark.data.db import get_session

    await _reset_data_engine(monkeypatch, tmp_path)

    req = ProductionSpineRequest(
        ingestion_payload=_ingestion_payload("2026-01-01T02:00:00Z", "2026-01-01T01:00:00Z"),
        simulated_time=datetime.fromisoformat("2026-01-01T02:00:00+00:00"),
        prediction={"direction": "buy"},
        confidence=0.7,
        abstention_state="act",
        subject_identity="BTCUSDT",
        input_identity="input-1",
        idempotency_key="idempotent-key-1",
    )
    async with get_session() as session:
        first = await run_production_temporal_spine(session, req)
    async with get_session() as session:
        second = await run_production_temporal_spine(session, req)
    assert first.status == "completed"
    assert second.status == "completed"
    assert first.event_id == second.event_id


def test_ingestion_payload_missing_provenance_fail_closed() -> None:
    payload = {
        "entity_key": "BTCUSDT",
        "event_type": "market_tick",
        "observation": build_observation_dict(
            event_time="2026-01-01T02:00:00Z",
            observed_time="2026-01-01T02:00:00Z",
            available_at="2026-01-01T01:00:00Z",
            ingested_at="2026-01-01T01:00:00Z",
            effective_at="2026-01-01T02:00:00Z",
            revised_at="2026-01-01T01:00:00Z",
        ),
        "provenance": {"source": "binance"},
    }
    with pytest.raises(PitContractViolation):
        from blackdark.temporal.normalization import normalize_ingestion_to_canonical_event

        normalize_ingestion_to_canonical_event(payload, strict=True)
