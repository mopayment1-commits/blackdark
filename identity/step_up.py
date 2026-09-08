"""Step-up authentication — ID-026, ID-063."""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from typing import Any

STEP_UP_MAX_AGE_SECONDS = int(os.getenv("IDENTITY_STEP_UP_MAX_AGE_SECONDS", "900"))


def _utcnow() -> datetime:
    return datetime.now(UTC)


def parse_step_up_at(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def step_up_fresh(step_up_at: str | None, *, max_age: int | None = None) -> bool:
    ts = parse_step_up_at(step_up_at)
    if ts is None:
        return False
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=UTC)
    age = (_utcnow() - ts).total_seconds()
    return age <= (max_age or STEP_UP_MAX_AGE_SECONDS)


async def mark_step_up(user_id: int) -> str:
    from database import set_user_step_up_at

    ts = _utcnow().isoformat()
    await set_user_step_up_at(user_id, ts)
    return ts


async def require_step_up(user: dict[str, Any], *, action: str) -> None:
    if not step_up_fresh(user.get("step_up_at")):
        raise ValueError(f"Recent authentication required for {action}")


SENSITIVE_ACTIONS = frozenset(
    {
        "password.change",
        "email.change",
        "phone.change",
        "mfa.disable",
        "mfa.replace",
        "passkey.add",
        "passkey.remove",
        "provider.link",
        "provider.unlink",
        "billing.sensitive",
        "api_key.create",
        "api_key.revoke",
        "data.export",
        "account.delete",
        "admin.identity",
    }
)
