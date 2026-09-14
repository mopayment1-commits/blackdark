"""Dependence-aware evaluation sampling (P4 / TEMP-AR-0073..0085, 0457)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Sequence


DEPENDENCE_AWARE_SAMPLING_CONTRACT_VERSION = "p4.dependence.1.0"
EVALUATION_INSTANCES_NOT_AUTO_INDEPENDENT = True


class DependenceDimension(str, Enum):
    TEMPORAL_OVERLAP = "temporal_overlap"
    SHARED_EVENT = "shared_event"
    ASSET_CORRELATION = "asset_correlation"
    SHARED_LABEL = "shared_label"
    SHARED_REGIME = "shared_regime"
    SHARED_SOURCE_DEPENDENCY = "shared_source_dependency"
    SHARED_MODEL_FAMILY = "shared_model_family"


@dataclass(frozen=True, slots=True)
class DependenceRecord:
    case_id: str
    event_family: str
    dependence_cluster: str
    dimensions: Mapping[str, Any]
    raw_instance_count: int
    effective_independent_count: float

    def to_metadata(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "event_family": self.event_family,
            "dependence_cluster": self.dependence_cluster,
            "dimensions": dict(self.dimensions),
            "raw_instance_count": self.raw_instance_count,
            "effective_independent_count": self.effective_independent_count,
        }


@dataclass
class DependenceAwareSampler:
    """Track evaluation instances with dependence metadata."""

    _records: list[DependenceRecord] = field(default_factory=list)

    def record_instance(
        self,
        *,
        case_id: str,
        event_family: str,
        dependence_cluster: str,
        dimensions: Mapping[str, Any],
        overlap_factor: float = 1.0,
    ) -> DependenceRecord:
        cluster_size = sum(
            1 for r in self._records if r.dependence_cluster == dependence_cluster
        ) + 1
        effective = compute_effective_independent_count(
            raw_count=cluster_size,
            overlap_factor=overlap_factor,
            dimensions=dimensions,
        )
        record = DependenceRecord(
            case_id=case_id,
            event_family=event_family,
            dependence_cluster=dependence_cluster,
            dimensions=dict(dimensions),
            raw_instance_count=cluster_size,
            effective_independent_count=effective,
        )
        self._records.append(record)
        return record

    def list_records(self) -> tuple[DependenceRecord, ...]:
        return tuple(self._records)

    def total_raw_instances(self) -> int:
        return len(self._records)

    def total_effective_independent(self) -> float:
        clusters: dict[str, float] = {}
        for record in self._records:
            clusters[record.dependence_cluster] = record.effective_independent_count
        return sum(clusters.values())


def compute_effective_independent_count(
    *,
    raw_count: int,
    overlap_factor: float,
    dimensions: Mapping[str, Any],
) -> float:
    """Down-weight correlated instances; never treat raw count as fully independent."""
    if raw_count <= 0:
        return 0.0
    active_dims = sum(1 for dim in DependenceDimension if dimensions.get(dim.value))
    penalty = 1.0 + (active_dims * 0.15) + max(0.0, overlap_factor - 1.0)
    return max(1.0, raw_count / penalty)


def dependence_cluster_key(*, event_family: str, dimensions: Mapping[str, Any]) -> str:
    payload = {"event_family": event_family, "dimensions": dict(dimensions)}
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]
