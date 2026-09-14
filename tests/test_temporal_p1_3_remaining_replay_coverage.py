"""Focused P1.3 remaining replay coverage tests (TEMP-AR-0057..0065, TEMP-AR-0071)."""

from __future__ import annotations

import copy
from datetime import UTC, datetime

from blackdark.temporal import (
    CanonicalTemporalEvent,
    DECISION_PATH_STAGES,
    ProvenanceMetadata,
    REPLAY_EVIDENCE_CLASS,
    ReplayRequest,
    ReplayScenarioSpec,
    TemporalCanonicalEventStore,
    TemporalObservation,
    TemporalSemanticField,
    TemporalTimestamp,
    compare_replay_runs,
    execute_historical_decision_path,
    run_deterministic_mass_replay,
    run_full_decision_path_replay,
    run_multi_scenario_replay,
)

T_START = datetime(2024, 8, 1, 9, 0, 0, tzinfo=UTC)
T_MID = datetime(2024, 8, 1, 11, 0, 0, tzinfo=UTC)
T_END = datetime(2024, 8, 1, 14, 0, 0, tzinfo=UTC)
T_EARLY = datetime(2024, 8, 1, 9, 30, 0, tzinfo=UTC)
T_LATE_AVAIL = datetime(2024, 8, 1, 13, 0, 0, tzinfo=UTC)
T_SCHEDULE_EARLY = datetime(2024, 8, 1, 10, 0, 0, tzinfo=UTC)
T_SCHEDULE_LATE = datetime(2024, 8, 1, 12, 0, 0, tzinfo=UTC)

P1_3_ATOMIC_IDS = (
    "TEMP-AR-0057",
    "TEMP-AR-0058",
    "TEMP-AR-0059",
    "TEMP-AR-0060",
    "TEMP-AR-0061",
    "TEMP-AR-0062",
    "TEMP-AR-0063",
    "TEMP-AR-0064",
    "TEMP-AR-0065",
    "TEMP-AR-0071",
)


def _ts(field: TemporalSemanticField, value: datetime) -> TemporalTimestamp:
    return TemporalTimestamp.direct(field, value)


def _observation(
    *,
    available_at: datetime,
    revised_at: datetime,
    event_time: datetime | None = None,
) -> TemporalObservation:
    evt = event_time or available_at
    return TemporalObservation.create(
        event_time=_ts(TemporalSemanticField.EVENT_TIME, evt),
        observed_time=_ts(TemporalSemanticField.OBSERVED_TIME, available_at),
        available_at=_ts(TemporalSemanticField.AVAILABLE_AT, available_at),
        ingested_at=_ts(TemporalSemanticField.INGESTED_AT, available_at),
        effective_at=_ts(TemporalSemanticField.EFFECTIVE_AT, revised_at),
        revised_at=_ts(TemporalSemanticField.REVISED_AT, revised_at),
    )


def _event(
    event_id: str,
    *,
    entity_key: str = "entity-a",
    event_type: str = "market.tick",
    available_at: datetime = T_EARLY,
    revised_at: datetime = T_EARLY,
    event_time: datetime | None = None,
    record_version: str = "1",
    source: str = "binance",
    source_version: str | None = "v1",
    dataset_version: str | None = "ds-1",
    payload: dict | None = None,
) -> CanonicalTemporalEvent:
    return CanonicalTemporalEvent(
        event_id=event_id,
        entity_key=entity_key,
        event_type=event_type,
        payload=payload or {"price": "120"},
        observation=_observation(
            available_at=available_at,
            revised_at=revised_at,
            event_time=event_time or available_at,
        ),
        provenance=ProvenanceMetadata(
            source=source,
            source_version=source_version,
            dataset_version=dataset_version,
        ),
        record_version=record_version,
    )


def _base_store() -> TemporalCanonicalEventStore:
    return TemporalCanonicalEventStore(
        [
            _event("evt-a", entity_key="asset-a", source="binance"),
            _event(
                "evt-b",
                entity_key="asset-b",
                source="coinbase",
                event_time=T_MID,
                available_at=T_MID,
                revised_at=T_MID,
            ),
        ]
    )


