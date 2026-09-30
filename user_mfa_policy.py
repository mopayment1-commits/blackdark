"""
User MFA enrollment policy (CISA Secure by Demand — MFA by default).

Normative: CISA Secure by Demand Aug 2024; OWASP ASVS authentication.
"""

from __future__ import annotations

import os

from security_auth import is_production_env


def user_mfa_enrollment_required() -> bool:
    """When true, authenticated users without MFA may only access MFA setup routes."""
    raw = os.getenv("USER_MFA_ENROLL_REQUIRED", "").strip().lower()
    if raw in {"0", "false", "no", "off"}:
        return False
    if raw in {"1", "true", "yes", "on"}:
        return True
    # Production strict default: require enrollment (Launch-57 remediation).
    return is_production_env()


def mfa_setup_exempt_path(path: str) -> bool:
    """Paths reachable while MFA enrollment is pending."""
    if path.startswith("/api/auth/mfa/"):
        return True
    if path in {"/api/auth/logout", "/api/auth/identity", "/api/security/status"}:
        return True
    if path.startswith("/api/security/customer-logs"):
        return True
    return False


def assert_user_mfa_enrollment(user: dict, path: str) -> None:
    from fastapi import HTTPException

    if not user_mfa_enrollment_required():
        return
    if mfa_setup_exempt_path(path):
        return
    if bool(user.get("mfa_enabled")) or bool(int(user.get("mfa_enabled") or 0)):
        return
    raise HTTPException(
        status_code=403,
        detail={
            "error": "mfa_enrollment_required",
            "message": "Enroll TOTP at /api/auth/mfa/enroll before accessing this resource.",
            "policy": "USER_MFA_ENROLL_REQUIRED",
        },
    )
