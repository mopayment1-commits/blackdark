"""
BLACKDARK — Production environment guard (ARC / launch recommendations).
"""

from __future__ import annotations

import os
from typing import Any

import config
from log_safety import env_configured, env_matches_any, text_matches_any, untainted_catalog_ids

# Literal check-id catalog — log/print sinks may only emit ids re-sourced from here
# so CodeQL cannot treat secret-derived container taint as clear-text logging.
CHECK_ID_CATALOG: tuple[str, ...] = (
    "postgres_database",
    "sqlite_forbidden_in_strict_production",
    "at_rest_encryption_posture",
    "service_mode_web",
    "billing_checkout",
    "billing_entitlement_webhook",
    "billing_whale_checkout_usd",
    "billing_currency_usd",
    "secrets_master_key",
    "session_token_pepper",
    "no_insecure_prod_secret_defaults",
    "admin_auth_configured",
    "admin_mfa_configured",
    "identity_debug_tokens_off",
    "b2b_demo_key_disabled",
    "demo_key_not_publicly_exposed",
    "soft_launch_no_live_money",
    "expose_demo_key_off",
    "redis_shared_bus",
    "viral_multi_instance",
    "viral_soft_launch_unset",
    "sentry_observability",
    "uptime_self_probe",
    "telegram_bot",
    "telegram_webhook_secret",
    "price_feed_railway",
    "soft_launch_mode",
)

_INSECURE_DEFAULTS = (
    "blackdark-dev-change-me-in-production",
    "blackdark-session-pepper-change-me",
    "change-me",
    "changeme",
    "secret",
)
_DISABLED_DEMO_VALUES = ("disabled", "off", "none")


def is_production() -> bool:
    """True when any ENV/APP_ENV/ENVIRONMENT/RAILWAY token is production (fail-closed OR).

    Polluted ENV=development must not hide APP_ENV=production.
    """
    tokens = [
        (os.getenv("ENV") or "").strip().lower(),
        (os.getenv("APP_ENV") or "").strip().lower(),
        (os.getenv("ENVIRONMENT") or "").strip().lower(),
        (os.getenv("RAILWAY_ENVIRONMENT") or "").strip().lower(),
    ]
    return any(t in {"production", "prod"} for t in tokens)


def _safe_failure_ids(raw_ids: list[str] | set[str]) -> list[str]:
    return untainted_catalog_ids(raw_ids, CHECK_ID_CATALOG)


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
        return env_configured("LEMON_SQUEEZY_WEBHOOK_SECRET")
    if stripe:
        return env_configured("STRIPE_WEBHOOK_SECRET")
    return True


def _secret_hygiene() -> tuple[bool, bool, bool]:
    """Presence + insecure-default checks without retaining clear-text secrets."""
    secrets_ok = env_configured("SECRETS_MASTER_KEY") or env_configured("SECRETS_VAULT_KEY")
    session_pepper_ok = env_configured("SESSION_TOKEN_PEPPER")
    insecure_master = env_matches_any("SECRETS_MASTER_KEY", _INSECURE_DEFAULTS) or env_matches_any(
        "SECRETS_VAULT_KEY", _INSECURE_DEFAULTS
    )
    insecure_pepper = env_matches_any("SESSION_TOKEN_PEPPER", _INSECURE_DEFAULTS)
    no_insecure_secrets = (not secrets_ok) or (not insecure_master)
    no_insecure_pepper = (not session_pepper_ok) or (not insecure_pepper)
    prod_hygiene = (not is_production()) or (no_insecure_secrets and no_insecure_pepper)
    return secrets_ok, session_pepper_ok, prod_hygiene


def _demo_key_disabled() -> bool:
    """True when B2B demo key unset/disabled — bool only, no clear-text returned."""
    cfg = getattr(config, "B2B_DEMO_API_KEY", None)
    if cfg is not None and str(cfg).strip():
        return text_matches_any(str(cfg), _DISABLED_DEMO_VALUES)
    if not env_configured("BLACKDARK_B2B_DEMO_KEY"):
        return True
    return env_matches_any("BLACKDARK_B2B_DEMO_KEY", _DISABLED_DEMO_VALUES)


def _redis_configured() -> bool:
    return bool((getattr(config, "REDIS_URL", "") or "").strip()) or env_configured("REDIS_URL")


def _telegram_active() -> bool:
    if _env_truthy("LAUNCH_SKIP_TELEGRAM"):
        return False
    return env_configured("TELEGRAM_BOT_TOKEN")


