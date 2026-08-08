"""
BLACKDARK — Production environment guard (ARC / launch recommendations).
"""

from __future__ import annotations

import os
from typing import Any

import config


def is_production() -> bool:
    """True when ENV/RAILWAY is production — LOCAL_DEV never overrides explicit prod."""
    env = (os.getenv("ENV") or os.getenv("RAILWAY_ENVIRONMENT") or "").strip().lower()
    return env in {"production", "prod"}


def _check(name: str, ok: bool, *, required: bool, hint: str) -> dict[str, Any]:
    return {
        "id": name,
        "ok": ok,
        "required": required,
        "status": "pass" if ok else ("fail" if required else "warn"),
        "hint": hint,
    }


def _service_mode() -> str:
    return (os.getenv("SERVICE_MODE") or getattr(config, "SERVICE_MODE", "all") or "all").strip().lower()


def evaluate_production_guard() -> dict[str, Any]:
    from billing_service import billing_configured
    from postgres_backend import use_postgres

    pg = use_postgres()
    mode = _service_mode()
    soft_launch = os.getenv("SOFT_LAUNCH", "").lower() in {"1", "true", "yes"}
    redis_url = (getattr(config, "REDIS_URL", "") or "").strip()
    billing = billing_configured()
    sentry = bool(os.getenv("SENTRY_DSN", "").strip())
    uptime_probe = os.getenv("UPTIME_SELF_PROBE_ENABLED", "true").lower() in {"1", "true", "yes"}
    lemon = bool(os.getenv("LEMON_SQUEEZY_CHECKOUT_PRO", "").strip())
    stripe = bool(os.getenv("STRIPE_SECRET_KEY", "").strip())
    telegram = bool(os.getenv("TELEGRAM_BOT_TOKEN", "").strip())
    telegram_secret = bool(os.getenv("TELEGRAM_WEBHOOK_SECRET", "").strip())
    lemon_webhook = bool(os.getenv("LEMON_SQUEEZY_WEBHOOK_SECRET", "").strip())
    stripe_webhook = bool(os.getenv("STRIPE_WEBHOOK_SECRET", "").strip())
    secrets_ok = bool(
        os.getenv("SECRETS_MASTER_KEY", "").strip() or os.getenv("SECRETS_VAULT_KEY", "").strip()
    )
    session_pepper_ok = bool(os.getenv("SESSION_TOKEN_PEPPER", "").strip())
    admin_ok = bool(os.getenv("ADMIN_API_KEY", "").strip() or os.getenv("ADMIN_EMAILS", "").strip())
    admin_mfa_ok = bool(os.getenv("ADMIN_TOTP_SECRET", "").strip()) or soft_launch
    oauth_ok = bool(
        (
            os.getenv("OAUTH_GOOGLE_CLIENT_ID", "").strip()
            and os.getenv("OAUTH_GOOGLE_CLIENT_SECRET", "").strip()
        )
        or (
            os.getenv("OAUTH_GITHUB_CLIENT_ID", "").strip()
            and os.getenv("OAUTH_GITHUB_CLIENT_SECRET", "").strip()
        )
    )
    demo_key = (getattr(config, "B2B_DEMO_API_KEY", "") or os.getenv("BLACKDARK_B2B_DEMO_KEY", "")).strip()
    demo_disabled = demo_key in {"", "disabled", "off", "none"}
    redis_ok = bool(redis_url) and not getattr(config, "SERVICE_BUS_LOCAL", True)

    # Billing entitlement webhook: Lemon secret if Lemon checkout, else Stripe secret if Stripe.
    billing_webhook_ok = True
    if lemon:
        billing_webhook_ok = lemon_webhook
    elif stripe:
        billing_webhook_ok = stripe_webhook

    checks = [
        _check(
            "postgres_database",
            pg or soft_launch,
            required=True,
            hint=(
                "Set Postgres DATABASE_URL=postgresql://... "
                "(or SOFT_LAUNCH=true for free SQLite demo)"
            ),
        ),
        _check(
            "service_mode_web",
            mode == "web",
            required=True,
            hint="Set SERVICE_MODE=web on Railway (lighter Oracle-only process)",
        ),
        _check(
            "billing_checkout",
            billing or soft_launch,
            required=True,
            hint="Set LEMON_SQUEEZY_CHECKOUT_PRO or Stripe live keys (or SOFT_LAUNCH=true)",
        ),
        _check(
            "billing_entitlement_webhook",
            billing_webhook_ok or soft_launch,
            required=True,
            hint=(
                "Set LEMON_SQUEEZY_WEBHOOK_SECRET (POST /webhook/lemon) "
                "or STRIPE_WEBHOOK_SECRET (POST /webhook) — or SOFT_LAUNCH=true"
            ),
        ),
        _check(
            "secrets_master_key",
            secrets_ok,
            required=True,
            hint="Set SECRETS_MASTER_KEY or SECRETS_VAULT_KEY (no insecure default in prod)",
        ),
        _check(
            "session_token_pepper",
            session_pepper_ok,
            required=True,
            hint="Set SESSION_TOKEN_PEPPER to a long random secret",
        ),
        _check(
            "admin_auth_configured",
            admin_ok,
            required=True,
            hint="Set ADMIN_API_KEY and/or ADMIN_EMAILS",
        ),
        _check(
            "admin_mfa_totp",
            admin_mfa_ok,
            required=True,
            hint="Set ADMIN_TOTP_SECRET (base32) for admin API-key MFA (or SOFT_LAUNCH=true)",
        ),
        _check(
            "b2b_demo_key_disabled",
            demo_disabled,
            required=False,
            hint="Unset BLACKDARK_B2B_DEMO_KEY or set to disabled in production",
        ),
        _check(
            "redis_shared_bus",
            redis_ok or soft_launch,
            required=True,
            hint="Add Redis REDIS_URL + SERVICE_BUS_LOCAL=false (or SOFT_LAUNCH=true)",
        ),
        _check(
            "oauth2_social_login",
            oauth_ok or soft_launch,
            required=False,
            hint="Set OAUTH_GOOGLE_* and/or OAUTH_GITHUB_* client credentials",
        ),
        _check(
            "sentry_observability",
            sentry,
            required=False,
            hint="Set SENTRY_DSN for production error tracking",
        ),
        _check(
            "uptime_self_probe",
            uptime_probe,
            required=False,
            hint="UPTIME_SELF_PROBE_ENABLED=true (default) + UptimeRobot external",
        ),
        _check(
            "telegram_bot",
            telegram,
            required=False,
            hint="Set TELEGRAM_BOT_TOKEN + webhook for GTM growth loop",
        ),
        _check(
            "telegram_webhook_secret",
            (not telegram) or telegram_secret,
            required=bool(telegram),
            hint="Set TELEGRAM_WEBHOOK_SECRET when TELEGRAM_BOT_TOKEN is set",
        ),
        _check(
            "price_feed_railway",
            not getattr(config, "PRICE_FEED_WS_ONLY", True),
            required=False,
            hint="PRICE_FEED_WS_ONLY=false on Railway cloud",
        ),
        _check(
            "soft_launch_mode",
            soft_launch,
            required=False,
            hint="SOFT_LAUNCH=true enables free SQLite demo without Postgres/billing webhooks",
        ),
    ]

    required_fail = [c for c in checks if c["required"] and not c["ok"]]
    warn = [c for c in checks if not c["required"] and not c["ok"]]

    return {
        "production": is_production(),
        "soft_launch": soft_launch,
        "service_mode": mode,
        "database": "postgresql" if pg else "sqlite",
        "billing_provider": "lemon_squeezy" if lemon else ("stripe" if stripe else "none"),
        "checks": checks,
        "required_pass": len(required_fail) == 0,
        "required_failures": [c["id"] for c in required_fail],
        "warnings": [c["id"] for c in warn],
        "railway_replicas_hint": "Set numReplicas=2 in railway.json or Railway dashboard",
        "uptimerobot_url": f"{os.getenv('APP_BASE_URL', 'https://blackdark-production.up.railway.app')}/health/live",
    }


