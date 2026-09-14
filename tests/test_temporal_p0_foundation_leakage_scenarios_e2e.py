"""Runtime/E2E coverage for TEMP-PR-0016 leakage scenarios (TEMP-AR-0035..0042)."""

from __future__ import annotations

import os
import socket
import uuid
from datetime import UTC, datetime

import pytest

from blackdark.temporal.firewall import LeakageClass, TemporalProcessingContext, evaluate_temporal_leakage_firewall
from blackdark.temporal.normalization import build_observation_dict, build_provenance_dict
from blackdark.temporal.production_spine import ProductionSpineRequest, run_production_temporal_spine
from blackdark.temporal.reconstruction import TemporalRecord
from blackdark.temporal.truth import TemporalObservation, TemporalSemanticField, TemporalTimestamp


POSTGRES_URL = os.getenv(
    "BLACKDARK_TEST_DATABASE_URL",
    "postgresql://blackdark:blackdark@127.0.0.1:5432/blackdark_clean",
)

SIM = datetime(2026, 3, 1, 12, 0, 0, tzinfo=UTC)
EARLY = datetime(2026, 3, 1, 10, 0, 0, tzinfo=UTC)
LATE = datetime(2026, 3, 1, 14, 0, 0, tzinfo=UTC)
FUTURE_REV = datetime(2026, 3, 1, 15, 0, 0, tzinfo=UTC)

FAIL_CLOSED_CODES = frozenset(
    {
        "PIT_RECONSTRUCTION_EMPTY",
        "TEMPORAL_LEAKAGE_REJECTED",
        "INGESTION_PIT_CONTRACT_INCOMPLETE",
    }
)


def _postgres_reachable() -> bool:
    try:
        with socket.create_connection(("127.0.0.1", 5432), timeout=1.5):
            return True
    except OSError:
        return False


def _iso(dt: datetime) -> str:
    return dt.astimezone(UTC).isoformat().replace("+00:00", "Z")


async def _prepare_engine(monkeypatch) -> None:
    import config
    import blackdark.data.db as db_module
    from blackdark.data.db import init_data_engine

    monkeypatch.setattr(config, "DATABASE_URL", POSTGRES_URL)
    os.environ["DATABASE_URL"] = POSTGRES_URL
    db_module._engine = None
    db_module._session_factory = None
    db_module._schema_ready = False
    db_module._bootstrapped = False
    await init_data_engine()


def _payload(
    *,
    event_time: datetime,
    available_at: datetime,
    revised_at: datetime | None = None,
    effective_at: datetime | None = None,
    suffix: str,
) -> dict:
    revised = revised_at or available_at
    effective = effective_at or event_time
    return {
        "entity_key": f"LEAK-{suffix}",
        "event_type": "market_tick",
        "payload": {"scenario": suffix},
        "observation": build_observation_dict(
            event_time=_iso(event_time),
            observed_time=_iso(available_at),
            available_at=_iso(available_at),
            ingested_at=_iso(available_at),
            effective_at=_iso(effective),
            revised_at=_iso(revised),
        ),
        "provenance": build_provenance_dict(
            source="binance",
            source_version="v1",
            dataset_version=f"ds-leak-{suffix}",
            rights_or_provenance={"permitted_purpose": "historical_evaluation"},
        ),
    }


def _ts(field: TemporalSemanticField, value: datetime) -> TemporalTimestamp:
    return TemporalTimestamp.direct(field, value)


def _firewall_record(
    *,
    record_id: str,
    entity_key: str,
    available_at: datetime,
    revised_at: datetime,
    effective_at: datetime | None = None,
    event_time: datetime | None = None,
) -> TemporalRecord:
    effective = effective_at or available_at
    event = event_time or available_at
    observation = TemporalObservation.create(
        event_time=_ts(TemporalSemanticField.EVENT_TIME, event),
        observed_time=_ts(TemporalSemanticField.OBSERVED_TIME, available_at),
        available_at=_ts(TemporalSemanticField.AVAILABLE_AT, available_at),
        ingested_at=_ts(TemporalSemanticField.INGESTED_AT, available_at),
        effective_at=_ts(TemporalSemanticField.EFFECTIVE_AT, effective),
        revised_at=_ts(TemporalSemanticField.REVISED_AT, revised_at),
    )
    return TemporalRecord(
        record_id=record_id,
        entity_key=entity_key,
        observation=observation,
        payload={"scenario": record_id},
        version="1",
    )


async def _run_spine(
    monkeypatch,
    payload: dict,
    simulated_time: datetime,
    *,
    expect_failed: bool = True,
) -> str | None:
    from blackdark.data.db import get_session

    await _prepare_engine(monkeypatch)
    async with get_session() as session:
        result = await run_production_temporal_spine(
            session,
            ProductionSpineRequest(
                ingestion_payload=payload,
                simulated_time=simulated_time,
                prediction={"direction": "hold"},
                confidence=0.5,
                abstention_state="abstain",
                subject_identity=payload["entity_key"],
                input_identity=f"leak-{payload['payload']['scenario']}",
                idempotency_key=f"leak-{uuid.uuid4().hex[:12]}",
            ),
        )
    if expect_failed:
        assert result.status == "failed"
        assert result.error_code in FAIL_CLOSED_CODES
        return result.error_code
    assert result.status == "completed"
    return None


@pytest.mark.asyncio
@pytest.mark.skipif(not _postgres_reachable(), reason="Postgres unavailable")
async def test_temp_ar_0035_delayed_publications_rejected_runtime(monkeypatch) -> None:
    """TEMP-AR-0035: delayed publications — available_at after simulated decision time."""
    code = await _run_spine(
        monkeypatch,
        _payload(event_time=EARLY, available_at=LATE, suffix="0035"),
        SIM,
    )
    assert code in FAIL_CLOSED_CODES


