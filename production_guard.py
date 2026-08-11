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
    if ok:
        status = "pass"
    elif required:
        status = "fail"
    else:
        status = "warn"
    return {
        "id": name,
        "ok": ok,
        "required": required,
        "status": status,
        "hint": hint,
    }


def _service_mode() -> str:
    return (os.getenv("SERVICE_MODE") or getattr(config, "SERVICE_MODE", "all") or "all").strip().lower()



def _env_truthy(name: str, default: str = "") -> bool:
    return os.getenv(name, default).lower() in {"1", "true", "yes"}


def _parallelism_snapshot() -> dict[str, Any]:
    try:
        from viral_capacity import effective_parallelism

        return effective_parallelism()
    except Exception:
        return {
            "workers": int(os.getenv("WEB_CONCURRENCY", os.getenv("UVICORN_WORKERS", "1")) or 1),
            "replicas": int(os.getenv("WEB_REPLICAS", "1") or 1),
            "parallelism": 1,
        }


def _billing_webhook_ok(lemon: bool, stripe: bool) -> bool:
    if lemon:
        return bool(os.getenv("LEMON_SQUEEZY_WEBHOOK_SECRET", "").strip())
    if stripe:
        return bool(os.getenv("STRIPE_WEBHOOK_SECRET", "").strip())
    return True


def _secret_hygiene() -> tuple[bool, bool, bool]:
    secrets_raw = (
        os.getenv("SECRETS_MASTER_KEY", "").strip() or os.getenv("SECRETS_VAULT_KEY", "").strip()
    )
    session_pepper = os.getenv("SESSION_TOKEN_PEPPER", "").strip()
    insecure_defaults = {
        "blackdark-dev-change-me-in-production",
        "blackdark-session-pepper-change-me",
        "change-me",
        "changeme",
        "secret",
    }
    no_insecure_secrets = secrets_raw.lower() not in insecure_defaults if secrets_raw else True
    no_insecure_pepper = session_pepper.lower() not in insecure_defaults if session_pepper else True
    prod_hygiene = (not is_production()) or (no_insecure_secrets and no_insecure_pepper)
    return bool(secrets_raw), bool(session_pepper), prod_hygiene


def _collect_guard_context() -> dict[str, Any]:
    from billing_service import billing_configured
    from postgres_backend import use_postgres

    pg = use_postgres()
    soft_launch = _env_truthy("SOFT_LAUNCH")
    lemon = bool(os.getenv("LEMON_SQUEEZY_CHECKOUT_PRO", "").strip())
    stripe = bool(os.getenv("STRIPE_SECRET_KEY", "").strip())
    lemon_whale = bool(os.getenv("LEMON_SQUEEZY_CHECKOUT_WHALE", "").strip())
    stripe_price_whale = bool(os.getenv("STRIPE_PRICE_WHALE", "").strip())
    expose_demo = _env_truthy("EXPOSE_B2B_DEMO_KEY")
    live_exec = _env_truthy("LIVE_EXECUTION_ALLOW_API")
    strict_prod = is_production() and not soft_launch
    viral_mode = _env_truthy("VIRAL_MODE", "true")
    viral_ha = strict_prod and viral_mode
    parallel = _parallelism_snapshot()
    redis_url = (getattr(config, "REDIS_URL", "") or "").strip()
    secrets_ok, session_pepper_ok, prod_secrets_hygiene = _secret_hygiene()
    demo_key = (getattr(config, "B2B_DEMO_API_KEY", "") or os.getenv("BLACKDARK_B2B_DEMO_KEY", "")).strip()
    return {
        "pg": pg,
        "mode": _service_mode(),
        "soft_launch": soft_launch,
        "redis_url": redis_url,
        "billing": billing_configured(),
        "sentry": bool(os.getenv("SENTRY_DSN", "").strip()),
        "uptime_probe": _env_truthy("UPTIME_SELF_PROBE_ENABLED", "true"),
        "lemon": lemon,
        "stripe": stripe,
        "telegram": bool(os.getenv("TELEGRAM_BOT_TOKEN", "").strip()),
        "telegram_secret": bool(os.getenv("TELEGRAM_WEBHOOK_SECRET", "").strip()),
        "whale_checkout_ok": lemon_whale or stripe_price_whale or (stripe and not lemon),
        "secrets_ok": secrets_ok,
        "session_pepper_ok": session_pepper_ok,
        "admin_ok": bool(os.getenv("ADMIN_API_KEY", "").strip() or os.getenv("ADMIN_EMAILS", "").strip()),
        "demo_disabled": demo_key in {"", "disabled", "off", "none"},
        "expose_demo": expose_demo,
        "soft_launch_safe": (not soft_launch) or (not live_exec and not expose_demo),
        "billing_webhook_ok": _billing_webhook_ok(lemon, stripe),
        "strict_prod": strict_prod,
        "viral_mode": viral_mode,
        "viral_ha": viral_ha,
        "parallel": parallel,
        "redis_shared_ok": bool(redis_url) and not getattr(config, "SERVICE_BUS_LOCAL", True),
        "multi_instance_ok": int(parallel.get("parallelism") or 1) >= 2,
        "sqlite_forbidden_ok": pg if strict_prod else (pg or soft_launch or not is_production()),
        "prod_secrets_hygiene": prod_secrets_hygiene,
    }



