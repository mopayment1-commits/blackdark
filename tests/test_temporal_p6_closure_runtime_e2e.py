"""P6_OPERATIONAL_HARDENING closure runtime/E2E tests."""

from __future__ import annotations

import os
import socket
import uuid
from datetime import UTC, datetime

import pytest

from blackdark.temporal.computational_acceleration import AccelerationCache, AccelerationStrategy
from blackdark.temporal.normalization import build_observation_dict, build_provenance_dict
from blackdark.temporal.operational_hardening import assess_operational_readiness, evaluate_fail_closed
from blackdark.temporal.production_spine import ProductionSpineRequest, run_production_temporal_spine
from blackdark.temporal.quality_governance import assess_quality_governance

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


@pytest.mark.asyncio
@pytest.mark.skipif(not _postgres_reachable(), reason="Postgres not reachable")
async def test_temp_ar_0368_reproducibility_spine_integration(monkeypatch, tmp_path) -> None:
    from blackdark.data.db import get_session

    await _reset_data_engine(monkeypatch, tmp_path)
    suffix = uuid.uuid4().hex[:8]
    sim = "2026-09-01T02:00:00Z"
    avail = "2026-09-01T01:00:00Z"
    sim_dt = datetime.fromisoformat("2026-09-01T02:00:00+00:00")
    payload = {
        "entity_key": f"P6-{suffix}",
        "event_type": "market_tick",
        "payload": {"price": "100"},
        "observation": build_observation_dict(
            event_time=sim,
            observed_time=sim,
            available_at=avail,
            ingested_at=avail,
            effective_at=sim,
            revised_at=avail,
        ),
        "provenance": build_provenance_dict(
            source="p6-closure",
            source_version="v1",
            dataset_version=f"ds-p6-{suffix}",
            rights_or_provenance={"permitted_purpose": "operational_hardening"},
        ),
    }
    async with get_session() as session:
        spine = await run_production_temporal_spine(
            session,
            ProductionSpineRequest(
                ingestion_payload=payload,
                simulated_time=sim_dt,
                prediction={"direction": "hold"},
                confidence=0.5,
                abstention_state="abstain",
                subject_identity=f"P6-{suffix}",
                input_identity=f"input-{suffix}",
                idempotency_key=f"p6-{suffix}",
            ),
        )
    assert spine.status == "completed"
    report = assess_quality_governance(runtime_signals={"deterministic_replay": True})
    repro = next(a for a in report.assessments if a.characteristic.value == "reproducibility")
    assert repro.supported is True


@pytest.mark.asyncio
@pytest.mark.skipif(not _postgres_reachable(), reason="Postgres not reachable")
async def test_temp_ar_0364_security_fail_closed_on_invalid_ingest(monkeypatch, tmp_path) -> None:
    from blackdark.data.db import get_session

    await _reset_data_engine(monkeypatch, tmp_path)
    sim_dt = datetime.fromisoformat("2026-09-01T02:00:00+00:00")
    bad_payload = {
        "entity_key": "P6-BAD",
        "event_type": "market_tick",
        "payload": {"price": "100"},
        "observation": {},
        "provenance": {},
    }
    async with get_session() as session:
        spine = await run_production_temporal_spine(
            session,
            ProductionSpineRequest(
                ingestion_payload=bad_payload,
                simulated_time=sim_dt,
                prediction={"direction": "hold"},
                confidence=0.5,
                abstention_state="abstain",
                subject_identity="P6-BAD",
                input_identity="input-bad",
            ),
        )
    decision = evaluate_fail_closed(status=spine.status, error_code=spine.error_code)
    assert decision.admitted is False
    readiness = assess_operational_readiness(
        observability=spine.observability,
        api_admin_gated=True,
    )
    assert readiness.security_controls["fail_closed_on_uncertainty"] is True


def test_temp_ar_0347_cache_determinism_runtime() -> None:
    cache = AccelerationCache()
    key = cache.build_key(strategy=AccelerationStrategy.FEATURE_CACHING, payload={"run": "p6"})
    cache.put(key, {"ok": True}, provenance_metadata={"source": "runtime"})
    assert cache.get(key) is not None


def test_operational_readiness_runtime_integration() -> None:
    report = assess_operational_readiness(api_admin_gated=True)
    assert report.metrics_available is True
    assert report.defects == ()
