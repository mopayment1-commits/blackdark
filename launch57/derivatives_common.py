"""
Launch-57 Phase 5 — shared derivatives + habits spine consuming Phase 1–3 layers.
"""

from __future__ import annotations

import os
from typing import Any

from launch57.decision_common import (
    attach_decision_envelope,
    load_decision_spine,
    stale_gate_body,
    stamp_decision_batch,
)

_LIGHT_HEATMAP_DISCLAIMER = (
    "Light liquidation heatmap preview only — not global liquidation coverage or "
    "full exchange-wide cascade mapping. Verify primary venue sources independently."
)

_L1_ORDER_BOOK_DISCLAIMER = (
    "L1 top-of-book depth at minimum — deeper L2/L3 ladders not claimed unless explicitly sourced."
)

_LIMITED_WATCHLIST = (
    "Limited launch watchlists — token + wallet tracking without full multi-venue alert mesh."
)


def attach_derivatives_envelope(body: dict[str, Any], *, spine: dict[str, Any] | None = None) -> dict[str, Any]:
    out = attach_decision_envelope(body, spine=spine)
    out["derivatives_habits_layer"] = {
        "phase": "5_DERIVATIVES_HABITS",
        "data_spine_consumed": (spine or {}).get("data_spine"),
        "freshness_state": (spine or {}).get("freshness_state"),
        "live_eligible": (spine or {}).get("live_eligible"),
        "evidence_class_visible": out.get("evidence_class_visible"),
    }
    return out


def light_heatmap_footer() -> dict[str, str | bool]:
    return {
        "disclaimer": _LIGHT_HEATMAP_DISCLAIMER,
        "global_liquidation_coverage_claim": "FORBIDDEN",
        "heatmap_scope": "light_preview_only",
    }


def l1_order_book_footer(*, depth_level: str = "L1") -> dict[str, str | bool]:
    deeper = depth_level.upper() not in {"L1", "TOP_OF_BOOK"}
    return {
        "disclaimer": _L1_ORDER_BOOK_DISCLAIMER,
        "depth_level": depth_level,
        "deeper_than_l1_claimed": deeper,
        "l1_minimum_met": depth_level.upper() in {"L1", "TOP_OF_BOOK"},
    }


def limited_watchlist_footer() -> dict[str, str | bool]:
    return {
        "disclaimer": _LIMITED_WATCHLIST,
        "full_multi_venue_mesh": False,
        "limited_launch_scope": True,
    }


def smart_alerts_external_status() -> dict[str, Any]:
    token = (os.getenv("TELEGRAM_BOT_TOKEN") or "").strip()
    chat = (os.getenv("TELEGRAM_CHAT_ID") or "").strip()
    push_live = bool(token and chat)
    return {
        "local_evaluation": True,
        "external_push_live": push_live,
        "delivery_status": "LIVE" if push_live else "BLOCKED_EXTERNAL",
        "blocked_reason": None if push_live else "telegram_credentials_not_configured",
        "blocked_channels": ["telegram_push"] if not push_live else [],
        "live_channels": ["in_app_evaluation", "api_response"] + (["telegram_push"] if push_live else []),
    }