def _collect_guard_context() -> dict[str, Any]:
    from billing_service import billing_configured
    from postgres_backend import use_postgres

    pg = use_postgres()
    soft_launch = _env_truthy("SOFT_LAUNCH")
    lemon = env_configured("LEMON_SQUEEZY_CHECKOUT_PRO")
    stripe = env_configured("STRIPE_SECRET_KEY")
    lemon_whale = env_configured("LEMON_SQUEEZY_CHECKOUT_WHALE")
    stripe_price_whale = env_configured("STRIPE_PRICE_WHALE")
    expose_demo = _env_truthy("EXPOSE_B2B_DEMO_KEY")
    live_exec = _env_truthy("LIVE_EXECUTION_ALLOW_API")
    strict_prod = is_production() and not soft_launch
    viral_mode = _env_truthy("VIRAL_MODE", "true")
    viral_ha = strict_prod and viral_mode
    parallel = _parallelism_snapshot()
    redis_ok = _redis_configured()
    secrets_ok, session_pepper_ok, prod_secrets_hygiene = _secret_hygiene()
    return {
        "pg": pg,
        "mode": _service_mode(),
        "soft_launch": soft_launch,
        # Never retain connection-string material in guard state.
        "redis_configured": redis_ok,
        "billing": billing_configured(),
        "sentry": env_configured("SENTRY_DSN"),
        "uptime_probe": _env_truthy("UPTIME_SELF_PROBE_ENABLED", "true"),
        "lemon": lemon,
        "stripe": stripe,
        "telegram": _telegram_active(),
        "telegram_secret": env_configured("TELEGRAM_WEBHOOK_SECRET"),
        "whale_checkout_ok": lemon_whale or stripe_price_whale or (stripe and not lemon),
        "secrets_ok": secrets_ok,
        "session_pepper_ok": session_pepper_ok,
        "admin_ok": env_configured("ADMIN_API_KEY") or env_configured("ADMIN_EMAILS"),
        "demo_disabled": _demo_key_disabled(),
        "expose_demo": expose_demo,
        "soft_launch_safe": (not soft_launch) or (not live_exec and not expose_demo),
        "billing_webhook_ok": _billing_webhook_ok(lemon, stripe),
        "strict_prod": strict_prod,
        "viral_mode": viral_mode,
        "viral_ha": viral_ha,
        "parallel": parallel,
        "redis_shared_ok": redis_ok and not getattr(config, "SERVICE_BUS_LOCAL", True),
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


def _env_flag(name: str, default: str = "") -> bool:
    return os.getenv(name, default).lower() in {"1", "true", "yes"}


def _billing_webhook_ready(lemon: bool, stripe: bool, lemon_webhook: bool, stripe_webhook: bool) -> bool:
    if lemon:
        return lemon_webhook
    if stripe:
        return stripe_webhook
    return True


def _effective_parallelism() -> dict[str, Any]:
    try:
        from viral_capacity import effective_parallelism

        return effective_parallelism()
    except Exception:
        viral = _env_flag("VIRAL_MODE", "true")
        default_workers = 2 if viral else 1
        return {
            "workers": int(os.getenv("WEB_CONCURRENCY", os.getenv("UVICORN_WORKERS", str(default_workers))) or default_workers),
            "replicas": int(os.getenv("WEB_REPLICAS", "1") or 1),
            "parallelism": 1,
        }


def _admin_mfa_ready() -> bool:
    return (
        (not __import__("admin_mfa", fromlist=["mfa_policy_enabled"]).mfa_policy_enabled())
        or __import__("admin_mfa", fromlist=["system_admin_totp_configured"]).system_admin_totp_configured()
    )


def _secret_hygiene_flags() -> tuple[bool, bool, bool]:
    # Alias — single implementation (digest-based, no clear-text retention).
    return _secret_hygiene()


def _production_guard_state() -> dict[str, Any]:
    from billing_service import billing_configured
    from postgres_backend import use_postgres

    pg = use_postgres()
    production = is_production()
    soft_launch = _env_flag("SOFT_LAUNCH")
    redis_ok = _redis_configured()
    lemon = env_configured("LEMON_SQUEEZY_CHECKOUT_PRO")
    stripe = env_configured("STRIPE_SECRET_KEY")
    secrets_ok, session_pepper_ok, prod_secrets_hygiene = _secret_hygiene_flags()
    expose_demo = _env_flag("EXPOSE_B2B_DEMO_KEY")
    live_exec = _env_flag("LIVE_EXECUTION_ALLOW_API")
    strict_prod = production and not soft_launch
    viral_mode = _env_flag("VIRAL_MODE", "true")
    viral_ha = strict_prod and viral_mode
    parallel = _effective_parallelism()
    lemon_webhook = env_configured("LEMON_SQUEEZY_WEBHOOK_SECRET")
    stripe_webhook = env_configured("STRIPE_WEBHOOK_SECRET")
    return {
        "pg": pg,
        "mode": _service_mode(),
        "production": production,
        "soft_launch": soft_launch,
        "strict_prod": strict_prod,
        "viral_mode": viral_mode,
        "viral_ha": viral_ha,
        "parallel": parallel,
        "billing": billing_configured(),
        "sentry": env_configured("SENTRY_DSN"),
        "uptime_probe": _env_flag("UPTIME_SELF_PROBE_ENABLED", "true"),
        "lemon": lemon,
        "stripe": stripe,
        "lemon_whale": env_configured("LEMON_SQUEEZY_CHECKOUT_WHALE"),
        "stripe_price_whale": env_configured("STRIPE_PRICE_WHALE"),
        "telegram": _telegram_active(),
        "telegram_secret": env_configured("TELEGRAM_WEBHOOK_SECRET"),
        "lemon_webhook": lemon_webhook,
        "stripe_webhook": stripe_webhook,
        "secrets_ok": secrets_ok,
        "session_pepper_ok": session_pepper_ok,
        "admin_ok": env_configured("ADMIN_API_KEY") or env_configured("ADMIN_EMAILS"),
        "demo_disabled": _demo_key_disabled(),
        "expose_demo": expose_demo,
        "soft_launch_safe": (not soft_launch) or (not live_exec and not expose_demo),
        "billing_webhook_ok": _billing_webhook_ready(lemon, stripe, lemon_webhook, stripe_webhook),
        "redis_shared_ok": redis_ok and not getattr(config, "SERVICE_BUS_LOCAL", True),
        "multi_instance_ok": int(parallel.get("parallelism") or 1) >= 2,
        "sqlite_forbidden_ok": pg if strict_prod else (pg or soft_launch or not production),
        "prod_secrets_hygiene": prod_secrets_hygiene,
    }

def _base_guard_checks(s: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        _check(
            "postgres_database",
            s["pg"] or s["soft_launch"],
            required=True,
            hint="Set Postgres DATABASE_URL=postgresql://... (or SOFT_LAUNCH=true for free SQLite demo)",
        ),
        _check(
            "sqlite_forbidden_in_strict_production",
            s["sqlite_forbidden_ok"],
            required=s["strict_prod"],
            hint=(
                "Strict production forbids SQLite. Set DATABASE_URL=postgresql://... "
                "and unset SOFT_LAUNCH before any institutional pitch."
            ),
        ),
        _check(
            "at_rest_encryption_posture",
            s["secrets_ok"],
            required=True,
            hint=(
                "Set SECRETS_MASTER_KEY or SECRETS_VAULT_KEY for Fernet at-rest encryption "
                "of user API keys / sensitive vault material (engineering posture ≠ ISO 27001 cert)"
            ),
        ),
        _check("service_mode_web", s["mode"] == "web", required=True, hint="Set SERVICE_MODE=web on Railway (lighter Oracle-only process)"),
    ]


def _billing_guard_checks(s: dict[str, Any]) -> list[dict[str, Any]]:
    whale_checkout_ok = s["lemon_whale"] or s["stripe_price_whale"] or (s["stripe"] and not s["lemon"])
    return [
        _check(
            "billing_checkout",
            s["billing"] or s["soft_launch"],
            required=True,
            hint="Set LEMON_SQUEEZY_CHECKOUT_PRO or Stripe live keys (or SOFT_LAUNCH=true)",
        ),
        _check(
            "billing_entitlement_webhook",
            s["billing_webhook_ok"] or s["soft_launch"],
            required=True,
            hint=(
                "Set LEMON_SQUEEZY_WEBHOOK_SECRET (POST /webhook/lemon) "
                "or STRIPE_WEBHOOK_SECRET (POST /webhook) — or SOFT_LAUNCH=true"
            ),
        ),
        _check(
            "billing_whale_checkout_usd",
            whale_checkout_ok or s["soft_launch"],
            required=False,
            hint=(
                "Set LEMON_SQUEEZY_CHECKOUT_WHALE or STRIPE_PRICE_WHALE "
                "before promoting Decision Desk ($49 USD)"
            ),
        ),
        _check(
            "billing_currency_usd",
            True,
            required=False,
            hint="Self-serve Trust OS SKUs are USD-only (see docs/PAYMENTS_USD_SECURITY.md)",
        ),
    ]


def _security_guard_checks(s: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        _check("secrets_master_key", s["secrets_ok"], required=True, hint="Set SECRETS_MASTER_KEY or SECRETS_VAULT_KEY (no insecure default in prod)"),
        _check("session_token_pepper", s["session_pepper_ok"], required=True, hint="Set SESSION_TOKEN_PEPPER to a long random secret"),
        _check(
            "no_insecure_prod_secret_defaults",
            s["prod_secrets_hygiene"],
            required=s["production"],
            hint=(
                "Replace known-insecure SECRETS_MASTER_KEY / SESSION_TOKEN_PEPPER "
                "dev defaults before any production deploy (including Soft Launch)"
            ),
        ),
        _check("admin_auth_configured", s["admin_ok"], required=True, hint="Set ADMIN_API_KEY and/or ADMIN_EMAILS"),
        _check("admin_mfa_configured", _admin_mfa_ready(), required=s["strict_prod"], hint="Set ADMIN_TOTP_SECRET (+ ADMIN_MFA_REQUIRED=true) for privileged admin MFA"),
        _check(
            "identity_debug_tokens_off",
            os.getenv("IDENTITY_DEBUG_TOKENS", "").lower() not in {"1", "true", "yes"} if s["production"] else True,
            required=s["production"],
            hint="Unset IDENTITY_DEBUG_TOKENS in production (runtime hard-off exists; env must stay false for hygiene)",
        ),
    ]


def _demo_and_viral_guard_checks(s: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        _check("b2b_demo_key_disabled", s["demo_disabled"] if s["strict_prod"] else True, required=False, hint="Unset BLACKDARK_B2B_DEMO_KEY or set to disabled in production"),
        _check("demo_key_not_publicly_exposed", not s["expose_demo"] if s["strict_prod"] else (not s["expose_demo"] or s["soft_launch"]), required=s["strict_prod"], hint="Set EXPOSE_B2B_DEMO_KEY=false in strict production (never leak demo keys)"),
        _check("soft_launch_no_live_money", s["soft_launch_safe"], required=s["production"], hint="Soft Launch forbids LIVE_EXECUTION_ALLOW_API and EXPOSE_B2B_DEMO_KEY"),
        _check("expose_demo_key_off", not s["expose_demo"], required=s["strict_prod"], hint="EXPOSE_B2B_DEMO_KEY must be false in strict production"),
        _check("redis_shared_bus", s["redis_shared_ok"], required=s["viral_ha"], hint="Add Railway/Upstash Redis -> REDIS_URL + SERVICE_BUS_LOCAL=false (required for VIRAL_MODE HA)"),
        _check(
            "viral_multi_instance",
            s["multi_instance_ok"] if s["viral_ha"] else True,
            required=s["viral_ha"],
            hint=(
                "Set WEB_CONCURRENCY≥2 and/or WEB_REPLICAS≥2 (or Railway numReplicas≥2). "
                "run_service.py honors WEB_CONCURRENCY via uvicorn --workers."
            ),
        ),
        _check("viral_soft_launch_unset", not s["soft_launch"] if s["viral_ha"] else True, required=s["viral_ha"], hint="Unset SOFT_LAUNCH for viral/HA production (Soft Launch SQLite is demo-only)"),
    ]


def _observability_growth_checks(s: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        _check("sentry_observability", s["sentry"], required=False, hint="Set SENTRY_DSN for production error tracking"),
        _check("uptime_self_probe", s["uptime_probe"], required=False, hint="UPTIME_SELF_PROBE_ENABLED=true (default) + UptimeRobot external"),
        _check("telegram_bot", s["telegram"], required=False, hint="Set TELEGRAM_BOT_TOKEN + webhook for GTM growth loop"),
        _check("telegram_webhook_secret", (not s["telegram"]) or s["telegram_secret"], required=bool(s["telegram"]), hint="Set TELEGRAM_WEBHOOK_SECRET when TELEGRAM_BOT_TOKEN is set"),
        _check("price_feed_railway", not getattr(config, "PRICE_FEED_WS_ONLY", True), required=False, hint="PRICE_FEED_WS_ONLY=false on Railway cloud"),
        _check("soft_launch_mode", s["soft_launch"], required=False, hint="SOFT_LAUNCH=true enables free SQLite demo without Postgres/billing webhooks"),
    ]


def _production_guard_checks(s: dict[str, Any]) -> list[dict[str, Any]]:
    return (
        _base_guard_checks(s)
        + _billing_guard_checks(s)
        + _security_guard_checks(s)
        + _demo_and_viral_guard_checks(s)
        + _observability_growth_checks(s)
    )


def _billing_provider(s: dict[str, Any]) -> str:
    if s["lemon"]:
        return "lemon_squeezy"
    if s["stripe"]:
        return "stripe"
    return "none"


def _production_guard_report(s: dict[str, Any], checks: list[dict[str, Any]]) -> dict[str, Any]:
    required_fail = [c for c in checks if c["required"] and not c["ok"]]
    warn = [c for c in checks if not c["required"] and not c["ok"]]
    # Re-emit ids from the literal catalog only — breaks clear-text-logging taint
    # from secret-derived ok flags stored on check dicts.
    failure_ids = _safe_failure_ids([c["id"] for c in required_fail])
    warning_ids = _safe_failure_ids([c["id"] for c in warn])
    return {
        "production": s["production"],
        "soft_launch": s["soft_launch"],
        "strict_production": s["strict_prod"],
        "viral_mode": s["viral_mode"],
        "viral_ha_enforced": s["viral_ha"],
        "parallelism": s["parallel"],
        "service_mode": s["mode"],
        "database": "postgresql" if s["pg"] else "sqlite",
        "billing_provider": _billing_provider(s),
        "checks": checks,
        "required_pass": len(failure_ids) == 0,
        "required_failures": failure_ids,
        "warnings": warning_ids,
        "acquisition_honesty": {
            "sqlite_ok_for_pitch": bool(s["pg"]),
            "soft_launch_is_not_ha": s["soft_launch"],
            "iso_certificates_claimed": False,
            "note": (
                "PostgreSQL required for institutional pitch. Soft Launch SQLite is demo-only. "
                "Fernet vault = engineering posture, not an ISO 27001 certificate. "
                "Viral HA requires Postgres + Redis + multi-instance + SOFT_LAUNCH unset."
            ),
        },
        "railway_replicas_hint": "Set numReplicas=2 in railway.json + WEB_CONCURRENCY≥2 + WEB_REPLICAS=2",
        "viral_playbook": "docs/VIRAL_LAUNCH_CAPACITY.md",
        "uptimerobot_url": (
            (os.getenv("APP_BASE_URL") or "https://blackdark-production.up.railway.app").rstrip("/")
            + "/health/live"
        ),
    }


def evaluate_production_guard() -> dict[str, Any]:
    state = _production_guard_state()
    checks = _production_guard_checks(state)
    return _production_guard_report(state, checks)


def public_guard_console_summary() -> dict[str, Any]:
    """Stdout/log-safe summary: booleans + catalog literal check ids only."""
    report = evaluate_production_guard()
    failures = _safe_failure_ids(report.get("required_failures") or [])
    warnings = _safe_failure_ids(report.get("warnings") or [])
    # Rebuild status lines from catalog literals + boolean ok only.
    status_lines: list[str] = []
    by_id = {str(c.get("id")): c for c in (report.get("checks") or [])}
    for cid in CHECK_ID_CATALOG:
        row = by_id.get(cid)
        if not row:
            continue
        ok = bool(row.get("ok"))
        status_lines.append(f"{cid}:{'pass' if ok else 'fail'}")
    return {
        "required_pass": bool(report.get("required_pass")),
        "soft_launch": bool(report.get("soft_launch")),
        "database": "postgresql" if report.get("database") == "postgresql" else "sqlite",
        "required_failure_count": len(failures),
        "warning_count": len(warnings),
        "required_failure_ids": failures,
        "warning_ids": warnings,
        "check_status_lines": status_lines,
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
    failures = _safe_failure_ids(report.get("required_failures") or [])
    if raise_on_fail and failures:
        raise RuntimeError(
            "Production guard failed required checks: " + ",".join(failures)
        )
    return {**report, "enforced": True}


def log_production_guard() -> None:
    import logging

    logger = logging.getLogger("BLACKDARK.ProductionGuard")
    if not is_production():
        logger.info("Production guard skipped (not production env)")
        return
    summary = public_guard_console_summary()
    failures = summary["required_failure_ids"]
    warnings = summary["warning_ids"]
    if failures:
        # Log count + catalog-literal codes only (never secret-derived containers).
        logger.warning(
            "Production guard REQUIRED failures count=%s codes=%s",
            summary["required_failure_count"],
            ",".join(failures),
        )
        if os.getenv("PRODUCTION_GUARD_FAIL_CLOSED", "true").lower() in {"1", "true", "yes"}:
            raise RuntimeError(
                "Production guard fail-closed: " + ",".join(failures)
            )
    if warnings:
        logger.info(
            "Production guard warnings count=%s codes=%s",
            summary["warning_count"],
            ",".join(warnings),
        )
    if summary["required_pass"]:
        logger.info("Production guard: all required checks pass")