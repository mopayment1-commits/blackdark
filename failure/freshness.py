"""Canonical data freshness model (ERR-011, ERR-038)."""

from __future__ import annotations

import time
from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class FreshnessState(StrEnum):
    LIVE = "LIVE"
    NEAR_LIVE = "NEAR_LIVE"
    DELAYED = "DELAYED"
    STALE = "STALE"
    CACHED = "CACHED"
    PARTIAL = "PARTIAL"
    UNKNOWN = "UNKNOWN"


@dataclass(slots=True)
class FreshnessEvidence:
    state: FreshnessState
    source_timestamp: float | None = None
    observed_at: float | None = None
    ingested_at: float | None = None
    last_successful_update: float | None = None
    age_seconds: float | None = None
    fallback_used: bool = False
    cache_disclosed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "state": self.state.value,
            "source_timestamp": self.source_timestamp,
            "observed_at": self.observed_at,
            "ingested_at": self.ingested_at,
            "last_successful_update": self.last_successful_update,
            "age_seconds": self.age_seconds,
            "fallback_used": self.fallback_used,
            "cache_disclosed": self.cache_disclosed,
        }


def classify_freshness(
    *,
    age_seconds: float | None = None,
    freshness_ms: float | None = None,
    cached: bool = False,
    partial: bool = False,
    fallback: bool = False,
) -> FreshnessEvidence:
    now = time.time()
    age: float | None = None
    if age_seconds is not None:
        age = float(age_seconds)
    elif freshness_ms is not None:
        age = float(freshness_ms) / 1000.0

    if partial:
        return FreshnessEvidence(
            state=FreshnessState.PARTIAL,
            observed_at=now,
            age_seconds=age,
            fallback_used=fallback,
            cache_disclosed=cached or fallback,
        )
    if cached or fallback:
        return FreshnessEvidence(
            state=FreshnessState.CACHED,
            observed_at=now,
            age_seconds=age,
            fallback_used=fallback,
            cache_disclosed=True,
        )
    if age is None:
        return FreshnessEvidence(state=FreshnessState.UNKNOWN, observed_at=now, cache_disclosed=False)
    if age <= 2.0:
        state = FreshnessState.LIVE
    elif age <= 15.0:
        state = FreshnessState.NEAR_LIVE
    elif age <= 60.0:
        state = FreshnessState.DELAYED
    else:
        state = FreshnessState.STALE
    return FreshnessEvidence(
        state=state,
        observed_at=now,
        age_seconds=round(age, 3),
        last_successful_update=now - age,
        cache_disclosed=False,
    )


def attach_freshness(payload: dict[str, Any]) -> dict[str, Any]:
    """Improve legacy data_freshness chip with canonical model."""
    out = dict(payload)
    ms = out.get("freshness_ms")
    age = out.get("data_age_sec") or out.get("quote_age_sec")
    chip = out.get("data_freshness") if isinstance(out.get("data_freshness"), dict) else {}
    if ms is None and chip:
        ms = chip.get("freshness_ms")
    if age is None and chip:
        age = chip.get("age_sec")
    evidence = classify_freshness(
        age_seconds=float(age) if age is not None else None,
        freshness_ms=float(ms) if ms is not None else None,
        cached=bool(out.get("from_cache")),
        partial=str(chip.get("state", "")).lower() == "partial",
        fallback=bool(out.get("fallback_used")),
    )
    out["freshness"] = evidence.to_dict()
    out["data_freshness"] = {
        **chip,
        "canonical_state": evidence.state.value,
        "age_sec": evidence.age_seconds,
        "cache_disclosed": evidence.cache_disclosed,
    }
    return out
