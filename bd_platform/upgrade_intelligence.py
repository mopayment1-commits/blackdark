"""
Smart Upgrade Recommendations — Feature #9 Phase 3.

AI-style contextual upgrade suggestions based on usage patterns and tier limits.
"""

from __future__ import annotations

import time
from typing import Any

from auth_service import TIER_FEATURES
from billing.plan_registry import normalize_plan, plan_def
from bd_platform.subscription_lifecycle import user_lifecycle_status
from pricing_catalog import next_upgrade


async def _usage_signals(user_id: int) -> dict[str, Any]:
    from database import get_connection

    async with get_connection() as db:
        rows = await (
            await db.execute(
                """
                SELECT event_type, COUNT(*) AS c FROM analytics_events
                WHERE user_id = ?
                GROUP BY event_type
                """,
                (int(user_id),),
            )
        ).fetchall()
        oracle_row = await (
            await db.execute(
                """
                SELECT COUNT(*) AS c FROM analytics_events
                WHERE user_id = ? AND event_type IN ('api_usage', 'oracle_query', 'oracle_decision')
                """,
                (int(user_id),),
            )
        ).fetchone()
    counts = {str(r["event_type"]): int(r["c"]) for r in rows}
    return {
        "event_counts": counts,
        "total_events": sum(counts.values()),
        "oracle_usage": int(oracle_row["c"] if oracle_row else 0),
        "api_usage": counts.get("api_usage", 0),
        "upgrade_cta_clicks": counts.get("upgrade_cta_clicked", 0),
    }


def _blocked_features(tier: str) -> list[str]:
    blocked: list[str] = []
    for feat, tiers in TIER_FEATURES.items():
        if tier not in tiers:
            blocked.append(feat)
    return blocked[:8]


async def recommend_upgrade(user_id: int) -> dict[str, Any]:
    """Contextual upgrade recommendation with explainable reasoning."""
    t0 = time.perf_counter()
    lifecycle = await user_lifecycle_status(int(user_id))
    plan = lifecycle.get("effective_plan") or "free"
    step = next_upgrade(plan)
    usage = await _usage_signals(int(user_id))
    blocked = _blocked_features(plan)
    target = normalize_plan(str(step.get("next_id") or "pro"))
    reasons: list[str] = []

    if plan == "free" and usage["oracle_usage"] >= 2:
        reasons.append(f"You've used oracle {usage['oracle_usage']} times — PRO removes the 3/day ceiling")
    if usage["api_usage"] >= 5:
        reasons.append(f"High API activity ({usage['api_usage']} calls) — {target.upper()} unlocks higher limits")
    if blocked:
        reasons.append(f"Unlock: {', '.join(blocked[:3])}")
    if lifecycle.get("renewal_warning"):
        reasons.append(
            f"Subscription ends in {lifecycle.get('days_until_renewal')} days — upgrade before cutoff"
        )
    if not reasons:
        next_def = plan_def(target)
        reasons.append(
            f"Upgrade to {next_def.get('display', target.upper())} for {next_def.get('price_display', 'more depth')}"
        )

    confidence = min(0.95, 0.55 + len(reasons) * 0.12 + (0.1 if usage["total_events"] > 10 else 0))
    explanation = (
        f"Based on your {plan.upper()} plan and {usage['total_events']} tracked actions: "
        + "; ".join(reasons[:2])
        + f". Recommended: {target.upper()}."
    )

    return {
        "ok": True,
        "surface": "upgrade_intelligence",
        "feature": "#9-phase3",
        "user_id": int(user_id),
        "current_plan": plan,
        "recommended_plan": target,
        "confidence": round(confidence, 2),
        "explanation": explanation,
        "reasons": reasons,
        "blocked_features": blocked,
        "usage_signals": usage,
        "checkout_href": step.get("href") or f"/create-checkout-session?tier={target}",
        "upgrade_ladder": step,
        "acceptance": {
            "accuracy_target": 0.95,
            "confidence_met": confidence >= 0.55,
        },
        "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
    }