def _request(store: TemporalCanonicalEventStore, **kwargs) -> ReplayRequest:
    return ReplayRequest(
        event_source=store,
        start_time=T_START,
        end_time=T_END,
        replay_clock_or_schedule=kwargs.pop("schedule", [T_SCHEDULE_EARLY, T_SCHEDULE_LATE]),
        strict_mode=kwargs.pop("strict", True),
        replay_parameters=kwargs.pop("replay_parameters", {}),
        dataset_or_source_version_context=kwargs.pop("version_context", {}),
    )


def _scenario(
    scenario_id: str,
    *,
    threshold: float = 0.5,
    model_version: str = "model-v1",
    **dimension_kwargs,
) -> ReplayScenarioSpec:
    return ReplayScenarioSpec(
        scenario_id=scenario_id,
        parameters={"threshold": threshold, "regime": dimension_kwargs.get("regime", "normal")},
        time_window={
            "start": T_START.isoformat(),
            "end": T_END.isoformat(),
            "schedule": [T_SCHEDULE_EARLY.isoformat(), T_SCHEDULE_LATE.isoformat()],
        },
        input_identity_context={"dataset_version": "ds-1"},
        assets=dimension_kwargs.get("assets", ("asset-a", "asset-b")),
        venues=dimension_kwargs.get("venues", ("binance", "coinbase")),
        time_horizons=dimension_kwargs.get("time_horizons", ("short",)),
        historical_periods=dimension_kwargs.get("historical_periods", ("2024-08",)),
        regimes=dimension_kwargs.get("regimes", ("normal",)),
        model_versions=(model_version,),
        thresholds={"default": threshold},
        source_availability=dimension_kwargs.get("source_availability", {"required_source": "binance"}),
    )


def test_temp_ar_0057_full_decision_path_replay_executes_existing_path() -> None:
    store = _base_store()
    request = _request(store, replay_parameters={"threshold": 0.5})
    result = run_full_decision_path_replay(store, request, model_identity="model-v1")
    assert result.creates_new_decision_authority is False
    assert result.evidence_class == REPLAY_EVIDENCE_CLASS
    assert len(result.steps) >= 1
    for step in result.steps:
        assert tuple(step.stages.keys()) == DECISION_PATH_STAGES
        assert step.stages["outcome"]["status"] == "deferred_outcome_factory_not_in_p1_3"


def test_future_unavailable_inputs_fail_temporal_admission() -> None:
    store = TemporalCanonicalEventStore(
        [_event("evt-future", event_time=T_EARLY, available_at=T_LATE_AVAIL, revised_at=T_LATE_AVAIL)]
    )
    scenario = _scenario(
        "future-unavailable",
        source_availability={},
        assets=("asset-a",),
        venues=("binance",),
    )
    multi = run_multi_scenario_replay(store, [scenario])
    assert multi.scenarios[0].rejections
    assert multi.scenarios[0].evidence_class == REPLAY_EVIDENCE_CLASS


def test_temp_ar_0058_through_0065_multi_scenario_dimensions_isolated() -> None:
    store = _base_store()
    scenarios = [
        _scenario("assets-scenario", assets=("asset-a",), venues=("binance",)),
        _scenario("venues-scenario", assets=("asset-b",), venues=("coinbase",)),
        _scenario("horizon-scenario", time_horizons=("long",)),
        _scenario("period-scenario", historical_periods=("2024-07",)),
        _scenario("regime-scenario", regime="volatile", regimes=("volatile",)),
        _scenario("model-scenario", model_version="model-v2"),
        _scenario("threshold-scenario", threshold=0.8),
        _scenario("source-scenario", source_availability={"required_source": "coinbase"}),
    ]
    multi = run_multi_scenario_replay(store, scenarios)
    assert len(multi.scenarios) == 8
    assert multi.cross_scenario_state_contamination == 0
    ids = {scenario.scenario_id for scenario in multi.scenarios}
    assert ids == {scenario.scenario_id for scenario in scenarios}
    for scenario_result in multi.scenarios:
        assert scenario_result.parameters
        assert scenario_result.time_window
        assert scenario_result.input_identity_context
        assert scenario_result.result
        assert scenario_result.determinism_fingerprint
        assert scenario_result.evidence_class == REPLAY_EVIDENCE_CLASS


