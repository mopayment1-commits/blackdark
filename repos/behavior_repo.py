"""Repository layer — behavior events (thin wrapper over database)."""

from __future__ import annotations

from typing import Any

from database import fetch_behavior_event_stats, insert_behavior_event


async def record_event(
    event_type: str,
    *,
    user_email: str | None = None,
    tier: str | None = None,
    asset: str | None = None,
    session_id: str | None = None,
    payload_json: str = "{}",
) -> int:
    return await insert_behavior_event(
        event_type,
        user_email=user_email,
        tier=tier,
        asset=asset,
        session_id=session_id,
        payload_json=payload_json,
    )


async def stats(*, days: int = 30) -> dict[str, Any]:
    return await fetch_behavior_event_stats(days=days)