def _admin_mfa_ok() -> bool:
    admin_mfa = __import__("admin_mfa", fromlist=["mfa_policy_enabled", "system_admin_totp_configured"])
    return (not admin_mfa.mfa_policy_enabled()) or admin_mfa.system_admin_totp_configured()


def _build_guard_checks(ctx: dict[str, Any]) -> list[dict[str, Any]]:
    soft_launch = ctx["soft_launch"]
    strict_prod = ctx["strict_prod"]
    viral_ha = ctx["viral_ha"]
    expose_demo = ctx["expose_demo"]
    telegram = ctx["telegram"]
    return [
        _check("postgres_database", ctx["pg"] or soft_launch, required=True,
               hint="Set Postgres DATABASE_URL=postgresql://... (or SOFT_LAUNCH=true for free SQLite demo)"),
        _check("sqlite_forbidden_in_strict_production", ctx["sqlite_forbidden_ok"], required=strict_prod,
               hint="Strict production forbids SQLite. Set DATABASE_URL=postgresql://... and unset SOFT_LAUNCH before any institutional pitch."),
        _check("at_rest_encryption_posture", ctx["secrets_ok"], required=True,
               hint="Set SECRETS_MASTER_KEY or SECRETS_VAULT_KEY for Fernet at-rest encryption of user API keys / sensitive vault material (engineering posture ≠ ISO 27001 cert)"),
        _check("service_mode_web", ctx["mode"] == "web", required=True,
               hint="Set SERVICE_MODE=web on Railway (lighter Oracle-only process)"),
        _check("billing_checkout", ctx["billing"] or soft_launch, required=True,
               hint="Set LEMON_SQUEEZY_CHECKOUT_PRO or Stripe live keys (or SOFT_LAUNCH=true)"),
        _check("billing_entitlement_webhook", ctx["billing_webhook_ok"] or soft_launch, required=True,
               hint="Set LEMON_SQUEEZY_WEBHOOK_SECRET (POST /webhook/lemon) or STRIPE_WEBHOOK_SECRET (POST /webhook) — or SOFT_LAUNCH=true"),
        _check("billing_whale_checkout_usd", ctx["whale_checkout_ok"] or soft_launch, required=False,
               hint="Set LEMON_SQUEEZY_CHECKOUT_WHALE or STRIPE_PRICE_WHALE before promoting Decision Desk ($49 USD)"),
        _check("billing_currency_usd", True, required=False,
               hint="Self-serve Trust OS SKUs are USD-only (see docs/PAYMENTS_USD_SECURITY.md)"),
        _check("secrets_master_key", ctx["secrets_ok"], required=True,
               hint="Set SECRETS_MASTER_KEY or SECRETS_VAULT_KEY (no insecure default in prod)"),
        _check("session_token_pepper", ctx["session_pepper_ok"], required=True,
               hint="Set SESSION_TOKEN_PEPPER to a long random secret"),
        _check("no_insecure_prod_secret_defaults", ctx["prod_secrets_hygiene"], required=is_production(),
               hint="Replace known-insecure SECRETS_MASTER_KEY / SESSION_TOKEN_PEPPER dev defaults before any production deploy (including Soft Launch)"),
        _check("admin_auth_configured", ctx["admin_ok"], required=True,
               hint="Set ADMIN_API_KEY and/or ADMIN_EMAILS"),
        _check("b2b_demo_key_disabled", ctx["demo_disabled"] if strict_prod else True, required=False,
               hint="Unset BLACKDARK_B2B_DEMO_KEY or set to disabled in production"),
        _check("demo_key_not_publicly_exposed", (not expose_demo) if strict_prod else (not expose_demo or soft_launch),
               required=strict_prod, hint="Set EXPOSE_B2B_DEMO_KEY=false in strict production (never leak demo keys)"),
        _check("soft_launch_no_live_money", ctx["soft_launch_safe"], required=is_production(),
               hint="Soft Launch forbids LIVE_EXECUTION_ALLOW_API and EXPOSE_B2B_DEMO_KEY"),
        _check("admin_mfa_configured", _admin_mfa_ok(), required=strict_prod,
               hint="Set ADMIN_TOTP_SECRET (+ ADMIN_MFA_REQUIRED=true) for privileged admin MFA"),
        _check("expose_demo_key_off", not expose_demo, required=strict_prod,
               hint="EXPOSE_B2B_DEMO_KEY must be false in strict production"),
        _check("redis_shared_bus", ctx["redis_shared_ok"], required=viral_ha,
               hint="Add Railway/Upstash Redis -> REDIS_URL + SERVICE_BUS_LOCAL=false (required for VIRAL_MODE HA)"),
        _check("viral_multi_instance", ctx["multi_instance_ok"] if viral_ha else True, required=viral_ha,
               hint="Set WEB_CONCURRENCY≥2 and/or WEB_REPLICAS≥2 (or Railway numReplicas≥2). run_service.py honors WEB_CONCURRENCY via uvicorn --workers."),
        _check("viral_soft_launch_unset", (not soft_launch) if viral_ha else True, required=viral_ha,
               hint="Unset SOFT_LAUNCH for viral/HA production (Soft Launch SQLite is demo-only)"),
        _check("sentry_observability", ctx["sentry"], required=False,
               hint="Set SENTRY_DSN for production error tracking"),
        _check("uptime_self_probe", ctx["uptime_probe"], required=False,
               hint="UPTIME_SELF_PROBE_ENABLED=true (default) + UptimeRobot external"),
        _check("telegram_bot", telegram, required=False,
               hint="Set TELEGRAM_BOT_TOKEN + webhook for GTM growth loop"),
        _check("telegram_webhook_secret", (not telegram) or ctx["telegram_secret"], required=bool(telegram),
               hint="Set TELEGRAM_WEBHOOK_SECRET when TELEGRAM_BOT_TOKEN is set"),
        _check("price_feed_railway", not getattr(config, "PRICE_FEED_WS_ONLY", True), required=False,
               hint="PRICE_FEED_WS_ONLY=false on Railway cloud"),
        _check("soft_launch_mode", soft_launch, required=False,
               hint="SOFT_LAUNCH=true enables free SQLite demo without Postgres/billing webhooks"),
        _check(
            "identity_debug_tokens_off",
            (os.getenv("IDENTITY_DEBUG_TOKENS", "").lower() not in {"1", "true", "yes"}) if is_production() else True,
            required=is_production(),
            hint="Unset IDENTITY_DEBUG_TOKENS in production (runtime hard-off exists; env must stay false for hygiene)",
        ),
    ]


