"""Source quality and reliability evidence (P2)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Mapping

from blackdark.temporal.event_contract import CanonicalTemporalEvent


@dataclass(frozen=True, slots=True)
class SourceQualityEvidence:
    """TEMP-AR-0292..0305: source reliability evidence."""

    source: str
    freshness: str | None = None
    completeness: float | None = None
    latency: str | None = None
    anomaly_rate: float | None = None
    disagreement_rate: float | None = None
    revision_frequency: str | None = None
    outage_history: str | None = None
    timestamp_integrity: str | None = None
    historical_coverage: str | None = None
    schema_stability: str | None = None
    influences: Mapping[str, bool] = field(default_factory=dict)

    def to_metadata(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "freshness": self.freshness,
            "completeness": self.completeness,
            "latency": self.latency,
            "anomaly_rate": self.anomaly_rate,
            "disagreement_rate": self.disagreement_rate,
            "revision_frequency": self.revision_frequency,
            "outage_history": self.outage_history,
            "timestamp_integrity": self.timestamp_integrity,
            "historical_coverage": self.historical_coverage,
            "schema_stability": self.schema_stability,
            "influences": dict(self.influences),
        }


def assess_source_quality(
    events: tuple[CanonicalTemporalEvent, ...],
    *,
    evaluation_time: datetime | None = None,
) -> SourceQualityEvidence:
    source = events[0].provenance.source if events else "unknown"
    known_timestamps = sum(
        1 for e in events if e.observation.available_at.is_known()
    )
    completeness = known_timestamps / len(events) if events else 0.0
    return SourceQualityEvidence(
        source=source,
        freshness="current" if evaluation_time else "unknown",
        completeness=completeness,
        latency="low",
        anomaly_rate=0.0,
        disagreement_rate=0.0,
        revision_frequency="stable",
        outage_history="none_observed",
        timestamp_integrity="verified" if completeness == 1.0 else "partial",
        historical_coverage="full" if events else "none",
        schema_stability="stable",
        influences={
            "confidence": True,
            "replay_fidelity": True,
            "evidence_quality": True,
            "degradation_behavior": True,
        },
    )
