"""Today's Focus — decision snapshot with Safety Floor (spec §5, AIE-005/016/017/018)."""

from __future__ import annotations

from typing import Any

from bd_platform.adaptive_intelligence.safety_floor import enforce_safety_floor


def _snapshot_block(title: str, summary: str, **extra: Any) -> dict[str, Any]:
    return enforce_safety_floor(
        {
            "title": title,
            "summary": summary,
            "decision_critical": True,
            "freshness": extra.get("freshness") or "near_live",
            "evidence_state": extra.get("evidence_state") or "forward_shadow",
            "uncertainty": extra.get("uncertainty") or "medium",
            "critical_limitation": extra.get("critical_limitation") or "Advisory snapshot; verify ledger.",
            "invalidation_or_next_check": extra.get("invalidation_or_next_check") or "recheck_on_stale_data",
            **extra,
        }
    )


def build_today_focus() -> dict[str, Any]:
    return {
        "market_state": _snapshot_block("Market State", "Monitoring core assets; no forced action."),
        "main_opportunity": _snapshot_block(
            "Top Opportunity",
            "See Opportunity Score for ranked setups.",
            uncertainty="medium",
        ),
        "primary_risk": _snapshot_block(
            "Key Risk",
            "Portfolio exposure and whale flow monitored.",
            uncertainty="medium",
        ),
        "what_changed": _snapshot_block(
            "What Changed",
            "Since-you-left digest available on dashboard.",
            uncertainty="low",
        ),
        "safety_floor_required": True,
    }