def _billing_provider_name(lemon: bool, stripe: bool) -> str:
    if lemon:
        return "lemon_squeezy"
    if stripe:
        return "stripe"
    return "none"


def evaluate_production_guard() -> dict[str, Any]:
    ctx = _collect_guard_context()
    checks = _build_guard_checks(ctx)
    required_fail = [c for c in checks if c["required"] and not c["ok"]]
    warn = [c for c in checks if not c["required"] and not c["ok"]]
    return {
        "production": is_production(),
        "soft_launch": ctx["soft_launch"],
        "strict_production": ctx["strict_prod"],
        "viral_mode": ctx["viral_mode"],
        "viral_ha_enforced": ctx["viral_ha"],
        "parallelism": ctx["parallel"],
        "service_mode": ctx["mode"],
        "database": "postgresql" if ctx["pg"] else "sqlite",
        "billing_provider": _billing_provider_name(ctx["lemon"], ctx["stripe"]),
        "checks": checks,
        "required_pass": len(required_fail) == 0,
        "required_failures": [c["id"] for c in required_fail],
        "warnings": [c["id"] for c in warn],
        "acquisition_honesty": {
            "sqlite_ok_for_pitch": bool(ctx["pg"]),
            "soft_launch_is_not_ha": ctx["soft_launch"],
            "iso_certificates_claimed": False,
            "note": (
                "PostgreSQL required for institutional pitch. Soft Launch SQLite is demo-only. "
                "Fernet vault = engineering posture, not an ISO 27001 certificate. "
                "Viral HA requires Postgres + Redis + multi-instance + SOFT_LAUNCH unset."
            ),
        },
        "railway_replicas_hint": "Set numReplicas=2 in railway.json + WEB_CONCURRENCY≥2 + WEB_REPLICAS=2",
        "viral_playbook": "docs/VIRAL_LAUNCH_CAPACITY.md",
        "uptimerobot_url": f"{os.getenv('APP_BASE_URL', 'https://blackdark-production.up.railway.app')}/health/live",
    }


def enforce_production_guard(*, raise_on_fail: bool | None = None) -> dict[str, Any]:
    """Fail closed in production when required checks fail (opt-out via env)."""
    report = evaluate_production_guard()
    if not is_production():
        # Distinct return shape so callers can tell "not enforced" from "enforced OK".
        return {**report, "enforced": False}
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
    return {**report, "enforced": True}


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
