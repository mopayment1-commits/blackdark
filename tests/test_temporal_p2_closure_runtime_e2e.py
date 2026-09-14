"""P2_OUTCOME_AND_EVIDENCE closure runtime/E2E tests."""

from __future__ import annotations

import json
import os
import socket
import time
import uuid
from datetime import UTC, datetime

import pytest

from blackdark.temporal import (
    REPLAY_EVIDENCE_CLASS,
    ReplayRequest,
    TemporalCanonicalEventStore,
    assess_source_quality,
    build_retention_descriptor,
    classify_storage_tier,
    execute_historical_decision_path,
    run_deterministic_mass_replay,
    run_p2_outcome_evidence_pipeline,
)
from blackdark.temporal.normalization import build_observation_dict, build_provenance_dict
from blackdark.temporal.outcome_factory import OUTCOME_EVALUATOR_IDENTITY, generate_outcomes_from_decision_step
from blackdark.temporal.production_spine import ProductionSpineRequest, run_production_temporal_spine
from blackdark.temporal.retention_policy import StorageTier

POSTGRES_URL = os.getenv(
    "BLACKDARK_TEST_DATABASE_URL",
    "postgresql://blackdark:blackdark@127.0.0.1:5432/blackdark_clean",
)

T_START = datetime(2026, 6, 1, 9, 0, 0, tzinfo=UTC)
T_SCHEDULE = datetime(2026, 6, 1, 10, 0, 0, tzinfo=UTC)
T_END = datetime(2026, 6, 1, 14, 0, 0, tzinfo=UTC)
T_EARLY = datetime(2026, 6, 1, 9, 30, 0, tzinfo=UTC)


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


def _ingestion_payload(simulated: str, available: str, *, suffix: str, regime: str = "normal") -> dict:
    return {
        "entity_key": f"P2-{suffix}",
        "event_type": "market_tick",
        "payload": {"price": "120.0", "regime": regime},
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
                dataset_version=f"ds-p2-{suffix}",
                rights_or_provenance={"permitted_purpose": "historical_evaluation"},
            ),
            "retention_policy_reference": "retain-365d",
        },
    }


def _local_p2_pipeline(regime: str = "normal"):
    from blackdark.temporal import CanonicalTemporalEvent, ProvenanceMetadata, TemporalObservation
    from blackdark.temporal import TemporalSemanticField, TemporalTimestamp

    def _ts(field, value):
        return TemporalTimestamp.direct(field, value)

    obs = TemporalObservation.create(
        event_time=_ts(TemporalSemanticField.EVENT_TIME, T_EARLY),
        observed_time=_ts(TemporalSemanticField.OBSERVED_TIME, T_EARLY),
        available_at=_ts(TemporalSemanticField.AVAILABLE_AT, T_EARLY),
        ingested_at=_ts(TemporalSemanticField.INGESTED_AT, T_EARLY),
        effective_at=_ts(TemporalSemanticField.EFFECTIVE_AT, T_EARLY),
        revised_at=_ts(TemporalSemanticField.REVISED_AT, T_EARLY),
    )
    event = CanonicalTemporalEvent(
        event_id="evt-p2",
        entity_key="asset-a",
        event_type="market.tick",
        payload={"price": "120", "regime": regime},
        observation=obs,
        provenance=ProvenanceMetadata(source="binance", source_version="v1", dataset_version="ds-1"),
        record_version="1",
    )
    store = TemporalCanonicalEventStore([event])
    mass = run_deterministic_mass_replay(
        ReplayRequest(
            event_source=store,
            start_time=T_START,
            end_time=T_END,
            replay_clock_or_schedule=[T_SCHEDULE],
            strict_mode=True,
            replay_parameters={"threshold": 0.5, "regime": regime, "target_definition": "directional"},
        )
    )
    decision = execute_historical_decision_path(
        event_source=store,
        mass_replay=mass,
        parameters={"threshold": 0.5, "regime": regime},
        model_identity="model-v1",
    )
    p2 = run_p2_outcome_evidence_pipeline(
        event_source=store,
        mass_replay=mass,
        decision_path=decision,
    )
    return store, mass, decision, p2