def enforce_production_guard(*, raise_on_fail: bool | None = None) -> dict[str, Any]:
    """Fail closed in production when required checks fail (opt-out via env)."""
    report = evaluate_production_guard()
    if not is_production():
        return report
    if raise_on_fail is None:
        raise_on_fail = os.getenv("PRODUCTION_GUARD_FAIL_CLOSED", "true").lower() in {
            "1",
            "true",
            "yes",
        }
    if raise_on_fail and report["required_failures"]:
        raise RuntimeError(
            "Production guard failed required checks: "
            + ", ".join(report["required_failures"])
        )
    return report


def log_production_guard() -> None:
    import logging

    logger = logging.getLogger("BLACKDARK.ProductionGuard")
    report = evaluate_production_guard()
    if not is_production():
        logger.info("Production guard skipped (not production env)")
        return
    if report["required_failures"]:
        logger.warning(
            "Production guard REQUIRED failures: %s",
            ", ".join(report["required_failures"]),
        )
        if os.getenv("PRODUCTION_GUARD_FAIL_CLOSED", "true").lower() in {"1", "true", "yes"}:
            raise RuntimeError(
                "Production guard fail-closed: "
                + ", ".join(report["required_failures"])
            )
    if report["warnings"]:
        logger.info("Production guard warnings: %s", ", ".join(report["warnings"]))
    if report["required_pass"]:
        logger.info("Production guard: all required checks pass")