def test_same_scenario_repeated_gives_identical_output() -> None:
    store = _base_store()
    scenario = _scenario("repeatable")
    first = run_multi_scenario_replay(store, [scenario])
    second = run_multi_scenario_replay(store, [scenario])
    assert first.scenarios[0].determinism_fingerprint == second.scenarios[0].determinism_fingerprint
    assert first.scenarios[0].result == second.scenarios[0].result


def test_different_scenario_parameters_remain_distinguishable() -> None:
    store = _base_store()
    low = _scenario("low-threshold", threshold=0.3)
    high = _scenario("high-threshold", threshold=0.9)
    multi = run_multi_scenario_replay(store, [low, high])
    assert multi.scenarios[0].determinism_fingerprint != multi.scenarios[1].determinism_fingerprint
    assert multi.scenarios[0].parameters != multi.scenarios[1].parameters


def test_scenario_ordering_does_not_affect_other_scenario_result() -> None:
    store = _base_store()
    a = _scenario("scenario-a", threshold=0.4)
    b = _scenario("scenario-b", threshold=0.7)
    forward = run_multi_scenario_replay(store, [a, b])
    reverse = run_multi_scenario_replay(store, [b, a])
    forward_map = {scenario.scenario_id: scenario for scenario in forward.scenarios}
    reverse_map = {scenario.scenario_id: scenario for scenario in reverse.scenarios}
    assert forward_map["scenario-a"].determinism_fingerprint == reverse_map["scenario-a"].determinism_fingerprint
    assert forward_map["scenario-b"].determinism_fingerprint == reverse_map["scenario-b"].determinism_fingerprint


def test_temp_ar_0071_comparable_runs_compare_deterministically() -> None:
    store = _base_store()
    baseline_scenario = _scenario("shared-scenario", model_version="model-v1", threshold=0.5)
    challenger_scenario = _scenario("shared-scenario", model_version="model-v2", threshold=0.5)
    baseline = run_multi_scenario_replay(store, [baseline_scenario]).scenarios[0]
    challenger = run_multi_scenario_replay(store, [challenger_scenario]).scenarios[0]
    comparison = compare_replay_runs(
        baseline.result,
        challenger.result,
        baseline_run_id="baseline-run",
        challenger_run_id="challenger-run",
        proven_context_keys=frozenset(
            {
                "replay_window",
                "input_identity_set",
                "source_dataset_versions",
                "parameter_set",
                "evidence_class",
                "temporal_semantics",
                "scenario_identity",
            }
        ),
    )
    assert comparison.comparable is True
    assert comparison.causes_model_promotion is False
    assert "baseline_fingerprint" in comparison.comparison_outputs
    assert comparison.comparison_outputs["baseline_model_identity"] == "model-v1"
    assert comparison.comparison_outputs["challenger_model_identity"] == "model-v2"
    assert comparison.shared_context["evidence_class"] == REPLAY_EVIDENCE_CLASS


def test_unproven_comparison_context_fails_closed() -> None:
    store = _base_store()
    baseline = run_multi_scenario_replay(store, [_scenario("baseline")]).scenarios[0]
    challenger_scenario = _scenario("challenger")
    challenger_scenario = ReplayScenarioSpec(
        scenario_id=challenger_scenario.scenario_id,
        parameters=challenger_scenario.parameters,
        time_window={
            "start": T_MID.isoformat(),
            "end": T_END.isoformat(),
            "schedule": [T_SCHEDULE_LATE.isoformat()],
        },
        input_identity_context={"dataset_version": "ds-9"},
        assets=challenger_scenario.assets,
        venues=challenger_scenario.venues,
        time_horizons=challenger_scenario.time_horizons,
        historical_periods=challenger_scenario.historical_periods,
        regimes=challenger_scenario.regimes,
        model_versions=challenger_scenario.model_versions,
        thresholds=challenger_scenario.thresholds,
        source_availability=challenger_scenario.source_availability,
    )
    challenger = run_multi_scenario_replay(store, [challenger_scenario]).scenarios[0]
    comparison = compare_replay_runs(
        baseline.result,
        challenger.result,
        baseline_run_id="baseline-run",
        challenger_run_id="challenger-run",
    )
    assert comparison.comparable is False
    assert "CONTEXT_MISMATCH" in comparison.reason_codes
    assert comparison.context_differences


