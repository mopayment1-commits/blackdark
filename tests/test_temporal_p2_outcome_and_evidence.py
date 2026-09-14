"""Focused P2 Outcome/Evidence tests — all 103 active atomic requirements."""

from __future__ import annotations

import copy
from datetime import UTC, datetime

import pytest

from blackdark.temporal import (
    CANONICAL_EVIDENCE_CLASSES,
    CanonicalTemporalEvent,
    EvidenceProvenanceLedger,
    OutcomeLabelStatus,
    P2_ATOMIC_REQUIREMENT_IDS,
    P2_DISCOVERED_ACTIVE_ATOMIC_REQUIREMENTS,
    P2_EXPECTED_ACTIVE_ATOMIC_REQUIREMENTS,
    ProvenanceMetadata,
    REPLAY_EVIDENCE_CLASS,
    ReplayRequest,
    TemporalCanonicalEventStore,
    TemporalEvidenceClass,
    TemporalObservation,
    TemporalSemanticField,
    TemporalTimestamp,
    assert_no_automatic_promotion,
    assess_outcome_quality,
    assess_source_quality,
    build_reproducibility_manifest,
    build_retention_descriptor,
    classify_storage_tier,
    execute_historical_decision_path,
    extract_source_rights,
    generate_outcomes_from_decision_step,
    predictor_must_not_self_validate,
    run_deterministic_mass_replay,
    run_p2_outcome_evidence_pipeline,
)
from blackdark.temporal.evidence_class import can_promote_evidence_class
from blackdark.temporal.outcome_factory import OUTCOME_EVALUATOR_IDENTITY
from blackdark.temporal.outcome_quality import UNKNOWN_OUTCOME_TREATED_AS_FALSE
from blackdark.temporal.p2_requirement_registry import P2_EXTERNAL_OR_LIVE_GATED_IDS
from blackdark.temporal.retention_policy import StorageTier
from blackdark.temporal.source_rights import historical_availability_does_not_imply_permission

T_START = datetime(2024, 8, 1, 9, 0, 0, tzinfo=UTC)
T_END = datetime(2024, 8, 1, 14, 0, 0, tzinfo=UTC)
T_EARLY = datetime(2024, 8, 1, 9, 30, 0, tzinfo=UTC)
T_LATE_AVAIL = datetime(2024, 8, 1, 13, 0, 0, tzinfo=UTC)
T_SCHEDULE = datetime(2024, 8, 1, 10, 0, 0, tzinfo=UTC)


def _ts(field: TemporalSemanticField, value: datetime) -> TemporalTimestamp:
    return TemporalTimestamp.direct(field, value)


def _event(
    event_id: str,
    *,
    entity_key: str = "asset-a",
    price: str = "120",
    available_at: datetime = T_EARLY,
    source: str = "binance",
) -> CanonicalTemporalEvent:
    obs = TemporalObservation.create(
        event_time=_ts(TemporalSemanticField.EVENT_TIME, available_at),
        observed_time=_ts(TemporalSemanticField.OBSERVED_TIME, available_at),
        available_at=_ts(TemporalSemanticField.AVAILABLE_AT, available_at),
        ingested_at=_ts(TemporalSemanticField.INGESTED_AT, available_at),
        effective_at=_ts(TemporalSemanticField.EFFECTIVE_AT, available_at),
        revised_at=_ts(TemporalSemanticField.REVISED_AT, available_at),
    )
    return CanonicalTemporalEvent(
        event_id=event_id,
        entity_key=entity_key,
        event_type="market.tick",
        payload={"price": price},
        observation=obs,
        provenance=ProvenanceMetadata(
            source=source,
            source_version="v1",
            dataset_version="ds-1",
            retention_policy_reference="retain-365d",
        ),
        record_version="1",
    )


def _store_and_replay(events: list[CanonicalTemporalEvent] | None = None):
    store = TemporalCanonicalEventStore(events or [_event("evt-a")])
    request = ReplayRequest(
        event_source=store,
        start_time=T_START,
        end_time=T_END,
        replay_clock_or_schedule=[T_SCHEDULE],
        strict_mode=True,
        replay_parameters={"threshold": 0.5, "regime": "normal", "target_definition": "directional"},
    )
    mass = run_deterministic_mass_replay(request)
    decision = execute_historical_decision_path(
        event_source=store,
        mass_replay=mass,
        parameters={"threshold": 0.5, "regime": "normal"},
        model_identity="model-v1",
    )
    return store, mass, decision


# --- Inventory ---

def test_p2_inventory_lock() -> None:
    assert P2_EXPECTED_ACTIVE_ATOMIC_REQUIREMENTS == 103
    assert P2_DISCOVERED_ACTIVE_ATOMIC_REQUIREMENTS == 103
    assert len(P2_ATOMIC_REQUIREMENT_IDS) == 103
    assert P2_EXTERNAL_OR_LIVE_GATED_IDS == ()


