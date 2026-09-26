"""Production fail-closed crypto/secret policy guards (FDS-06/07/16)."""

from __future__ import annotations

import os
from typing import Any

_DEV_DEFAULT_SECRETS = frozenset(
    {
        "blackdark-dev-change-me-in-production",
        "blackdark-session-pepper-change-me",
        "blackdark-audit-dev-sign",
        "blackdark-mfa-dev-only",
        "change-me",
        "changeme",
        "secret",
    }
)


_STRICT_CRYPTO_ENV_TOKENS = frozenset({"production", "prod", "institutional"})


def is_production_crypto_env() -> bool:
    tokens = [
        (os.getenv("ENV") or "").strip().lower(),
        (os.getenv("APP_ENV") or "").strip().lower(),
        (os.getenv("ENVIRONMENT") or "").strip().lower(),
        (os.getenv("RAILWAY_ENVIRONMENT") or "").strip().lower(),
        (os.getenv("DEPLOY_ENV") or "").strip().lower(),
    ]
    return any(t in _STRICT_CRYPTO_ENV_TOKENS for t in tokens)


def _env(name: str) -> str:
    return (os.getenv(name) or "").strip()


def _is_dev_default(value: str) -> bool:
    return value.lower() in _DEV_DEFAULT_SECRETS


def assert_master_secret_allowed(master: str, *, vault_key: str = "") -> None:
    """Fail closed in production/institutional — no missing or dev-default vault material."""
    if not is_production_crypto_env():
        return
    if vault_key.strip():
        return
    if not master.strip():
        raise RuntimeError(
            "SECRETS_MASTER_KEY or SECRETS_VAULT_KEY is required in production/institutional"
        )
    if _is_dev_default(master):
        raise RuntimeError(
            "SECRETS_MASTER_KEY dev-only value is forbidden in production/institutional"
        )


def production_policy_violations() -> list[dict[str, str]]:
    violations: list[dict[str, str]] = []
    if not is_production_crypto_env():
        return violations

    for env_name in ("SECRETS_MASTER_KEY", "SECRETS_VAULT_KEY", "SESSION_TOKEN_PEPPER", "AUDIT_SIGNING_KEY"):
        val = _env(env_name)
        if val and _is_dev_default(val):
            violations.append({"check": "production_default_secret", "env": env_name})

    if not (_env("SECRETS_MASTER_KEY") or _env("SECRETS_VAULT_KEY")):
        violations.append({"check": "missing_master_secret", "env": "SECRETS_MASTER_KEY"})

    if not _env("AUDIT_SIGNING_KEY"):
        violations.append({"check": "missing_audit_signing_key", "env": "AUDIT_SIGNING_KEY"})

    if _env("AUDIT_SIGNING_KEY") and _env("SECRETS_MASTER_KEY") and _env("AUDIT_SIGNING_KEY") == _env("SECRETS_MASTER_KEY"):
        violations.append({"check": "audit_key_must_be_distinct", "env": "AUDIT_SIGNING_KEY"})

    provider = _env("SECRET_MANAGER_PROVIDER").lower() or ("hashicorp" if _env("VAULT_ADDR") else "")
    kms_provider = _env("KMS_PROVIDER").lower() or provider
    if provider == "local_fernet" or kms_provider == "local_dev":
        violations.append({"check": "local_fallback_forbidden_in_production", "env": "SECRET_MANAGER_PROVIDER"})

    if not provider and not _env("VAULT_ADDR"):
        violations.append({"check": "secret_manager_required", "env": "SECRET_MANAGER_PROVIDER"})

    if kms_provider not in {"hashicorp", "managed_env", "vault_transit"} and not _env("KMS_KEY_ID"):
        violations.append({"check": "kms_required", "env": "KMS_PROVIDER"})

    return violations


def assert_production_crypto_policy() -> None:
    violations = production_policy_violations()
    if violations:
        raise RuntimeError(f"production_crypto_policy_violation:{violations[0]['check']}")


def production_policy_status() -> dict[str, Any]:
    return {
        "production": is_production_crypto_env(),
        "violations": production_policy_violations(),
        "fail_closed": len(production_policy_violations()) == 0 or not is_production_crypto_env(),
    }