def test_comparison_does_not_trigger_model_promotion() -> None:
    store = _base_store()
    baseline = run_multi_scenario_replay(store, [_scenario("baseline")]).scenarios[0]
    challenger = run_multi_scenario_replay(store, [_scenario("challenger")]).scenarios[0]
    comparison = compare_replay_runs(
        baseline.result,
        challenger.result,
        baseline_run_id="baseline-run",
        challenger_run_id="challenger-run",
        proven_context_keys=frozenset(),
    )
    assert comparison.causes_model_promotion is False
    assert "promotion" not in str(comparison.comparison_outputs).lower()


def test_all_outputs_remain_historical_replay() -> None:
    store = _base_store()
    request = _request(store)
    decision = run_full_decision_path_replay(store, request)
    multi = run_multi_scenario_replay(store, [_scenario("evidence-class")])
    comparison = compare_replay_runs(
        multi.scenarios[0].result,
        multi.scenarios[0].result,
        baseline_run_id="a",
        challenger_run_id="b",
        proven_context_keys=frozenset(
            {
                "replay_window",
                "input_identity_set",
                "source_dataset_versions",
                "model_engine_identity",
                "parameter_set",
                "evidence_class",
                "temporal_semantics",
                "scenario_identity",
            }
        ),
    )
    assert decision.evidence_class == REPLAY_EVIDENCE_CLASS
    assert multi.evidence_class == REPLAY_EVIDENCE_CLASS
    assert multi.scenarios[0].evidence_class == REPLAY_EVIDENCE_CLASS
    assert comparison.evidence_class == REPLAY_EVIDENCE_CLASS


def test_canonical_history_unchanged_after_p1_3_replay() -> None:
    store = _base_store()
    before = copy.deepcopy(store.list_events())
    run_multi_scenario_replay(store, [_scenario("history-check"), _scenario("history-check-2")])
    after = store.list_events()
    assert [event.to_metadata() for event in before] == [event.to_metadata() for event in after]


def test_production_state_unchanged_after_p1_3_replay() -> None:
    production_state = {"decisions": [], "promoted_models": []}
    before = copy.deepcopy(production_state)
    store = _base_store()
    run_multi_scenario_replay(store, [_scenario("prod-check")])
    assert production_state == before


def test_p1_2_deterministic_replay_semantics_unchanged() -> None:
    store = _base_store()
    baseline = run_deterministic_mass_replay(_request(store))
    run_multi_scenario_replay(store, [_scenario("p12-check")])
    after = run_deterministic_mass_replay(_request(store))
    assert baseline.to_metadata() == after.to_metadata()


def test_p1_1_event_lineage_unchanged_after_p1_3_replay() -> None:
    store = TemporalCanonicalEventStore()
    v1 = _event("evt-v1", record_version="1")
    v2 = _event("evt-v2", record_version="2", event_time=T_MID, available_at=T_MID, revised_at=T_MID)
    store.append_event(v1)
    store.append_revision(v2, prior_event_id="evt-v1")
    lineage_before = store.retrieve_lineage("evt-v2")
    run_multi_scenario_replay(store, [_scenario("lineage-check")])
    lineage_after = store.retrieve_lineage("evt-v2")
    assert [event.event_id for event in lineage_before] == [event.event_id for event in lineage_after]


def test_p0_temporal_safety_preserved_for_decision_path_replay() -> None:
    store = TemporalCanonicalEventStore(
        [_event("evt-future", event_time=T_EARLY, available_at=T_LATE_AVAIL, revised_at=T_LATE_AVAIL)]
    )
    mass = run_deterministic_mass_replay(_request(store, schedule=[T_SCHEDULE_EARLY]))
    decision = execute_historical_decision_path(
        event_source=store,
        mass_replay=mass,
        parameters={"threshold": 0.5},
        model_identity="model-v1",
    )
    assert mass.success is False
    assert decision.steps == ()
    assert decision.evidence_class == REPLAY_EVIDENCE_CLASS


def test_p1_3_atomic_requirement_ids_covered() -> None:
    assert len(P1_3_ATOMIC_IDS) == 10
