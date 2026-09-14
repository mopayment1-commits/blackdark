"""Experience coverage vector tracking (P4 / TEMP-AR-0214..0229, 0459)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

EXPERIENCE_COVERAGE_CONTRACT_VERSION = "p4.experience_coverage.1.0"
ELAPSED_TIME_ALONE_PROXY_PROHIBITED = True


@dataclass(frozen=True, slots=True)
class ExperienceCoverageVector:
    historical_span_coverage: float
    regime_coverage: Mapping[str, float]
    independent_event_families: int
    effective_independent_sample_count: float
    prediction_outcome_pairs: int
    tail_event_coverage: float
    asset_coverage: Mapping[str, float]
    venue_coverage: Mapping[str, float]
    source_diversity: float
    calibration_coverage: float
    failure_corpus_coverage: float
    replay_fidelity_coverage: float
    forward_shadow_duration_hours: float
    forward_shadow_sample_count: int
    composite_index: float | None
    elapsed_time_proxy_used: bool = False

    def to_metadata(self) -> dict[str, Any]:
        return {
            "historical_span_coverage": self.historical_span_coverage,
            "regime_coverage": dict(self.regime_coverage),
            "independent_event_families": self.independent_event_families,
            "effective_independent_sample_count": self.effective_independent_sample_count,
            "prediction_outcome_pairs": self.prediction_outcome_pairs,
            "tail_event_coverage": self.tail_event_coverage,
            "asset_coverage": dict(self.asset_coverage),
            "venue_coverage": dict(self.venue_coverage),
            "source_diversity": self.source_diversity,
            "calibration_coverage": self.calibration_coverage,
            "failure_corpus_coverage": self.failure_corpus_coverage,
            "replay_fidelity_coverage": self.replay_fidelity_coverage,
            "forward_shadow_duration_hours": self.forward_shadow_duration_hours,
            "forward_shadow_sample_count": self.forward_shadow_sample_count,
            "composite_index": self.composite_index,
            "elapsed_time_proxy_used": self.elapsed_time_proxy_used,
        }


def assess_experience_coverage(
    *,
    historical_span_ratio: float,
    regimes_observed: Mapping[str, int],
    event_families: Sequence[str],
    effective_independent_count: float,
    prediction_outcome_pairs: int,
    tail_events: int,
    total_events: int,
    assets: Sequence[str],
    venues: Sequence[str],
    sources: Sequence[str],
    calibration_bins_covered: int,
    calibration_bins_total: int,
    failure_cases: int,
    replay_fidelity_score: float,
    forward_shadow_hours: float,
    forward_shadow_samples: int,
    elapsed_days: float | None = None,
) -> ExperienceCoverageVector:
    """Build multi-dimensional experience coverage; elapsed time is never sole proxy."""
    regime_cov = {
        regime: min(1.0, count / max(total_events, 1))
        for regime, count in regimes_observed.items()
    }
    asset_cov = {asset: 1.0 for asset in assets}
    venue_cov = {venue: 1.0 for venue in venues}
    source_diversity = min(1.0, len(set(sources)) / max(len(sources), 1))
    tail_cov = min(1.0, tail_events / max(total_events, 1))
    cal_cov = (
        calibration_bins_covered / calibration_bins_total
        if calibration_bins_total > 0
        else 0.0
    )
    failure_cov = min(1.0, failure_cases / max(prediction_outcome_pairs, 1))
    components = [
        historical_span_ratio,
        sum(regime_cov.values()) / max(len(regime_cov), 1),
        min(1.0, len(event_families) / 10.0),
        min(1.0, effective_independent_count / max(prediction_outcome_pairs, 1)),
        tail_cov,
        source_diversity,
        cal_cov,
        failure_cov,
        replay_fidelity_score,
    ]
    composite = sum(components) / len(components)
    return ExperienceCoverageVector(
        historical_span_coverage=historical_span_ratio,
        regime_coverage=regime_cov,
        independent_event_families=len(set(event_families)),
        effective_independent_sample_count=effective_independent_count,
        prediction_outcome_pairs=prediction_outcome_pairs,
        tail_event_coverage=tail_cov,
        asset_coverage=asset_cov,
        venue_coverage=venue_cov,
        source_diversity=source_diversity,
        calibration_coverage=cal_cov,
        failure_corpus_coverage=failure_cov,
        replay_fidelity_coverage=replay_fidelity_score,
        forward_shadow_duration_hours=forward_shadow_hours,
        forward_shadow_sample_count=forward_shadow_samples,
        composite_index=composite,
        elapsed_time_proxy_used=False if elapsed_days is None else False,
    )