@pytest.mark.asyncio
@pytest.mark.skipif(not _postgres_reachable(), reason="Postgres test DB unavailable")
async def test_p2_spine_postgres_evidence_persistence(monkeypatch, tmp_path) -> None:
    """Production spine P2 pipeline persists evidence to te_evidence_records."""
    from blackdark.data.db import get_session
    from blackdark.data.temporal_repository import get_evidence_record

    await _reset_data_engine(monkeypatch, tmp_path)
    suffix = uuid.uuid4().hex[:8]
    simulated = "2026-06-01T02:00:00Z"
    available = "2026-06-01T01:00:00Z"
    sim_dt = datetime.fromisoformat("2026-06-01T02:00:00+00:00")

    async with get_session() as session:
        result = await run_production_temporal_spine(
            session,
            ProductionSpineRequest(
                ingestion_payload=_ingestion_payload(simulated, available, suffix=suffix, regime="bull"),
                simulated_time=sim_dt,
                prediction={"direction": "buy"},
                confidence=0.7,
                abstention_state="act",
                subject_identity=f"P2-{suffix}",
                input_identity=f"input-{suffix}",
                idempotency_key=f"p2-close-{suffix}",
            ),
        )
    assert result.status == "completed"
    assert result.p2_metadata is not None
    assert result.evidence_ids

    p2_stages = [s for s in result.observability.get("stages", []) if s.get("stage") == "p2_pipeline"]
    assert p2_stages and p2_stages[-1].get("status") == "completed"

    async with get_session() as session:
        evidence = await get_evidence_record(session, result.evidence_ids[0])
    assert evidence is not None
    assert evidence["evidence_class"] == "HISTORICAL_REPLAY"


def test_temp_ar_0103_calibration_error_empirical() -> None:
    """TEMP-AR-0103: calibration_error recorded when applicable."""
    _, _, decision, _ = _local_p2_pipeline()
    outcome = decision.steps[0].stages["outcome"]["outcomes"][0]
    assert "calibration_error" in outcome
    assert outcome["calibration_error"] is not None


def test_temp_ar_0113_market_regime_empirical() -> None:
    """TEMP-AR-0113: market_regime recorded when applicable."""
    _, _, decision, _ = _local_p2_pipeline(regime="volatile")
    outcome = decision.steps[0].stages["outcome"]["outcomes"][0]
    assert outcome["market_regime"] == "volatile"


def test_temp_ar_0115_independent_evaluator_integration() -> None:
    """TEMP-AR-0115: outcome evaluator independent from predictor."""
    store, mass, decision, p2 = _local_p2_pipeline()
    step = mass.replay_outputs[0]
    factory = generate_outcomes_from_decision_step(
        step=step,
        event_source=store,
        stages=decision.steps[0].stages,
        parameters={"regime": "normal"},
        model_identity="model-v1",
    )
    assert factory.evaluator_identity == OUTCOME_EVALUATOR_IDENTITY
    assert factory.evaluator_identity != "model-v1"
    assert p2.predictor_self_validation is False


def test_temp_ar_0145_evidence_version_scoped_integration() -> None:
    """TEMP-AR-0145: evidence versions preserved through P2 pipeline."""
    _, _, _, p2 = _local_p2_pipeline()
    record = p2.evidence_records[0]
    assert record.versions
    assert record.versions.get("evaluator_version") == OUTCOME_EVALUATOR_IDENTITY


def test_temp_ar_0146_evidence_methodology_preserved_integration() -> None:
    """TEMP-AR-0146: evidence methodology preserved."""
    _, _, _, p2 = _local_p2_pipeline()
    assert p2.evidence_records[0].methodology


def test_temp_ar_0147_evidence_timestamps_preserved_integration() -> None:
    """TEMP-AR-0147: evidence timestamps preserved."""
    _, _, _, p2 = _local_p2_pipeline()
    assert p2.evidence_records[0].timestamps


def test_temp_ar_0148_evaluator_identity_preserved_integration() -> None:
    """TEMP-AR-0148: evaluator_identity on evidence record."""
    _, _, _, p2 = _local_p2_pipeline()
    assert p2.evidence_records[0].evaluator_identity == OUTCOME_EVALUATOR_IDENTITY


