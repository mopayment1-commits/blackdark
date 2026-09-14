"""Replay fidelity profile dimensions (P4 / TEMP-AR-0203..0213, 0454, 0458)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping

from blackdark.temporal.replay import ReplayResult

REPLAY_FIDELITY_CONTRACT_VERSION = "p4.replay_fidelity.1.0"


class ReplayFidelityDimension(str, Enum):
    TEMPORAL = "temporal_fidelity"
    SOURCE_COVERAGE = "source_coverage"
    SOURCE_COMPLETENESS = "source_completeness"
    ORDER_BOOK_DEPTH = "order_book_depth_fidelity"
    LATENCY = "latency_fidelity"
    TRANSACTION_COST = "transaction_cost_fidelity"
    REVISION_INTEGRITY = "revision_integrity"
    VENUE_AVAILABILITY = "venue_availability"
    PROVENANCE_COMPLETENESS = "provenance_completeness"
    RIGHTS_COMPLETENESS = "rights_completeness"


@dataclass(frozen=True, slots=True)
class ReplayFidelityProfile:
    dimensions: Mapping[str, float]
    composite_score: float | None
    replay_id: str
    evidence_class: str

    def to_metadata(self) -> dict[str, Any]:
        return {
            "dimensions": dict(self.dimensions),
            "composite_score": self.composite_score,
            "replay_id": self.replay_id,
            "evidence_class": self.evidence_class,
        }


def assess_replay_fidelity(
    replay: ReplayResult,
    *,
    source_coverage: float = 1.0,
    source_completeness: float = 1.0,
    order_book_depth: float = 1.0,
    latency_fidelity: float = 1.0,
    transaction_cost_fidelity: float = 1.0,
    revision_integrity: float = 1.0,
    venue_availability: float = 1.0,
    provenance_completeness: float = 1.0,
    rights_completeness: float = 1.0,
) -> ReplayFidelityProfile:
    temporal = 1.0 if replay.success and replay.rejected_event_count == 0 else 0.5
    dimensions = {
        ReplayFidelityDimension.TEMPORAL.value: temporal,
        ReplayFidelityDimension.SOURCE_COVERAGE.value: source_coverage,
        ReplayFidelityDimension.SOURCE_COMPLETENESS.value: source_completeness,
        ReplayFidelityDimension.ORDER_BOOK_DEPTH.value: order_book_depth,
        ReplayFidelityDimension.LATENCY.value: latency_fidelity,
        ReplayFidelityDimension.TRANSACTION_COST.value: transaction_cost_fidelity,
        ReplayFidelityDimension.REVISION_INTEGRITY.value: revision_integrity,
        ReplayFidelityDimension.VENUE_AVAILABILITY.value: venue_availability,
        ReplayFidelityDimension.PROVENANCE_COMPLETENESS.value: provenance_completeness,
        ReplayFidelityDimension.RIGHTS_COMPLETENESS.value: rights_completeness,
    }
    composite = sum(dimensions.values()) / len(dimensions)
    return ReplayFidelityProfile(
        dimensions=dimensions,
        composite_score=composite,
        replay_id=replay.replay_id,
        evidence_class=replay.evidence_class,
    )
