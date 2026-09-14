"""P4_LEARNING_AND_EVALUATION closure runtime/E2E tests."""

from __future__ import annotations

import os
import socket
from datetime import UTC, datetime, timedelta

import pytest

from uuid import uuid4

from blackdark.temporal.contamination_registry import (
    ContaminationEntry,
    ContaminationPurpose,
    ContaminationState,
)
from blackdark.temporal.controlled_learning import ControlledLearningEngine
from blackdark.temporal.dependence_aware_sampling import DependenceAwareSampler, dependence_cluster_key
from blackdark.temporal.experience_coverage import assess_experience_coverage
from blackdark.temporal.learning_value import LearningStream, LearningValueEngine
from blackdark.temporal.persistence.postgres import PostgresContaminationRegistry
from blackdark.temporal.replay_fidelity import assess_replay_fidelity
from blackdark.temporal.walk_forward import (
    WalkForwardControl,
    WalkForwardFreezeContext,
    generate_walk_forward_windows,
    run_walk_forward_evaluation,
)

POSTGRES_URL = os.getenv(
    "BLACKDARK_TEST_DATABASE_URL",
    "postgresql://blackdark:blackdark@127.0.0.1:5432/blackdark_clean",
)

T_START = datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC)
T_NOW = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)
CTX = {"available_at": T_NOW.isoformat()}
PROV = "prov-ref-1"


def _outcome(**kwargs):
    from blackdark.temporal.outcome_contract import OUTCOME_EVALUATOR_IDENTITY, OutcomeContract, OutcomeLabelStatus

    defaults = {
        "outcome_id": "outcome-1",
        "subject_identity": "asset-a",
        "prediction_identity": "model-v1",
        "decision_identity": "asset-a:act",
        "target_definition": "directional",
        "evaluation_horizon": "1h",
        "outcome_timestamp": T_NOW,
        "realized_result": 100.0,
        "benchmark_result": 99.0,
        "confidence": 0.9,
        "calibration_error": 0.1,
        "directional_correctness": False,
        "magnitude_error": 0.1,
        "regret": 0.1,
        "favorable_excursion": 1.0,
        "adverse_excursion": 0.0,
        "drawdown": None,
        "false_positive_cost": 1.0,
        "false_negative_cost": None,
        "abstention_quality": "evaluated",
        "market_regime": "bull",
        "evaluator_version": OUTCOME_EVALUATOR_IDENTITY,
        "label_status": OutcomeLabelStatus.VERIFIED,
    }
    defaults.update(kwargs)
    return OutcomeContract(**defaults)


