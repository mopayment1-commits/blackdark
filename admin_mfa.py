"""
BLACKDARK — Admin TOTP MFA (NIST-aligned second factor for privileged access).
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger("BLACKDARK.AdminMFA")


def mfa_policy_enabled() -> bool:
    """When true, admin routes require a valid TOTP after identity match."""
    raw = os.getenv("ADMIN_MFA_REQUIRED", "true").strip().lower()
    return raw in {"1", "true", "yes"}


def system_admin_totp_configured() -> bool:
    return bool(os.getenv("ADMIN_TOTP_SECRET", "").strip())


def mfa_status() -> dict[str, Any]:
    return {
        "required": mfa_policy_enabled(),
        "system_totp_configured": system_admin_totp_configured(),
        "hint": "Set ADMIN_TOTP_SECRET (base32) and enroll admin emails via /api/auth/admin/totp/setup",
    }


def generate_totp_secret() -> str:
    import pyotp

    return pyotp.random_base32()


def provisioning_uri(secret: str, email: str, *, issuer: str = "BLACKDARK Admin") -> str:
    import pyotp

    return pyotp.TOTP(secret).provisioning_uri(name=email, issuer_name=issuer)


def verify_totp(secret: str, code: str, *, window: int = 1) -> bool:
    if not secret or not code:
        return False
    import pyotp

    cleaned = "".join(ch for ch in str(code) if ch.isdigit())
    if len(cleaned) < 6:
        return False
    return bool(pyotp.TOTP(secret).verify(cleaned, valid_window=window))


def verify_system_admin_totp(code: str | None) -> bool:
    secret = os.getenv("ADMIN_TOTP_SECRET", "").strip()
    if not secret:
        return False
    return verify_totp(secret, code or "")


def encrypt_totp_secret(secret: str) -> str:
    from secrets_vault import encrypt_secret

    return encrypt_secret(secret)


def decrypt_totp_secret(ciphertext: str) -> str:
    from secrets_vault import decrypt_secret

    return decrypt_secret(ciphertext)


async def enroll_user_totp(user_id: int, email: str) -> dict[str, Any]:
    from database import set_user_totp_secret

    secret = generate_totp_secret()
    await set_user_totp_secret(user_id, encrypt_totp_secret(secret), enabled=False)
    return {
        "secret": secret,
        "otpauth_url": provisioning_uri(secret, email),
        "enabled": False,
        "next": "POST /api/auth/admin/totp/verify with the 6-digit code to enable MFA",
    }


async def confirm_user_totp(user_id: int, code: str) -> bool:
    from database import fetch_user_by_id, set_user_totp_enabled

    user = await fetch_user_by_id(user_id)
    if not user or not user.get("totp_secret_encrypted"):
        return False
    secret = decrypt_totp_secret(str(user["totp_secret_encrypted"]))
    if not verify_totp(secret, code):
        return False
    await set_user_totp_enabled(user_id, True)
    return True


async def verify_user_totp(user: dict[str, Any], code: str | None) -> bool:
    if not user.get("totp_enabled"):
        return False
    enc = user.get("totp_secret_encrypted")
    if not enc:
        return False
    try:
        secret = decrypt_totp_secret(str(enc))
    except Exception:
        logger.warning("Failed to decrypt user TOTP secret | user_id=%s", user.get("id"))
        return False
    return verify_totp(secret, code or "")
