"""Runtime DB failure / rollback verification for production temporal spine."""

from __future__ import annotations

import os
import socket
import uuid

import pytest

from blackdark.temporal.normalization import build_observation_dict, build_provenance_dict
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


def _payload(sim: str, avail: str, *, suffix: str) -> dict:
    return {
        "entity_key": f"ROLLBACK-{suffix}",
        "event_type": "market_tick",
        "payload": {"price": "100.0", "rollback_suffix": suffix},
        "observation": build_observation_dict(
            event_time=sim,
            observed_time=sim,
            available_at=avail,
            ingested_at=avail,
            effective_at=sim,
            revised_at=avail,
        ),
        "provenance": build_provenance_dict(
            source="binance",
            source_version="v1",
            dataset_version=f"ds-rollback-{suffix}",
            rights_or_provenance={"permitted_purpose": "historical_evaluation"},
        ),
    }


@pytest.mark.asyncio
@pytest.mark.skipif(not _postgres_reachable(), reason="Postgres unavailable")
async def test_spine_rollback_prevents_orphan_rows_on_mid_pipeline_failure(monkeypatch) -> None:
    import asyncpg

    import config
    import blackdark.data.db as db_module
    from blackdark.data.db import get_session

    monkeypatch.setattr(config, "DATABASE_URL", POSTGRES_URL)
    db_module._engine = None
    db_module._session_factory = None
    db_module._schema_ready = False
    db_module._bootstrapped = False

    before_events = before_evidence = before_receipts = 0
    raw = await asyncpg.connect(POSTGRES_URL)
    before_events = await raw.fetchval("SELECT COUNT(*) FROM te_canonical_events")
    before_evidence = await raw.fetchval("SELECT COUNT(*) FROM te_evidence_records")
    before_receipts = await raw.fetchval("SELECT COUNT(*) FROM te_forward_shadow_receipts")
    await raw.close()

    import blackdark.temporal.production_spine as production_spine

    original_persist = production_spine.PostgresForwardShadowLedger.persist_receipt

    async def failing_persist(self, receipt, *, idempotency_key=None):
        raise RuntimeError("injected_receipt_persist_failure")

    production_spine.PostgresForwardShadowLedger.persist_receipt = failing_persist

    run_suffix = uuid.uuid4().hex[:12]
    idempotency_key = f"rollback-runtime-{run_suffix}"
    offset = int(run_suffix[:6], 16) % 3600
    sim = f"2026-02-01T02:{offset // 60:02d}:{offset % 60:02d}Z"
    avail = f"2026-02-01T01:{offset // 60:02d}:{offset % 60:02d}Z"
    simulated_time = __import__("datetime").datetime.fromisoformat(sim.replace("Z", "+00:00"))

    with pytest.raises(RuntimeError, match="injected_receipt_persist_failure"):
        async with get_session() as session:
            await run_production_temporal_spine(
                session,
                ProductionSpineRequest(
                    ingestion_payload=_payload(sim, avail, suffix=run_suffix),
                    simulated_time=simulated_time,
                    prediction={"direction": "buy"},
                    confidence=0.7,
                    abstention_state="act",
                    subject_identity="BTCUSDT",
                    input_identity="rollback-test-1",
                    idempotency_key=idempotency_key,
                ),
            )

    raw = await asyncpg.connect(POSTGRES_URL)
    after_events = await raw.fetchval("SELECT COUNT(*) FROM te_canonical_events")
    after_evidence = await raw.fetchval("SELECT COUNT(*) FROM te_evidence_records")
    after_receipts = await raw.fetchval("SELECT COUNT(*) FROM te_forward_shadow_receipts")
    orphan_event = await raw.fetchval(
        "SELECT COUNT(*) FROM te_canonical_events WHERE idempotency_key=$1",
        idempotency_key,
    )
    await raw.close()

    assert after_events == before_events
    assert after_evidence == before_evidence
    assert after_receipts == before_receipts
    assert orphan_event == 0

    production_spine.PostgresForwardShadowLedger.persist_receipt = original_persist

    async with get_session() as session:
        result = await run_production_temporal_spine(
            session,
            ProductionSpineRequest(
                ingestion_payload=_payload(sim, avail, suffix=run_suffix),
                simulated_time=simulated_time,
                prediction={"direction": "buy"},
                confidence=0.7,
                abstention_state="act",
                subject_identity="BTCUSDT",
                input_identity="rollback-test-1",
                idempotency_key=idempotency_key,
            ),
        )
    assert result.status == "completed"
    assert result.event_id