def _evidence(ledger, evidence_class: str):
    from blackdark.temporal.outcome_contract import OUTCOME_EVALUATOR_IDENTITY

    return ledger.record_evidence(
        evidence_class=evidence_class,
        producer="test",
        source_provenance={"provenance_reference": PROV},
        temporal_context=CTX,
        versions={"model_version": "model-v1"},
        lineage=("line-1",),
        quality_state={"outcome_quality": "direct_observed", "label_confidence": 0.95},
        limitations=(),
        methodology="test",
        timestamps={"recorded_at": T_NOW.isoformat()},
        evaluator_identity=OUTCOME_EVALUATOR_IDENTITY,
        payload={},
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
async def test_temp_ar_0095_tuning_contamination_postgres_integration(monkeypatch, tmp_path) -> None:
    from blackdark.data.db import get_session

    await _reset_data_engine(monkeypatch, tmp_path)
    async with get_session() as session:
        registry = PostgresContaminationRegistry(session)
        await registry.hydrate()
        entry = await registry.record_exposure_persisted(
            ContaminationEntry(
                entry_id=str(uuid4()),
                dataset_id="ds-p4",
                window_start=T_START,
                window_end=T_START + timedelta(hours=1),
                usage_purpose=ContaminationPurpose.TUNING,
                model_version="m1",
                config_version="c1",
                dataset_version="d1",
                exposure_count=1,
                contamination_state=ContaminationState.EXPOSED,
                metadata={},
            )
        )
        assert entry.usage_purpose == ContaminationPurpose.TUNING

    import blackdark.data.db as db_module

    db_module._engine = None
    db_module._session_factory = None
    db_module._schema_ready = False

    from blackdark.data.db import get_session, init_data_engine

    await init_data_engine()
    async with get_session() as session:
        reloaded = PostgresContaminationRegistry(session)
        await reloaded.hydrate()
        gate = reloaded.check_evaluation_admission(
            dataset_id="ds-p4",
            window_start=T_START,
            window_end=T_START + timedelta(hours=1),
            model_version="m1",
            config_version="c1",
            dataset_version="d1",
            fail_closed=False,
        )
        assert gate.prior_exposures >= 1
        assert gate.contamination_state == ContaminationState.CONTAMINATED


@pytest.mark.asyncio
@pytest.mark.skipif(not _postgres_reachable(), reason="Postgres not reachable")
async def test_temp_ar_0322_contamination_reuse_visibility_postgres(monkeypatch, tmp_path) -> None:
    from blackdark.data.db import get_session

    await _reset_data_engine(monkeypatch, tmp_path)
    async with get_session() as session:
        registry = PostgresContaminationRegistry(session)
        await registry.hydrate()
        await registry.record_exposure_persisted(
            ContaminationEntry(
                entry_id=str(uuid4()),
                dataset_id="ds-reuse",
                window_start=T_START,
                window_end=T_START + timedelta(hours=1),
                usage_purpose=ContaminationPurpose.EVALUATION,
                model_version=None,
                config_version=None,
                dataset_version=None,
                exposure_count=1,
                contamination_state=ContaminationState.EXPOSED,
                metadata={},
            )
        )
        gate = registry.check_evaluation_admission(
            dataset_id="ds-reuse",
            window_start=T_START,
            window_end=T_START + timedelta(hours=1),
            fail_closed=True,
        )
        assert gate.contamination_state == ContaminationState.REUSE_VISIBLE
        assert gate.admitted is False


def test_temp_ar_0073_dependence_integration_effective_independent() -> None:
    sampler = DependenceAwareSampler()
    dims = {"temporal_overlap": True}
    cluster = dependence_cluster_key(event_family="wf-fam", dimensions=dims)
    for i in range(6):
        sampler.record_instance(
            case_id=f"wf-case-{i}",
            event_family="wf-fam",
            dependence_cluster=cluster,
            dimensions=dims,
            overlap_factor=3.0,
        )
    assert sampler.total_raw_instances() == 6
    assert sampler.total_effective_independent() < 6


def test_temp_ar_0188_learning_value_prioritization_integration() -> None:
    from blackdark.temporal.evidence_class import TemporalEvidenceClass
    from blackdark.temporal.evidence_provenance import EvidenceProvenanceLedger
    from blackdark.temporal.failure_surprise_corpus import FailureSurpriseCorpus

    outcome = _outcome(outcome_id="out-1")
    corpus = FailureSurpriseCorpus()
    case = corpus.capture_high_confidence_wrong(
        case_id="lv-int-1",
        prediction_identity="model-v1",
        decision_identity="decision-1",
        outcome=outcome,
        shadow_receipt_id="shadow-1",
        evidence_class=TemporalEvidenceClass.FORWARD_SHADOW.value,
        recorded_at=T_NOW,
        temporal_context=CTX,
        provenance_reference=PROV,
        confidence=0.95,
    )
    ledger = EvidenceProvenanceLedger()
    record = _evidence(ledger, TemporalEvidenceClass.FORWARD_SHADOW.value)
    engine = LearningValueEngine()
    results = engine.prioritize(
        evidence_records=(record,),
        corpus_cases=(case,),
        outcomes={outcome.outcome_id: outcome},
    )
    assert len(results) >= 2
    assert any(r.learning_value > 0 for r in results)


def test_temp_ar_0189_learning_value_does_not_replace_sampling() -> None:
    from blackdark.temporal.evidence_class import TemporalEvidenceClass
    from blackdark.temporal.evidence_provenance import EvidenceProvenanceLedger

    outcome = _outcome(outcome_id="out-2")
    ledger = EvidenceProvenanceLedger()
    record = _evidence(ledger, TemporalEvidenceClass.HISTORICAL_REPLAY.value)
    engine = LearningValueEngine()
    rep = engine.evaluate_evidence(record, outcome=outcome, stream=LearningStream.REPRESENTATIVE)
    hi = engine.evaluate_evidence(record, outcome=outcome, stream=LearningStream.HIGH_INFORMATION)
    assert rep.sampling_stream == LearningStream.REPRESENTATIVE.value
    assert hi.sampling_stream == LearningStream.HIGH_INFORMATION.value


def test_temp_ar_0213_replay_fidelity_composite_integration() -> None:
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
    event = CanonicalTemporalEvent(
        event_id="p4-evt-1",
        entity_key="asset-a",
        event_type="market.tick",
        payload={"price": "100"},
        observation=obs,
        provenance=ProvenanceMetadata(source="binance", source_version="v1", dataset_version="ds-1"),
        record_version="1",
    )
    store = TemporalCanonicalEventStore([event])
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
    assert len(profile.dimensions) >= 1


def test_temp_ar_0229_experience_coverage_composite_integration() -> None:
    vector = assess_experience_coverage(
        historical_span_ratio=0.6,
        regimes_observed={"bull": 8, "bear": 4, "sideways": 2},
        event_families=["fam-a", "fam-b"],
        effective_independent_count=15.0,
        prediction_outcome_pairs=30,
        tail_events=3,
        total_events=200,
        assets=["BTC", "ETH"],
        venues=["binance"],
        sources=["binance", "kraken"],
        calibration_bins_covered=7,
        calibration_bins_total=10,
        failure_cases=5,
        replay_fidelity_score=0.88,
        forward_shadow_hours=48.0,
        forward_shadow_samples=120,
    )
    assert vector.composite_index is not None
    assert vector.calibration_coverage == 0.7
    assert vector.replay_fidelity_coverage == 0.88


def test_temp_ar_0234_controlled_learning_candidate_weights_integration() -> None:
    from blackdark.temporal.controlled_learning import CandidateArtifactType
    from blackdark.temporal.evidence_class import TemporalEvidenceClass
    from blackdark.temporal.evidence_provenance import EvidenceProvenanceLedger

    outcome = _outcome(outcome_id="out-cl-1")
    ledger = EvidenceProvenanceLedger()
    record = _evidence(ledger, TemporalEvidenceClass.FORWARD_SHADOW.value)
    lv = LearningValueEngine().evaluate_evidence(record, outcome=outcome)
    engine = ControlledLearningEngine()
    request = engine.create_request(
        artifact_type=CandidateArtifactType.WEIGHTS,
        proposed_change={"weights_delta": {"layer_1": 0.01}},
        learning_value=lv,
        outcome=outcome,
        evidence_records=(record,),
    )
    result = engine.evaluate_request(request)
    assert request.artifact_type == CandidateArtifactType.WEIGHTS.value
    assert result.deployed is False


def test_temp_ar_0239_controlled_learning_promotion_gate_integration() -> None:
    from blackdark.temporal.controlled_learning import CandidateArtifactType
    from blackdark.temporal.evidence_class import TemporalEvidenceClass
    from blackdark.temporal.evidence_provenance import EvidenceProvenanceLedger

    outcome = _outcome(outcome_id="out-cl-2")
    ledger = EvidenceProvenanceLedger()
    record = _evidence(ledger, TemporalEvidenceClass.FORWARD_SHADOW.value)
    lv = LearningValueEngine().evaluate_evidence(record, outcome=outcome)
    engine = ControlledLearningEngine()
    request = engine.create_request(
        artifact_type=CandidateArtifactType.MODEL,
        proposed_change={"model_variant": "candidate-v2"},
        learning_value=lv,
        outcome=outcome,
        evidence_records=(record,),
    )
    result = engine.evaluate_request(request)
    assert result.promotion_gate_required is True
    assert result.deployed is False


def test_temp_ar_0313_drift_representativeness_invalidation_integration() -> None:
    from blackdark.temporal.p4_drift import P4DriftDimension, evaluate_p4_drift

    result = evaluate_p4_drift(
        baseline={P4DriftDimension.REPRESENTATIVENESS_INVALIDATION.value: "stable"},
        current={P4DriftDimension.REPRESENTATIVENESS_INVALIDATION.value: "broken"},
        historical_sample_scale=1_000_000,
    )
    assert result.representativeness_invalidated is True
    assert any(s.dimension.value == "representativeness_invalidation" for s in result.signals)


def test_temp_ar_0323_claim_strength_reduction_integration() -> None:
    from blackdark.temporal.contamination_registry import ContaminationRegistry

    registry = ContaminationRegistry()
    registry.record_exposure(
        dataset_id="ds-claim",
        window_start=T_START,
        window_end=T_START + timedelta(hours=1),
        purpose=ContaminationPurpose.EVALUATION,
    )
    gate = registry.check_evaluation_admission(
        dataset_id="ds-claim",
        window_start=T_START,
        window_end=T_START + timedelta(hours=1),
        fail_closed=False,
    )
    assert gate.claim_strength_reduction > 0


def test_temp_ar_0457_effective_independent_sample_count_integration() -> None:
    sampler = DependenceAwareSampler()
    dims = {"shared_event": True}
    cluster = dependence_cluster_key(event_family="fam-x", dimensions=dims)
    sampler.record_instance(
        case_id="c1",
        event_family="fam-x",
        dependence_cluster=cluster,
        dimensions=dims,
        overlap_factor=4.0,
    )
    sampler.record_instance(
        case_id="c2",
        event_family="fam-x",
        dependence_cluster=cluster,
        dimensions=dims,
        overlap_factor=4.0,
    )
    assert sampler.total_effective_independent() < sampler.total_raw_instances()


def test_temp_ar_0458_replay_fidelity_dimensions_visible_integration() -> None:
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
    event = CanonicalTemporalEvent(
        event_id="p4-evt-2",
        entity_key="asset-b",
        event_type="market.tick",
        payload={"price": "200"},
        observation=obs,
        provenance=ProvenanceMetadata(source="kraken", source_version="v1", dataset_version="ds-2"),
        record_version="1",
    )
    store = TemporalCanonicalEventStore([event])
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
    assert len(profile.dimensions) >= 1
    for dim_name, score in profile.dimensions.items():
        assert dim_name
        assert score is not None


def test_temp_ar_0459_experience_coverage_weak_dimensions_visible() -> None:
    vector = assess_experience_coverage(
        historical_span_ratio=0.2,
        regimes_observed={"bull": 1},
        event_families=["fam-only"],
        effective_independent_count=2.0,
        prediction_outcome_pairs=3,
        tail_events=0,
        total_events=10,
        assets=["BTC"],
        venues=["binance"],
        sources=["binance"],
        calibration_bins_covered=1,
        calibration_bins_total=10,
        failure_cases=0,
        replay_fidelity_score=0.4,
        forward_shadow_hours=1.0,
        forward_shadow_samples=2,
    )
    assert vector.composite_index is not None
    assert vector.calibration_coverage == 0.1
    assert vector.replay_fidelity_coverage == 0.4


def test_walk_forward_multi_fold_contamination_integration() -> None:
    from blackdark.temporal.contamination_registry import ContaminationRegistry

    registry = ContaminationRegistry()
    samples = [
        {"event_time": "2026-01-01T00:30:00Z", "value": 1.0},
        {"event_time": "2026-01-01T01:30:00Z", "value": 2.0},
        {"event_time": "2026-01-01T02:30:00Z", "value": 3.0},
        {"event_time": "2026-01-01T03:30:00Z", "value": 4.0},
        {"event_time": "2026-01-01T04:30:00Z", "value": 5.0},
        {"event_time": "2026-01-01T05:30:00Z", "value": 6.0},
    ]
    windows = generate_walk_forward_windows(
        dataset_id="ds-wf-p4",
        series_start="2026-01-01T00:00:00Z",
        series_end="2026-01-01T08:00:00Z",
        train_duration=timedelta(hours=2),
        eval_duration=timedelta(hours=1),
        step=timedelta(hours=1),
    )
    result = run_walk_forward_evaluation(
        dataset_id="ds-wf-p4",
        samples=samples,
        windows=windows,
        freeze=WalkForwardFreezeContext(
            model_version="m1",
            dataset_version="d1",
            config_version="c1",
            controls=(WalkForwardControl.PURGE,),
        ),
        contamination_registry=registry,
        evaluate_fold=lambda train, eval_set, freeze: {"train": len(train), "eval": len(eval_set)},
        fail_closed_on_contamination=True,
    )
    assert len(result.folds) == len(windows)
    assert all(f.contamination_checked for f in result.folds)
