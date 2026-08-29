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


def _is_production() -> bool:
    """Any ENV/APP_ENV/ENVIRONMENT/RAILWAY production marker wins (fail-closed OR)."""
    tokens = [
        (os.getenv("ENV") or "").strip().lower(),
        (os.getenv("APP_ENV") or "").strip().lower(),
        (os.getenv("ENVIRONMENT") or "").strip().lower(),
        (os.getenv("RAILWAY_ENVIRONMENT") or "").strip().lower(),
    ]
    return any(t in {"production", "prod"} for t in tokens)


def get_vault_key() -> bytes:
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
    raise RuntimeError(
        "SECRETS_MASTER_KEY or SECRETS_VAULT_KEY must be set — "
        "no dev fallback vault key is permitted"
    )


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


def encrypt_secret_gcm(plaintext: str, *, aad: bytes = b"blackdark-d02") -> str:
    """AES-256-GCM envelope (D-02 upgrade path alongside Fernet)."""
    if not plaintext:
        return ""
    import os

    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    key = hashlib.sha256(get_vault_key()).digest()
    nonce = os.urandom(12)
    ct = AESGCM(key).encrypt(nonce, plaintext.encode("utf-8"), aad)
    return base64.b64encode(nonce + ct).decode("ascii")


def decrypt_secret_gcm(ciphertext: str, *, aad: bytes = b"blackdark-d02") -> str:
    if not ciphertext:
        return ""
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    raw = base64.b64decode(ciphertext.encode("ascii"))
    nonce, ct = raw[:12], raw[12:]
    key = hashlib.sha256(get_vault_key()).digest()
    return AESGCM(key).decrypt(nonce, ct, aad).decode("utf-8")


def rotate_vault_reencrypt(values: list[str]) -> list[str]:
    """Re-encrypt plaintexts with current vault key (rotation drill)."""
    return [encrypt_secret(v) for v in values]
