"""P4 remaining module tests — walk-forward, contamination, dependence, coverage, fidelity, counterfactual, drift."""

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
from blackdark.temporal.contamination_registry import ContaminationPurpose, ContaminationRegistry
from blackdark.temporal.counterfactual_lab import (
    CounterfactualQuestion,
    CounterfactualSpec,
    build_counterfactual_suite,
    run_counterfactual_replay,
)
from blackdark.temporal.dependence_aware_sampling import (
    DependenceAwareSampler,
    DependenceDimension,
    EVALUATION_INSTANCES_NOT_AUTO_INDEPENDENT,
    dependence_cluster_key,
)
from blackdark.temporal.experience_coverage import (
    ELAPSED_TIME_ALONE_PROXY_PROHIBITED,
    assess_experience_coverage,
)
from blackdark.temporal.p4_drift import (
    HISTORICAL_SCALE_DOES_NOT_OVERRIDE_INVALIDATION,
    P4DriftDimension,
    evaluate_p4_drift,
)
from blackdark.temporal.p4_requirement_registry import (
    P4_ATOMIC_REQUIREMENT_IDS,
    P4_DISCOVERED_ACTIVE_ATOMIC_REQUIREMENTS,
    P4_EXPECTED_ACTIVE_ATOMIC_REQUIREMENTS,
    P4_EXTERNAL_OR_LIVE_GATED_ATOMIC_IDS,
    P4_REQUIREMENT_OWNERS,
)
from blackdark.temporal.replay_fidelity import ReplayFidelityDimension, assess_replay_fidelity
from blackdark.temporal.walk_forward import (
    TRAIN_ON_ALL_HISTORY_PROHIBITED,
    WalkForwardControl,
    WalkForwardFreezeContext,
    generate_walk_forward_windows,
    record_tuning_contamination,
    run_walk_forward_evaluation,
)

T_START = datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC)


def _ts(field: TemporalSemanticField, value: datetime) -> TemporalTimestamp:
    return TemporalTimestamp.direct(field, value)


def _event(event_id: str, *, source: str = "binance") -> CanonicalTemporalEvent:
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
        provenance=ProvenanceMetadata(source=source, source_version="v1", dataset_version="ds-1"),
        record_version="1",
    )


def test_p4_master_inventory_lock() -> None:
    assert P4_EXPECTED_ACTIVE_ATOMIC_REQUIREMENTS == 111
    assert P4_DISCOVERED_ACTIVE_ATOMIC_REQUIREMENTS == 111
    assert len(P4_ATOMIC_REQUIREMENT_IDS) == 111
    assert P4_EXTERNAL_OR_LIVE_GATED_ATOMIC_IDS == ()
    assert len(P4_REQUIREMENT_OWNERS) == 111


# --- WALK_FORWARD_VALIDATION TEMP-AR-0086..0095 ---

def test_temp_ar_0086_train_on_all_history_prohibited() -> None:
    assert TRAIN_ON_ALL_HISTORY_PROHIBITED is True
    with pytest.raises(ValueError):
        run_walk_forward_evaluation(
            dataset_id="ds-1",
            samples=[],
            windows=(),
            freeze=WalkForwardFreezeContext("m1", "d1", "c1", (WalkForwardControl.PURGE,)),
            contamination_registry=ContaminationRegistry(),
            evaluate_fold=lambda t, e, f: {},
        )


def test_temp_ar_0088_purge_control_applied() -> None:
    windows = generate_walk_forward_windows(
        dataset_id="ds-1",
        series_start="2026-01-01T00:00:00Z",
        series_end="2026-01-01T12:00:00Z",
        train_duration=timedelta(hours=2),
        eval_duration=timedelta(hours=1),
        step=timedelta(hours=1),
        purge_gap_seconds=300,
    )
    assert windows[0].purge_gap_seconds == 300


def test_temp_ar_0095_tuning_contamination_tracked() -> None:
    registry = ContaminationRegistry()
    record_tuning_contamination(
        registry=registry,
        dataset_id="ds-1",
        window_start=T_START,
        window_end=T_START + timedelta(hours=1),
        model_version="m1",
        config_version="c1",
        dataset_version="d1",
    )
    assert any(e.usage_purpose == ContaminationPurpose.TUNING for e in registry.list_entries())