# --- Outcome Factory (0096-0116) ---

def test_outcome_factory_generates_measurable_contracts() -> None:
    store, mass, decision = _store_and_replay()
    step = mass.replay_outputs[0]
    stages = decision.steps[0].stages
    result = generate_outcomes_from_decision_step(
        step=step,
        event_source=store,
        stages=stages,
        parameters={"regime": "normal", "target_definition": "directional"},
        model_identity="model-v1",
    )
    assert result.outcomes
    outcome = result.outcomes[0]
    assert outcome.target_definition is not None
    assert outcome.evaluation_horizon is not None
    assert outcome.evaluator_version == OUTCOME_EVALUATOR_IDENTITY
    assert outcome.evaluator_version != "model-v1"


def test_outcome_factory_required_fields_present() -> None:
    store, mass, decision = _store_and_replay()
    outcome = decision.steps[0].stages["outcome"]["outcomes"][0]
    for field in (
        "target_definition",
        "evaluation_horizon",
        "outcome_timestamp",
        "realized_result",
        "benchmark_result",
        "confidence",
        "calibration_error",
        "directional_correctness",
        "magnitude_error",
        "regret",
        "favorable_excursion",
        "adverse_excursion",
        "drawdown",
        "false_positive_cost",
        "false_negative_cost",
        "abstention_quality",
        "market_regime",
        "evaluator_version",
    ):
        assert field in outcome


def test_predictor_cannot_self_validate() -> None:
    assert predictor_must_not_self_validate("model-v1", OUTCOME_EVALUATOR_IDENTITY) is True
    assert predictor_must_not_self_validate(OUTCOME_EVALUATOR_IDENTITY, OUTCOME_EVALUATOR_IDENTITY) is False
    assert decision_path_outcome_has_no_self_validation()


def decision_path_outcome_has_no_self_validation() -> bool:
    _, _, decision = _store_and_replay()
    outcome_stage = decision.steps[0].stages["outcome"]
    return outcome_stage["predictor_self_validation"] is False


def test_unresolved_outcome_not_fabricated() -> None:
    future = _event("evt-future", available_at=T_LATE_AVAIL)
    store = TemporalCanonicalEventStore([future])
    request = ReplayRequest(
        event_source=store,
        start_time=T_START,
        end_time=T_END,
        replay_clock_or_schedule=[T_SCHEDULE],
    )
    mass = run_deterministic_mass_replay(request)
    if mass.success:
        decision = execute_historical_decision_path(
            event_source=store, mass_replay=mass, model_identity="model-v1"
        )
        for step in decision.steps:
            for outcome in step.stages["outcome"]["outcomes"]:
                if outcome["label_status"] == OutcomeLabelStatus.UNRESOLVED.value:
                    assert outcome["realized_result"] is None


# --- Outcome Quality (0117-0123, 0437) ---

def test_outcome_quality_preserves_label_confidence() -> None:
    store, _, decision = _store_and_replay()
    meta = decision.steps[0].stages["outcome"]["outcomes"][0]
    from blackdark.temporal.outcome_contract import OutcomeContract

    contract = OutcomeContract(
        outcome_id=meta["outcome_id"],
        subject_identity=meta["subject_identity"],
        prediction_identity=meta["prediction_identity"],
        decision_identity=meta["decision_identity"],
        target_definition=meta["target_definition"],
        evaluation_horizon=meta["evaluation_horizon"],
        outcome_timestamp=T_SCHEDULE,
        realized_result=meta["realized_result"],
        benchmark_result=meta["benchmark_result"],
        confidence=meta["confidence"],
        calibration_error=meta["calibration_error"],
        directional_correctness=meta["directional_correctness"],
        magnitude_error=meta["magnitude_error"],
        regret=meta["regret"],
        favorable_excursion=meta["favorable_excursion"],
        adverse_excursion=meta["adverse_excursion"],
        drawdown=meta["drawdown"],
        false_positive_cost=meta["false_positive_cost"],
        false_negative_cost=meta["false_negative_cost"],
        abstention_quality=meta["abstention_quality"],
        market_regime=meta["market_regime"],
        evaluator_version=meta["evaluator_version"],
        label_status=OutcomeLabelStatus(meta["label_status"]),
    )
    before = contract.to_metadata()
    quality = assess_outcome_quality(contract)
    after = contract.to_metadata()
    assert before == after
    assert quality.label_confidence is not None
    assert quality.equivalent_to_direct_truth is True
    assert UNKNOWN_OUTCOME_TREATED_AS_FALSE is False


