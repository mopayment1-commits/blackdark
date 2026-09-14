"""P5_USER_EVIDENCE_EXPERIENCE closure runtime/E2E tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from blackdark.temporal.evidence_class import TemporalEvidenceClass
from blackdark.temporal.evidence_provenance import EvidenceProvenanceLedger
from blackdark.temporal import (
    CanonicalTemporalEvent,
    ProvenanceMetadata,
    TemporalCanonicalEventStore,
    TemporalObservation,
    TemporalSemanticField,
    TemporalTimestamp,
)
from blackdark.temporal.market_time_machine import (
    build_user_facing_experience,
    run_market_time_machine_replay,
)
from blackdark.temporal.outcome_contract import OUTCOME_EVALUATOR_IDENTITY
from blackdark.temporal.p5_closure_verification import probe_temp_ar_0261_status
from blackdark.temporal.public_evidence import build_public_disclosure_from_ledger
from blackdark.temporal.user_behavioral_learning import (
    BehavioralLearningPurpose,
    BehavioralConsentRecord,
    build_behavioral_learning_state,
    record_behavioral_signal,
)

T_START = datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC)
T_NOW = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)


def _event(event_id: str) -> CanonicalTemporalEvent:
    t = datetime(2026, 1, 1, 10, 0, 0, tzinfo=UTC)

    def _ts(field: TemporalSemanticField, value: datetime) -> TemporalTimestamp:
        return TemporalTimestamp.direct(field, value)

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


def test_temp_ar_0261_external_gate_probe() -> None:
    status = probe_temp_ar_0261_status()
    assert status["local_engineering_complete"] is True
    assert status["historical_replay_never_implies_live"] is True
    assert status["external_evidence_pending"] is True
    assert status["forward_issuance_verified"] is False


def test_temp_ar_0259_user_facing_experience_runtime_integration() -> None:
    store = TemporalCanonicalEventStore([_event("p5-evt-1")])
    replay = run_market_time_machine_replay(
        event_source=store,
        selected_timestamp=T_START + timedelta(hours=2),
        start_time=T_START,
        end_time=T_START + timedelta(hours=4),
        entity_key="asset-a",
    )
    exp = build_user_facing_experience(
        experience_id="p5-runtime-1",
        selected_timestamp=T_START + timedelta(hours=2),
        replay=replay,
        entity_key="asset-a",
    )
    assert exp.implies_live_issuance is False
    assert exp.mandatory_disclosure == "Historical Replay"
    assert exp.accessibility["wcag_version"] == "2.2"


def test_temp_ar_0263_public_disclosure_runtime_integration() -> None:
    ledger = EvidenceProvenanceLedger()
    ledger.record_evidence(
        evidence_class=TemporalEvidenceClass.HISTORICAL_REPLAY.value,
        producer="runtime",
        source_provenance={"provenance_reference": "prov-runtime"},
        temporal_context={"available_at": T_NOW.isoformat()},
        versions={"model_version": "m-runtime"},
        lineage=("line-runtime",),
        quality_state={"label_confidence": 0.8},
        limitations=("pending unresolved excluded",),
        methodology="deterministic replay",
        timestamps={"recorded_at": T_NOW.isoformat()},
        evaluator_identity=OUTCOME_EVALUATOR_IDENTITY,
        payload={},
    )
    disclosure = build_public_disclosure_from_ledger(
        claim_id="runtime-claim",
        ledger=ledger,
        regime_distribution={"bull": 0.5, "bear": 0.5},
        asset_universe=("BTC",),
        evaluation_horizon="1h",
        maturity_sufficient=True,
        freshness_timestamp=T_NOW,
    )
    meta = disclosure.to_metadata()
    assert meta["evidence_class"] == TemporalEvidenceClass.HISTORICAL_REPLAY.value
    assert meta["freshness_timestamp"]


def test_temp_ar_0352_behavioral_learning_runtime_integration() -> None:
    consent = BehavioralConsentRecord(
        user_key="runtime-user",
        purpose=BehavioralLearningPurpose.DISCIPLINE_COACHING,
        legal_basis="explicit_consent",
        consented_at=T_NOW,
        minimized_fields=("action_type",),
    )
    signal = record_behavioral_signal(
        user_key="runtime-user",
        action_type="follow",
        asset="ETH",
        followed_system=False,
        consent=consent,
    )
    state = build_behavioral_learning_state(
        user_key="runtime-user",
        purpose=BehavioralLearningPurpose.DISCIPLINE_COACHING,
        signals=(signal,),
        consent=consent,
    )
    assert state.eligible_for_adaptation is True
    assert state.separated_from_objective_outcomes is True
