"""Opportunity capacity estimation (DTS-014)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from decision_truth.methodology import METHODOLOGY_VERSIONS


def estimate_capacity(opportunity: dict[str, Any], *, net_edge: dict[str, Any] | None = None) -> dict[str, Any]:
    depth = opportunity.get("depth_usd") or opportunity.get("liquidity_usd")
    notional = opportunity.get("quote_amount") or 1000.0
    try:
        depth_f = float(depth) if depth is not None else None
    except (TypeError, ValueError):
        depth_f = None

    if depth_f is None:
        return {
            "capacity_usd": None,
            "limiting_factor": "insufficient_liquidity_data",
            "status": "unavailable",
            "confidence": "low",
            "methodology_version": METHODOLOGY_VERSIONS["capacity"],
            "evaluated_at": datetime.now(UTC).isoformat(),
        }

    capacity = min(depth_f * 0.15, float(notional) * 5.0)
    limiting = "order_book_depth" if capacity < depth_f * 0.2 else "quote_notional"
    expected = (net_edge or {}).get("expected_net_edge_usd")
    if expected is not None and float(expected) < 0.08:
        capacity = min(capacity, float(notional))
        limiting = "edge_threshold"

    return {
        "capacity_usd": round(capacity, 2),
        "limiting_factor": limiting,
        "status": "estimated",
        "confidence": "medium" if depth_f > 10_000 else "low",
        "methodology_version": METHODOLOGY_VERSIONS["capacity"],
        "evaluated_at": datetime.now(UTC).isoformat(),
    }
