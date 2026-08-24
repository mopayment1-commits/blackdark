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

# Sonar S1192: duplicated string literals
STR_TRUST_OS = 'Trust OS'

logger = logging.getLogger("BLACKDARK.Auth")

Tier = Literal["free", "pro", "elite", "quant", "institutional", "whale"]

TIER_RANK: dict[str, int] = {
    "free": 0,
    "pro": 1,
    "elite": 2,
    "whale": 2,  # legacy alias
    "quant": 3,
    "institutional": 4,
}


def normalize_tier(tier: str | None) -> str:
    from billing.plan_registry import normalize_plan

    canonical = normalize_plan(tier)
    return canonical if canonical in TIER_RANK or canonical == "institutional" else "free"


TIER_FEATURES: dict[str, dict[str, Any]] = {
    "free": {
        "label": "FREE",
        "oracle_daily_limit": 3,
        "market_radar_delay_minutes": 15,
        "alerts_max": 3,
        "export_monthly_limit": 0,
        "api_monthly_limit": 0,
        "backtest_hours_monthly": 0,
        "arbitrage": False,
        "arbitrage_catalog": False,
        "voice": False,
        "research_lab": False,
        "alerts": False,
        "ai_chat": False,
        "journal": True,
        "portfolio_ai": False,
        "market_radar": True,
        "b2b_api": False,
        "evidence_pack": False,
        "quant_backtest": False,
        "ux_pro_default": False,
        "proof_watermark": True,
        "product_name": STR_TRUST_OS,
    },
    "pro": {
        "label": "PRO",
        "oracle_daily_limit": None,
        "market_radar_delay_minutes": 0,
        "alerts_max": 10,
        "export_monthly_limit": 50,
        "api_monthly_limit": 0,
        "backtest_hours_monthly": 0,
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
        "quant_backtest": False,
        "ux_pro_default": True,
        "proof_watermark": False,
        "product_name": STR_TRUST_OS,
    },
    "elite": {
        "label": "ELITE",
        "oracle_daily_limit": None,
        "market_radar_delay_minutes": 0,
        "alerts_max": None,
        "export_monthly_limit": 200,
        "api_monthly_limit": 10000,
        "backtest_hours_monthly": 5,
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
        "quant_backtest": False,
        "ux_pro_default": True,
        "proof_watermark": False,
        "product_name": STR_TRUST_OS,
    },
    "whale": {  # legacy alias — same as elite
        "label": "ELITE",
        "oracle_daily_limit": None,
        "export_monthly_limit": 200,
        "api_monthly_limit": 10000,
        "backtest_hours_monthly": 5,
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
        "quant_backtest": False,
        "ux_pro_default": True,
        "proof_watermark": False,
        "product_name": STR_TRUST_OS,
    },
    "quant": {
        "label": "QUANT",
        "oracle_daily_limit": None,
        "export_monthly_limit": None,
        "api_monthly_limit": 100000,
        "backtest_hours_monthly": 40,
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
        "quant_backtest": True,
        "ux_pro_default": True,
        "proof_watermark": False,
        "product_name": STR_TRUST_OS,
    },
    "institutional": {
        "label": "INSTITUTIONAL",
        "oracle_daily_limit": None,
        "export_monthly_limit": None,
        "api_monthly_limit": None,
        "backtest_hours_monthly": None,
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
        "quant_backtest": True,
        "ux_pro_default": True,
        "proof_watermark": False,
        "product_name": STR_TRUST_OS,
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
    actual_n = normalize_tier(actual)
    required_n = normalize_tier(required)
    return TIER_RANK.get(actual_n, 0) >= TIER_RANK.get(required_n, 0)


async def resolve_user_tier(email: str) -> str:
    from database import fetch_user_by_email
    from billing.subscription_engine import resolve_entitlements_for_user
    from billing.subscription_store import ensure_subscription_account

    user = await fetch_user_by_email(email.strip().lower())
    if not user:
        return "free"
    uid = int(user["id"])
    await ensure_subscription_account(uid, email)
    ent = await resolve_entitlements_for_user(uid)
    if ent.get("entitlement_allowed"):
        return normalize_tier(str(ent.get("effective_plan") or "free"))
    return "free"


async def register_user(
    email: str,
    password: str,
    name: str = "",
    *,
    username: str = "",
    accepted_terms: bool = False,
    plan: str = "free",
) -> dict[str, Any]:
    from database import create_user, fetch_user_by_email, fetch_user_by_username
    from billing.subscription_engine import start_paid_trial
    from identity_service import (
        send_verification_email,
        validate_display_name,
        validate_email,
        validate_password,
        validate_username,
    )
    from pricing_catalog import normalize_signup_plan, signup_next_after_register

    if not accepted_terms:
        raise ValueError("You must accept Terms, Privacy, and Risk Disclaimer")
    email = validate_email(email)
    validate_password(password, email=email)
    display = validate_display_name(name)
    handle = validate_username(username) if username.strip() else ""
    selected_plan = normalize_signup_plan(plan)
    next_step = signup_next_after_register(selected_plan)

    if await fetch_user_by_email(email):
        raise ValueError("Email already registered")
    if handle and await fetch_user_by_username(handle):
        raise ValueError("Username already taken")

    user_id = await create_user(email, hash_password(password), display)
    if handle:
        from database import update_user_profile_fields

        await update_user_profile_fields(user_id, {"username": handle})

    trial_payload: dict[str, Any] | None = None
    if next_step.get("start_paid_trial") and selected_plan != "free":
        trial = await start_paid_trial(user_id, email, selected_plan)
        trial_payload = {
            "active": True,
            "ends_at": trial.get("trial_ends_at") or trial.get("current_period_end"),
            "days": next_step.get("trial_days"),
            "plan": selected_plan,
        }
    elif next_step.get("start_pro_trial"):
        trial = await start_paid_trial(user_id, email, "pro")
        trial_payload = {
            "active": True,
            "ends_at": trial.get("trial_ends_at"),
            "days": trial.get("trial_ends_at"),
            "plan": "pro",
        }

    session = await create_session(user_id)
    tier = await resolve_user_tier(email)
    verify = await send_verification_email(user_id, email)
    return {
        "token": session["token"],
        "expires_at": session["expires_at"],
        "selected_plan": selected_plan,
        "next": next_step,
        "trial": trial_payload,
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
            "selected_plan": selected_plan,
        },
    }


def _record_invalid_login(email: str) -> None:
    from security_auth import record_login_failure

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


async def _login_org_mfa_policy(email: str, *, mfa_enabled: bool, mfa_code: str | None) -> dict[str, Any]:
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
        return org_mfa
    except ValueError:
        raise
    except Exception:
        return {"org_mfa_enforced": False}


def _mfa_challenge_response(user: dict[str, Any], email: str, org_mfa: dict[str, Any]) -> dict[str, Any]:
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


async def _verify_login_mfa(user: dict[str, Any], email: str, mfa_code: str | None) -> dict[str, Any] | None:
    if not mfa_code:
        return None
    from mfa_service import verify_user_mfa
    from security_auth import record_login_failure

    ok = await verify_user_mfa(int(user["id"]), mfa_code)
    if not ok:
        record_login_failure(email)
        raise ValueError("Invalid MFA code")
    return None


async def login_user(
    email: str,
    password: str,
    *,
    mfa_code: str | None = None,
) -> dict[str, Any]:
    from database import fetch_user_by_email, touch_user_login
    from security_auth import check_login_rate_limit

    email = normalize_email(email)
    check_login_rate_limit(email)
    user = await fetch_user_by_email(email)
    if user is None or not verify_password(password, str(user.get("password_hash") or "")):
        _record_invalid_login(email)
        raise ValueError("Invalid email or password")

    mfa_enabled = bool(int(user.get("mfa_enabled") or 0))
    # Org-enforced MFA (Report-2 C-P0-02) — refuse login if org requires MFA and user not enrolled.
    org_mfa = await _login_org_mfa_policy(email, mfa_enabled=mfa_enabled, mfa_code=mfa_code)

    if mfa_enabled or (org_mfa.get("org_mfa_enforced") and mfa_enabled):
        if not mfa_code:
            return _mfa_challenge_response(user, email, org_mfa)
        await _verify_login_mfa(user, email, mfa_code)

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
    tier = normalize_tier((user or {}).get("tier") or "free")
    features = TIER_FEATURES.get(tier) or TIER_FEATURES.get(normalize_tier(tier)) or TIER_FEATURES["free"]
    return bool(features.get(feature))


def tier_payload(user: dict[str, Any] | None, subscription: dict[str, Any] | None = None) -> dict[str, Any]:
    tier = normalize_tier((user or {}).get("tier") or "free")
    features = TIER_FEATURES.get(tier) or TIER_FEATURES["free"]
    payload = {
        "tier": tier,
        "label": features["label"],
        "features": features,
    }
    if subscription and subscription.get("status") in {"trial", "trialing"}:
        payload["trial"] = True
        payload["trial_ends_at"] = subscription.get("trial_ends_at")
        payload["label"] = f"{features['label']} (Trial)"
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
