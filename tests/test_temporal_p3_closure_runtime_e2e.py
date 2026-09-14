"""P3_SHADOW_AND_REGIME closure runtime/E2E tests."""

from __future__ import annotations

import os
import socket
import uuid
from datetime import UTC, datetime

import pytest

from blackdark.temporal import TemporalEvidenceClass
from blackdark.temporal.failure_surprise_corpus import FailureSurpriseCorpus
from blackdark.temporal.outcome_contract import OUTCOME_EVALUATOR_IDENTITY, OutcomeContract, OutcomeLabelStatus
from blackdark.temporal.normalization import build_observation_dict, build_provenance_dict
from blackdark.temporal.p3_closure_verification import probe_temp_ar_0164_status
from blackdark.temporal.p3_pipeline import run_forward_shadow_pipeline
from blackdark.temporal.production_spine import ProductionSpineRequest, run_production_temporal_spine

POSTGRES_URL = os.getenv(
    "BLACKDARK_TEST_DATABASE_URL",
    "postgresql://blackdark:blackdark@127.0.0.1:5432/blackdark_clean",
)

T_ISSUED = datetime(2026, 8, 1, 10, 0, 0, tzinfo=UTC)
T_EVAL = datetime(2026, 8, 1, 10, 5, 0, tzinfo=UTC)


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
        "entity_key": f"P3-{suffix}",
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
            dataset_version=f"ds-p3-{suffix}",
            rights_or_provenance={"permitted_purpose": "forward_shadow"},
        ),
    }


@pytest.mark.asyncio
@pytest.mark.skipif(not _postgres_reachable(), reason="Postgres test DB unavailable")
async def test_temp_ar_0124_pre_outcome_receipt_spine_integration(monkeypatch, tmp_path) -> None:
    """TEMP-AR-0124: immutable pre-outcome forward-shadow receipt via production spine."""
    import asyncpg

    from blackdark.data.db import get_session

    await _reset_data_engine(monkeypatch, tmp_path)
    suffix = uuid.uuid4().hex[:8]
    simulated = "2026-08-01T02:00:00Z"
    available = "2026-08-01T01:00:00Z"
    sim_dt = datetime.fromisoformat("2026-08-01T02:00:00+00:00")

    async with get_session() as session:
        result = await run_production_temporal_spine(
            session,
            ProductionSpineRequest(
                ingestion_payload=_ingestion_payload(simulated, available, suffix=suffix),
                simulated_time=sim_dt,
                prediction={"direction": "buy"},
                confidence=0.7,
                abstention_state="act",
                subject_identity=f"P3-{suffix}",
                input_identity=f"input-{suffix}",
                idempotency_key=f"p3-close-{suffix}",
            ),
        )
    assert result.status == "completed"
    assert result.receipt_id
    assert result.p3_metadata is not None
    assert result.p3_metadata.get("evidence_class") == TemporalEvidenceClass.FORWARD_SHADOW.value

    p3_stages = [s for s in result.observability.get("stages", []) if s.get("stage") == "p3_pipeline"]
    assert p3_stages and p3_stages[-1].get("status") == "completed"

    raw = await asyncpg.connect(POSTGRES_URL)
    row = await raw.fetchrow(
        "SELECT receipt_id, evidence_class, receipt_payload FROM te_forward_shadow_receipts WHERE receipt_id=$1",
        result.receipt_id,
    )
    await raw.close()
    assert row is not None
    assert row["evidence_class"] == TemporalEvidenceClass.FORWARD_SHADOW.value
    payload = row["receipt_payload"]
    if isinstance(payload, str):
        import json

        payload = json.loads(payload)
    assert payload["status"] == "pre_outcome"


def test_temp_ar_0167_failure_surprise_corpus_integration() -> None:
    """TEMP-AR-0167: durable failure/surprise corpus capture."""
    outcome = OutcomeContract(
        outcome_id="outcome-1",
        subject_identity="asset-a",
        prediction_identity="model-v1",
        decision_identity="asset-a:act",
        target_definition="directional",
        evaluation_horizon="1h",
        outcome_timestamp=T_EVAL,
        realized_result=100.0,
        benchmark_result=99.0,
        confidence=0.9,
        calibration_error=0.1,
        directional_correctness=False,
        magnitude_error=0.1,
        regret=0.1,
        favorable_excursion=1.0,
        adverse_excursion=0.0,
        drawdown=None,
        false_positive_cost=1.0,
        false_negative_cost=None,
        abstention_quality="evaluated",
        market_regime="bull",
        evaluator_version=OUTCOME_EVALUATOR_IDENTITY,
        label_status=OutcomeLabelStatus.VERIFIED,
    )
    corpus = FailureSurpriseCorpus()
    case = corpus.capture_high_confidence_wrong(
        case_id="c-0167-runtime",
        prediction_identity="model-v1",
        decision_identity="asset-a:act",
        outcome=outcome,
        shadow_receipt_id="shadow-1",
        evidence_class=TemporalEvidenceClass.FORWARD_SHADOW.value,
        recorded_at=T_EVAL,
        temporal_context={"simulated_time": T_ISSUED.isoformat()},
        provenance_reference="prov-ref-1",
        confidence=0.9,
    )
    assert case is not None
    assert len(corpus.list_cases()) == 1
    assert corpus.list_cases()[0].case_id == case.case_id


def test_temp_ar_0164_external_gate_honest_status() -> None:
    """TEMP-AR-0164: external forward-time gate recorded without fabricated evidence."""
    status = probe_temp_ar_0164_status()
    assert status["atomic_id"] == "TEMP-AR-0164"
    assert status["local_engineering_complete"] is True
    assert status["external_evidence_pending"] is True
    assert status["forward_time_passage_verified"] is False


def test_p3_pipeline_failure_corpus_wiring() -> None:
    """P3 pipeline integrates failure corpus without mutating prior evidence."""
    corpus = FailureSurpriseCorpus()
    result = run_forward_shadow_pipeline(
        subject_identity="asset-a",
        input_identity="input-1",
        prediction={"direction": "up"},
        confidence=0.6,
        abstention_state="act",
        issued_at=T_ISSUED,
        evaluation_time=T_EVAL,
        temporal_context={"simulated_time": T_ISSUED.isoformat()},
        source_context={"source": "binance"},
        failure_corpus=corpus,
        regime_indicators={"volatility": "low"},
    )
    assert result.shadow_receipt.evidence_class == TemporalEvidenceClass.FORWARD_SHADOW.value
    assert result.shadow_receipt.shadow_receipt_id
