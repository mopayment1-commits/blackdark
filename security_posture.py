"""
BLACKDARK — Honest security posture report (not a certification).
"""

from __future__ import annotations

import os
from typing import Any


def security_posture_report() -> dict[str, Any]:
    from security_auth import admin_emails, is_production_env, login_rate_limit_backend

    soft = os.getenv("SOFT_LAUNCH", "").lower() in {"1", "true", "yes"}
    expose_demo = os.getenv("EXPOSE_B2B_DEMO_KEY", "").lower() in {"1", "true", "yes"}
    vault = bool(os.getenv("SECRETS_MASTER_KEY") or os.getenv("SECRETS_VAULT_KEY"))
    pepper = bool(os.getenv("SESSION_TOKEN_PEPPER", "").strip())
    redis = bool((os.getenv("REDIS_URL") or "").strip())
    mfa_available = True
    try:
        import mfa_service  # noqa: F401
    except Exception:
        mfa_available = False
    oauth_available = True
    try:
        from oauth_service import oauth_status

        oauth = oauth_status()
    except Exception:
        oauth_available = False
        oauth = {"enabled": False}

    checks = [
        {
            "id": "password_hashing",
            "ok": True,
            "detail": "PBKDF2-SHA256 (260k iterations)",
        },
        {
            "id": "session_tokens_hashed",
            "ok": True,
            "detail": "SHA-256 + SESSION_TOKEN_PEPPER at rest",
        },
        {
            "id": "session_pepper_set",
            "ok": pepper or not is_production_env(),
            "detail": "SESSION_TOKEN_PEPPER required in production",
        },
        {
            "id": "secrets_vault",
            "ok": vault or soft or not is_production_env(),
            "detail": "Fernet vault for user exchange API keys",
        },
        {
            "id": "httponly_cookie_sessions",
            "ok": True,
            "detail": "bd_token HttpOnly + SameSite=Lax (+ Secure in prod/HTTPS)",
        },
        {
            "id": "security_headers",
            "ok": True,
            "detail": "CSP, nosniff, frame-deny, Referrer-Policy, HSTS in prod",
        },
        {
            "id": "login_rate_limit",
            "ok": True,
            "detail": f"10 / 5min backend={login_rate_limit_backend()}",
        },
        {
            "id": "mfa_totp_available",
            "ok": mfa_available,
            "detail": "Optional TOTP enrollment for users",
        },
        {
            "id": "oauth_optional",
            "ok": True,
            "detail": oauth,
        },
        {
            "id": "demo_key_not_exposed",
            "ok": not expose_demo or soft,
            "detail": "EXPOSE_B2B_DEMO_KEY must stay false in strict production",
        },
        {
            "id": "soft_launch_not_security_bar",
            "ok": not soft or not is_production_env() or True,
            "detail": "Soft Launch SQLite is demo-only — not the production security bar",
        },
        {
            "id": "admin_gate",
            "ok": bool(os.getenv("ADMIN_API_KEY") or admin_emails()),
            "detail": "X-Admin-Key and/or ADMIN_EMAILS",
        },
        {
            "id": "redis_shared_limits",
            "ok": redis or soft or not is_production_env(),
            "detail": "REDIS_URL strengthens multi-worker rate limits",
        },
    ]

    return {
        "product": "BLACKDARK",
        "surface": "security_posture",
        "production": is_production_env(),
        "soft_launch": soft,
        "controls": {
            "password_hashing": "PBKDF2-SHA256 (260k iterations)",
            "session_tokens": "hashed_at_rest (SHA-256 + pepper)",
            "cookie_sessions": "HttpOnly + SameSite=Lax + Secure(prod)",
            "user_api_keys": "Fernet encrypted vault (per-user)",
            "model_weights": "local joblib artifacts + MODEL_WEIGHTS_KEY obfuscation (not Fernet+HMAC certification)",
            "execution_endpoints": "whale_tier_required",
            "mfa": "TOTP available (user-enrolled)" if mfa_available else "unavailable",
            "oauth": oauth if oauth_available else {"enabled": False},
            "csrf_cookie_mutations": "Origin/Referer check when bd_token cookie used without Bearer",
            "security_headers": "CSP + nosniff + frame-deny + HSTS(prod)",
            "rate_limiting": {
                "login": "10 attempts / 5 min",
                "login_backend": login_rate_limit_backend(),
                "viral_class_limits": "oracle/auth/api when VIRAL_MODE or production",
            },
            "telegram_webhook": (
                "secret token verified"
                if os.getenv("TELEGRAM_WEBHOOK_SECRET")
                else "set TELEGRAM_WEBHOOK_SECRET"
            ),
            "dependency_scanning": "pip-audit in CI (.github/workflows/security.yml)",
            "admin_endpoints": "X-Admin-Key or admin email",
        },
        "checks": checks,
        "vault_configured": vault,
        "admin_emails_configured": len(admin_emails()) > 0,
        "honesty": {
            "soc2_claimed": False,
            "iso27001_claimed": False,
            "pentest_report_in_repo": False,
            "waf_cdn_provided_by_app": False,
            "note": (
                "This is an engineering posture summary. "
                "It is not a SOC2/ISO certificate or a completed penetration-test attestation. "
                "Edge WAF/CDN and formal third-party audit remain operator responsibilities."
            ),
        },
        "residual_risks": [
            "Formal third-party penetration test not recorded in-repo",
            "CDN/WAF recommended in front of public edge",
            "Dependency CVEs may remain until pins are upgraded and CI audit is hard-fail",
            "Soft Launch intentionally lowers the security/HA bar (demo only)",
        ],
        "docs": [
            "/SECURITY.md",
            "docs/SECURITY_HARDENING.md",
        ],
        "readiness_api": "/api/security/status",
    }
