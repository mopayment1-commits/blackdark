"""Execution feasibility score 0..100 with explainable reason codes (DTS-013)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from decision_truth.methodology import METHODOLOGY_VERSIONS


def compute_execution_feasibility(opportunity: dict[str, Any], *, net_edge: dict[str, Any] | None = None) -> dict[str, Any]:
    reasons: list[str] = []
    score = 70.0

    truth = (net_edge or {}).get("truth") or opportunity.get("net_edge_truth") or {}
    if truth.get("reject"):
        score = 15.0
        reasons.append("net_edge_rejected")
    if opportunity.get("half_life_killed"):
        score = min(score, 10.0)
        reasons.append("half_life_expired")
    if opportunity.get("conflict_vetoed"):
        score = min(score, 5.0)
        reasons.append("dimension_conflict_veto")
    if opportunity.get("conflict_abstain"):
        score = min(score, 25.0)
        reasons.append("dimension_conflict_abstain")

    existing = str(opportunity.get("execution_feasibility") or "")
    if existing == "not_executable":
        score = min(score, 20.0)
        reasons.append("marked_not_executable")

    age_ms = (truth.get("economics") or {}).get("quote_age_ms")
    if age_ms is not None and float(age_ms) > 2500:
        score -= 25.0
        reasons.append("stale_quote")

    spread_bps = opportunity.get("spread_bps")
    if spread_bps is not None and float(spread_bps) < 3:
        score -= 15.0
        reasons.append("tight_spread")

    depth_usd = opportunity.get("depth_usd") or opportunity.get("liquidity_usd")
    if depth_usd is not None and float(depth_usd) < 5000:
        score -= 20.0
        reasons.append("low_depth")

    score = max(0.0, min(100.0, round(score, 2)))
    if not reasons:
        reasons.append("baseline_feasible")

    return {
        "execution_feasibility_score": score,
        "reason_codes": reasons,
        "methodology_version": METHODOLOGY_VERSIONS["execution_feasibility"],
        "evaluated_at": datetime.now(UTC).isoformat(),
        "fill_probability": (net_edge or {}).get("fill_probability"),
    }
