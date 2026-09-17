"""
Launch-57 canonical #41 freshness assurance owner.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from launch57.temporal_common import (
    AvailabilityState,
    TemporalEnvelope,
    parse_rfc3339,
    to_rfc3339,
    utc_now,
    validate_provider_timestamp,
)


class FreshnessState(str, Enum):
    LIVE = "LIVE"
    NEAR_LIVE = "NEAR_LIVE"
    DELAYED = "DELAYED"
    STALE = "STALE"
    UNKNOWN = "UNKNOWN"


# Explicit capability thresholds (seconds) — T0 market quote class.
THRESHOLD_LIVE_SEC = 5.0
THRESHOLD_NEAR_LIVE_SEC = 15.0
THRESHOLD_DELAYED_SEC = 60.0

_LIVE_PRESENTATION_ELIGIBLE = frozenset(
    {
        FreshnessState.LIVE.value,
        FreshnessState.NEAR_LIVE.value,
        FreshnessState.DELAYED.value,
    }
)


@dataclass(frozen=True)
class FreshnessEvidence:
    age_sec: float | None
    source_time: str | None
    observed_at: str
    ingested_at: str
    available_at: str | None
    availability_state: AvailabilityState
    source_validation_ok: bool
    thresholds_sec: dict[str, float]

    def to_dict(self) -> dict[str, Any]:
        return {
            "age_sec": self.age_sec,
            "source_time": self.source_time,
            "observed_at": self.observed_at,
            "ingested_at": self.ingested_at,
            "available_at": self.available_at,
            "availability_state": self.availability_state.value,
            "source_validation_ok": self.source_validation_ok,
            "thresholds_sec": self.thresholds_sec,
            "owner": "launch57.freshness_common",
        }


@dataclass(frozen=True)
class FreshnessAssessment:
    freshness_state: FreshnessState
    presented_as_live: bool
    delayed_label: str | None
    evidence: FreshnessEvidence
    success: bool
    error: str | None = None

    def to_payload(self) -> dict[str, Any]:
        return {
            "freshness_state": self.freshness_state.value,
            "presented_as_live": self.presented_as_live,
            "delayed_label": self.delayed_label,
            "freshness_evidence": self.evidence.to_dict(),
            "freshness_owner": "launch57.freshness_common",
            "freshness_launch_item_id": 41,
            "success": self.success,
            "error": self.error,
            "policy": "stale_or_unknown_never_passes_as_live",
        }


def _classify_age(age_sec: float | None) -> FreshnessState:
    if age_sec is None:
        return FreshnessState.UNKNOWN
    if age_sec <= THRESHOLD_LIVE_SEC:
        return FreshnessState.LIVE
    if age_sec <= THRESHOLD_NEAR_LIVE_SEC:
        return FreshnessState.NEAR_LIVE
    if age_sec <= THRESHOLD_DELAYED_SEC:
        return FreshnessState.DELAYED
    return FreshnessState.STALE


def _delayed_label(state: FreshnessState) -> str | None:
    if state == FreshnessState.DELAYED:
        return "DELAYED — within SLO tolerance; not presented as LIVE"
    if state == FreshnessState.STALE:
        return "STALE — not presented as real-time"
    if state == FreshnessState.UNKNOWN:
        return "UNKNOWN — freshness not asserted as LIVE"
    return None


def assess_freshness(
    *,
    age_sec: float | None = None,
    source_time: Any = None,
    observed_at: str | None = None,
    ingested_at: str | None = None,
    available_at: str | None = None,
    availability_state: str | None = None,
    quote_fresh: bool | None = None,
) -> FreshnessAssessment:
    """Canonical #41 freshness from temporal evidence only — never fabricates available_at."""
    now = utc_now()
    observed = observed_at or to_rfc3339(now)
    ingested = ingested_at or observed

    source_validation = validate_provider_timestamp(source_time) if source_time is not None else None
    if source_time is not None and source_validation and not source_validation.ok:
        evidence = FreshnessEvidence(
            age_sec=age_sec,
            source_time=str(source_time),
            observed_at=observed,
            ingested_at=ingested,
            available_at=None,
            availability_state=AvailabilityState.UNKNOWN,
            source_validation_ok=False,
            thresholds_sec={
                "live": THRESHOLD_LIVE_SEC,
                "near_live": THRESHOLD_NEAR_LIVE_SEC,
                "delayed": THRESHOLD_DELAYED_SEC,
            },
        )
        return FreshnessAssessment(
            freshness_state=FreshnessState.UNKNOWN,
            presented_as_live=False,
            delayed_label="UNKNOWN — invalid provider timestamp",
            evidence=evidence,
            success=False,
            error=f"provider_timestamp_invalid:{source_validation.error}",
        )

    if availability_state in {s.value for s in AvailabilityState}:
        avail_state = AvailabilityState(availability_state)
    elif available_at:
        avail_state = AvailabilityState.KNOWN
    elif age_sec is not None:
        # Observed quote age is temporal evidence; does not fabricate available_at.
        avail_state = AvailabilityState.KNOWN
    else:
        avail_state = AvailabilityState.UNKNOWN
    if avail_state == AvailabilityState.UNKNOWN and age_sec is None:
        state = FreshnessState.UNKNOWN
    else:
        state = _classify_age(age_sec)

    presented = state.value in _LIVE_PRESENTATION_ELIGIBLE and avail_state == AvailabilityState.KNOWN
    if quote_fresh is False:
        presented = False

    evidence = FreshnessEvidence(
        age_sec=age_sec,
        source_time=to_rfc3339(source_validation.canonical) if source_validation and source_validation.canonical else None,
        observed_at=observed,
        ingested_at=ingested,
        available_at=available_at,
        availability_state=avail_state,
        source_validation_ok=source_validation.ok if source_validation else age_sec is not None,
        thresholds_sec={
            "live": THRESHOLD_LIVE_SEC,
            "near_live": THRESHOLD_NEAR_LIVE_SEC,
            "delayed": THRESHOLD_DELAYED_SEC,
        },
    )
    success = presented and state != FreshnessState.STALE
    error = None if success else "freshness_not_live_eligible"
    return FreshnessAssessment(
        freshness_state=state,
        presented_as_live=presented,
        delayed_label=_delayed_label(state),
        evidence=evidence,
        success=success,
        error=error,
    )