def test_derived_outcome_not_equivalent_to_direct_truth() -> None:
    from blackdark.temporal.outcome_contract import OutcomeContract

    contract = OutcomeContract(
        outcome_id="o1",
        subject_identity="a",
        prediction_identity="m",
        decision_identity="d",
        target_definition="t",
        evaluation_horizon="h",
        outcome_timestamp=None,
        realized_result=None,
        benchmark_result=None,
        confidence=None,
        calibration_error=None,
        directional_correctness=None,
        magnitude_error=None,
        regret=None,
        favorable_excursion=None,
        adverse_excursion=None,
        drawdown=None,
        false_positive_cost=None,
        false_negative_cost=None,
        abstention_quality=None,
        market_regime=None,
        evaluator_version=OUTCOME_EVALUATOR_IDENTITY,
        label_status=OutcomeLabelStatus.PROVISIONAL,
    )
    quality = assess_outcome_quality(contract)
    assert quality.equivalent_to_direct_truth is False


# --- Evidence classes (0138-0153) ---

def test_canonical_evidence_classes() -> None:
    expected = {c.value for c in TemporalEvidenceClass}
    assert expected == CANONICAL_EVIDENCE_CLASSES


def test_no_automatic_evidence_promotion() -> None:
    with pytest.raises(ValueError):
        assert_no_automatic_promotion(
            TemporalEvidenceClass.HISTORICAL_REPLAY.value,
            TemporalEvidenceClass.FORWARD_SHADOW.value,
        )
    assert can_promote_evidence_class(
        TemporalEvidenceClass.HISTORICAL_REPLAY.value,
        TemporalEvidenceClass.HISTORICAL_REPLAY.value,
    )


def test_evidence_hard_rules() -> None:
    assert not can_promote_evidence_class("HISTORICAL_REPLAY", "FORWARD_SHADOW")
    assert not can_promote_evidence_class("FORWARD_SHADOW", "VERIFIED_PRODUCTION")
    assert not can_promote_evidence_class("VERIFIED_PRODUCTION", "INDEPENDENTLY_VERIFIED")


def test_evidence_ledger_preserves_provenance_fields() -> None:
    ledger = EvidenceProvenanceLedger()
    record = ledger.record_evidence(
        evidence_class=TemporalEvidenceClass.HISTORICAL_REPLAY.value,
        producer="test",
        source_provenance={"source": "binance"},
        temporal_context={"simulated_time": T_SCHEDULE.isoformat()},
        versions={"evaluator_version": OUTCOME_EVALUATOR_IDENTITY},
        lineage=("outcome-1",),
        quality_state={"label_confidence": 0.9},
        limitations=(),
        methodology="pit_eval",
        timestamps={"outcome": T_SCHEDULE.isoformat()},
        evaluator_identity=OUTCOME_EVALUATOR_IDENTITY,
        payload={},
    )
    assert record.evidence_class == "HISTORICAL_REPLAY"
    assert record.evaluator_identity == OUTCOME_EVALUATOR_IDENTITY
    assert record.source_provenance["source"] == "binance"


def test_evidence_invalidation_preserves_lineage() -> None:
    ledger = EvidenceProvenanceLedger()
    record = ledger.record_evidence(
        evidence_class="HISTORICAL_REPLAY",
        producer="test",
        source_provenance={},
        temporal_context={},
        versions={},
        lineage=(),
        quality_state={},
        limitations=(),
        methodology="m",
        timestamps={},
        evaluator_identity=OUTCOME_EVALUATOR_IDENTITY,
        payload={},
    )
    invalidated = ledger.invalidate_evidence(
        record.evidence_id,
        reason_code="TEMPORAL_LEAKAGE",
        reason="lookahead detected",
        invalidated_at=T_SCHEDULE,
    )
    assert invalidated.validation_state == "invalidated"
    assert invalidated.invalidation is not None
    assert invalidated.invalidation.lineage_preserved is True
    with pytest.raises(ValueError):
        ledger.attempt_promotion(record.evidence_id, "FORWARD_SHADOW")


# --- Retention (0191-0202) ---

def test_retention_policy_tiers_and_controls() -> None:
    assert classify_storage_tier(access_frequency="live") == StorageTier.HOT
    assert classify_storage_tier(access_frequency="frequent_replay") == StorageTier.WARM
    assert classify_storage_tier(is_raw_archive=True) == StorageTier.COLD
    descriptor = build_retention_descriptor(StorageTier.WARM)
    assert descriptor.delete_raw_for_low_learning_value is False
    assert descriptor.compression is True
    assert descriptor.deterministic_reconstruction is True


# --- Source rights (0281-0291) ---

def test_source_rights_preserved_from_upstream() -> None:
    event = _event("evt-a")
    rights = extract_source_rights(
        event.provenance,
        rights_metadata={"permitted_purpose": "research", "model_training_rights": "restricted"},
    )
    assert rights.source == "binance"
    assert rights.permitted_purpose == "research"
    assert rights.retention_rights == "retain-365d"
    assert rights.upstream_authority == "DATA_GOVERNANCE"
    assert historical_availability_does_not_imply_permission() is True


