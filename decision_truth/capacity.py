"""Opportunity Capacity estimator (DTS-014)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

METHODOLOGY_VERSION = "dts-p2-capacity-1.0"


def _utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _optional_float(raw: Any) -> float | None:
    if raw is None:
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def estimate_opportunity_capacity(opportunity: dict[str, Any], *, economics: dict[str, Any] | None = None) -> dict[str, Any]:
    """Estimate executable size before edge erosion; no fabricated capacity."""
    opp = dict(opportunity or {})
    if opp.get("truth_indicative_only"):
        return {
            "state": "NOT_APPLICABLE",
            "reason": "advisory_only",
            "methodology_version": METHODOLOGY_VERSION,
            "timestamp_utc": _utc_now(),
        }

    depth = _optional_float(opp.get("depth_usd") or opp.get("liquidity_usd") or opp.get("book_depth_usd"))
    if depth is None:
        return {
            "state": "UNAVAILABLE",
            "reason": "insufficient_depth_evidence",
            "methodology_version": METHODOLOGY_VERSION,
            "timestamp_utc": _utc_now(),
        }

    slip_bps = _optional_float(opp.get("total_slippage_bps") or opp.get("slippage_bps"))
    if slip_bps is None:
        return {
            "state": "UNAVAILABLE",
            "reason": "missing_slippage_for_capacity",
            "methodology_version": METHODOLOGY_VERSION,
            "timestamp_utc": _utc_now(),
        }

    # Conservative: executable notional before slippage doubles observed bps.
    max_slip_bps = max(slip_bps * 2.0, slip_bps + 5.0)
    capacity_from_depth = depth * 0.25
    capacity_from_slip = depth * (slip_bps / max_slip_bps) * 0.5
    estimate = min(capacity_from_depth, capacity_from_slip)
    limiting = "depth" if capacity_from_depth <= capacity_from_slip else "slippage_sensitivity"

    expected_edge = _optional_float((economics or {}).get("expected_net_edge_usd"))
    if expected_edge is not None and expected_edge > 0:
        edge_per_1k = expected_edge / max(_optional_float(opp.get("quote_amount")) or 1000.0, 1.0) * 1000.0
        if edge_per_1k <= 0:
            estimate = 0.0
            limiting = "edge_exhausted"

    return {
        "state": "AVAILABLE",
        "capacity_usd": round(max(0.0, estimate), 4),
        "capacity_range_usd": {
            "low": round(max(0.0, estimate * 0.6), 4),
            "high": round(max(0.0, estimate * 1.1), 4),
        },
        "limiting_factor": limiting,
        "confidence": "medium" if depth >= 50_000 else "low",
        "uncertainty_state": "AVAILABLE",
        "methodology_version": METHODOLOGY_VERSION,
        "timestamp_utc": _utc_now(),
        "inputs": {"depth_usd": depth, "slippage_bps": slip_bps},
    }
