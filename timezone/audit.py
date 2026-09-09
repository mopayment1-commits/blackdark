"""Timezone preference audit — TZ-028."""

from __future__ import annotations

from typing import Any


async def record_timezone_change(
    user_id: int,
    *,
    old_timezone: str | None,
    new_timezone: str,
    source: str,
    actor: str | None = None,
) -> None:
    from identity.identity_audit import record_identity_event

    await record_identity_event(
        event_type="timezone.preference_changed",
        user_id=user_id,
        actor=actor or str(user_id),
        detail={
            "old_timezone": old_timezone or "UTC",
            "new_timezone": new_timezone,
            "source": source,
        },
    )


def audit_payload(**kwargs: Any) -> dict[str, Any]:
    return {"kind": "timezone_audit", **kwargs}