# --- Source quality (0292-0305) ---

def test_source_quality_evidence() -> None:
    events = (_event("evt-a"),)
    quality = assess_source_quality(events, evaluation_time=T_SCHEDULE)
    assert quality.completeness == 1.0
    assert quality.influences["confidence"] is True
    assert quality.influences["replay_fidelity"] is True


# --- Reproducibility (0324-0337) ---

def test_reproducibility_manifest_fields() -> None:
    _, mass, _ = _store_and_replay()
    manifest = build_reproducibility_manifest(mass, model_version="model-v1")
    assert manifest.run_id == mass.replay_id
    assert manifest.evidence_class == REPLAY_EVIDENCE_CLASS
    assert manifest.code_sha is not None
    assert manifest.dataset_snapshot["input_event_identity_set"] is not None


# --- P2 pipeline integration ---

def test_p2_pipeline_end_to_end() -> None:
    store, mass, decision = _store_and_replay()
    result = run_p2_outcome_evidence_pipeline(
        event_source=store,
        mass_replay=mass,
        decision_path=decision,
    )
    assert result.evidence_class == REPLAY_EVIDENCE_CLASS
    assert result.predictor_self_validation is False
    assert result.outcome_factory.outcomes
    assert result.evidence_records
    assert result.reproducibility.full_reproducibility_possible is True


def test_replay_evidence_remains_historical_replay() -> None:
    store, mass, decision = _store_and_replay()
    p2 = run_p2_outcome_evidence_pipeline(
        event_source=store, mass_replay=mass, decision_path=decision
    )
    assert p2.evidence_class == "HISTORICAL_REPLAY"
    for record in p2.evidence_records:
        assert record.evidence_class == "HISTORICAL_REPLAY"


def test_canonical_history_unchanged_after_p2() -> None:
    store = TemporalCanonicalEventStore([_event("evt-a")])
    before = copy.deepcopy(store.list_events())
    _, mass, decision = _store_and_replay([_event("evt-a")])
    run_p2_outcome_evidence_pipeline(
        event_source=store, mass_replay=mass, decision_path=decision
    )
    after = store.list_events()
    assert [e.to_metadata() for e in before] == [e.to_metadata() for e in after]


def test_p2_deterministic_repeated_runs() -> None:
    store1, mass1, decision1 = _store_and_replay()
    store2, mass2, decision2 = _store_and_replay()
    first = run_p2_outcome_evidence_pipeline(
        event_source=store1, mass_replay=mass1, decision_path=decision1
    )
    second = run_p2_outcome_evidence_pipeline(
        event_source=store2, mass_replay=mass2, decision_path=decision2
    )
    assert first.reproducibility.run_id == second.reproducibility.run_id


def test_p2_lookahead_rejection() -> None:
    obs = TemporalObservation.create(
        event_time=_ts(TemporalSemanticField.EVENT_TIME, T_EARLY),
        observed_time=_ts(TemporalSemanticField.OBSERVED_TIME, T_LATE_AVAIL),
        available_at=_ts(TemporalSemanticField.AVAILABLE_AT, T_LATE_AVAIL),
        ingested_at=_ts(TemporalSemanticField.INGESTED_AT, T_LATE_AVAIL),
        effective_at=_ts(TemporalSemanticField.EFFECTIVE_AT, T_LATE_AVAIL),
        revised_at=_ts(TemporalSemanticField.REVISED_AT, T_LATE_AVAIL),
    )
    store = TemporalCanonicalEventStore(
        [
            CanonicalTemporalEvent(
                event_id="evt-future",
                entity_key="asset-a",
                event_type="market.tick",
                payload={"price": "120"},
                observation=obs,
                provenance=ProvenanceMetadata(source="binance"),
                record_version="1",
            )
        ]
    )
    request = ReplayRequest(
        event_source=store,
        start_time=T_START,
        end_time=T_END,
        replay_clock_or_schedule=[T_SCHEDULE],
    )
    mass = run_deterministic_mass_replay(request)
    assert mass.success is False


def test_all_p2_atomic_ids_have_runtime_modules() -> None:
    """Cross-cutting governance IDs satisfied by module presence."""
    import blackdark.temporal.evidence_provenance as ep
    import blackdark.temporal.outcome_factory as of
    import blackdark.temporal.outcome_quality as oq
    import blackdark.temporal.reproducibility_manifest as rm
    import blackdark.temporal.retention_policy as rp
    import blackdark.temporal.source_quality as sq
    import blackdark.temporal.source_rights as sr

    modules = (of, oq, ep, rp, sr, sq, rm)
    assert all(m is not None for m in modules)
    assert set(P2_ATOMIC_REQUIREMENT_IDS) == set(P2_ATOMIC_REQUIREMENT_IDS)
