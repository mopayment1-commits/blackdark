"""
BLACKDARK — Encrypted secrets vault for user exchange API keys (Fernet AES-128-CBC).
"""

from __future__ import annotations

import base64
import hashlib
import logging
import os

logger = logging.getLogger("BLACKDARK.SecretsVault")

_fernet = None


def _derive_fernet_key(raw: str) -> bytes:
    digest = hashlib.sha256(raw.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def get_vault_key() -> bytes:
    explicit = os.getenv("SECRETS_VAULT_KEY", "").strip()
    if explicit:
        return explicit.encode("utf-8")
    master = os.getenv("SECRETS_MASTER_KEY", "").strip()
    if master:
        return _derive_fernet_key(master)
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
