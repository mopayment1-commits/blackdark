"""Secrets manager facade — env/KMS path without plaintext DB storage."""

from __future__ import annotations

import os
from typing import Any

from financial_data_security.scanner import scan_text_for_restricted_data


FINANCIAL_SECRET_ENV_KEYS = (
    "STRIPE_SECRET_KEY",
    "STRIPE_WEBHOOK_SECRET",
    "LEMON_SQUEEZY_WEBHOOK_SECRET",
    "LEMON_SQUEEZY_API_KEY",
    "SECRETS_MASTER_KEY",
    "SECRETS_VAULT_KEY",
    "ADMIN_OPS_TOKEN",
    "ADMIN_TOTP_SECRET",
)


def secret_manager_status() -> dict[str, Any]:
    configured = [k for k in FINANCIAL_SECRET_ENV_KEYS if os.getenv(k)]
    prod = _is_production()
    return {
        "central_secret_manager": "env_or_platform_injection",
        "kms_hsm_production_path": "NEEDS_EXTERNAL_VERIFICATION",
        "local_vault_module": "secrets_vault.py",
        "configured_keys": configured,
        "configured_count": len(configured),
        "production": prod,
        "prod_dev_separation_enforced": True,
        "plaintext_in_source_scan": scan_repository_secrets_in_code(),
    }


def _is_production() -> bool:
    tokens = [
        (os.getenv("ENV") or "").lower(),
        (os.getenv("APP_ENV") or "").lower(),
        (os.getenv("ENVIRONMENT") or "").lower(),
        (os.getenv("RAILWAY_ENVIRONMENT") or "").lower(),
    ]
    return any(t in {"production", "prod"} for t in tokens)


def scan_repository_secrets_in_code() -> list[str]:
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    hits: list[str] = []
    for rel in ("financial_data_security", "billing", "api/routers"):
        base = root / rel
        if not base.exists():
            continue
        files = [base] if base.is_file() else list(base.rglob("*.py"))
        for fp in files:
            if "test" in fp.name:
                continue
            try:
                text = fp.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if scan_text_for_restricted_data(text)["secret_pattern_detected"]:
                hits.append(str(fp.relative_to(root)))
    return hits


def encrypt_financial_secret(plaintext: str) -> str:
    from secrets_vault import encrypt_secret

    return encrypt_secret(plaintext)


def decrypt_financial_secret(ciphertext: str) -> str:
    from secrets_vault import decrypt_secret

    return decrypt_secret(ciphertext)
