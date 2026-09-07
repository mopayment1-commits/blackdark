"""Decision Contract — thresholds, uncertainty band, validity window, abstain logic."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any


def build_decision_contract(
    *,
    goal: str,
    symbol: str,
    candidates: list[dict[str, Any]],
    tier: str = "free",
) -> dict[str, Any]:
    if not candidates:
        return {"abstain": True, "reason": "no_candidates", "goal": goal}
    top = candidates[0]
    score = float(top.get("relevance_score") or 0)
    abstain = score < 1.0
    now = datetime.now(UTC)
    return {
        "goal": goal,
        "symbol": symbol.upper(),
        "tier": tier,
        "abstain": abstain,
        "direction": "explore" if not abstain else "none",
        "selected_capability_id": None if abstain else top["capability_id"],
        "uncertainty_band": "high" if score < 2 else "medium" if score < 3 else "low",
        "confidence_dimensions": {
            "trust": "catalog_match_only",
            "freshness": "not_live_verified",
            "coverage": len(candidates),
            "methodology": "deterministic_token_match",
            "evidence_class": "BACKTESTED",
        },
        "validity_window": {
            "starts_at": now.isoformat(),
            "ends_at": (now + timedelta(hours=1)).isoformat(),
        },
        "invalidation_triggers": ["catalog_change", "tier_denied", "freshness_stale"],
        "safety_floor": "mandatory_controls_before_recommendation",
    }
