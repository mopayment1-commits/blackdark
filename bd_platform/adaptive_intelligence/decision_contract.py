"""Decision Contract — thresholds, uncertainty band, validity window, abstain logic."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from failure.decision import DecisionSafetyState, evaluate_decision_safety
from failure.freshness import FreshnessState
from failure.quality import DataQualityState


def build_decision_contract(
    *,
    goal: str,
    symbol: str,
    candidates: list[dict[str, Any]],
    tier: str = "free",
    freshness_state: FreshnessState | str | None = None,
    quality_state: DataQualityState | str | None = None,
    source_count: int | None = None,
    conflicting: bool = False,
) -> dict[str, Any]:
    if not candidates:
        safety = evaluate_decision_safety(
            freshness=freshness_state or FreshnessState.UNKNOWN,
            quality=quality_state or DataQualityState.INSUFFICIENT,
            source_count=0,
            conflicting=conflicting,
        )
        return {
            "abstain": True,
            "reason": "no_candidates",
            "goal": goal,
            "decision_safety": safety.decision_state.value,
            "evidence_context": safety.to_dict(),
        }

    safety = evaluate_decision_safety(
        freshness=freshness_state or FreshnessState.UNKNOWN,
        quality=quality_state or DataQualityState.COMPLETE,
        source_count=source_count if source_count is not None else len(candidates),
        conflicting=conflicting,
    )

    top = candidates[0]
    score = float(top.get("relevance_score") or 0)
    abstain = score < 1.0
    reason = None

    if safety.decision_state in {
        DecisionSafetyState.ABSTAINED,
        DecisionSafetyState.UNAVAILABLE,
    }:
        abstain = True
        reason = safety.evidence_state
    elif safety.decision_state == DecisionSafetyState.DEGRADED and score < 2.0:
        abstain = True
        reason = safety.evidence_state

    now = datetime.now(UTC)
    if score < 2:
        uncertainty_band = "high"
    elif score < 3:
        uncertainty_band = "medium"
    else:
        uncertainty_band = "low"

    return {
        "goal": goal,
        "symbol": symbol.upper(),
        "tier": tier,
        "abstain": abstain,
        "reason": reason,
        "direction": "explore" if not abstain else "none",
        "selected_capability_id": None if abstain else top["capability_id"],
        "uncertainty_band": uncertainty_band,
        "decision_safety": safety.decision_state.value,
        "evidence_context": safety.to_dict(),
        "confidence_dimensions": {
            "trust": "catalog_match_only",
            "freshness": safety.freshness_state,
            "coverage": len(candidates),
            "methodology": "deterministic_token_match",
            "evidence_class": "BACKTESTED",
            "quality": safety.quality_state,
        },
        "validity_window": {
            "starts_at": now.isoformat(),
            "ends_at": (now + timedelta(hours=1)).isoformat(),
        },
        "invalidation_triggers": ["catalog_change", "tier_denied", "freshness_stale"],
        "safety_floor": "mandatory_controls_before_recommendation",
    }
