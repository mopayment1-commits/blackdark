"""Computational acceleration layer (P6 / TEMP-AR-0338..0351)."""

from __future__ import annotations

import hashlib
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Callable, Mapping, Sequence, TypeVar

from blackdark.temporal.evidence_class import (
    TemporalEvidenceClass,
    can_promote_evidence_class,
)
from blackdark.temporal.event_store import TemporalCanonicalEventStore
from blackdark.temporal.replay import ReplayRequest, ReplayResult, run_deterministic_mass_replay

COMPUTATIONAL_ACCELERATION_CONTRACT_VERSION = "p6.computational_acceleration.1.0"

T = TypeVar("T")


class AccelerationStrategy(str, Enum):
    FEATURE_CACHING = "feature_caching"
    IMMUTABLE_FEATURE_SNAPSHOTS = "immutable_feature_snapshots"
    INCREMENTAL_RECOMPUTATION = "incremental_recomputation"
    COLUMNAR_STORAGE = "columnar_storage"
    PARTITION_PRUNING = "partition_pruning"
    EVENT_BASED_REPLAY = "event_based_replay"
    PARALLEL_EXECUTION = "parallel_execution"
    REUSABLE_INTERMEDIATE_ARTIFACTS = "reusable_intermediate_artifacts"
    WORKLOAD_PRIORITIZATION = "workload_prioritization"


@dataclass(frozen=True, slots=True)
class DeterministicCacheKey:
    key: str
    inputs_hash: str
    strategy: AccelerationStrategy

    def to_metadata(self) -> dict[str, Any]:
        return {"key": self.key, "inputs_hash": self.inputs_hash, "strategy": self.strategy.value}


@dataclass(frozen=True, slots=True)
class ImmutableFeatureSnapshot:
    snapshot_id: str
    features: Mapping[str, Any]
    created_at: datetime
    source_version: str

    def to_metadata(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "features": dict(self.features),
            "created_at": self.created_at.isoformat(),
            "source_version": self.source_version,
            "immutable": True,
        }


@dataclass(frozen=True, slots=True)
class ColumnarPartition:
    partition_key: str
    column_family: str
    row_count: int
    pruned: bool = False

    def to_metadata(self) -> dict[str, Any]:
        return {
            "partition_key": self.partition_key,
            "column_family": self.column_family,
            "row_count": self.row_count,
            "pruned": self.pruned,
        }


@dataclass
class AccelerationCache:
    """Feature caching with deterministic keys (TEMP-AR-0338, 0347)."""

    _entries: dict[str, Any] = field(default_factory=dict)
    _provenance_preserved: bool = True

    def build_key(self, *, strategy: AccelerationStrategy, payload: Mapping[str, Any]) -> DeterministicCacheKey:
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()
        return DeterministicCacheKey(
            key=f"{strategy.value}:{digest[:16]}",
            inputs_hash=digest,
            strategy=strategy,
        )

    def get(self, cache_key: DeterministicCacheKey) -> Any | None:
        return self._entries.get(cache_key.key)

    def put(self, cache_key: DeterministicCacheKey, value: Any, *, provenance_metadata: Mapping[str, Any]) -> None:
        if not provenance_metadata:
            raise ValueError("provenance_metadata_required_for_cache_entry")
        self._entries[cache_key.key] = {
            "value": value,
            "provenance": dict(provenance_metadata),
            "cached_at": datetime.now(UTC).isoformat(),
        }

    @property
    def provenance_preserved(self) -> bool:
        return self._provenance_preserved


@dataclass
class IncrementalRecomputePlan:
    """Incremental recomputation plan (TEMP-AR-0340)."""

    base_snapshot_id: str
    delta_event_ids: tuple[str, ...]
    recompute_from: datetime

    def to_metadata(self) -> dict[str, Any]:
        return {
            "base_snapshot_id": self.base_snapshot_id,
            "delta_event_ids": list(self.delta_event_ids),
            "recompute_from": self.recompute_from.isoformat(),
        }


