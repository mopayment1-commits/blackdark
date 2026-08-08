"""
BLACKDARK — Security auth guards, session hashing, rate limiting.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

from fastapi import Cookie, Depends, Header, HTTPException, Request

logger = logging.getLogger("BLACKDARK.Security")

_login_attempts: dict[str, list[float]] = defaultdict(list)
_LOGIN_WINDOW_SEC = 300
_LOGIN_MAX_ATTEMPTS = 10
_AUTH_AUDIT_PATH = Path(
    os.getenv("AUTH_AUDIT_LOG_PATH", "data/auth_audit.jsonl")
)


def is_production_env() -> bool:
    """True when ENV/RAILWAY is production — LOCAL_DEV never overrides an explicit prod ENV."""
    env = (os.getenv("ENV") or os.getenv("RAILWAY_ENVIRONMENT") or "").strip().lower()
    if env in {"production", "prod"}:
        return True
    return False


def hash_session_token(token: str) -> str:
    pepper = os.getenv("SESSION_TOKEN_PEPPER", "").strip()
    if not pepper:
        if is_production_env():
            raise RuntimeError("SESSION_TOKEN_PEPPER must be set in production")
        pepper = "blackdark-session-pepper-change-me"
        logger.warning("SESSION_TOKEN_PEPPER unset — using insecure dev default")
    return hashlib.sha256(f"{pepper}:{token}".encode("utf-8")).hexdigest()


def check_login_rate_limit(key: str) -> None:
    """Raise if too many login attempts from email/IP."""
    now = time.time()
    window = _login_attempts[key]
    _login_attempts[key] = [t for t in window if now - t < _LOGIN_WINDOW_SEC]
    if len(_login_attempts[key]) >= _LOGIN_MAX_ATTEMPTS:
        raise HTTPException(status_code=429, detail="Too many login attempts. Try again in 5 minutes.")
    _login_attempts[key].append(now)


def persist_auth_audit(
    *,
    event: str,
    subject: str = "",
    reason: str = "",
    ip: str = "",
    meta: dict[str, Any] | None = None,
) -> None:
    """Append a durable auth audit event (JSONL). Best-effort; never raises to callers."""
    try:
        from security_models import AuditLogModel

        row = AuditLogModel(
            event=event,
            subject=subject,
            reason=reason,
            ip=ip,
            meta=meta or {},
        )
        _AUTH_AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with _AUTH_AUDIT_PATH.open("a", encoding="utf-8") as fh:
            fh.write(row.model_dump_json() + "\n")
    except Exception as exc:  # noqa: BLE001 — audit must not break login flow
        logger.warning("auth audit persist failed: %s", exc)


def record_login_failure(key: str, *, reason: str = "invalid_credentials") -> None:
    check_login_rate_limit(key)
    persist_auth_audit(event="login_failure", subject=key, reason=reason)


def admin_emails() -> set[str]:
    raw = os.getenv("ADMIN_EMAILS", "")
    return {e.strip().lower() for e in raw.split(",") if e.strip()}


def verify_admin_key(provided: str | None) -> bool:
    expected = os.getenv("ADMIN_API_KEY", "").strip()
    if not expected or not provided:
        return False
    return hmac.compare_digest(provided.strip(), expected)


def is_admin_user(user: dict | None) -> bool:
    if not user:
        return False
    email = str(user.get("email") or "").lower()
    if email in admin_emails():
        return True
    return False


async def optional_user_from_request(
    authorization: str | None = Header(None, alias="Authorization"),
    bd_token: str | None = Cookie(None, alias="bd_token"),
) -> dict | None:
    from auth_service import get_user_from_token

    token: str | None = None
    if authorization:
        token = authorization[7:] if authorization.startswith("Bearer ") else authorization
    elif bd_token:
        token = bd_token.strip()
    if not token:
        return None
    return await get_user_from_token(token.strip())


async def require_authenticated(
    user: dict | None = Depends(optional_user_from_request),
) -> dict:
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


async def require_whale(
    user: dict = Depends(require_authenticated),
) -> dict:
    tier = str(user.get("tier") or "free")
    if tier != "whale" and not is_admin_user(user):
        raise HTTPException(
            status_code=403,
            detail={"error": "whale_required", "message": "Whale tier or admin required for this action."},
        )
    return user


async def require_admin(
    user: dict | None = Depends(optional_user_from_request),
    x_admin_key: str | None = Header(None, alias="X-Admin-Key"),
    x_admin_totp: str | None = Header(None, alias="X-Admin-TOTP"),
) -> dict:
    from admin_mfa import (
        mfa_policy_enabled,
        system_admin_totp_configured,
        verify_system_admin_totp,
        verify_user_totp,
    )

    soft_launch = os.getenv("SOFT_LAUNCH", "").lower() in {"1", "true", "yes"}
    require_mfa = mfa_policy_enabled() and not soft_launch and is_production_env()

    if verify_admin_key(x_admin_key):
        if require_mfa:
            if not system_admin_totp_configured():
                raise HTTPException(
                    status_code=403,
                    detail="Admin MFA required — set ADMIN_TOTP_SECRET",
                )
            if not verify_system_admin_totp(x_admin_totp):
                persist_auth_audit(
                    event="admin_mfa_failure",
                    subject="admin@system",
                    reason="invalid_system_totp",
                )
                raise HTTPException(status_code=403, detail="Invalid admin TOTP (X-Admin-TOTP)")
        return {"email": "admin@system", "tier": "whale", "is_admin": True, "mfa_ok": True}

    if user and is_admin_user(user):
        if require_mfa:
            # Prefer per-user TOTP when enrolled; otherwise system ADMIN_TOTP_SECRET.
            from database import fetch_user_by_email

            db_user = await fetch_user_by_email(str(user.get("email") or ""))
            if db_user and db_user.get("totp_enabled"):
                if not await verify_user_totp(db_user, x_admin_totp):
                    persist_auth_audit(
                        event="admin_mfa_failure",
                        subject=str(user.get("email") or ""),
                        reason="invalid_user_totp",
                    )
                    raise HTTPException(status_code=403, detail="Invalid admin TOTP (X-Admin-TOTP)")
            elif system_admin_totp_configured():
                if not verify_system_admin_totp(x_admin_totp):
                    persist_auth_audit(
                        event="admin_mfa_failure",
                        subject=str(user.get("email") or ""),
                        reason="invalid_system_totp",
                    )
                    raise HTTPException(status_code=403, detail="Invalid admin TOTP (X-Admin-TOTP)")
            else:
                raise HTTPException(
                    status_code=403,
                    detail="Admin MFA required — enroll TOTP or set ADMIN_TOTP_SECRET",
                )
        user["is_admin"] = True
        user["mfa_ok"] = True
        return user
    raise HTTPException(status_code=403, detail="Admin authentication required (X-Admin-Key or admin email)")


def _is_localhost(request: Request) -> bool:
    host = request.client.host if request.client else ""
    return host in {"127.0.0.1", "::1", "localhost"}


async def require_admin_dev(
    request: Request,
    user: dict | None = Depends(optional_user_from_request),
    x_admin_key: str | None = Header(None, alias="X-Admin-Key"),
    x_admin_totp: str | None = Header(None, alias="X-Admin-TOTP"),
) -> dict:
    """Admin guard — loopback bypass only outside production (never via LOCAL_DEV alone)."""
    if not is_production_env() and _is_localhost(request):
        return {"email": "localhost-dev", "tier": "whale", "is_admin": True, "mfa_ok": True}
    return await require_admin(user, x_admin_key, x_admin_totp)


async def require_pro_or_above(
    user: dict = Depends(require_authenticated),
) -> dict:
    tier = str(user.get("tier") or "free")
    if tier in {"pro", "whale"} or is_admin_user(user):
        return user
    raise HTTPException(status_code=403, detail="Pro tier or above required")
