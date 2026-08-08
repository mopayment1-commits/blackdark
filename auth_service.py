"""
BLACKDARK — Authentication & subscription tier gating (Launch Week 1).
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.Auth")

Tier = Literal["free", "pro", "whale"]

TIER_RANK: dict[str, int] = {"free": 0, "pro": 1, "whale": 2}

TIER_FEATURES: dict[str, dict[str, Any]] = {
    "free": {
        "label": "Free",
        "oracle_daily_limit": 10,
        "arbitrage": False,
        "arbitrage_catalog": False,
        "voice": False,
        "research_lab": False,
        "alerts": False,
        "ai_chat": False,
        "journal": True,
        "portfolio_ai": True,
        "market_radar": True,
        "b2b_api": False,
        "evidence_pack": False,
        "ux_pro_default": False,
    },
    "pro": {
        "label": "Pro",
        "oracle_daily_limit": None,
        "arbitrage": True,
        "arbitrage_catalog": True,
        "voice": False,
        "research_lab": True,
        "alerts": True,
        "ai_chat": True,
        "journal": True,
        "portfolio_ai": True,
        "market_radar": True,
        "b2b_api": False,
        "evidence_pack": False,
        "ux_pro_default": True,
    },
    "whale": {
        "label": "Whale",
        "oracle_daily_limit": None,
        "arbitrage": True,
        "arbitrage_catalog": True,
        "voice": True,
        "research_lab": True,
        "alerts": True,
        "ai_chat": True,
        "journal": True,
        "portfolio_ai": True,
        "market_radar": True,
        "b2b_api": True,
        "evidence_pack": True,
        "ux_pro_default": True,
    },
}

SESSION_DAYS = int(os.getenv("AUTH_SESSION_DAYS", "30"))
PBKDF2_ITERATIONS = 260_000


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _utcnow_iso() -> str:
    return _utcnow().isoformat()


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PBKDF2_ITERATIONS,
    )
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, iterations, salt, digest_hex = stored.split("$", 3)
        if scheme != "pbkdf2_sha256":
            return False
        expected = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            int(iterations),
        )
        return hmac.compare_digest(expected.hex(), digest_hex)
    except (ValueError, TypeError):
        return False


def normalize_email(email: str) -> str:
    return email.strip().lower()


def tier_meets(required: Tier, actual: Tier) -> bool:
    return TIER_RANK.get(actual, 0) >= TIER_RANK.get(required, 0)


async def resolve_user_tier(email: str) -> Tier:
    from database import fetch_active_subscription_for_email

    sub = await fetch_active_subscription_for_email(email)
    if sub:
        tier = str(sub.get("tier") or "pro").lower()
        if tier in TIER_RANK:
            return tier  # type: ignore[return-value]
    return "free"


async def register_user(email: str, password: str, name: str = "") -> dict[str, Any]:
    from database import create_user, fetch_user_by_email, insert_pro_trial

    email = normalize_email(email)
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters")
    if "@" not in email:
        raise ValueError("Valid email required")

    if await fetch_user_by_email(email):
        raise ValueError("Email already registered")

    user_id = await create_user(email, hash_password(password), name.strip())
    trial = await insert_pro_trial(email)
    session = await create_session(user_id)
    tier = await resolve_user_tier(email)
    return {
        "token": session["token"],
        "expires_at": session["expires_at"],
        "trial": {
            "active": True,
            "ends_at": trial["trial_ends_at"],
            "days": trial["days"],
        },
        "user": {"id": user_id, "email": email, "name": name.strip(), "tier": tier},
    }


async def login_user(
    email: str,
    password: str,
    *,
    mfa_code: str | None = None,
) -> dict[str, Any]:
    from database import fetch_user_by_email, touch_user_login
    from security_auth import check_login_rate_limit, record_login_failure

    email = normalize_email(email)
    check_login_rate_limit(email)
    user = await fetch_user_by_email(email)
    if user is None or not verify_password(password, str(user.get("password_hash") or "")):
        record_login_failure(email)
        raise ValueError("Invalid email or password")

    mfa_enabled = bool(int(user.get("mfa_enabled") or 0))
    if mfa_enabled:
        if not mfa_code:
            # Do not issue a session until MFA is verified.
            challenge = secrets.token_urlsafe(24)
            _mfa_challenges[challenge] = {
                "user_id": int(user["id"]),
                "email": email,
                "expires": (_utcnow() + timedelta(minutes=5)).timestamp(),
            }
            return {
                "mfa_required": True,
                "mfa_challenge": challenge,
                "user": {"id": user["id"], "email": email, "name": user.get("name") or ""},
            }
        from mfa_service import verify_user_mfa

        ok = await verify_user_mfa(int(user["id"]), mfa_code)
        if not ok:
            record_login_failure(email)
            raise ValueError("Invalid MFA code")

    await touch_user_login(int(user["id"]))
    session = await create_session(int(user["id"]))
    tier = await resolve_user_tier(email)
    return {
        "token": session["token"],
        "expires_at": session["expires_at"],
        "mfa_required": False,
        "user": {
            "id": user["id"],
            "email": email,
            "name": user.get("name") or "",
            "tier": tier,
            "mfa_enabled": mfa_enabled,
        },
    }


_mfa_challenges: dict[str, dict[str, Any]] = {}


async def complete_mfa_login(challenge: str, code: str) -> dict[str, Any]:
    """Complete login after password step returned mfa_required."""
    from database import touch_user_login
    from mfa_service import verify_user_mfa
    from security_auth import record_login_failure

    row = _mfa_challenges.get(challenge)
    if not row or float(row.get("expires") or 0) < _utcnow().timestamp():
        _mfa_challenges.pop(challenge, None)
        raise ValueError("MFA challenge expired — login again")
    email = str(row["email"])
    user_id = int(row["user_id"])
    if not await verify_user_mfa(user_id, code):
        record_login_failure(email)
        raise ValueError("Invalid MFA code")
    _mfa_challenges.pop(challenge, None)
    await touch_user_login(user_id)
    session = await create_session(user_id)
    tier = await resolve_user_tier(email)
    return {
        "token": session["token"],
        "expires_at": session["expires_at"],
        "mfa_required": False,
        "user": {"id": user_id, "email": email, "tier": tier, "mfa_enabled": True},
    }


async def create_session(user_id: int, *, revoke_others: bool = True) -> dict[str, Any]:
    from security_auth import hash_session_token

    from database import delete_user_sessions_for_user, insert_user_session

    # New login regenerates session and revokes prior tokens (fixation / theft radius).
    if revoke_others:
        try:
            await delete_user_sessions_for_user(int(user_id))
        except Exception:
            pass
    token = secrets.token_urlsafe(48)
    token_hash = hash_session_token(token)
    expires_at = (_utcnow() + timedelta(days=SESSION_DAYS)).isoformat()
    await insert_user_session(user_id, token_hash, expires_at)
    return {"token": token, "expires_at": expires_at}


async def logout_user(token: str) -> None:
    from security_auth import hash_session_token, is_production_env

    from database import delete_user_session

    await delete_user_session(hash_session_token(token))
    # Legacy plaintext session rows — only wipe when explicitly allowed (never prod).
    allow_plain = os.getenv("ALLOW_PLAINTEXT_SESSION_LOOKUP", "").lower() in {
        "1",
        "true",
        "yes",
    }
    if allow_plain and not is_production_env():
        await delete_user_session(token)


async def get_user_from_token(token: str | None) -> dict[str, Any] | None:
    if not token:
        return None
    from security_auth import hash_session_token, is_production_env

    from database import fetch_user_by_session

    plain = token.strip()
    row = await fetch_user_by_session(hash_session_token(plain))
    # Legacy plaintext lookup: opt-in only, never in production.
    if row is None:
        allow_plain = os.getenv("ALLOW_PLAINTEXT_SESSION_LOOKUP", "").lower() in {
            "1",
            "true",
            "yes",
        }
        if allow_plain and not is_production_env():
            row = await fetch_user_by_session(plain)
    if row is None:
        return None
    email = str(row.get("email") or "")
    tier = await resolve_user_tier(email)
    return {
        "id": row["id"],
        "email": email,
        "name": row.get("name") or "",
        "tier": tier,
        # Never echo the bearer token in API payloads (XSS/log amplification).
        "telegram_chat_id": row.get("telegram_chat_id"),
        "stripe_customer_id": row.get("stripe_customer_id"),
    }


async def check_oracle_quota(user: dict[str, Any] | None) -> tuple[bool, str]:
    """Return (allowed, message). Anonymous users share a generous free pool."""
    from database import increment_oracle_usage, fetch_oracle_usage_today

    tier: Tier = (user or {}).get("tier") or "free"
    email = (user or {}).get("email") or "_anonymous_"
    limits = TIER_FEATURES[tier]
    daily_limit = limits.get("oracle_daily_limit")
    if daily_limit is None:
        if user:
            await increment_oracle_usage(email)
        return True, "ok"

    used = await fetch_oracle_usage_today(email)
    if used >= daily_limit:
        return False, f"Free limit reached ({daily_limit}/day). Upgrade to Pro for unlimited Oracle."
    await increment_oracle_usage(email)
    return True, "ok"


def feature_allowed(user: dict[str, Any] | None, feature: str) -> bool:
    tier: Tier = (user or {}).get("tier") or "free"
    return bool(TIER_FEATURES.get(tier, TIER_FEATURES["free"]).get(feature))


def tier_payload(user: dict[str, Any] | None, subscription: dict[str, Any] | None = None) -> dict[str, Any]:
    tier: Tier = (user or {}).get("tier") or "free"
    payload = {
        "tier": tier,
        "label": TIER_FEATURES[tier]["label"],
        "features": TIER_FEATURES[tier],
    }
    if subscription and subscription.get("status") == "trial":
        payload["trial"] = True
        payload["trial_ends_at"] = subscription.get("trial_ends_at")
        payload["label"] = f"{TIER_FEATURES[tier]['label']} (Trial)"
    return payload


async def redeem_promo_code(email: str, code: str) -> dict[str, Any]:
    import config
    from database import extend_pro_trial

    normalized = code.strip().upper()
    days = config.LAUNCH_PROMO_CODES.get(normalized)
    if not days:
        raise ValueError("Invalid promo code")
    result = await extend_pro_trial(normalize_email(email), days)
    tier = await resolve_user_tier(email)
    return {
        "success": True,
        "code": normalized,
        "days_added": days,
        "tier": tier,
        "trial_ends_at": result.get("trial_ends_at"),
    }
