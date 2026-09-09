"""Cross-surface timezone ownership registry — TZ-030."""

from __future__ import annotations

SURFACE_BINDINGS: dict[str, list[str]] = {
    "profile": ["templates/profile.html", "api/routers/auth.py", "timezone/resolver.py"],
    "dashboards": ["templates/dashboard.html", "static/js/bd_time.js", "timezone/format.py"],
    "charts": ["templates/dashboard.html", "templates/platform.html", "static/js/bd_time.js", "timezone/market.py"],
    "alerts_notifications": ["alert_service.py", "identity/security_notifications.py", "timezone/format.py"],
    "email": ["email_outbox.py", "identity/security_notifications.py", "timezone/format.py"],
    "ai_outputs": ["i18n_enforcement.py", "timezone/format.py"],
    "reports_exports": ["gdpr_service.py", "timezone/format.py"],
    "activity_logs": ["api/routers/auth.py", "identity/session_service.py", "timezone/format.py"],
    "billing": ["billing/subscription_engine.py", "timezone/format.py"],
    "api_contract": ["timezone/canonical.py", "timezone/request_context.py"],
}


def surface_audit() -> dict[str, list[str]]:
    return dict(SURFACE_BINDINGS)