@pytest.mark.asyncio
@pytest.mark.skipif(not _postgres_reachable(), reason="Postgres unavailable")
async def test_temp_ar_0036_revised_macroeconomic_data_rejected_runtime(monkeypatch) -> None:
    """TEMP-AR-0036: revised macroeconomic data — future revision not yet occurred."""
    code = await _run_spine(
        monkeypatch,
        _payload(
            event_time=EARLY,
            available_at=EARLY,
            revised_at=FUTURE_REV,
            suffix="0036",
        ),
        SIM,
    )
    assert code in FAIL_CLOSED_CODES
    record = _firewall_record(
        record_id="r-0036",
        entity_key="macro-0036",
        available_at=EARLY,
        revised_at=FUTURE_REV,
    )
    decision = evaluate_temporal_leakage_firewall(
        [record],
        TemporalProcessingContext(simulated_time=SIM, strict_mode=True),
    )
    assert decision.allowed is False
    assert LeakageClass.FUTURE_REVISION.value in decision.reason_codes


@pytest.mark.asyncio
@pytest.mark.skipif(not _postgres_reachable(), reason="Postgres unavailable")
async def test_temp_ar_0037_late_arriving_market_data_rejected_runtime(monkeypatch) -> None:
    """TEMP-AR-0037: late-arriving market/on-chain data."""
    code = await _run_spine(
        monkeypatch,
        _payload(event_time=EARLY, available_at=LATE, effective_at=EARLY, suffix="0037"),
        SIM,
    )
    assert code in FAIL_CLOSED_CODES


@pytest.mark.asyncio
@pytest.mark.skipif(not _postgres_reachable(), reason="Postgres unavailable")
async def test_temp_ar_0038_corrected_source_values_rejected_runtime(monkeypatch) -> None:
    """TEMP-AR-0038: corrected source values visible only after simulated time."""
    code = await _run_spine(
        monkeypatch,
        _payload(
            event_time=EARLY,
            available_at=EARLY,
            revised_at=FUTURE_REV,
            effective_at=LATE,
            suffix="0038",
        ),
        SIM,
    )
    assert code in FAIL_CLOSED_CODES
    record = _firewall_record(
        record_id="r-0038",
        entity_key="corrected-0038",
        available_at=EARLY,
        revised_at=FUTURE_REV,
        effective_at=LATE,
    )
    decision = evaluate_temporal_leakage_firewall(
        [record],
        TemporalProcessingContext(simulated_time=SIM, strict_mode=True),
    )
    assert decision.allowed is False


@pytest.mark.asyncio
@pytest.mark.skipif(not _postgres_reachable(), reason="Postgres unavailable")
async def test_temp_ar_0039_source_event_timestamp_mismatch_rejected_runtime(monkeypatch) -> None:
    """TEMP-AR-0039: source/event timestamp mismatch — event_time after simulated time."""
    code = await _run_spine(
        monkeypatch,
        _payload(event_time=LATE, available_at=EARLY, suffix="0039"),
        SIM,
    )
    assert code in {"TEMPORAL_LEAKAGE_REJECTED", "PIT_RECONSTRUCTION_EMPTY"}


@pytest.mark.asyncio
@pytest.mark.skipif(not _postgres_reachable(), reason="Postgres unavailable")
async def test_temp_ar_0040_missing_historical_timestamps_fail_closed_runtime(monkeypatch) -> None:
    """TEMP-AR-0040: missing historical timestamps fail closed at normalization."""
    await _prepare_engine(monkeypatch)
    payload = {
        "entity_key": "LEAK-0040",
        "event_type": "market_tick",
        "payload": {"scenario": "0040"},
        "observation": build_observation_dict(
            event_time=_iso(EARLY),
            observed_time=_iso(EARLY),
            available_at=_iso(EARLY),
            ingested_at=_iso(EARLY),
            effective_at=_iso(EARLY),
            revised_at=_iso(EARLY),
        ),
        "provenance": {"source": "binance"},
    }
    from blackdark.data.db import get_session

    async with get_session() as session:
        result = await run_production_temporal_spine(
            session,
            ProductionSpineRequest(
                ingestion_payload=payload,
                simulated_time=SIM,
                prediction={"direction": "hold"},
                confidence=0.5,
                abstention_state="abstain",
                subject_identity="LEAK-0040",
                input_identity="leak-0040",
            ),
        )
    assert result.status == "failed"
    assert result.error_code == "INGESTION_PIT_CONTRACT_INCOMPLETE"


@pytest.mark.asyncio
@pytest.mark.skipif(not _postgres_reachable(), reason="Postgres unavailable")
async def test_temp_ar_0041_unavailable_historical_features_rejected_runtime(monkeypatch) -> None:
    """TEMP-AR-0041: unavailable historical features — PIT reconstruction empty at simulated time."""
    code = await _run_spine(
        monkeypatch,
        _payload(event_time=LATE, available_at=LATE, suffix="0041"),
        SIM,
    )
    assert code in {"PIT_RECONSTRUCTION_EMPTY", "TEMPORAL_LEAKAGE_REJECTED"}


@pytest.mark.asyncio
@pytest.mark.skipif(not _postgres_reachable(), reason="Postgres unavailable")
async def test_temp_ar_0042_historical_source_latency_rejected_runtime(monkeypatch) -> None:
    """TEMP-AR-0042: historical source latency — data only available after simulated time."""
    code = await _run_spine(
        monkeypatch,
        _payload(event_time=EARLY, available_at=LATE, suffix="0042"),
        SIM,
    )
    assert code in FAIL_CLOSED_CODES