# --- CONTAMINATION_REGISTRY TEMP-AR-0315..0323 ---

def test_temp_ar_0315_contamination_purposes_defined() -> None:
    purposes = {p.value for p in ContaminationPurpose}
    assert "training" in purposes
    assert "tuning" in purposes
    assert "evaluation" in purposes


def test_temp_ar_0322_evaluation_reuse_visibility() -> None:
    from blackdark.temporal.contamination_registry import ContaminationState

    registry = ContaminationRegistry()
    registry.record_exposure(
        dataset_id="ds-1",
        window_start=T_START,
        window_end=T_START + timedelta(hours=1),
        purpose=ContaminationPurpose.EVALUATION,
        model_version="m1",
        config_version="c1",
        dataset_version="d1",
    )
    gate = registry.check_evaluation_admission(
        dataset_id="ds-1",
        window_start=T_START,
        window_end=T_START + timedelta(hours=1),
        model_version="m1",
        config_version="c1",
        dataset_version="d1",
        fail_closed=True,
    )
    assert gate.contamination_state == ContaminationState.REUSE_VISIBLE
    assert gate.prior_exposures >= 1


def test_temp_ar_0323_claim_strength_reduction() -> None:
    registry = ContaminationRegistry()
    registry.record_exposure(
        dataset_id="ds-1",
        window_start=T_START,
        window_end=T_START + timedelta(hours=1),
        purpose=ContaminationPurpose.TUNING,
        model_version="m1",
        config_version="c1",
        dataset_version="d1",
    )
    gate = registry.check_evaluation_admission(
        dataset_id="ds-1",
        window_start=T_START,
        window_end=T_START + timedelta(hours=1),
        model_version="m1",
        config_version="c1",
        dataset_version="d1",
        fail_closed=False,
    )
    assert gate.claim_strength_reduction > 0


# --- DEPENDENCE_AWARE_SAMPLING TEMP-AR-0073..0085 ---

def test_temp_ar_0073_many_instances_from_one_period() -> None:
    sampler = DependenceAwareSampler()
    dims = {DependenceDimension.TEMPORAL_OVERLAP.value: True}
    cluster = dependence_cluster_key(event_family="fam-1", dimensions=dims)
    for i in range(5):
        sampler.record_instance(
            case_id=f"case-{i}",
            event_family="fam-1",
            dependence_cluster=cluster,
            dimensions=dims,
            overlap_factor=2.0,
        )
    assert sampler.total_raw_instances() == 5
    assert sampler.total_effective_independent() < 5


def test_temp_ar_0074_not_auto_independent() -> None:
    assert EVALUATION_INSTANCES_NOT_AUTO_INDEPENDENT is True


def test_temp_ar_0082_case_id_recorded() -> None:
    sampler = DependenceAwareSampler()
    record = sampler.record_instance(
        case_id="case-abc",
        event_family="fam-1",
        dependence_cluster="cluster-1",
        dimensions={DependenceDimension.SHARED_EVENT.value: True},
    )
    assert record.case_id == "case-abc"


# --- EXPERIENCE_COVERAGE TEMP-AR-0214..0229 ---

def test_temp_ar_0214_elapsed_time_not_sole_proxy() -> None:
    assert ELAPSED_TIME_ALONE_PROXY_PROHIBITED is True
    vector = assess_experience_coverage(
        historical_span_ratio=0.8,
        regimes_observed={"bull": 10, "bear": 5},
        event_families=["fam-1", "fam-2"],
        effective_independent_count=12.0,
        prediction_outcome_pairs=20,
        tail_events=2,
        total_events=100,
        assets=["BTC"],
        venues=["binance"],
        sources=["binance", "kraken"],
        calibration_bins_covered=8,
        calibration_bins_total=10,
        failure_cases=3,
        replay_fidelity_score=0.9,
        forward_shadow_hours=24.0,
        forward_shadow_samples=50,
    )
    assert vector.elapsed_time_proxy_used is False
    assert vector.composite_index is not None


