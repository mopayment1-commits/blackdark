"""
Credential Vault Layer — merged into #907 Multi-Account Sync.

Isolates user read-only exchange API keys in Vault/HSM — no plaintext storage.
Non-custodial: sync keys only, no wallet private keys, no trade/withdraw permissions.
"""

from __future__ import annotations

import json
import logging
import os
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.CredentialVault")

_FEATURE = "credential_vault_layer"
_SEED_PATH = Path("data/credential_vault_seed.json")
_AUDIT_PATH = Path("data/credential_vault_audit.jsonl")
_FEE_PATH = Path("data/credential_vault_fees.jsonl")

_MULTI_ACCOUNT_REF = 907
_SESSION_REF = 1019
_INCIDENT_REF = 1017
_ENCRYPTION_REF = 1039
_ACTIVITY_REF = 1038
_RBAC_REF = 1022

RetrieveCaller = Literal[
    "multi_account_sync",
    "sync_connector",
    "credential_vault_self_test",
]


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _is_production() -> bool:
    tokens = [
        (os.getenv("ENV") or "").strip().lower(),
        (os.getenv("APP_ENV") or "").strip().lower(),
        (os.getenv("RAILWAY_ENVIRONMENT") or "").strip().lower(),
    ]
    return any(t in {"production", "prod"} for t in tokens)


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _cfg(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    return seed.get("credential_vault") or {}


def _tenant_aad(user_id: int, exchange: str) -> bytes:
    return f"blackdark-credential-vault:{user_id}:{exchange.lower()}".encode("utf-8")


def encrypt_credential(plaintext: str, *, user_id: int, exchange: str) -> str:
    """Tenant-bound AES-256-GCM encryption — extension of #1039 policy."""
    if not plaintext:
        return ""
    from secrets_vault import encrypt_secret_gcm

    return encrypt_secret_gcm(plaintext.strip(), aad=_tenant_aad(user_id, exchange))


def decrypt_credential(ciphertext: str, *, user_id: int, exchange: str) -> str:
    if not ciphertext:
        return ""
    from secrets_vault import decrypt_secret_gcm

    try:
        return decrypt_secret_gcm(ciphertext, aad=_tenant_aad(user_id, exchange))
    except Exception:
        # Legacy Fernet blobs from pre-vault migration
        from secrets_vault import decrypt_secret

        return decrypt_secret(ciphertext)


def _vault_secret_name(user_id: int, exchange: str) -> str:
    return f"sync_credential_u{user_id}_{exchange.lower()}"


def _mirror_to_hashicorp_vault(
    user_id: int,
    exchange: str,
    *,
    api_key_enc: str,
    api_secret_enc: str,
) -> dict[str, Any]:
    """Optional HashiCorp Vault mirror — ciphertext only, never plaintext."""
    from bd_platform.vault_client import store_secret, vault_configured

    if not vault_configured():
        return {"mirrored": False, "reason": "vault_not_configured"}
    payload = json.dumps(
        {
            "user_id": user_id,
            "exchange": exchange.lower(),
            "api_key_encrypted": api_key_enc,
            "api_secret_encrypted": api_secret_enc,
            "encryption": "AES-256-GCM-tenant",
        }
    )
    result = store_secret(_vault_secret_name(user_id, exchange), payload)
    return {"mirrored": bool(result.get("stored")), "source": result.get("source")}


def record_vault_audit(
    *,
    user_id: int | None,
    exchange: str,
    action: str,
    allowed: bool,
    reason: str = "",
    actor: str = "backend",
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Append-only audit — 2-year retention policy (#1038 cross-ref)."""
    entry = {
        "ts": time.time(),
        "iso": _utcnow(),
        "user_id": user_id,
        "exchange": exchange.lower(),
        "action": action,
        "allowed": allowed,
        "reason": reason or ("ok" if allowed else "denied"),
        "actor": actor,
        "feature": _FEATURE,
        "extra": extra or {},
    }
    _AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    try:
        with _AUDIT_PATH.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        logger.debug("credential vault audit persist failed", exc_info=True)

    try:
        from api_key_security_guard import record_key_access

        record_key_access(
            user_id=user_id,
            exchange=exchange,
            action=f"vault_{action}",
            allowed=allowed,
            reason=reason,
        )
    except ImportError:
        pass

    logger.info(
        "Credential vault audit | user_id=%s exchange=%s action=%s allowed=%s",
        user_id,
        exchange,
        action,
        allowed,
    )
    return entry


def record_fee_event(
    *,
    user_id: int,
    exchange: str,
    operation: str,
    cost_usd: float = 0.0,
) -> None:
    seed = _load_seed()
    fee_cfg = (_cfg(seed).get("fee_tracking") or {})
    if not fee_cfg.get("enabled", True):
        return
    row = {
        "ts": _utcnow(),
        "user_id": user_id,
        "exchange": exchange.lower(),
        "operation": operation,
        "cost_usd": cost_usd,
    }
    path = Path(fee_cfg.get("log_path") or _FEE_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row) + "\n")
    except OSError:
        logger.debug("credential vault fee log failed", exc_info=True)


def credential_vault_status(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    policy = (_cfg(seed).get("policy") or {})
    from bd_platform.vault_client import vault_status

    vault = vault_status()
    kms = (os.getenv("KMS_PROVIDER") or "").strip().lower() or (
        "aws_kms" if os.getenv("AWS_KMS_KEY_ID") else ("vault" if vault.get("hashicorp_authenticated") else "local_env")
    )
    return {
        "ok": True,
        "feature": _FEATURE,
        "standalone_rejected": seed.get("standalone_rejected", True),
        "merged_into": seed.get("merged_into"),
        "policy": policy,
        "vault_backend": vault,
        "kms_provider": kms,
        "encryption": policy.get("encryption_algorithm", "AES-256-GCM"),
        "tenant_specific_key": policy.get("tenant_specific_key", True),
        "read_only_only": policy.get("read_only_keys_only", True),
        "non_custodial": policy.get("non_custodial", True),
        "integrations": _cfg(seed).get("integrations") or {},
        "allowed_retrieve_callers": _cfg(seed).get("allowed_retrieve_callers") or [],
        "audit_path": str(_AUDIT_PATH),
        "audit_retention_days": policy.get("audit_retention_days", 730),
        "timestamp": _utcnow(),
    }


async def validate_read_only_sync_key(
    exchange: str,
    api_key: str,
    api_secret: str,
) -> dict[str, Any]:
    """Exchange API probe — reject trade/withdraw/write permissions."""
    from api_key_security_guard import validate_read_only_sync_key as _guard_validate

    result = await _guard_validate(exchange, api_key, api_secret)
    return {
        "exchange": result.exchange,
        "allowed": result.allowed,
        "valid": result.valid,
        "can_trade": result.can_trade,
        "can_withdraw": result.can_withdraw,
        "reason": result.reason,
        "details": result.details,
    }


async def store_sync_credential(
    user_id: int,
    exchange: str,
    api_key: str,
    api_secret: str,
    *,
    label: str = "",
    actor: str = "user",
) -> dict[str, Any]:
    """
    Store read-only sync credential — encrypted at rest, optional Vault mirror.
    Never stores plaintext in DB.
    """
    from database import upsert_user_api_key
    from secrets_vault import mask_secret

    ex = exchange.strip().lower()
    validation = await validate_read_only_sync_key(ex, api_key, api_secret)
    record_vault_audit(
        user_id=user_id,
        exchange=ex,
        action="store",
        allowed=validation["allowed"],
        reason=validation["reason"],
        actor=actor,
    )
    if not validation["allowed"]:
        if validation["reason"] in {"trade_permission_rejected", "withdraw_enabled_rejected"}:
            await _alert_user_validation_failure(user_id, ex, validation["reason"])
        return {
            "success": False,
            "exchange": ex,
            "reason": validation["reason"],
            "message": f"API key rejected: {validation['reason']}",
            "validation": validation,
        }

    api_key_enc = encrypt_credential(api_key, user_id=user_id, exchange=ex)
    api_secret_enc = encrypt_credential(api_secret, user_id=user_id, exchange=ex)
    assert api_key not in api_key_enc and api_secret not in api_secret_enc

    vault_mirror = _mirror_to_hashicorp_vault(
        user_id, ex, api_key_enc=api_key_enc, api_secret_enc=api_secret_enc
    )
    await upsert_user_api_key(user_id, ex, api_key_enc, api_secret_enc, label=label)
    record_fee_event(user_id=user_id, exchange=ex, operation="store", cost_usd=0.001)

    return {
        "success": True,
        "exchange": ex,
        "api_key_masked": mask_secret(api_key),
        "message": "Read-only sync keys encrypted and stored in credential vault.",
        "validation": validation["reason"],
        "vault_mirror": vault_mirror,
        "never_exposed": True,
    }


async def retrieve_for_sync(
    user_id: int,
    exchange: str,
    *,
    caller: RetrieveCaller,
) -> tuple[str, str] | None:
    """
    Backend-only credential retrieval for sync jobs — never exposed via API/UI.
    """
    seed = _load_seed()
    allowed_callers = set(_cfg(seed).get("allowed_retrieve_callers") or [])
    ex = exchange.strip().lower()

    if caller not in allowed_callers:
        record_vault_audit(
            user_id=user_id,
            exchange=ex,
            action="retrieve",
            allowed=False,
            reason="unauthorized_caller",
            actor=caller,
        )
        await _handle_unauthorized_vault_access(user_id, caller)
        return None

    from database import fetch_user_api_key_secrets

    row = await fetch_user_api_key_secrets(user_id, ex)
    if not row:
        record_vault_audit(
            user_id=user_id,
            exchange=ex,
            action="retrieve",
            allowed=False,
            reason="not_found",
            actor=caller,
        )
        return None

    try:
        api_key = decrypt_credential(str(row["api_key_encrypted"]), user_id=user_id, exchange=ex)
        api_secret = decrypt_credential(str(row["api_secret_encrypted"]), user_id=user_id, exchange=ex)
    except Exception as exc:
        record_vault_audit(
            user_id=user_id,
            exchange=ex,
            action="retrieve",
            allowed=False,
            reason=f"decrypt_failed:{exc}",
            actor=caller,
        )
        return None

    record_vault_audit(
        user_id=user_id,
        exchange=ex,
        action="retrieve",
        allowed=True,
        reason="sync_job",
        actor=caller,
    )
    record_fee_event(user_id=user_id, exchange=ex, operation="retrieve", cost_usd=0.0005)
    return api_key, api_secret


async def delete_sync_credential(
    user_id: int,
    exchange: str,
    *,
    actor: str = "user",
) -> dict[str, Any]:
    from database import delete_user_api_key

    ex = exchange.strip().lower()
    deleted = await delete_user_api_key(user_id, ex)
    record_vault_audit(
        user_id=user_id,
        exchange=ex,
        action="delete",
        allowed=deleted,
        reason="ok" if deleted else "not_found",
        actor=actor,
    )
    if deleted:
        record_fee_event(user_id=user_id, exchange=ex, operation="delete", cost_usd=0.0)
    return {"success": deleted, "exchange": ex}


async def rotate_user_credentials(user_id: int, exchange: str) -> dict[str, Any]:
    """Re-encrypt stored credentials with current master key (90-day rotation hook)."""
    creds = await retrieve_for_sync(user_id, exchange, caller="credential_vault_self_test")
    if not creds:
        return {"success": False, "reason": "not_found"}
    api_key, api_secret = creds
    result = await store_sync_credential(user_id, exchange, api_key, api_secret, actor="rotation")
    record_vault_audit(
        user_id=user_id,
        exchange=exchange,
        action="rotate",
        allowed=result.get("success", False),
        actor="system",
    )
    return result


async def _alert_user_validation_failure(user_id: int, exchange: str, reason: str) -> None:
    try:
        from security_events import record_security_event

        record_security_event(
            "credential_vault_validation_rejected",
            severity="warning",
            actor=f"user:{user_id}",
            detail={"exchange": exchange, "reason": reason, "action": "user_notified"},
        )
    except ImportError:
        pass


async def _handle_unauthorized_vault_access(user_id: int, caller: str) -> None:
    """#1017 — unauthorized vault access → alert + lockout hook."""
    try:
        from security_events import record_security_event

        record_security_event(
            "credential_vault_unauthorized_access",
            severity="critical",
            actor=caller,
            detail={"user_id": user_id, "action": "forensics_investigation"},
        )
    except ImportError:
        pass
    record_vault_audit(
        user_id=user_id,
        exchange="*",
        action="unauthorized_access",
        allowed=False,
        reason="incident_response_triggered",
        actor=caller,
    )


async def trigger_compromise_playbook(user_id: int, *, reason: str = "suspected_compromise") -> dict[str, Any]:
    """#1019 — revoke keys + security event on suspected compromise."""
    from database import fetch_user_api_keys

    rows = await fetch_user_api_keys(user_id)
    revoked: list[str] = []
    for row in rows:
        ex = str(row.get("exchange") or "")
        if ex:
            await delete_sync_credential(user_id, ex, actor="compromise_playbook")
            revoked.append(ex)

    try:
        from security_events import record_security_event

        record_security_event(
            "credential_vault_compromise_playbook",
            severity="critical",
            actor=f"user:{user_id}",
            detail={"reason": reason, "revoked_exchanges": revoked},
        )
    except ImportError:
        pass

    record_vault_audit(
        user_id=user_id,
        exchange="*",
        action="compromise_playbook",
        allowed=True,
        reason=reason,
        actor="system",
        extra={"revoked": revoked},
    )
    return {
        "ok": True,
        "user_id": user_id,
        "revoked_exchanges": revoked,
        "reason": reason,
        "session_kill": "hook_session_logout_all_when_available",
        "integration_ref": _SESSION_REF,
    }


def check_credential_vault_production_gate(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    status = credential_vault_status(seed=seed)
    policy = status["policy"]
    vault = status["vault_backend"]
    master_key = bool(os.getenv("SECRETS_MASTER_KEY") or os.getenv("SECRETS_VAULT_KEY"))
    vault_ok = vault.get("hashicorp_authenticated") or vault.get("local_fernet_available")

    checks = {
        "read_only_only": policy.get("read_only_keys_only") is True,
        "no_plaintext_policy": policy.get("plaintext_in_db_forbidden") is True,
        "tenant_encryption": policy.get("tenant_specific_key") is True,
        "aes_256_gcm": policy.get("encryption_algorithm") == "AES-256-GCM",
        "vault_backend": vault_ok or not _is_production(),
        "master_key": master_key or not _is_production(),
        "non_custodial": policy.get("non_custodial") is True,
        "never_exposed": policy.get("never_exposed_to_client") is True,
        "audit_retention": policy.get("audit_retention_days", 0) >= 730,
    }
    return {
        "ok": all(checks.values()),
        "feature": _FEATURE,
        "blocks_production": policy.get("blocks_production_if_plaintext", True),
        "checks": checks,
        "timestamp": _utcnow(),
    }


def run_credential_vault_e2e(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    checks: list[dict[str, Any]] = []

    status = credential_vault_status(seed=seed)
    checks.append({"id": "no_standalone", "passed": status["standalone_rejected"] is True})
    checks.append({"id": "read_only_policy", "passed": status["read_only_only"] is True})
    checks.append({"id": "tenant_encryption", "passed": status["tenant_specific_key"] is True})
    checks.append({"id": "non_custodial", "passed": status["non_custodial"] is True})

    plain = "read-only-sync-test-key-value"
    enc = encrypt_credential(plain, user_id=99, exchange="binance")
    dec = decrypt_credential(enc, user_id=99, exchange="binance")
    checks.append({"id": "roundtrip", "passed": dec == plain and plain not in enc})

    wrong_tenant = False
    try:
        decrypt_credential(enc, user_id=100, exchange="binance")
    except Exception:
        wrong_tenant = True
    checks.append({"id": "tenant_binding", "passed": wrong_tenant})

    gate = check_credential_vault_production_gate(seed=seed)
    checks.append({"id": "production_gate", "passed": gate["ok"] is True})

    all_passed = all(c["passed"] for c in checks)
    return {
        "ok": all_passed,
        "feature": _FEATURE,
        "all_passed": all_passed,
        "checks": checks,
        "timestamp": _utcnow(),
    }
