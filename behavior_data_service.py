"""
BLACKDARK — Behavior data asset (acquisition moat).

Captures non-code user/product behavior that cannot be rewritten in 6 months:
Oracle usage patterns, conversion funnel, feature adoption, retention signals.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import config

logger = logging.getLogger("BLACKDARK.BehaviorData")

ALLOWED_EVENT_TYPES = frozenset(
    {
        "oracle_query",
        "oracle_explain",
        "arbitrage_scan",
        "arbitrage_view",
        "auth_register",
        "auth_login",
        "auth_logout",
        "waitlist_join",
        "checkout_start",
        "alert_subscribe",
        "feature_gate_hit",
        "journal_entry",
        "dashboard_view",
        "landing_view",
        "voice_command",
        "research_lab_view",
        "simulation_run",
    }
)


def _enabled() -> bool:
    return getattr(config, "BEHAVIOR_DATA_ENABLED", True)


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def record_behavior_event(
    event_type: str,
    *,
    user_email: str | None = None,
    tier: str | None = None,
    asset: str | None = None,
    session_id: str | None = None,
    payload: dict[str, Any] | None = None,
) -> int:
    if not _enabled():
        return 0
    normalized = event_type.strip().lower()
    if normalized not in ALLOWED_EVENT_TYPES:
        logger.debug("Ignored behavior event type | type=%s", event_type)
        return 0
    try:
        from repos.behavior_repo import record_event

        return await record_event(
            normalized,
            user_email=user_email,
            tier=tier,
            asset=asset,
            session_id=session_id,
            payload_json=json.dumps(payload or {}, separators=(",", ":")),
        )
    except Exception:
        logger.exception("Behavior event insert failed | type=%s", normalized)
        return 0


async def fetch_behavior_asset_stats(*, days: int = 30) -> dict[str, Any]:
    from repos.behavior_repo import stats

    return await stats(days=days)


def behavior_data_status() -> dict[str, Any]:
    return {
        "enabled": _enabled(),
        "allowed_event_types": sorted(ALLOWED_EVENT_TYPES),
        "retention_days": int(getattr(config, "BEHAVIOR_DATA_RETENTION_DAYS", 365)),
    }