def test_temp_ar_0215_historical_span_tracked() -> None:
    vector = assess_experience_coverage(
        historical_span_ratio=0.75,
        regimes_observed={},
        event_families=[],
        effective_independent_count=1.0,
        prediction_outcome_pairs=1,
        tail_events=0,
        total_events=1,
        assets=[],
        venues=[],
        sources=[],
        calibration_bins_covered=0,
        calibration_bins_total=1,
        failure_cases=0,
        replay_fidelity_score=0.5,
        forward_shadow_hours=0.0,
        forward_shadow_samples=0,
    )
    assert vector.historical_span_coverage == 0.75


# --- REPLAY_FIDELITY TEMP-AR-0203..0213 ---

def test_temp_ar_0203_temporal_fidelity_dimension() -> None:
    store = TemporalCanonicalEventStore([_event("evt-1")])
    replay = run_deterministic_mass_replay(
        ReplayRequest(
            event_source=store,
            start_time=T_START,
            end_time=T_START + timedelta(hours=4),
            replay_clock_or_schedule=(T_START + timedelta(hours=2),),
            strict_mode=True,
        )
    )
    profile = assess_replay_fidelity(replay)
    assert ReplayFidelityDimension.TEMPORAL.value in profile.dimensions
    assert profile.composite_score is not None


def test_temp_ar_0213_composite_score_derived() -> None:
    store = TemporalCanonicalEventStore([_event("evt-1")])
    replay = run_deterministic_mass_replay(
        ReplayRequest(
            event_source=store,
            start_time=T_START,
            end_time=T_START + timedelta(hours=4),
            replay_clock_or_schedule=(T_START + timedelta(hours=2),),
            strict_mode=True,
        )
    )
    profile = assess_replay_fidelity(replay)
    assert profile.composite_score is not None


# --- COUNTERFACTUAL_LAB TEMP-AR-0241..0250 ---

def test_temp_ar_0241_confidence_threshold_counterfactual() -> None:
    store = TemporalCanonicalEventStore([_event("evt-1")])
    base = ReplayRequest(
        event_source=store,
        start_time=T_START,
        end_time=T_START + timedelta(hours=4),
        replay_clock_or_schedule=(T_START + timedelta(hours=2),),
        strict_mode=True,
        replay_parameters={"threshold": 0.5},
    )
    result = run_counterfactual_replay(
        event_source=store,
        base_request=base,
        spec=CounterfactualSpec(
            question=CounterfactualQuestion.CONFIDENCE_THRESHOLD,
            parameters={"threshold": 0.8},
            scenario_id="cf-1",
        ),
    )
    assert result.robustness_focus is True


def test_temp_ar_0250_robustness_not_direction_only() -> None:
    store = TemporalCanonicalEventStore([_event("evt-1"), _event("evt-2", source="kraken")])
    base = ReplayRequest(
        event_source=store,
        start_time=T_START,
        end_time=T_START + timedelta(hours=4),
        replay_clock_or_schedule=(T_START + timedelta(hours=2),),
        strict_mode=True,
    )
    suite = build_counterfactual_suite(event_source=store, base_request=base)
    assert len(suite) >= 1
    assert all(r.robustness_focus for r in suite)


# --- P4 DRIFT TEMP-AR-0306..0314 ---

def test_temp_ar_0306_feature_drift_monitored() -> None:
    result = evaluate_p4_drift(
        baseline={P4DriftDimension.FEATURE_DRIFT.value: 0.1},
        current={P4DriftDimension.FEATURE_DRIFT.value: 0.5},
    )
    feature = next(s for s in result.signals if s.dimension == P4DriftDimension.FEATURE_DRIFT)
    assert feature.detected is True


def test_temp_ar_0314_historical_scale_does_not_override_invalidation() -> None:
    assert HISTORICAL_SCALE_DOES_NOT_OVERRIDE_INVALIDATION is True
    result = evaluate_p4_drift(
        baseline={P4DriftDimension.REPRESENTATIVENESS_INVALIDATION.value: "stable"},
        current={P4DriftDimension.REPRESENTATIVENESS_INVALIDATION.value: "broken"},
        historical_sample_scale=2_000_000,
    )
    assert result.representativeness_invalidated is True
