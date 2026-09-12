"""Data quality degradation — DSR-017, D-14."""

from __future__ import annotations

from typing import Any

from blackdark.data.response_metadata import (
    DATA_STATE_LIVE,
    DATA_STATE_MISSING,
    DATA_STATE_STALE,
    DATA_STATE_UNKNOWN,
    resolve_data_state,
)


def apply_quality_to_confidence(
    *,
    base_confidence: float,
    data_state: str,
    data_state_reason: str | None = None,
) -> dict[str, Any]:
    """Quality failure must affect availability/confidence — no silent stale data."""
    if data_state == DATA_STATE_LIVE:
        return {
            "confidence": base_confidence,
            "availability": "full",
            "degraded": False,
            "data_state": data_state,
        }
    if data_state == DATA_STATE_STALE:
        return {
            "confidence": min(base_confidence, 0.3),
            "availability": "degraded_stale",
            "degraded": True,
            "data_state": data_state,
            "reason": data_state_reason,
            "policy": "stale_not_live_intelligence",
        }
    if data_state == DATA_STATE_MISSING:
        return {
            "confidence": 0.0,
            "availability": "unavailable",
            "degraded": True,
            "data_state": data_state,
            "reason": data_state_reason,
            "policy": "missing_not_zero_success",
        }
    if data_state == DATA_STATE_UNKNOWN:
        return {
            "confidence": 0.0,
            "availability": "unknown_upstream",
            "degraded": True,
            "data_state": data_state,
            "reason": data_state_reason,
            "policy": "unknown_not_live",
        }
    return {"confidence": 0.0, "availability": "blocked", "degraded": True, "data_state": data_state}


def evaluate_dataset_quality(
    *,
    count: int,
    dataset: str,
    latest_record_at: str | None = None,
    upstream_unknown: bool = False,
) -> dict[str, Any]:
    state, reason = resolve_data_state(
        count=count,
        dataset=dataset,
        latest_record_at=latest_record_at,
        upstream_unknown=upstream_unknown,
    )
    return apply_quality_to_confidence(base_confidence=1.0, data_state=state, data_state_reason=reason)