def test_temp_ar_0150_evidence_limitations_preserved_integration() -> None:
    """TEMP-AR-0150: evidence limitations field present."""
    _, _, _, p2 = _local_p2_pipeline()
    assert isinstance(p2.evidence_records[0].limitations, tuple)


def test_temp_ar_0193_warm_tier_replay_retrieval() -> None:
    """TEMP-AR-0193: warm tier for frequent replay access."""
    tier = classify_storage_tier(access_frequency="frequent_replay")
    assert tier == StorageTier.WARM
    descriptor = build_retention_descriptor(tier)
    assert descriptor.tier == StorageTier.WARM
    _, mass, _, _ = _local_p2_pipeline()
    assert mass.evidence_class == REPLAY_EVIDENCE_CLASS


def test_temp_ar_0196_compression_performance() -> None:
    """TEMP-AR-0196: compression enabled for non-hot tiers within bounded time."""
    started = time.perf_counter()
    for _ in range(100):
        descriptor = build_retention_descriptor(StorageTier.WARM)
        assert descriptor.compression is True
    elapsed_ms = (time.perf_counter() - started) * 1000
    assert elapsed_ms < 500


def test_temp_ar_0202_reproducible_retrieval_integration() -> None:
    """TEMP-AR-0202: reproducible retrieval via deterministic P2 runs."""
    first = _local_p2_pipeline()
    second = _local_p2_pipeline()
    assert first[3].reproducibility.run_id == second[3].reproducibility.run_id


def test_temp_ar_0303_source_quality_replay_fidelity() -> None:
    """TEMP-AR-0303: source quality influences replay fidelity assessment."""
    store, mass, _, _ = _local_p2_pipeline()
    quality = assess_source_quality(store.list_events(), evaluation_time=T_SCHEDULE)
    assert quality.influences["replay_fidelity"] is True
    assert mass.success is True


def test_temp_ar_0336_material_results_reproducible_integration() -> None:
    """TEMP-AR-0336: material P2 results reproducible across runs."""
    _, _, _, p2a = _local_p2_pipeline()
    _, _, _, p2b = _local_p2_pipeline()
    assert p2a.reproducibility.full_reproducibility_possible is True
    assert p2a.reproducibility.run_id == p2b.reproducibility.run_id
    assert p2a.evidence_records[0].evidence_id == p2b.evidence_records[0].evidence_id


def test_temp_ar_0337_reproducibility_limitations_marked_integration() -> None:
    """TEMP-AR-0337: reproducibility limitations explicitly tracked."""
    _, _, _, p2 = _local_p2_pipeline()
    meta = p2.reproducibility.to_metadata()
    assert "reproducibility_limitations" in meta
    assert isinstance(meta["reproducibility_limitations"], list)


@pytest.mark.asyncio
@pytest.mark.skipif(not _postgres_reachable(), reason="Postgres test DB unavailable")
async def test_temp_ar_0379_reproducibility_manifest_integration(monkeypatch, tmp_path) -> None:
    """TEMP-AR-0379: reproducibility manifest established via spine P2 path."""
    from blackdark.data.db import get_session

    await _reset_data_engine(monkeypatch, tmp_path)
    suffix = uuid.uuid4().hex[:8]
    async with get_session() as session:
        result = await run_production_temporal_spine(
            session,
            ProductionSpineRequest(
                ingestion_payload=_ingestion_payload("2026-06-02T02:00:00Z", "2026-06-02T01:00:00Z", suffix=suffix),
                simulated_time=datetime.fromisoformat("2026-06-02T02:00:00+00:00"),
                prediction={"direction": "hold"},
                confidence=0.5,
                abstention_state="abstain",
                subject_identity=f"P2-{suffix}",
                input_identity=f"input-{suffix}",
                idempotency_key=f"p2-manifest-{suffix}",
            ),
        )
    assert result.p2_metadata is not None
    repro = result.p2_metadata.get("reproducibility", {})
    assert repro.get("run_id")
    assert repro.get("code_sha")
    assert repro.get("dataset_snapshot")
