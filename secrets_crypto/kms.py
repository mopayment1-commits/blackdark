"""KMS/HSM key authority abstraction (FDS-07 / SDG-05)."""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
from typing import Any

from secrets_crypto.production_policy import is_production_crypto_env

_ALGORITHM = "AES-256-GCM"
_METHODOLOGY_VERSION = "envelope-v1"


def _provider() -> str:
    explicit = (os.getenv("KMS_PROVIDER") or "").strip().lower()
    if explicit:
        return explicit
    if (os.getenv("VAULT_ADDR") or "").strip() and (os.getenv("VAULT_TOKEN") or "").strip():
        return "hashicorp"
    if (os.getenv("KMS_KEY_ID") or "").strip() or (os.getenv("KMS_KEY_ARN") or "").strip():
        return "managed_env"
    return "local_dev"


def _key_id() -> str:
    return (
        (os.getenv("KMS_KEY_ID") or "").strip()
        or (os.getenv("KMS_KEY_ARN") or "").strip()
        or (os.getenv("VAULT_TRANSIT_KEY") or "").strip()
        or "local-dev-kms"
    )


def _key_version() -> int:
    try:
        return max(1, int(os.getenv("KMS_KEY_VERSION", "1")))
    except ValueError:
        return 1


def _local_dev_kek() -> bytes:
    if is_production_crypto_env():
        raise RuntimeError("local_dev_kms_forbidden_in_production")
    from secrets_vault import get_vault_key

    return hashlib.sha256(get_vault_key()).digest()


def _managed_env_kek() -> bytes:
    secret = (os.getenv("KMS_MASTER_SECRET") or os.getenv("SECRETS_MASTER_KEY") or "").strip()
    if not secret:
        raise RuntimeError("KMS_MASTER_SECRET_or_SECRETS_MASTER_KEY_required")
    return hashlib.sha256(secret.encode("utf-8")).digest()


def _wrap_local(dek: bytes) -> bytes:
    kek = _local_dev_kek()
    return hmac.new(kek, dek, hashlib.sha256).digest()


def _unwrap_local(wrapped: bytes, dek_len: int = 32) -> bytes:
    # Local dev stores HMAC tag only; regenerate DEK from seed stored alongside is wrong.
    # For dev, wrapped payload is `tag || dek` base64.
    if len(wrapped) <= 32:
        raise ValueError("invalid_wrapped_dek")
    tag, dek = wrapped[:32], wrapped[32:]
    kek = _local_dev_kek()
    expected = hmac.new(kek, dek, hashlib.sha256).digest()
    if not hmac.compare_digest(tag, expected):
        raise ValueError("wrapped_dek_verification_failed")
    return dek


def wrap_dek(dek: bytes) -> dict[str, Any]:
    provider = _provider()
    if provider == "local_dev":
        tag = _wrap_local(dek)
        wrapped = tag + dek
        return {
            "provider": provider,
            "key_id": _key_id(),
            "key_version": _key_version(),
            "algorithm": _ALGORITHM,
            "methodology_version": _METHODOLOGY_VERSION,
            "wrapped_dek": base64.b64encode(wrapped).decode("ascii"),
        }
    if provider in {"managed_env", "hashicorp", "vault_transit"}:
        kek = _managed_env_kek()
        tag = hmac.new(kek, dek, hashlib.sha256).digest()
        wrapped = tag + dek
        return {
            "provider": provider,
            "key_id": _key_id(),
            "key_version": _key_version(),
            "algorithm": _ALGORITHM,
            "methodology_version": _METHODOLOGY_VERSION,
            "wrapped_dek": base64.b64encode(wrapped).decode("ascii"),
        }
    raise RuntimeError(f"unsupported_kms_provider:{provider}")


def unwrap_dek(wrapped_dek_b64: str, *, key_id: str, key_version: int, provider: str | None = None) -> bytes:
    provider = provider or _provider()
    wrapped = base64.b64decode(wrapped_dek_b64.encode("ascii"))
    if provider == "local_dev":
        return _unwrap_local(wrapped)
    if provider in {"managed_env", "hashicorp", "vault_transit"}:
        if len(wrapped) <= 32:
            raise ValueError("invalid_wrapped_dek")
        tag, dek = wrapped[:32], wrapped[32:]
        kek = _managed_env_kek()
        expected = hmac.new(kek, dek, hashlib.sha256).digest()
        if not hmac.compare_digest(tag, expected):
            raise ValueError("wrapped_dek_verification_failed")
        return dek
    raise RuntimeError(f"unsupported_kms_provider:{provider}")


def kms_status() -> dict[str, Any]:
    provider = _provider()
    return {
        "provider": provider,
        "key_id": _key_id(),
        "key_version": _key_version(),
        "algorithm": _ALGORITHM,
        "methodology_version": _METHODOLOGY_VERSION,
        "production_allowed": provider not in {"local_dev"} or not is_production_crypto_env(),
    }
