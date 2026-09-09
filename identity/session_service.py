"""Session service — ID-027, ID-028, ID-029, ID-030."""

from __future__ import annotations

import os
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

SESSION_IDLE_MINUTES = int(os.getenv("IDENTITY_SESSION_IDLE_MINUTES", "720"))
SESSION_ABSOLUTE_DAYS = int(os.getenv("IDENTITY_SESSION_ABSOLUTE_DAYS", "30"))
SESSION_REMEMBER_DAYS = int(os.getenv("IDENTITY_SESSION_REMEMBER_DAYS", "90"))
PRIVILEGED_SESSION_MINUTES = int(os.getenv("IDENTITY_PRIVILEGED_SESSION_MINUTES", "15"))


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _iso(dt: datetime) -> str:
    return dt.isoformat()


def session_expiry(*, remember_me: bool = False) -> tuple[str, str]:
    now = _utcnow()
    absolute = now + timedelta(days=SESSION_REMEMBER_DAYS if remember_me else SESSION_ABSOLUTE_DAYS)
    idle = now + timedelta(minutes=SESSION_IDLE_MINUTES)
    return _iso(absolute), _iso(idle)


async def create_user_session(
    user_id: int,
    *,
    auth_method: str = "password",
    device_label: str = "unknown",
    browser: str = "unknown",
    ip_hash: str = "",
    country: str = "",
    remember_me: bool = False,
    rotate_from: str | None = None,
) -> dict[str, Any]:
    from database import insert_identity_session
    from security_auth import hash_session_token

    token = secrets.token_urlsafe(48)
    token_hash = hash_session_token(token)
    absolute_exp, idle_exp = session_expiry(remember_me=remember_me)
    session_id = await insert_identity_session(
        user_id,
        token_hash=token_hash,
        absolute_expires_at=absolute_exp,
        idle_expires_at=idle_exp,
        auth_method=auth_method,
        device_label=device_label,
        browser=browser,
        ip_hash=ip_hash,
        country=country,
        rotated_from=rotate_from,
    )
    from identity.identity_audit import record_identity_event

    await record_identity_event(
        event_type="session.create",
        user_id=user_id,
        detail={"session_id": session_id, "auth_method": auth_method},
    )
    return {
        "token": token,
        "session_id": session_id,
        "expires_at": absolute_exp,
        "idle_expires_at": idle_exp,
    }


async def list_user_sessions(user_id: int) -> list[dict[str, Any]]:
    from database import fetch_identity_sessions

    return await fetch_identity_sessions(user_id)


async def revoke_session(user_id: int, session_id: str, *, actor_user_id: int | None = None) -> bool:
    from database import revoke_identity_session
    from identity.identity_audit import record_identity_event

    ok = await revoke_identity_session(user_id, session_id)
    if ok:
        await record_identity_event(
            event_type="session.revoke",
            user_id=user_id,
            actor=str(actor_user_id or user_id),
            detail={"session_id": session_id},
        )
    return ok


async def revoke_other_sessions(user_id: int, *, keep_session_id: str | None = None) -> int:
    from database import revoke_other_identity_sessions
    from identity.identity_audit import record_identity_event

    count = await revoke_other_identity_sessions(user_id, keep_session_id=keep_session_id)
    await record_identity_event(
        event_type="session.revoke_others",
        user_id=user_id,
        detail={"count": count, "keep": keep_session_id},
    )
    return count


async def revoke_all_sessions(user_id: int) -> int:
    from database import revoke_all_identity_sessions
    from identity.identity_audit import record_identity_event

    count = await revoke_all_identity_sessions(user_id)
    await record_identity_event(event_type="session.revoke_all", user_id=user_id, detail={"count": count})
    return count


async def rotate_session(user_id: int, old_token: str, **kwargs: Any) -> dict[str, Any]:
    from database import fetch_session_by_token_hash
    from security_auth import hash_session_token

    old_hash = hash_session_token(old_token)
    existing = await fetch_session_by_token_hash(old_hash)
    if not existing or int(existing["user_id"]) != user_id:
        raise ValueError("Session not found")
    await revoke_session(user_id, str(existing["id"]), actor_user_id=user_id)
    return await create_user_session(user_id, rotate_from=str(existing["id"]), **kwargs)
