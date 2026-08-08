"""
BLACKDARK — Admin / user TOTP MFA (RFC 6238 via pyotp).

Engineering control for institutional packaging. Not a SOC2 certificate.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
from typing import Any

import config

ISSUER = "BLACKDARK"


def _fernet():
    from cryptography.fernet import Fernet

    raw = (
        os.getenv("SECRETS_MASTER_KEY", "").strip()
        or os.getenv("SECRETS_VAULT_KEY", "").strip()
        or os.getenv("MFA_ENCRYPTION_KEY", "").strip()
    )
    if not raw:
        if getattr(config, "ENV", "development") in {"production", "prod"} or (
            os.getenv("ENV") or ""
        ).lower() in {"production", "prod"}:
            raise RuntimeError("MFA requires SECRETS_MASTER_KEY (or MFA_ENCRYPTION_KEY)")
        # Deterministic local-dev key — never use in production (guarded above).
        digest = hashlib.sha256(b"blackdark-mfa-dev-only").digest()
        raw = base64.urlsafe_b64encode(digest).decode("ascii")
    if len(raw) == 44 and raw.endswith("="):
        key = raw.encode("utf-8")
    else:
        key = base64.urlsafe_b64encode(hashlib.sha256(raw.encode("utf-8")).digest())
    return Fernet(key)


def encrypt_secret(plain: str) -> str:
    return _fernet().encrypt(plain.encode("utf-8")).decode("utf-8")


def decrypt_secret(token: str) -> str:
    return _fernet().decrypt(token.encode("utf-8")).decode("utf-8")


def generate_totp_secret() -> str:
    import pyotp

    return pyotp.random_base32()


def provisioning_uri(*, email: str, secret: str) -> str:
    import pyotp

    return pyotp.TOTP(secret).provisioning_uri(name=email, issuer_name=ISSUER)


def verify_totp(secret: str, code: str, *, valid_window: int = 1) -> bool:
    import pyotp

    cleaned = (code or "").strip().replace(" ", "")
    if not cleaned.isdigit():
        return False
    return bool(pyotp.TOTP(secret).verify(cleaned, valid_window=valid_window))


def generate_recovery_codes(n: int = 8) -> list[str]:
    return [secrets.token_hex(4) for _ in range(n)]


def hash_recovery_code(code: str) -> str:
    pepper = os.getenv("SESSION_TOKEN_PEPPER", "blackdark-mfa-recovery").strip().encode()
    # PBKDF2 — recovery codes are secrets; avoid single-pass SHA-256.
    return hashlib.pbkdf2_hmac(
        "sha256",
        code.strip().lower().encode(),
        pepper + b":mfa-recovery",
        120_000,
    ).hex()


def verify_recovery_code(code: str, stored_hashes: list[str]) -> str | None:
    """Return the matching hash if valid, else None.

    Only PBKDF2 digests are accepted (no single-pass SHA-256 legacy path).
    """
    digest = hash_recovery_code(code)
    for h in stored_hashes:
        if hmac.compare_digest(digest, h):
            return h
    return None


async def mfa_status_for_user(user_id: int) -> dict[str, Any]:
    from database import fetch_user_mfa_row

    row = await fetch_user_mfa_row(user_id)
    if not row:
        return {"enabled": False, "enrolled": False}
    return {
        "enabled": bool(row.get("mfa_enabled")),
        "enrolled": bool(row.get("mfa_secret_enc")),
        "recovery_codes_remaining": int(row.get("mfa_recovery_remaining") or 0),
    }


async def begin_mfa_enroll(user_id: int, email: str) -> dict[str, Any]:
    from database import set_user_mfa_pending_secret

    secret = generate_totp_secret()
    await set_user_mfa_pending_secret(user_id, encrypt_secret(secret))
    return {
        "secret": secret,
        "otpauth_uri": provisioning_uri(email=email, secret=secret),
        "issuer": ISSUER,
        "note": "Scan with an authenticator app, then POST /api/auth/mfa/confirm with a code.",
    }


async def confirm_mfa_enroll(user_id: int, code: str) -> dict[str, Any]:
    from database import (
        enable_user_mfa,
        fetch_user_mfa_row,
        set_user_mfa_recovery_hashes,
    )

    row = await fetch_user_mfa_row(user_id)
    enc = (row or {}).get("mfa_secret_enc") or (row or {}).get("mfa_pending_secret_enc")
    if not enc:
        raise ValueError("MFA enrollment not started")
    secret = decrypt_secret(str(enc))
    if not verify_totp(secret, code):
        raise ValueError("Invalid authenticator code")
    recovery = generate_recovery_codes()
    hashes = [hash_recovery_code(c) for c in recovery]
    await enable_user_mfa(user_id, encrypt_secret(secret))
    await set_user_mfa_recovery_hashes(user_id, hashes)
    return {
        "enabled": True,
        "recovery_codes": recovery,
        "note": "Store recovery codes offline. They are shown once.",
    }


async def disable_mfa(user_id: int, code: str) -> dict[str, Any]:
    from database import clear_user_mfa, fetch_user_mfa_row

    row = await fetch_user_mfa_row(user_id)
    if not row or not row.get("mfa_enabled"):
        return {"enabled": False}
    secret = decrypt_secret(str(row["mfa_secret_enc"]))
    if not verify_totp(secret, code):
        # Allow recovery code as disable proof
        hashes = list(row.get("mfa_recovery_hashes") or [])
        matched = verify_recovery_code(code, hashes)
        if not matched:
            raise ValueError("Invalid MFA code")
    await clear_user_mfa(user_id)
    return {"enabled": False}


async def verify_user_mfa(user_id: int, code: str) -> bool:
    from database import consume_mfa_recovery_hash, fetch_user_mfa_row

    row = await fetch_user_mfa_row(user_id)
    if not row or not row.get("mfa_enabled") or not row.get("mfa_secret_enc"):
        return True
    secret = decrypt_secret(str(row["mfa_secret_enc"]))
    if verify_totp(secret, code):
        return True
    hashes = list(row.get("mfa_recovery_hashes") or [])
    matched = verify_recovery_code(code, hashes)
    if matched:
        await consume_mfa_recovery_hash(user_id, matched)
        return True
    return False


def admin_mfa_required() -> bool:
    """When true, admin routes require a recent MFA-verified session flag."""
    return os.getenv("ADMIN_MFA_REQUIRED", "true").lower() in {"1", "true", "yes"}
