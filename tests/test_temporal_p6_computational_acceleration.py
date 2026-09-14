"""P6 Computational Acceleration tests — TEMP-AR-0338..0351."""

from __future__ import annotations

import time
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
)
from blackdark.temporal.computational_acceleration import (
    AccelerationCache,
    AccelerationStrategy,
    ColumnarPartition,
    WorkloadPrioritizer,
    create_immutable_snapshot,
    prune_partitions,
    run_event_based_replay_accelerated,
    run_parallel_tasks,
    store_intermediate_artifact,
    validate_acceleration_guards,
)
from blackdark.temporal.evidence_class import TemporalEvidenceClass

T_START = datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC)


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


def test_temp_ar_0338_feature_caching() -> None:
    cache = AccelerationCache()
    key = cache.build_key(strategy=AccelerationStrategy.FEATURE_CACHING, payload={"feature": "x"})
    cache.put(key, {"value": 1}, provenance_metadata={"source": "binance"})
    assert cache.get(key) is not None


def test_temp_ar_0339_immutable_feature_snapshots() -> None:
    snap = create_immutable_snapshot(
        snapshot_id="snap-1",
        features={"rsi": 55.0},
        source_version="v1",
    )
    assert snap.to_metadata()["immutable"] is True


def test_temp_ar_0340_incremental_recomputation() -> None:
    from blackdark.temporal.computational_acceleration import IncrementalRecomputePlan

    plan = IncrementalRecomputePlan(
        base_snapshot_id="snap-1",
        delta_event_ids=("evt-2",),
        recompute_from=T_START,
    )
    assert plan.delta_event_ids == ("evt-2",)


def test_temp_ar_0341_columnar_storage() -> None:
    part = ColumnarPartition(partition_key="2026-01", column_family="features", row_count=100)
    assert part.column_family == "features"


def test_temp_ar_0342_partition_pruning() -> None:
    parts = (
        ColumnarPartition("2026-01", "features", 100),
        ColumnarPartition("2026-02", "features", 50),
    )
    pruned = prune_partitions(parts, required_keys=("2026-01",))
    assert any(p.pruned for p in pruned)
    assert any(not p.pruned for p in pruned)


def test_temp_ar_0343_event_based_replay() -> None:
    store = TemporalCanonicalEventStore([_event("evt-1")])
    replay = run_event_based_replay_accelerated(
        event_source=store,
        request=ReplayRequest(
            event_source=store,
            start_time=T_START,
            end_time=T_START + timedelta(hours=4),
            replay_clock_or_schedule=(T_START + timedelta(hours=2),),
            strict_mode=True,
        ),
    )
    assert replay.success is True


def test_temp_ar_0344_parallel_execution() -> None:
    results = run_parallel_tasks(
        {
            "a": lambda: 1,
            "b": lambda: 2,
        }
    )
    assert results["a"] == 1 and results["b"] == 2


def test_temp_ar_0345_reusable_intermediate_artifacts() -> None:
    artifacts: dict[str, object] = {}
    aid = store_intermediate_artifact(
        artifacts,
        artifact_id="art-1",
        payload={"matrix": [[1, 2]]},
        provenance={"source": "replay"},
    )
    assert aid in artifacts


def test_temp_ar_0346_workload_prioritization() -> None:
    prioritizer = WorkloadPrioritizer()
    prioritizer.submit(1, "low", lambda: "low")
    prioritizer.submit(10, "high", lambda: "high")
    results = prioritizer.execute_ordered()
    assert results[0][0] == "high"


def test_temp_ar_0347_deterministic_cache_keys() -> None:
    cache = AccelerationCache()
    k1 = cache.build_key(strategy=AccelerationStrategy.FEATURE_CACHING, payload={"x": 1})
    k2 = cache.build_key(strategy=AccelerationStrategy.FEATURE_CACHING, payload={"x": 1})
    assert k1.key == k2.key


def test_temp_ar_0348_provenance_not_weakened() -> None:
    cache = AccelerationCache()
    key = cache.build_key(strategy=AccelerationStrategy.FEATURE_CACHING, payload={"x": 1})
    with pytest.raises(ValueError, match="provenance_metadata_required"):
        cache.put(key, 1, provenance_metadata={})
    cache.put(key, 1, provenance_metadata={"source": "binance"})
    guards = validate_acceleration_guards(
        cache=cache,
        evidence_class=TemporalEvidenceClass.HISTORICAL_REPLAY.value,
    )
    assert guards.provenance_preserved is True


def test_temp_ar_0349_temporal_integrity_not_weakened() -> None:
    cache = AccelerationCache()
    guards = validate_acceleration_guards(
        cache=cache,
        evidence_class=TemporalEvidenceClass.HISTORICAL_REPLAY.value,
        strict_mode=True,
    )
    assert guards.temporal_integrity_preserved is True
    bad = validate_acceleration_guards(
        cache=cache,
        evidence_class=TemporalEvidenceClass.HISTORICAL_REPLAY.value,
        strict_mode=False,
    )
    assert bad.temporal_integrity_preserved is False


def test_temp_ar_0350_reproducibility_not_weakened() -> None:
    cache = AccelerationCache()
    guards = validate_acceleration_guards(
        cache=cache,
        evidence_class=TemporalEvidenceClass.HISTORICAL_REPLAY.value,
        skip_replay_validation=True,
    )
    assert guards.reproducibility_preserved is False


def test_temp_ar_0351_evidence_classification_not_weakened() -> None:
    cache = AccelerationCache()
    guards = validate_acceleration_guards(
        cache=cache,
        evidence_class=TemporalEvidenceClass.HISTORICAL_REPLAY.value,
    )
    assert guards.evidence_classification_preserved is True


def test_temp_ar_0344_parallel_execution_performance() -> None:
    def slow() -> int:
        time.sleep(0.05)
        return 1

    start = time.perf_counter()
    run_parallel_tasks({"a": slow, "b": slow}, max_workers=2)
    elapsed = time.perf_counter() - start
    assert elapsed < 0.15
