"""Launch-57 identity closure — sessions, login history, notifications, homoglyph."""

from __future__ import annotations

import os
import unicodedata
from typing import Any

HOMOGLYPH_STATUS = "minimum_ascii_nfkc_mixed_script_reject"
HOMOGLYPH_FULL_DEFERRED = True


def homoglyph_policy_metadata() -> dict[str, Any]:
    return {
        "status": HOMOGLYPH_STATUS,
        "full_confusable_skeleton": "deferred" if HOMOGLYPH_FULL_DEFERRED else "enabled",
        "minimum": ["nfkc", "ascii_only", "mixed_script_reject", "reserved", "case_fold"],
    }


def _script_of_char(ch: str) -> str | None:
    try:
        name = unicodedata.name(ch)
    except ValueError:
        return None
    return name.split()[0] if name else None


def reject_obvious_mixed_script_username(username: str) -> None:
    """Minimum homoglyph guard — reject mixed alphabetic scripts (full skeleton deferred)."""
    scripts: set[str] = set()
    for ch in username:
        if ch.isalpha():
            script = _script_of_char(ch)
            if script:
                scripts.add(script)
    if len(scripts) > 1:
        raise ValueError("Username mixes character scripts — choose ASCII letters only")


def notify_security_event(
    *,
    user_id: int | None,
    email: str | None,
    kind: str,
    detail: dict[str, Any] | None = None,
    request: Any | None = None,
) -> dict[str, Any]:
    """Record security notification in audit trail; live delivery BLOCKED_EXTERNAL."""
    from identity_audit import log_identity_auth_event

    log_identity_auth_event(
        f"security_notification_{kind}",
        actor=email,
        user_id=user_id,
        request=request,
        detail={**(detail or {}), "delivery_status": "BLOCKED_EXTERNAL"},
    )
    return {
        "logged": True,
        "delivered": False,
        "delivery_status": "BLOCKED_EXTERNAL",
        "reason": "Production email delivery not enabled in this environment",
    }


async def record_login_history(
    *,
    user_id: int | None,
    email: str,
    method: str,
    status: str,
    ip: str | None = None,
    user_agent: str | None = None,
) -> None:
    from database import insert_login_history

    await insert_login_history(
        user_id=user_id,
        email=email.strip().lower(),
        method=method,
        status=status,
        ip=ip,
        user_agent=(user_agent or "")[:512] or None,
    )


async def list_login_history(user_id: int, *, limit: int = 50) -> list[dict[str, Any]]:
    from database import fetch_login_history

    rows = await fetch_login_history(user_id, limit=limit)
    return [
        {
            "occurred_at": row.get("occurred_at"),
            "method": row.get("method") or "password",
            "status": row.get("status"),
            "ip": row.get("ip"),
            "device": _device_label(row.get("user_agent")),
        }
        for row in rows
    ]


def _device_label(user_agent: str | None) -> str:
    ua = (user_agent or "").lower()
    if not ua:
        return "Unknown device"
    if "mobile" in ua or "android" in ua or "iphone" in ua:
        return "Mobile browser"
    if "chrome" in ua:
        return "Chrome"
    if "firefox" in ua:
        return "Firefox"
    if "safari" in ua:
        return "Safari"
    return "Browser"


async def list_user_sessions(user_id: int, *, current_token_hash: str | None = None) -> list[dict[str, Any]]:
    from database import fetch_user_sessions

    rows = await fetch_user_sessions(user_id)
    out: list[dict[str, Any]] = []
    for row in rows:
        out.append(
            {
                "id": row["id"],
                "created_at": row.get("created_at"),
                "expires_at": row.get("expires_at"),
                "last_seen_at": row.get("last_seen_at") or row.get("created_at"),
                "auth_method": row.get("auth_method") or "password",
                "ip": row.get("ip"),
                "device": _device_label(row.get("user_agent")),
                "current": bool(
                    current_token_hash and str(row.get("token") or "") == current_token_hash
                ),
            }
        )
    return out


async def revoke_user_session(user_id: int, session_id: int) -> bool:
    from database import delete_user_session_by_id

    return await delete_user_session_by_id(user_id, session_id)


async def secure_my_account(
    user_id: int,
    *,
    email: str,
    keep_current_token_hash: str | None = None,
    request: Any | None = None,
) -> dict[str, Any]:
    from database import delete_user_session_except, delete_user_sessions_for_user, revoke_auth_tokens_for_user

    if keep_current_token_hash:
        revoked = await delete_user_session_except(user_id, keep_current_token_hash)
    else:
        revoked = await delete_user_sessions_for_user(user_id)
    tokens = await revoke_auth_tokens_for_user(user_id)
    notify_security_event(
        user_id=user_id,
        email=email,
        kind="secure_my_account",
        detail={"sessions_revoked": revoked, "auth_tokens_revoked": tokens},
        request=request,
    )
    return {
        "ok": True,
        "sessions_revoked": revoked,
        "auth_tokens_revoked": tokens,
        "message": "Sessions and recovery tokens revoked. Sign in again on each device.",
    }


async def request_account_deletion(email: str, user_id: int, *, request: Any = None) -> dict[str, Any]:
    from database import set_account_deletion_pending

    state = await set_account_deletion_pending(user_id)
    notify_security_event(
        user_id=user_id,
        email=email,
        kind="deletion_requested",
        detail={"account_state": state.get("account_state")},
        request=request,
    )
    return state


async def request_email_change(user_id: int, new_email: str, *, request: Any = None) -> dict[str, Any]:
    from database import fetch_user_by_email, set_pending_email
    from identity_service import send_email_change_verification, validate_email

    normalized = validate_email(new_email)
    existing = await fetch_user_by_email(normalized)
    if existing and int(existing["id"]) != user_id:
        raise ValueError("Email already in use")
    await set_pending_email(user_id, normalized)
    sent = await send_email_change_verification(user_id, normalized)
    notify_security_event(
        user_id=user_id,
        email=normalized,
        kind="email_change_requested",
        detail={"pending_email": normalized},
        request=request,
    )
    return {"ok": True, "pending_email": normalized, "verification": sent}


async def finalize_email_change(user_id: int) -> dict[str, Any]:
    from database import apply_pending_email

    row = await apply_pending_email(user_id)
    if not row:
        raise ValueError("No pending email change")
    notify_security_event(
        user_id=user_id,
        email=str(row.get("email")),
        kind="email_change_completed",
        detail={"previous_email": row.get("previous_email")},
    )
    return row


def public_profile_payload(profile: dict[str, Any]) -> dict[str, Any]:
    """Public-safe profile — username/display visible; email and private fields omitted."""
    return {
        "username": profile.get("username"),
        "display_name": profile.get("name") or profile.get("display_name"),
        "avatar_url": profile.get("avatar_url"),
        "initials": profile.get("initials"),
        "public_safe_identity_projection": True,
    }
