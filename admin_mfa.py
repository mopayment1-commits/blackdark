"""
BLACKDARK — System-admin TOTP MFA (privileged second factor).

When ADMIN_MFA_REQUIRED is enabled (default true in production), admin routes
require a valid X-Admin-TOTP matching ADMIN_TOTP_SECRET, or the admin user's
enrolled TOTP.

Not a SOC2 certificate — engineering control for privileged access.
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger("BLACKDARK.AdminMFA")


def mfa_policy_enabled() -> bool:
    try:
        from session_account_security_1019 import assert_no_skip_admin_mfa

        assert_no_skip_admin_mfa()
    except ImportError:
        pass
    raw = os.getenv("ADMIN_MFA_REQUIRED", "").strip().lower()
    if raw in {"0", "false", "no", "off"}:
        return False
    if raw in {"1", "true", "yes", "on"}:
        return True
    env = (os.getenv("ENV") or os.getenv("RAILWAY_ENVIRONMENT") or "").strip().lower()
    return env in {"production", "prod"}


def system_admin_totp_configured() -> bool:
    return bool(os.getenv("ADMIN_TOTP_SECRET", "").strip())


def generate_totp_secret() -> str:
    from mfa_service import generate_totp_secret as _gen

    return _gen()


def provisioning_uri(*, secret: str, label: str = "BLACKDARK Admin") -> str:
    import pyotp

    return pyotp.TOTP(secret).provisioning_uri(name=label, issuer_name="BLACKDARK")


def verify_totp(secret: str, code: str) -> bool:
    from mfa_service import verify_totp as _verify

    return _verify(secret, code)


def verify_system_admin_totp(code: str | None) -> bool:
    secret = os.getenv("ADMIN_TOTP_SECRET", "").strip()
    if not secret or not code:
        return False
    return verify_totp(secret, str(code).strip())


def mfa_status() -> dict[str, Any]:
    return {
        "policy_enabled": mfa_policy_enabled(),
        "system_admin_totp_configured": system_admin_totp_configured(),
        "hint": (
            "Set ADMIN_TOTP_SECRET (base32 from: python -c \"import pyotp; print(pyotp.random_base32())\") "
            "and send header X-Admin-TOTP on admin routes when policy is enabled."
        ),
    }


async def assert_admin_mfa(
    *,
    x_admin_totp: str | None,
    user: dict | None = None,
) -> None:
    """Raise HTTPException if admin MFA policy is unmet."""
    from fastapi import HTTPException

    if not mfa_policy_enabled():
        return
    if verify_system_admin_totp(x_admin_totp):
        return
    if user and user.get("id") and x_admin_totp:
        try:
            from mfa_service import verify_user_mfa

            if await verify_user_mfa(int(user["id"]), str(x_admin_totp)):
                return
        except Exception:
            logger.debug("user MFA admin check failed", exc_info=True)
    if not system_admin_totp_configured():
        raise HTTPException(
            status_code=403,
            detail={
                "error": "admin_mfa_not_configured",
                "message": "ADMIN_TOTP_SECRET must be configured when ADMIN_MFA_REQUIRED=true",
            },
        )
    raise HTTPException(
        status_code=403,
        detail={
            "error": "admin_mfa_required",
            "message": "Valid X-Admin-TOTP required for privileged actions",
        },
    )
