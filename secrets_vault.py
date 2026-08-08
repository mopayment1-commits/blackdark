"""
BLACKDARK — Encrypted secrets vault for user exchange API keys (Fernet AES-128-CBC).
"""

from __future__ import annotations

import base64
import hashlib
import logging
import os
from datetime import date, datetime, timezone

logger = logging.getLogger("BLACKDARK.SecretsVault")

_fernet = None
_rotation_checked = False


def _derive_fernet_key(raw: str) -> bytes:
    digest = hashlib.sha256(raw.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def _is_production() -> bool:
    local_dev = os.getenv("LOCAL_DEV", "false").lower() in {"1", "true", "yes"}
    if local_dev:
        return False
    env = (os.getenv("ENV") or os.getenv("RAILWAY_ENVIRONMENT") or "").strip().lower()
    return env in {"production", "prod"}


def check_vault_key_rotation_policy() -> dict:
    """
    Evaluate VAULT_KEY_ROTATION_DAYS against VAULT_KEY_LAST_ROTATED_AT.
    Returns status dict; logs a warning when overdue (does not fail-closed).
    """
    try:
        import config as cfg

        days = int(getattr(cfg, "VAULT_KEY_ROTATION_DAYS", 90) or 90)
        last_raw = str(getattr(cfg, "VAULT_KEY_LAST_ROTATED_AT", "") or "").strip()
    except Exception:
        days = int(os.getenv("VAULT_KEY_ROTATION_DAYS", "90") or "90")
        last_raw = os.getenv("VAULT_KEY_LAST_ROTATED_AT", "").strip()

    if days <= 0:
        return {"ok": True, "policy_days": days, "status": "disabled"}
    if not last_raw:
        status = {
            "ok": False,
            "policy_days": days,
            "status": "unknown_last_rotation",
            "hint": "Set VAULT_KEY_LAST_ROTATED_AT=YYYY-MM-DD after rotating SECRETS_MASTER_KEY",
        }
        if _is_production():
            logger.warning("Vault key rotation date unset (policy=%sd): %s", days, status["hint"])
        return status

    try:
        last = date.fromisoformat(last_raw[:10])
    except ValueError:
        return {"ok": False, "policy_days": days, "status": "invalid_last_rotation", "raw": last_raw}

    age = (datetime.now(timezone.utc).date() - last).days
    overdue = age > days
    result = {
        "ok": not overdue,
        "policy_days": days,
        "age_days": age,
        "last_rotated_at": last.isoformat(),
        "status": "overdue" if overdue else "current",
    }
    if overdue:
        logger.warning(
            "Vault key rotation overdue: age=%sd policy=%sd last=%s — rotate SECRETS_MASTER_KEY",
            age,
            days,
            last.isoformat(),
        )
    return result


def get_vault_key() -> bytes:
    global _rotation_checked
    if not _rotation_checked:
        _rotation_checked = True
        try:
            check_vault_key_rotation_policy()
        except Exception as exc:  # noqa: BLE001
            logger.debug("vault rotation check skipped: %s", exc)

    explicit = os.getenv("SECRETS_VAULT_KEY", "").strip()
    if explicit:
        # Accept either raw Fernet key or derive from arbitrary secret material.
        try:
            from cryptography.fernet import Fernet

            Fernet(explicit.encode("utf-8"))
            return explicit.encode("utf-8")
        except Exception:
            return _derive_fernet_key(explicit)
    master = os.getenv("SECRETS_MASTER_KEY", "").strip()
    if master:
        return _derive_fernet_key(master)
    if _is_production():
        raise RuntimeError("SECRETS_MASTER_KEY or SECRETS_VAULT_KEY must be set in production")
    logger.warning("SECRETS_MASTER_KEY not set — using dev-only vault key")
    return _derive_fernet_key("blackdark-dev-change-me-in-production")


def _fernet_instance():
    global _fernet
    if _fernet is None:
        from cryptography.fernet import Fernet

        _fernet = Fernet(get_vault_key())
    return _fernet


def encrypt_secret(plaintext: str) -> str:
    if not plaintext:
        return ""
    return _fernet_instance().encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt_secret(ciphertext: str) -> str:
    if not ciphertext:
        return ""
    return _fernet_instance().decrypt(ciphertext.encode("utf-8")).decode("utf-8")


def mask_secret(value: str, *, visible: int = 4) -> str:
    if len(value) <= visible * 2:
        return "****"
    return f"{value[:visible]}...{value[-visible:]}"
