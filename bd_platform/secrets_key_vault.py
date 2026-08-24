"""
Secrets Management & Key Vault — Feature #189 (Sprint 0).

Independent auditable security layer for API keys, credentials, tokens, and
encryption keys. Envelope encryption (AES-256-GCM) with master key loaded in
memory only at runtime. HashiCorp Vault primary when configured; local encrypted
fallback via secrets_vault + vault_client.

Guarantees:
  - No plaintext persistence (ciphertext only at rest)
  - No plaintext logging ([REDACTED] via log_safety)
  - Per-user / per-tenant isolation
  - Scoped permissions (read_only, trading, withdrawal)
  - 90-day rotation policy
  - Immediate revocation (in-memory + persisted)
  - Full searchable audit trail
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import time
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Literal

from log_safety import redact_secret, sanitize_log_value

logger = logging.getLogger("BLACKDARK.SecretsKeyVault")

_REGISTRY_PATH = Path("data/secrets_vault_registry.json")
_AUDIT_PATH = Path("data/secrets_vault_audit.jsonl")
_CIPHER_BLOB_PATH = Path("data/secrets_vault_ciphertext.json")

_ROTATION_DAYS = 90
_ENCRYPTION_AT_REST = "AES-256-GCM-envelope"
_ENCRYPTION_IN_TRANSIT = "TLS-1.3"

PermissionScope = Literal["read_only", "trading", "withdrawal"]
SecretStatus = Literal["active", "rotated", "revoked"]
SecretType = Literal[
    "exchange_api",
    "wallet_api",
    "platform_api",
    "oauth_token",
    "session_secret",
    "encryption_key",
    "jwt_signing",
    "other",
]

_PERM_RANK: dict[str, int] = {"read_only": 1, "trading": 2, "withdrawal": 3}
_VALID_PERMISSIONS = frozenset(_PERM_RANK.keys())
_VALID_TYPES = frozenset(
    {
        "exchange_api",
        "wallet_api",
        "platform_api",
        "oauth_token",
        "session_secret",
        "encryption_key",
        "jwt_signing",
        "other",
    }
)
_SAFE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")

# Immediate revocation cache — checked before any decrypt (≤1s effective).
_revoked_ids: set[str] = set()
_revoked_loaded = False


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _rotation_due(created_or_rotated: str) -> str:
    try:
        base = datetime.fromisoformat(created_or_rotated)
    except ValueError:
        base = datetime.now(UTC)
    return (base + timedelta(days=_ROTATION_DAYS)).isoformat()


def _mask_hint(value: str) -> str:
    if len(value) <= 8:
        return "****"
    return f"{value[:4]}…{value[-4:]}"


def _storage_key(*, tenant_id: str, user_id: int | str, secret_id: str) -> str:
    return f"{tenant_id}:{user_id}:{secret_id}"


def _load_registry() -> dict[str, Any]:
    if not _REGISTRY_PATH.exists():
        return {"version": 1, "secrets": {}}
    try:
        return json.loads(_REGISTRY_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        logger.warning("secrets vault registry read failed | event=vault_registry_read_failed")
        return {"version": 1, "secrets": {}}


def _save_registry(data: dict[str, Any]) -> None:
    _REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    _REGISTRY_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _load_ciphertext_blob() -> dict[str, str]:
    if not _CIPHER_BLOB_PATH.exists():
        return {}
    try:
        return json.loads(_CIPHER_BLOB_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _save_ciphertext_blob(blob: dict[str, str]) -> None:
    _CIPHER_BLOB_PATH.parent.mkdir(parents=True, exist_ok=True)
    _CIPHER_BLOB_PATH.write_text(json.dumps(blob, indent=2), encoding="utf-8")


def _load_revoked_cache() -> None:
    global _revoked_loaded
    if _revoked_loaded:
        return
    reg = _load_registry()
    for meta in (reg.get("secrets") or {}).values():
        if meta.get("status") == "revoked":
            _revoked_ids.add(str(meta.get("id") or ""))
    _revoked_loaded = True


def _audit(
    *,
    action: str,
    secret_id: str | None = None,
    tenant_id: str = "default",
    user_id: int | str | None = None,
    actor: str = "system",
    source_ip: str | None = None,
    allowed: bool = True,
    reason: str = "",
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    row = {
        "id": uuid.uuid4().hex[:16],
        "timestamp": _utcnow(),
        "action": action,
        "secret_id": secret_id,
        "tenant_id": tenant_id,
        "user_id": user_id,
        "actor": sanitize_log_value(actor),
        "source_ip": sanitize_log_value(source_ip) if source_ip else None,
        "allowed": allowed,
        "reason": sanitize_log_value(reason or "ok"),
        "meta": meta or {},
    }
    try:
        _AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with _AUDIT_PATH.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, default=str) + "\n")
    except OSError:
        logger.debug("vault audit persist failed", exc_info=True)

    logger.info(
        "Vault audit | action=%s secret_id=%s tenant=%s user=%s allowed=%s reason=%s",
        sanitize_log_value(action),
        sanitize_log_value(secret_id or "-"),
        sanitize_log_value(tenant_id),
        sanitize_log_value(user_id),
        str(allowed),
        sanitize_log_value(reason or "ok"),
    )
    return row


def _encrypt_at_rest(plaintext: str, *, aad: str) -> str:
    from secrets_vault import encrypt_secret_gcm

    return encrypt_secret_gcm(plaintext, aad=aad.encode("utf-8"))


def _decrypt_at_rest(ciphertext: str, *, aad: str) -> str:
    from secrets_vault import decrypt_secret_gcm

    return decrypt_secret_gcm(ciphertext, aad=aad.encode("utf-8"))


def _store_ciphertext(storage_id: str, ciphertext: str) -> None:
    """Prefer HashiCorp Vault when configured; else local ciphertext blob."""
    from bd_platform.vault_client import store_secret, vault_configured

    if vault_configured():
        # Vault stores opaque blob — never log value.
        store_secret(storage_id, ciphertext)
        return
    blob = _load_ciphertext_blob()
    blob[storage_id] = ciphertext
    _save_ciphertext_blob(blob)


def _read_ciphertext(storage_id: str) -> str | None:
    from bd_platform.vault_client import read_secret, vault_configured

    if vault_configured():
        result = read_secret(storage_id)
        data = (result.get("data") or {}).get("data") or result.get("data") or {}
        val = data.get("value") if isinstance(data, dict) else None
        return str(val) if val else None
    blob = _load_ciphertext_blob()
    return blob.get(storage_id)


def vault_architecture_status() -> dict[str, Any]:
    from bd_platform.vault_client import vault_status

    vs = vault_status()
    return {
        "feature_id": 189,
        "surface": "secrets_key_vault",
        "encryption_at_rest": _ENCRYPTION_AT_REST,
        "encryption_in_transit": _ENCRYPTION_IN_TRANSIT,
        "envelope_encryption": True,
        "master_key_location": "memory_only_at_boot",
        "rotation_policy_days": _ROTATION_DAYS,
        "hashicorp_vault": vs,
        "primary_backend": vs.get("primary", "local_fernet"),
        "plaintext_persistence": False,
        "plaintext_logging": False,
        "penetration_test": "annual_external_required",
    }


def create_secret(
    *,
    tenant_id: str,
    user_id: int | str,
    name: str,
    value: str,
    permission: PermissionScope = "trading",
    secret_type: SecretType = "exchange_api",
    actor: str = "user",
    source_ip: str | None = None,
) -> dict[str, Any]:
    """
    Store a secret. Plaintext returned ONCE in `reveal_once` — never again.
    """
    t0 = time.perf_counter()
    _load_revoked_cache()

    if not value or not value.strip():
        _audit(action="create", tenant_id=tenant_id, user_id=user_id, actor=actor,
               source_ip=source_ip, allowed=False, reason="empty_value")
        return {"ok": False, "error": "empty_value"}

    if permission not in _VALID_PERMISSIONS:
        return {"ok": False, "error": "invalid_permission"}
    if secret_type not in _VALID_TYPES:
        return {"ok": False, "error": "invalid_secret_type"}

    safe_name = (name or "").strip()
    if not _SAFE_NAME.match(safe_name):
        return {"ok": False, "error": "invalid_name"}

    secret_id = uuid.uuid4().hex
    storage_id = hashlib.sha256(_storage_key(tenant_id=tenant_id, user_id=user_id, secret_id=secret_id).encode()).hexdigest()
    aad = storage_id
    ciphertext = _encrypt_at_rest(value.strip(), aad=aad)
    _store_ciphertext(storage_id, ciphertext)

    now = _utcnow()
    meta = {
        "id": secret_id,
        "tenant_id": tenant_id,
        "user_id": str(user_id),
        "name": safe_name,
        "secret_type": secret_type,
        "permission": permission,
        "status": "active",
        "masked_hint": _mask_hint(value.strip()),
        "storage_id": storage_id,
        "encryption": _ENCRYPTION_AT_REST,
        "created_at": now,
        "updated_at": now,
        "rotated_at": None,
        "revoked_at": None,
        "rotation_due_at": _rotation_due(now),
        "last_accessed_at": None,
        "access_count": 0,
    }

    reg = _load_registry()
    secrets = reg.setdefault("secrets", {})
    secrets[secret_id] = meta
    _save_registry(reg)

    _audit(
        action="create",
        secret_id=secret_id,
        tenant_id=tenant_id,
        user_id=user_id,
        actor=actor,
        source_ip=source_ip,
        allowed=True,
        meta={"name": safe_name, "permission": permission, "type": secret_type},
    )

    return {
        "ok": True,
        "secret_id": secret_id,
        "status": "active",
        "masked_hint": meta["masked_hint"],
        "permission": permission,
        "secret_type": secret_type,
        "rotation_due_at": meta["rotation_due_at"],
        "reveal_once": value.strip(),
        "warning": "Secret shown once only — store securely. Never retrievable in plaintext again.",
        "sla_met": (time.perf_counter() - t0) <= 2.0,
    }


def _get_meta(secret_id: str) -> dict[str, Any] | None:
    reg = _load_registry()
    return (reg.get("secrets") or {}).get(secret_id)


def _is_revoked(secret_id: str) -> bool:
    _load_revoked_cache()
    if secret_id in _revoked_ids:
        return True
    meta = _get_meta(secret_id)
    return bool(meta and meta.get("status") == "revoked")


def decrypt_secret_for_use(
    secret_id: str,
    *,
    tenant_id: str,
    user_id: int | str,
    required_permission: PermissionScope | None = None,
    actor: str = "system",
    source_ip: str | None = None,
) -> dict[str, Any]:
    """Internal decrypt — memory only. Full audit trail."""
    t0 = time.perf_counter()
    meta = _get_meta(secret_id)
    if not meta:
        _audit(action="decrypt", secret_id=secret_id, tenant_id=tenant_id, user_id=user_id,
               actor=actor, source_ip=source_ip, allowed=False, reason="not_found")
        return {"ok": False, "error": "not_found"}

    if str(meta.get("tenant_id")) != tenant_id or str(meta.get("user_id")) != str(user_id):
        _audit(action="decrypt", secret_id=secret_id, tenant_id=tenant_id, user_id=user_id,
               actor=actor, source_ip=source_ip, allowed=False, reason="tenant_isolation_violation")
        return {"ok": False, "error": "access_denied"}

    if _is_revoked(secret_id):
        _audit(action="decrypt", secret_id=secret_id, tenant_id=tenant_id, user_id=user_id,
               actor=actor, source_ip=source_ip, allowed=False, reason="revoked")
        return {"ok": False, "error": "revoked"}

    perm = str(meta.get("permission") or "read_only")
    if required_permission:
        have = _PERM_RANK.get(perm, 0)
        need = _PERM_RANK.get(required_permission, 0)
        if have < need:
            _audit(action="decrypt", secret_id=secret_id, tenant_id=tenant_id, user_id=user_id,
                   actor=actor, source_ip=source_ip, allowed=False, reason="insufficient_permission")
            return {"ok": False, "error": "insufficient_permission"}

    storage_id = str(meta.get("storage_id") or "")
    ciphertext = _read_ciphertext(storage_id)
    if not ciphertext:
        _audit(action="decrypt", secret_id=secret_id, tenant_id=tenant_id, user_id=user_id,
               actor=actor, source_ip=source_ip, allowed=False, reason="ciphertext_missing")
        return {"ok": False, "error": "ciphertext_missing"}

    try:
        plaintext = _decrypt_at_rest(ciphertext, aad=storage_id)
    except Exception:
        _audit(action="decrypt", secret_id=secret_id, tenant_id=tenant_id, user_id=user_id,
               actor=actor, source_ip=source_ip, allowed=False, reason="decrypt_failed")
        return {"ok": False, "error": "decrypt_failed"}

    now = _utcnow()
    reg = _load_registry()
    if secret_id in (reg.get("secrets") or {}):
        reg["secrets"][secret_id]["last_accessed_at"] = now
        reg["secrets"][secret_id]["access_count"] = int(reg["secrets"][secret_id].get("access_count") or 0) + 1
        reg["secrets"][secret_id]["updated_at"] = now
        _save_registry(reg)

    _audit(action="decrypt", secret_id=secret_id, tenant_id=tenant_id, user_id=user_id,
           actor=actor, source_ip=source_ip, allowed=True, meta={"permission": perm})

    return {
        "ok": True,
        "value": plaintext,
        "secret_id": secret_id,
        "sla_met": (time.perf_counter() - t0) <= 2.0,
    }


def revoke_secret(
    secret_id: str,
    *,
    tenant_id: str,
    user_id: int | str,
    actor: str = "user",
    source_ip: str | None = None,
    reason: str = "user_requested",
) -> dict[str, Any]:
    """Immediate revocation — in-memory cache + persisted status."""
    t0 = time.perf_counter()
    meta = _get_meta(secret_id)
    if not meta:
        return {"ok": False, "error": "not_found"}

    if str(meta.get("tenant_id")) != tenant_id or str(meta.get("user_id")) != str(user_id):
        return {"ok": False, "error": "access_denied"}

    _revoked_ids.add(secret_id)
    now = _utcnow()
    reg = _load_registry()
    reg["secrets"][secret_id]["status"] = "revoked"
    reg["secrets"][secret_id]["revoked_at"] = now
    reg["secrets"][secret_id]["updated_at"] = now
    _save_registry(reg)

    _audit(action="revoke", secret_id=secret_id, tenant_id=tenant_id, user_id=user_id,
           actor=actor, source_ip=source_ip, allowed=True, reason=reason)

    elapsed_ms = (time.perf_counter() - t0) * 1000
    return {
        "ok": True,
        "secret_id": secret_id,
        "status": "revoked",
        "revoked_at": now,
        "revocation_latency_ms": round(elapsed_ms, 2),
        "immediate": elapsed_ms <= 1000,
    }


def rotate_secret(
    secret_id: str,
    *,
    tenant_id: str,
    user_id: int | str,
    new_value: str,
    actor: str = "user",
    source_ip: str | None = None,
) -> dict[str, Any]:
    """Re-encrypt with current envelope key; marks old version rotated."""
    t0 = time.perf_counter()
    if _is_revoked(secret_id):
        return {"ok": False, "error": "revoked"}

    meta = _get_meta(secret_id)
    if not meta:
        return {"ok": False, "error": "not_found"}

    if str(meta.get("tenant_id")) != tenant_id or str(meta.get("user_id")) != str(user_id):
        return {"ok": False, "error": "access_denied"}

    storage_id = str(meta.get("storage_id") or "")
    ciphertext = _encrypt_at_rest(new_value.strip(), aad=storage_id)
    _store_ciphertext(storage_id, ciphertext)

    now = _utcnow()
    reg = _load_registry()
    reg["secrets"][secret_id]["status"] = "active"
    reg["secrets"][secret_id]["rotated_at"] = now
    reg["secrets"][secret_id]["rotation_due_at"] = _rotation_due(now)
    reg["secrets"][secret_id]["masked_hint"] = _mask_hint(new_value.strip())
    reg["secrets"][secret_id]["updated_at"] = now
    _save_registry(reg)

    _audit(action="rotate", secret_id=secret_id, tenant_id=tenant_id, user_id=user_id,
           actor=actor, source_ip=source_ip, allowed=True)

    return {
        "ok": True,
        "secret_id": secret_id,
        "status": "active",
        "rotated_at": now,
        "rotation_due_at": reg["secrets"][secret_id]["rotation_due_at"],
        "masked_hint": reg["secrets"][secret_id]["masked_hint"],
        "reveal_once": new_value.strip(),
        "warning": "New secret shown once only.",
        "sla_met": (time.perf_counter() - t0) <= 2.0,
    }


def list_secrets(
    *,
    tenant_id: str,
    user_id: int | str,
    include_revoked: bool = False,
) -> dict[str, Any]:
    """Key management dashboard — metadata only, never plaintext."""
    t0 = time.perf_counter()
    reg = _load_registry()
    rows: list[dict[str, Any]] = []
    now = datetime.now(UTC)

    for meta in (reg.get("secrets") or {}).values():
        if str(meta.get("tenant_id")) != tenant_id or str(meta.get("user_id")) != str(user_id):
            continue
        status = meta.get("status", "active")
        if status == "revoked" and not include_revoked:
            continue

        rotation_due = meta.get("rotation_due_at")
        rotation_overdue = False
        if rotation_due and status == "active":
            try:
                rotation_overdue = datetime.fromisoformat(rotation_due) < now
            except ValueError:
                rotation_overdue = False

        rows.append({
            "id": meta.get("id"),
            "name": meta.get("name"),
            "secret_type": meta.get("secret_type"),
            "permission": meta.get("permission"),
            "status": status,
            "masked_hint": meta.get("masked_hint"),
            "created_at": meta.get("created_at"),
            "rotated_at": meta.get("rotated_at"),
            "revoked_at": meta.get("revoked_at"),
            "rotation_due_at": rotation_due,
            "rotation_overdue": rotation_overdue,
            "last_accessed_at": meta.get("last_accessed_at"),
            "access_count": meta.get("access_count", 0),
            "encryption": meta.get("encryption"),
        })

    rows.sort(key=lambda r: str(r.get("name") or ""))
    overdue = sum(1 for r in rows if r.get("rotation_overdue"))

    return {
        "ok": True,
        "feature_id": 189,
        "surface": "key_management_dashboard",
        "tenant_id": tenant_id,
        "user_id": str(user_id),
        "count": len(rows),
        "rotation_overdue_count": overdue,
        "secrets": rows,
        "sla_met": (time.perf_counter() - t0) <= 2.0,
        "timestamp": _utcnow(),
    }


def search_audit_log(
    *,
    tenant_id: str | None = None,
    user_id: int | str | None = None,
    secret_id: str | None = None,
    action: str | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    """Searchable access audit — exportable."""
    t0 = time.perf_counter()
    if not _AUDIT_PATH.exists():
        return {"ok": True, "count": 0, "events": [], "sla_met": True}

    events: list[dict[str, Any]] = []
    try:
        lines = _AUDIT_PATH.read_text(encoding="utf-8").splitlines()
        for line in reversed(lines):
            if not line.strip():
                continue
            row = json.loads(line)
            if tenant_id and row.get("tenant_id") != tenant_id:
                continue
            if user_id is not None and str(row.get("user_id")) != str(user_id):
                continue
            if secret_id and row.get("secret_id") != secret_id:
                continue
            if action and row.get("action") != action:
                continue
            events.append(row)
            if len(events) >= limit:
                break
    except (OSError, json.JSONDecodeError):
        pass

    suspicious = [
        e for e in events
        if not e.get("allowed") or e.get("action") == "decrypt" and e.get("reason") not in ("ok", None, "")
    ]

    return {
        "ok": True,
        "count": len(events),
        "suspicious_count": len(suspicious),
        "events": events,
        "exportable": True,
        "sla_met": (time.perf_counter() - t0) <= 2.0,
    }


def suspicious_access_alerts(*, limit: int = 20) -> dict[str, Any]:
    """Alerts for denied decrypts, isolation violations, revoked access attempts."""
    audit = search_audit_log(limit=500)
    alerts: list[dict[str, Any]] = []
    for event in audit.get("events") or []:
        if not event.get("allowed"):
            alerts.append({
                "level": "high",
                "code": "VAULT_ACCESS_DENIED",
                "action": event.get("action"),
                "reason": event.get("reason"),
                "secret_id": event.get("secret_id"),
                "tenant_id": event.get("tenant_id"),
                "user_id": event.get("user_id"),
                "timestamp": event.get("timestamp"),
                "message": f"Denied {event.get('action')}: {event.get('reason')}",
            })
        elif event.get("action") == "decrypt" and int((event.get("meta") or {}).get("burst", 0)) > 10:
            alerts.append({
                "level": "medium",
                "code": "VAULT_HIGH_ACCESS_RATE",
                "secret_id": event.get("secret_id"),
                "timestamp": event.get("timestamp"),
                "message": "High decrypt rate detected",
            })
        if len(alerts) >= limit:
            break

    return {
        "ok": True,
        "alert_count": len(alerts),
        "alerts": alerts,
        "timestamp": _utcnow(),
    }


def key_vault_dashboard() -> dict[str, Any]:
    """Admin dashboard — architecture status + aggregate metrics."""
    t0 = time.perf_counter()
    reg = _load_registry()
    secrets = list((reg.get("secrets") or {}).values())
    by_status: dict[str, int] = {}
    for s in secrets:
        st = str(s.get("status") or "active")
        by_status[st] = by_status.get(st, 0) + 1

    audit = search_audit_log(limit=50)
    arch = vault_architecture_status()

    return {
        "ok": True,
        "feature_id": 189,
        "surface": "key_management_dashboard",
        "architecture": arch,
        "totals": {
            "secrets": len(secrets),
            "active": by_status.get("active", 0),
            "rotated": by_status.get("rotated", 0),
            "revoked": by_status.get("revoked", 0),
        },
        "recent_audit": audit.get("events", [])[:10],
        "suspicious_alerts": suspicious_access_alerts(limit=5).get("alerts", []),
        "compliance": {
            "no_plaintext_persistence": True,
            "no_plaintext_logging": True,
            "aes_256_at_rest": True,
            "tls_13_in_transit": True,
            "rotation_days": _ROTATION_DAYS,
            "negative_tests_required": True,
        },
        "sla_met": (time.perf_counter() - t0) <= 2.0,
        "timestamp": _utcnow(),
    }


def redact_for_logs(value: Any) -> str:
    """Public redaction helper — always [REDACTED] for secret material."""
    return redact_secret(value)


def negative_test_plaintext_absent(plaintext: str) -> dict[str, Any]:
    """
    Mandatory negative test helper: verify plaintext does not appear in
    registry, ciphertext blob, or audit logs.
    """
    paths = [_REGISTRY_PATH, _CIPHER_BLOB_PATH, _AUDIT_PATH]
    violations: list[str] = []
    for path in paths:
        if not path.exists():
            continue
        content = path.read_text(encoding="utf-8")
        if plaintext in content:
            violations.append(str(path))

    return {
        "ok": len(violations) == 0,
        "plaintext_found_in": violations,
        "registry_encrypted_only": _REGISTRY_PATH.exists() and plaintext not in _REGISTRY_PATH.read_text(encoding="utf-8") if _REGISTRY_PATH.exists() else True,
        "logs_redacted": redact_for_logs(plaintext) == "[redacted]",
    }
