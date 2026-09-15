"""Canonical secret manager facade (FDS-07)."""

from __future__ import annotations

import os
from typing import Any

from secrets_crypto.production_policy import is_production_crypto_env


def _provider() -> str:
    explicit = (os.getenv("SECRET_MANAGER_PROVIDER") or "").strip().lower()
    if explicit:
        return explicit
    if (os.getenv("VAULT_ADDR") or "").strip() and (os.getenv("VAULT_TOKEN") or "").strip():
        return "hashicorp"
    return "local_fernet"


def secret_manager_status() -> dict[str, Any]:
    provider = _provider()
    from secrets_crypto.kms import kms_status

    return {
        "provider": provider,
        "production": is_production_crypto_env(),
        "canonical_primary": provider in {"hashicorp", "managed_env"},
        "local_fernet_allowed": not is_production_crypto_env(),
        "kms": kms_status(),
    }


def get_secret(name: str) -> dict[str, Any]:
    provider = _provider()
    if provider == "local_fernet" and is_production_crypto_env():
        raise RuntimeError("local_fernet_secret_manager_forbidden_in_production")
    from bd_platform.vault_client import read_secret

    result = read_secret(name)
    if provider == "hashicorp" and result.get("source") != "hashicorp" and is_production_crypto_env():
        raise RuntimeError("secret_manager_unavailable_in_production")
    return result


def put_secret(name: str, value: str) -> dict[str, Any]:
    provider = _provider()
    if provider == "local_fernet" and is_production_crypto_env():
        raise RuntimeError("local_fernet_secret_manager_forbidden_in_production")
    from bd_platform.vault_client import store_secret

    result = store_secret(name, value)
    if provider == "hashicorp" and not result.get("stored") and is_production_crypto_env():
        raise RuntimeError("secret_manager_write_failed_in_production")
    return result