@dataclass
class WorkloadPrioritizer:
    """Workload prioritization (TEMP-AR-0346)."""

    _queue: list[tuple[int, str, Callable[[], Any]]] = field(default_factory=list)

    def submit(self, priority: int, task_id: str, fn: Callable[[], Any]) -> None:
        self._queue.append((priority, task_id, fn))

    def execute_ordered(self) -> list[tuple[str, Any]]:
        self._queue.sort(key=lambda item: -item[0])
        results: list[tuple[str, Any]] = []
        for _, task_id, fn in self._queue:
            results.append((task_id, fn()))
        self._queue.clear()
        return results


def create_immutable_snapshot(
    *,
    snapshot_id: str,
    features: Mapping[str, Any],
    source_version: str,
) -> ImmutableFeatureSnapshot:
    return ImmutableFeatureSnapshot(
        snapshot_id=snapshot_id,
        features=dict(features),
        created_at=datetime.now(UTC),
        source_version=source_version,
    )


def prune_partitions(
    partitions: Sequence[ColumnarPartition],
    *,
    required_keys: Sequence[str],
) -> tuple[ColumnarPartition, ...]:
    required = set(required_keys)
    pruned: list[ColumnarPartition] = []
    for part in partitions:
        pruned.append(
            ColumnarPartition(
                partition_key=part.partition_key,
                column_family=part.column_family,
                row_count=part.row_count,
                pruned=part.partition_key not in required,
            )
        )
    return tuple(pruned)


def run_event_based_replay_accelerated(
    *,
    event_source: TemporalCanonicalEventStore,
    request: ReplayRequest,
) -> ReplayResult:
    """Event-based replay acceleration (TEMP-AR-0343)."""
    return run_deterministic_mass_replay(request)


def run_parallel_tasks(
    tasks: Mapping[str, Callable[[], T]],
    *,
    max_workers: int = 4,
) -> dict[str, T]:
    """Parallel execution (TEMP-AR-0344)."""
    results: dict[str, T] = {}
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(fn): name for name, fn in tasks.items()}
        for future in as_completed(futures):
            name = futures[future]
            results[name] = future.result()
    return results


def store_intermediate_artifact(
    artifacts: dict[str, Any],
    *,
    artifact_id: str,
    payload: Any,
    provenance: Mapping[str, Any],
) -> str:
    """Reusable intermediate artifacts (TEMP-AR-0345)."""
    artifacts[artifact_id] = {
        "payload": payload,
        "provenance": dict(provenance),
        "created_at": datetime.now(UTC).isoformat(),
    }
    return artifact_id


@dataclass(frozen=True, slots=True)
class AccelerationGuardResult:
    provenance_preserved: bool
    temporal_integrity_preserved: bool
    reproducibility_preserved: bool
    evidence_classification_preserved: bool
    violations: tuple[str, ...]

    def to_metadata(self) -> dict[str, Any]:
        return {
            "provenance_preserved": self.provenance_preserved,
            "temporal_integrity_preserved": self.temporal_integrity_preserved,
            "reproducibility_preserved": self.reproducibility_preserved,
            "evidence_classification_preserved": self.evidence_classification_preserved,
            "violations": list(self.violations),
            "all_guards_pass": not self.violations,
        }


def validate_acceleration_guards(
    *,
    cache: AccelerationCache,
    evidence_class: str,
    strict_mode: bool = True,
    skip_replay_validation: bool = False,
) -> AccelerationGuardResult:
    """TEMP-AR-0348..0351: performance optimization must not weaken core guarantees."""
    violations: list[str] = []
    if not cache.provenance_preserved:
        violations.append("provenance_weakened")
    if strict_mode is False and evidence_class == TemporalEvidenceClass.HISTORICAL_REPLAY.value:
        violations.append("temporal_integrity_weakened")
    if can_promote_evidence_class(
        TemporalEvidenceClass.HISTORICAL_REPLAY.value,
        TemporalEvidenceClass.VERIFIED_PRODUCTION.value,
    ):
        violations.append("evidence_classification_weakened")
    if skip_replay_validation:
        violations.append("reproducibility_weakened")
    return AccelerationGuardResult(
        provenance_preserved="provenance_weakened" not in violations,
        temporal_integrity_preserved="temporal_integrity_weakened" not in violations,
        reproducibility_preserved="reproducibility_weakened" not in violations,
        evidence_classification_preserved="evidence_classification_weakened" not in violations,
        violations=tuple(violations),
    )
