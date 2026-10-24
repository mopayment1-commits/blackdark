"""Server-side live data refresh intervals — keyed off entitlements, not client tier params."""

from __future__ import annotations

from typing import Any

from entitlements_registry import entitlements_for_plan, normalize_entitlement_plan
from entitlements_service import async_resolve_entitlements


def live_refresh_policy_for_plan(plan: str | None) -> dict[str, Any]:
    row = entitlements_for_plan(plan)
    poll_sec = int(row.get("live_poll_interval_sec") or 45)
    poll_sec = max(5, min(60, poll_sec))
    stream = bool(row.get("live_stream_enabled"))
    return {
        "poll_interval_sec": poll_sec,
        "poll_interval_ms": poll_sec * 1000,
        "live_stream_enabled": stream,
        "trust_pulse_stream": "/api/trust-pulse/stream" if stream else None,
        "ledger_poll_enabled": True,
        "server_enforced": True,
        "effective_plan": normalize_entitlement_plan(plan),
    }


async def resolve_live_refresh_policy(user_id: int | None) -> dict[str, Any]:
    ent = await async_resolve_entitlements(user_id)
    plan = str(ent.get("effective_plan") or "free")
    policy = live_refresh_policy_for_plan(plan)
    policy["entitlement_allowed"] = bool(ent.get("entitlement_allowed", True))
    return policy
