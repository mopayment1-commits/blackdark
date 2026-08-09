"""
BLACKDARK — Authentication & subscription tier gating (Launch Week 1).
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.Auth")

Tier = Literal["free", "pro", "whale"]

TIER_RANK: dict[str, int] = {"free": 0, "pro": 1, "whale": 2}

TIER_FEATURES: dict[str, dict[str, Any]] = {
    # Proof Pass — viral free wedge: OQS Why + shareable Decision Certificate.
    # Conversion levers: 3/day cap, Free Proof watermark, no Portfolio AI.
    "free": {
        "label": "Proof Pass",
        "oracle_daily_limit": 3,
        "arbitrage": False,
        "arbitrage_catalog": False,
        "voice": False,
        "research_lab": False,
        "alerts": False,
        "ai_chat": False,
        "journal": True,
        "portfolio_ai": False,
        "market_radar": True,  # light public radar; full depth is Pro
        "b2b_api": False,
        "evidence_pack": False,
        "ux_pro_default": False,
        "proof_watermark": True,
        "product_name": "Trust OS",
    },
    # Decision Pro — daily decision habit ($29). 7-day trial stays.
    "pro": {
        "label": "Decision Pro",
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
        "proof_watermark": False,
        "product_name": "Trust OS",
    },
    # Decision Desk — edge + serious tools ($49).
    "whale": {
        "label": "Decision Desk",
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
        "proof_watermark": False,
        "product_name": "Trust OS",
    },
}

SESSION_DAYS = int(os.getenv("AUTH_SESSION_DAYS", "30"))
PBKDF2_ITERATIONS = 260_000


def _utcnow() -> datetime:
    return datetime.now(UTC)


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


async def register_user(
    email: str,
    password: str,
    name: str = "",
    *,
    username: str = "",
    accepted_terms: bool = False,
) -> dict[str, Any]:
    from database import create_user, fetch_user_by_email, fetch_user_by_username, insert_pro_trial
    from identity_service import (
        send_verification_email,
        validate_display_name,
        validate_email,
        validate_password,
        validate_username,
    )

    if not accepted_terms:
        raise ValueError("You must accept Terms, Privacy, and Risk Disclaimer")
    email = validate_email(email)
    validate_password(password, email=email)
    display = validate_display_name(name)
    handle = validate_username(username) if username.strip() else ""

    if await fetch_user_by_email(email):
        raise ValueError("Email already registered")
    if handle and await fetch_user_by_username(handle):
        raise ValueError("Username already taken")

    user_id = await create_user(email, hash_password(password), display)
    if handle:
        from database import update_user_profile_fields

        await update_user_profile_fields(user_id, {"username": handle})
    trial = await insert_pro_trial(email)
    session = await create_session(user_id)
    tier = await resolve_user_tier(email)
    verify = await send_verification_email(user_id, email)
    return {
        "token": session["token"],
        "expires_at": session["expires_at"],
        "trial": {
            "active": True,
            "ends_at": trial["trial_ends_at"],
            "days": trial["days"],
        },
        "email_verification": {
            "required": True,
            "sent": True,
            **{k: verify[k] for k in ("debug_token", "debug_link") if k in verify},
        },
        "user": {
            "id": user_id,
            "email": email,
            "name": display,
            "username": handle or None,
            "tier": tier,
            "email_verified": False,
        },
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
        try:
            from security_events import record_security_event

            record_security_event(
                "login_failure",
                severity="warning",
                actor=email,
                detail={"reason": "invalid_credentials"},
            )
        except Exception:
            pass
        raise ValueError("Invalid email or password")

    mfa_enabled = bool(int(user.get("mfa_enabled") or 0))
    # Org-enforced MFA (Report-2 C-P0-02) — refuse login if org requires MFA and user not enrolled.
    try:
        from org_mfa_policy import assert_login_mfa_policy

        org_mfa = await assert_login_mfa_policy(
            email,
            mfa_enabled=mfa_enabled,
            mfa_code_present=bool(mfa_code),
        )
        if org_mfa.get("mfa_required") and not mfa_enabled:
            raise ValueError(
                "Organization MFA is required. Enroll TOTP at /settings/security before login."
            )
    except ValueError:
        raise
    except Exception:
        org_mfa = {"org_mfa_enforced": False}

    if mfa_enabled or (org_mfa.get("org_mfa_enforced") and mfa_enabled):
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
                "org_mfa_enforced": bool(org_mfa.get("org_mfa_enforced")),
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
    from database import delete_user_sessions_for_user, insert_user_session
    from security_auth import hash_session_token

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
    from database import delete_user_session
    from security_auth import hash_session_token, is_production_env

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
    from database import fetch_user_by_session
    from security_auth import hash_session_token, is_production_env

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
        "username": row.get("username") or None,
        "tier": tier,
        # Never echo the bearer token in API payloads (XSS/log amplification).
        "telegram_chat_id": row.get("telegram_chat_id"),
        "stripe_customer_id": row.get("stripe_customer_id"),
        "email_verified": bool(row.get("email_verified_at")),
        "avatar_url": row.get("avatar_url") or f"/api/auth/avatar/{row['id']}.svg",
        "ui_lang": row.get("ui_lang") or "en",
        "ux_mode_pref": row.get("ux_mode_pref") or "beginner",
        "timezone": row.get("timezone") or "UTC",
        "password_is_set": bool(int(row.get("password_is_set") if row.get("password_is_set") is not None else 1)),
        "oauth_provider": row.get("oauth_provider"),
    }


async def check_oracle_quota(user: dict[str, Any] | None) -> tuple[bool, str]:
    """Return (allowed, message). Anonymous users share a generous free pool."""
    from database import fetch_oracle_usage_today, increment_oracle_usage

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
        return False, f"Proof Pass limit reached ({daily_limit}/day). Start Decision Pro trial for unlimited Oracle + no Free watermark."
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
