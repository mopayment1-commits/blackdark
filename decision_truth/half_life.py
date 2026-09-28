"""Opportunity Half-Life integration for Decision Truth (DTS-015)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

METHODOLOGY_VERSION = "dts-p2-half-life-1.0"
MIN_SAMPLES_FOR_CONFIDENT_ESTIMATE = 3


def _utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def evaluate_opportunity_half_life(payload: dict[str, Any], *, asset: str | None = None) -> dict[str, Any]:
    """Attach governed half-life contract; separate local engineering from live validation."""
    out = dict(payload)
    sym = str(asset or out.get("symbol") or out.get("asset") or "BTC").upper()
    kind = str(out.get("kind") or "cross_exchange")

    try:
        from opportunity_tracker import estimate_opportunity_half_life, half_life_sample_count

        sample_count = half_life_sample_count(kind=kind, asset=sym)
        hl = estimate_opportunity_half_life(out, live_duration_seconds=out.get("live_duration_seconds"))
        has_live = out.get("live_duration_seconds") is not None or out.get("quote_age_ms") is not None
        if sample_count < MIN_SAMPLES_FOR_CONFIDENT_ESTIMATE and not has_live:
            contract = {
                "state": "HALF_LIFE_UNAVAILABLE",
                "reason": "insufficient_half_life_evidence",
                "asset": sym,
                "kind": kind,
                "sample_count": sample_count,
                "methodology_version": METHODOLOGY_VERSION,
                "timestamp_utc": _utc_now(),
                "local_engineering": "LOCAL_ENGINEERING_COMPLETE",
                "live_validation": "LIVE_VALIDATION_PENDING",
            }
        else:
            contract = {
                "state": "AVAILABLE",
                "expected_half_life_seconds": hl.get("expected_half_life_seconds"),
                "remaining_seconds": hl.get("remaining_seconds"),
                "disappearance_probability": hl.get("disappearance_probability"),
                "urgency": hl.get("urgency"),
                "model": hl.get("model"),
                "asset": sym,
                "kind": kind,
                "sample_count": sample_count,
                "methodology_version": METHODOLOGY_VERSION,
                "timestamp_utc": _utc_now(),
                "local_engineering": "LOCAL_ENGINEERING_COMPLETE",
                "live_validation": "LIVE_VALIDATION_PENDING",
            }
        out["opportunity_half_life"] = contract
        return out
    except Exception as exc:
        out["opportunity_half_life"] = {
            "state": "HALF_LIFE_UNAVAILABLE",
            "reason": f"half_life_engine_error:{exc}",
            "asset": sym,
            "methodology_version": METHODOLOGY_VERSION,
            "timestamp_utc": _utc_now(),
            "local_engineering": "LOCAL_ENGINEERING_COMPLETE",
            "live_validation": "LIVE_VALIDATION_PENDING",
        }
        return out


def attach_half_life(payload: dict[str, Any], *, asset: str | None = None) -> dict[str, Any]:
    """Backward-compatible alias."""
    return evaluate_opportunity_half_life(payload, asset=asset)
