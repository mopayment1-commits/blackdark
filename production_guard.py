"""
BLACKDARK — Production environment guard (ARC / launch recommendations).
"""

from __future__ import annotations

import os
from typing import Any

import config


def is_production() -> bool:
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


def evaluate_production_guard() -> dict[str, Any]:
    from billing_service import billing_configured
    from postgres_backend import use_postgres

    pg = use_postgres()
    mode = getattr(config, "SERVICE_MODE", "all")
    redis_url = (getattr(config, "REDIS_URL", "") or "").strip()
    billing = billing_configured()
    sentry = bool(os.getenv("SENTRY_DSN", "").strip())
    uptime_probe = os.getenv("UPTIME_SELF_PROBE_ENABLED", "true").lower() in {"1", "true", "yes"}
    lemon = bool(os.getenv("LEMON_SQUEEZY_CHECKOUT_PRO", "").strip())
    stripe = bool(os.getenv("STRIPE_SECRET_KEY", "").strip())
    telegram = bool(os.getenv("TELEGRAM_BOT_TOKEN", "").strip())

    checks = [
        _check(
            "postgres_database",
            pg,
            required=True,
            hint="Set Railway Postgres plugin -> DATABASE_URL=postgresql://...",
        ),
        _check(
            "service_mode_web",
            mode == "web",
            required=True,
            hint="Set SERVICE_MODE=web on Railway (lighter Oracle-only process)",
        ),
        _check(
            "billing_checkout",
            billing,
            required=True,
            hint="Set LEMON_SQUEEZY_CHECKOUT_PRO or Stripe live keys",
        ),
        _check(
            "redis_shared_bus",
            bool(redis_url) and not getattr(config, "SERVICE_BUS_LOCAL", True),
            required=False,
            hint="Add Railway/Upstash Redis -> REDIS_URL + SERVICE_BUS_LOCAL=false",
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
            "price_feed_railway",
            not getattr(config, "PRICE_FEED_WS_ONLY", True),
            required=False,
            hint="PRICE_FEED_WS_ONLY=false on Railway cloud",
        ),
    ]

    required_fail = [c for c in checks if c["required"] and not c["ok"]]
    warn = [c for c in checks if not c["required"] and not c["ok"]]

    return {
        "production": is_production(),
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
    if report["warnings"]:
        logger.info("Production guard warnings: %s", ", ".join(report["warnings"]))
    if report["required_pass"]:
        logger.info("Production guard: all required checks pass")
