"""P5 Market Time Machine tests — TEMP-AR-0251..0261."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from blackdark.temporal import (
    CanonicalTemporalEvent,
    ProvenanceMetadata,
    ReplayRequest,
    TemporalCanonicalEventStore,
    TemporalObservation,
    TemporalSemanticField,
    TemporalTimestamp,
    run_deterministic_mass_replay,
)
from blackdark.temporal.evidence_class import TemporalEvidenceClass
from blackdark.temporal.market_time_machine import (
    IMPLIED_LIVE_ISSUANCE_PROHIBITED,
    MANDATORY_HISTORICAL_REPLAY_DISCLOSURE,
    InternalModePurpose,
    MarketTimeMachineMode,
    build_internal_experience,
    build_user_facing_experience,
    evaluate_live_issuance_claim,
    run_market_time_machine_replay,
    supported_internal_purposes,
)
from blackdark.temporal.p5_requirement_registry import P5_ATOMIC_REQUIREMENT_IDS

T_START = datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC)


def _ts(field: TemporalSemanticField, value: datetime) -> TemporalTimestamp:
    return TemporalTimestamp.direct(field, value)


def _event(event_id: str) -> CanonicalTemporalEvent:
    t = datetime(2026, 1, 1, 10, 0, 0, tzinfo=UTC)
    obs = TemporalObservation.create(
        event_time=_ts(TemporalSemanticField.EVENT_TIME, t),
        observed_time=_ts(TemporalSemanticField.OBSERVED_TIME, t),
        available_at=_ts(TemporalSemanticField.AVAILABLE_AT, t),
        ingested_at=_ts(TemporalSemanticField.INGESTED_AT, t),
        effective_at=_ts(TemporalSemanticField.EFFECTIVE_AT, t),
        revised_at=_ts(TemporalSemanticField.REVISED_AT, t),
    )
    return CanonicalTemporalEvent(
        event_id=event_id,
        entity_key="asset-a",
        event_type="market.tick",
        payload={"price": "100"},
        observation=obs,
        provenance=ProvenanceMetadata(source="binance", source_version="v1", dataset_version="ds-1"),
        record_version="1",
    )


def _store() -> TemporalCanonicalEventStore:
    return TemporalCanonicalEventStore([_event("evt-1")])


@pytest.mark.parametrize(
    "purpose,atomic_id",
    [
        (InternalModePurpose.QA, "TEMP-AR-0251"),
        (InternalModePurpose.DEBUGGING, "TEMP-AR-0252"),
        (InternalModePurpose.RESEARCH, "TEMP-AR-0253"),
        (InternalModePurpose.MODEL_COMPARISON, "TEMP-AR-0254"),
        (InternalModePurpose.REPLAY, "TEMP-AR-0255"),
        (InternalModePurpose.FAILURE_REPRODUCTION, "TEMP-AR-0256"),
        (InternalModePurpose.EVIDENCE_GENERATION, "TEMP-AR-0257"),
        (InternalModePurpose.ROOT_CAUSE_ANALYSIS, "TEMP-AR-0258"),
    ],
)
def test_internal_mode_purposes(purpose: InternalModePurpose, atomic_id: str) -> None:
    assert atomic_id in P5_ATOMIC_REQUIREMENT_IDS
    store = _store()
    replay = run_market_time_machine_replay(
        event_source=store,
        selected_timestamp=T_START + timedelta(hours=2),
        start_time=T_START,
        end_time=T_START + timedelta(hours=4),
    )
    exp = build_internal_experience(
        experience_id=f"int-{purpose.value}",
        purpose=purpose,
        selected_timestamp=T_START + timedelta(hours=2),
        replay=replay,
    )
    assert exp.mode == MarketTimeMachineMode.INTERNAL
    assert exp.internal_purpose == purpose
    assert exp.mandatory_disclosure == MANDATORY_HISTORICAL_REPLAY_DISCLOSURE


def test_temp_ar_0255_replay_internal_mode() -> None:
    store = _store()
    replay = run_deterministic_mass_replay(
        ReplayRequest(
            event_source=store,
            start_time=T_START,
            end_time=T_START + timedelta(hours=4),
            replay_clock_or_schedule=(T_START + timedelta(hours=2),),
            strict_mode=True,
        )
    )
    assert replay.success is True


def test_temp_ar_0259_user_facing_timestamp_selection() -> None:
    store = _store()
    replay = run_market_time_machine_replay(
        event_source=store,
        selected_timestamp=T_START + timedelta(hours=2),
        start_time=T_START,
        end_time=T_START + timedelta(hours=4),
        entity_key="asset-a",
    )
    exp = build_user_facing_experience(
        experience_id="user-1",
        selected_timestamp=T_START + timedelta(hours=2),
        replay=replay,
        entity_key="asset-a",
    )
    assert exp.mode == MarketTimeMachineMode.USER_FACING
    assert exp.selected_entity_key == "asset-a"
    assert exp.knowable_at_timestamp["selected_timestamp"]


def test_temp_ar_0260_mandatory_disclosure() -> None:
    assert MANDATORY_HISTORICAL_REPLAY_DISCLOSURE == "Historical Replay"
    store = _store()
    replay = run_market_time_machine_replay(
        event_source=store,
        selected_timestamp=T_START + timedelta(hours=2),
        start_time=T_START,
        end_time=T_START + timedelta(hours=4),
    )
    exp = build_user_facing_experience(
        experience_id="disc-1",
        selected_timestamp=T_START + timedelta(hours=2),
        replay=replay,
    )
    assert exp.mandatory_disclosure == "Historical Replay"
    assert exp.accessibility["disclosure_visible"] is True


def test_temp_ar_0261_never_implies_live_issuance_without_forward_evidence() -> None:
    assert IMPLIED_LIVE_ISSUANCE_PROHIBITED is True
    result = evaluate_live_issuance_claim(
        evidence_class=TemporalEvidenceClass.HISTORICAL_REPLAY.value,
        forward_evidence_present=False,
    )
    assert result["implies_live_issuance"] is False
    forward = evaluate_live_issuance_claim(
        evidence_class=TemporalEvidenceClass.FORWARD_SHADOW.value,
        forward_evidence_present=False,
        uses_simulated_time=True,
    )
    assert forward["external_runtime_gate_pending"] is True


def test_supported_internal_purposes_complete() -> None:
    assert len(supported_internal_purposes()) == 8
