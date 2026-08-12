"""
BLACKDARK — Security auth guards, session hashing, rate limiting.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
import time
from collections import defaultdict
from typing import Annotated

from fastapi import Cookie, Depends, Header, HTTPException, Request

logger = logging.getLogger("BLACKDARK.Security")

_login_attempts: dict[str, list[float]] = defaultdict(list)
_LOGIN_WINDOW_SEC = 300
_LOGIN_MAX_ATTEMPTS = 10
_LOGIN_RL_PREFIX = "bd:login_rl:"
_rate_limit_backend = "memory"
_redis_sync = None
_redis_fail_until = 0.0
_REDIS_NEG_TTL_SEC = float(os.getenv("LOGIN_RL_REDIS_NEG_TTL_SEC", "30"))
_REDIS_CONNECT_TIMEOUT = float(os.getenv("LOGIN_RL_REDIS_CONNECT_TIMEOUT_SEC", "0.08"))
_REDIS_SOCKET_TIMEOUT = float(os.getenv("LOGIN_RL_REDIS_SOCKET_TIMEOUT_SEC", "0.08"))


def is_production_env() -> bool:
    """True when any ENV/APP_ENV/ENVIRONMENT/RAILWAY token is production.

    First-wins chaining incorrectly ignored APP_ENV=production when a polluted
    ENV=development remained set. LOCAL_DEV never downgrades an explicit prod marker.
    """
    tokens = [
        (os.getenv("ENV") or "").strip().lower(),
        (os.getenv("APP_ENV") or "").strip().lower(),
        (os.getenv("ENVIRONMENT") or "").strip().lower(),
        (os.getenv("RAILWAY_ENVIRONMENT") or "").strip().lower(),
    ]
    return any(t in {"production", "prod"} for t in tokens)


def login_rate_limit_backend() -> str:
    """Report the backend that will be used for login RL (probe Redis when idle)."""
    global _rate_limit_backend
    if _rate_limit_backend == "redis":
        return "redis"
    # HA readiness must not require a prior failed login to discover Redis.
    if _redis_client_sync() is not None:
        _rate_limit_backend = "redis"
        return "redis"
    return _rate_limit_backend


def hash_session_token(token: str) -> str:
    pepper = os.getenv("SESSION_TOKEN_PEPPER", "").strip()
    if not pepper:
        if is_production_env():
            raise RuntimeError("SESSION_TOKEN_PEPPER must be set in production")
        pepper = "blackdark-session-pepper-change-me"
        logger.warning("SESSION_TOKEN_PEPPER unset — using insecure dev default")
    return hashlib.sha256(f"{pepper}:{token}".encode()).hexdigest()


def _memory_login_rate_limit(key: str) -> None:
    global _rate_limit_backend
    _rate_limit_backend = "memory"
    now = time.time()
    window = _login_attempts[key]
    _login_attempts[key] = [t for t in window if now - t < _LOGIN_WINDOW_SEC]
    if len(_login_attempts[key]) >= _LOGIN_MAX_ATTEMPTS:
        raise HTTPException(status_code=429, detail="Too many login attempts. Try again in 5 minutes.")
    _login_attempts[key].append(now)


def _redis_client_sync():
    """Shared sync Redis client for login RL — negative-caches dead REDIS_URL."""
    global _redis_sync, _redis_fail_until
    if _redis_sync is not None:
        return _redis_sync
    if time.time() < _redis_fail_until:
        return None
    try:
        import config

        url = (getattr(config, "REDIS_URL", "") or os.getenv("REDIS_URL", "")).strip()
        if not url:
            return None
        import redis

        client = redis.from_url(
            url,
            decode_responses=True,
            socket_connect_timeout=_REDIS_CONNECT_TIMEOUT,
            socket_timeout=_REDIS_SOCKET_TIMEOUT,
            max_connections=int(os.getenv("LOGIN_RL_REDIS_MAX_CONNECTIONS", "20")),
        )
        client.ping()
        _redis_sync = client
        _redis_fail_until = 0.0
        return _redis_sync
    except Exception:
        _redis_fail_until = time.time() + max(1.0, _REDIS_NEG_TTL_SEC)
        return None


def check_login_rate_limit(key: str) -> None:
    """Raise if too many login attempts from email/IP. Uses Redis when available."""
    global _rate_limit_backend
    redis_key = f"{_LOGIN_RL_PREFIX}{key.strip().lower()}"
    client = _redis_client_sync()
    if client is not None:
        try:
            count = int(client.incr(redis_key))
            if count == 1:
                client.expire(redis_key, _LOGIN_WINDOW_SEC)
            _rate_limit_backend = "redis"
            if count > _LOGIN_MAX_ATTEMPTS:
                raise HTTPException(
                    status_code=429,
                    detail="Too many login attempts. Try again in 5 minutes.",
                )
            return
        except HTTPException:
            raise
        except Exception:
            logger.warning("Redis login rate limit failed — falling back to memory", exc_info=True)
    _memory_login_rate_limit(key)


def record_login_failure(key: str) -> None:
    check_login_rate_limit(key)


def admin_emails() -> set[str]:
    raw = os.getenv("ADMIN_EMAILS", "")
    return {e.strip().lower() for e in raw.split(",") if e.strip()}


def _admin_api_key_expected() -> str:
    """Load admin API key from env or ADMIN_API_KEY_FILE (mode-0600 secret file)."""
    expected = os.getenv("ADMIN_API_KEY", "").strip()
    if expected:
        return expected
    path = os.getenv("ADMIN_API_KEY_FILE", "").strip()
    if not path:
        return ""
    try:
        from pathlib import Path

        p = Path(path)
        if not p.is_file():
            return ""
        return p.read_text(encoding="utf-8").strip().splitlines()[0].strip()
    except Exception:
        return ""


def verify_admin_key(provided: str | None) -> bool:
    expected = _admin_api_key_expected()
    if not expected or not provided:
        return False
    return hmac.compare_digest(provided.strip(), expected)


def is_admin_user(user: dict | None) -> bool:
    if not user:
        return False
    email = str(user.get("email") or "").lower()
    return email in admin_emails()


async def optional_user_from_request(
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
    bd_token: Annotated[str | None, Cookie(alias="bd_token")] = None,
) -> dict | None:
    """Resolve user from Bearer or Fernet-sealed HttpOnly bd_token cookie."""
    from auth_service import get_user_from_token

    token: str | None = None
    if authorization:
        token = authorization.removeprefix("Bearer ").strip()
    elif bd_token:
        from security_middleware import cookie_to_session_bearer

        token = cookie_to_session_bearer(bd_token)
    if not token:
        return None
    return await get_user_from_token(token.strip())


def require_authenticated(
    user: Annotated[dict | None, Depends(optional_user_from_request)],
) -> dict:
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


def require_whale(
    user: Annotated[dict, Depends(require_authenticated)],
) -> dict:
    tier = str(user.get("tier") or "free")
    if tier != "whale" and not is_admin_user(user):
        raise HTTPException(
            status_code=403,
            detail={"error": "whale_required", "message": "Whale tier or admin required for this action."},
        )
    return user


async def require_admin(
    user: Annotated[dict | None, Depends(optional_user_from_request)],
    x_admin_key: Annotated[str | None, Header(alias="X-Admin-Key")] = None,
    x_admin_totp: Annotated[str | None, Header(alias="X-Admin-TOTP")] = None,
) -> dict:
    """Fail-closed admin auth — never trusts reverse-proxy peer/loopback.

    Requires X-Admin-Key or an ADMIN_EMAILS session, plus admin MFA when policy is on.
    """
    admin_user: dict | None = None
    if verify_admin_key(x_admin_key):
        admin_user = {"email": "admin@system", "tier": "whale", "is_admin": True}
    elif user and is_admin_user(user):
        user = dict(user)
        user["is_admin"] = True
        admin_user = user
    if admin_user is None:
        raise HTTPException(
            status_code=403,
            detail="Admin authentication required (X-Admin-Key or admin email)",
        )
    from admin_mfa import assert_admin_mfa

    await assert_admin_mfa(x_admin_totp=x_admin_totp, user=admin_user)
    return admin_user


def _is_localhost(request: Request) -> bool:
    """Peer-address helper for diagnostics only — NEVER used for authorization."""
    host = request.client.host if request.client else ""
    return host in {"127.0.0.1", "::1", "localhost"}


async def require_admin_dev(
    request: Request,
    user: Annotated[dict | None, Depends(optional_user_from_request)],
    x_admin_key: Annotated[str | None, Header(alias="X-Admin-Key")] = None,
    x_admin_totp: Annotated[str | None, Header(alias="X-Admin-TOTP")] = None,
) -> dict:
    """Same as require_admin — loopback peer trust removed (proxy-safe)."""
    _ = request  # retained for FastAPI signature compatibility with call sites
    return await require_admin(user=user, x_admin_key=x_admin_key, x_admin_totp=x_admin_totp)


def require_pro_or_above(
    user: Annotated[dict, Depends(require_authenticated)],
) -> dict:
    tier = str(user.get("tier") or "free")
    if tier in {"pro", "whale"} or is_admin_user(user):
        return user
    raise HTTPException(status_code=403, detail="Pro tier or above required")
