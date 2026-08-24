"""
API Security Encryption — Feature #165 (Sprint 1, non-negotiable security layer).

Encrypt at rest/in transit; per-user isolation; scoped permissions;
rotation/revocation; no plaintext persistence or logging.

Integrates with #192 Security-First Architecture and existing secrets_vault.
"""

from __future__ import annotations

import json
import logging
import re
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from secrets_vault import decrypt_secret, encrypt_secret, mask_secret, rotate_vault_reencrypt

logger = logging.getLogger("BLACKDARK.ApiSecurityEncryption")

_FEATURE_ID = 165
_REGISTRY_PATH = Path("data/api_key_security_registry.json")
_REVOCATIONS_PATH = Path("data/api_key_revocations.json")
_AUDIT_PATH = Path("data/api_key_security_audit.jsonl")

_SECRET_PATTERN = re.compile(
    r"(api[_-]?key|api[_-]?secret|secret|token|password|bearer)\s*[:=]\s*\S+",
    re.IGNORECASE,
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _redact_message(message: str) -> str:
    return _SECRET_PATTERN.sub(r"\1=****", message or "")


def _load_registry() -> dict[str, Any]:
    if not _REGISTRY_PATH.is_file():
        return {"keys": {}}
    try:
        return json.loads(_REGISTRY_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"keys": {}}


def _save_registry(blob: dict[str, Any]) -> None:
    _REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    _REGISTRY_PATH.write_text(json.dumps(blob, indent=2), encoding="utf-8")


def _load_revocations() -> dict[str, Any]:
    if not _REVOCATIONS_PATH.is_file():
        return {"revoked": {}}
    try:
        return json.loads(_REVOCATIONS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"revoked": {}}


def _save_revocations(blob: dict[str, Any]) -> None:
    _REVOCATIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    _REVOCATIONS_PATH.write_text(json.dumps(blob, indent=2), encoding="utf-8")


def _append_audit(
    *,
    user_id: int | str,
    key_id: str,
    action: str,
    allowed: bool,
    reason: str = "",
    scopes: list[str] | None = None,
) -> dict[str, Any]:
    row = {
        "id": str(uuid.uuid4()),
        "timestamp": _utcnow(),
        "user_id": user_id,
        "key_id": key_id,
        "action": action,
        "allowed": allowed,
        "reason": _redact_message(reason),
        "scopes": scopes or [],
    }
    _AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _AUDIT_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    from api_key_security_guard import record_key_access

    record_key_access(
        user_id=int(user_id) if str(user_id).isdigit() else None,
        exchange=str(scopes[0] if scopes else "vault"),
        action=action,
        allowed=allowed,
        reason=reason,
    )
    logger.info(
        "API security audit | user_id=%s key_id=%s action=%s allowed=%s",
        str(user_id),
        key_id,
        action,
        allowed,
    )
    return row


def _key_record_id(user_id: int | str, label: str) -> str:
    return f"u{user_id}:{label}"


def is_key_revoked(key_id: str) -> bool:
    revoked = _load_revocations().get("revoked") or {}
    entry = revoked.get(key_id)
    if not entry:
        return False
    return bool(entry.get("revoked"))


def store_user_api_secret(
    *,
    user_id: int | str,
    label: str,
    plaintext: str,
    scopes: list[str] | None = None,
    exchange: str = "generic",
) -> dict[str, Any]:
    """Store encrypted secret with per-user isolation — never logs plaintext."""
    if not plaintext or not plaintext.strip():
        return {"ok": False, "error": "empty_secret"}

    key_id = _key_record_id(user_id, label)
    registry = _load_registry()
    keys = registry.setdefault("keys", {})

    encrypted = encrypt_secret(plaintext.strip())
    keys[key_id] = {
        "key_id": key_id,
        "user_id": str(user_id),
        "label": label,
        "exchange": exchange.lower(),
        "encrypted_value": encrypted,
        "scopes": scopes or ["read"],
        "masked_preview": mask_secret(plaintext.strip()),
        "created_at": _utcnow(),
        "updated_at": _utcnow(),
        "revoked": False,
        "rotation_count": int((keys.get(key_id) or {}).get("rotation_count") or 0),
    }
    _save_registry(registry)
    _append_audit(
        user_id=user_id,
        key_id=key_id,
        action="store",
        allowed=True,
        reason="encrypted_at_rest",
        scopes=scopes,
    )
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "key_id": key_id,
        "masked_preview": keys[key_id]["masked_preview"],
        "scopes": keys[key_id]["scopes"],
        "encryption": "fernet_aes128_cbc",
        "plaintext_logged": False,
    }


def access_user_api_secret(
    *,
    user_id: int | str,
    key_id: str,
    action: str = "read",
    requester_user_id: int | str | None = None,
) -> dict[str, Any]:
    """Decrypt secret for authorized user — immediate revocation check."""
    requester = str(requester_user_id if requester_user_id is not None else user_id)
    owner = str(user_id)

    if is_key_revoked(key_id):
        _append_audit(
            user_id=requester,
            key_id=key_id,
            action=action,
            allowed=False,
            reason="key_revoked",
        )
        return {"ok": False, "error": "key_revoked", "allowed": False}

    registry = _load_registry()
    record = (registry.get("keys") or {}).get(key_id)
    if not record:
        _append_audit(
            user_id=requester,
            key_id=key_id,
            action=action,
            allowed=False,
            reason="key_not_found",
        )
        return {"ok": False, "error": "key_not_found", "allowed": False}

    if record.get("user_id") != owner or requester != owner:
        _append_audit(
            user_id=requester,
            key_id=key_id,
            action=action,
            allowed=False,
            reason="per_user_isolation_violation",
        )
        return {"ok": False, "error": "access_denied", "allowed": False}

    if action not in (record.get("scopes") or ["read"]):
        _append_audit(
            user_id=requester,
            key_id=key_id,
            action=action,
            allowed=False,
            reason="scope_denied",
            scopes=record.get("scopes"),
        )
        return {"ok": False, "error": "scope_denied", "allowed": False}

    plaintext = decrypt_secret(str(record.get("encrypted_value") or ""))
    _append_audit(
        user_id=requester,
        key_id=key_id,
        action=action,
        allowed=True,
        reason="ok",
        scopes=record.get("scopes"),
    )
    return {
        "ok": True,
        "key_id": key_id,
        "value": plaintext,
        "masked_preview": record.get("masked_preview"),
        "allowed": True,
        "plaintext_logged": False,
    }


def revoke_user_api_secret(*, user_id: int | str, key_id: str) -> dict[str, Any]:
    """Immediate revocation — subsequent access denied."""
    revocations = _load_revocations()
    revoked = revocations.setdefault("revoked", {})
    revoked[key_id] = {
        "key_id": key_id,
        "user_id": str(user_id),
        "revoked": True,
        "revoked_at": _utcnow(),
    }
    _save_revocations(revocations)

    registry = _load_registry()
    if key_id in (registry.get("keys") or {}):
        registry["keys"][key_id]["revoked"] = True
        registry["keys"][key_id]["updated_at"] = _utcnow()
        _save_registry(registry)

    _append_audit(
        user_id=user_id,
        key_id=key_id,
        action="revoke",
        allowed=True,
        reason="immediate_revocation",
    )
    return {"ok": True, "key_id": key_id, "revoked": True, "revoked_at": revoked[key_id]["revoked_at"]}


def rotate_user_api_secret(*, user_id: int | str, key_id: str, new_plaintext: str) -> dict[str, Any]:
    """Rotate secret — re-encrypt with current vault key."""
    access = access_user_api_secret(user_id=user_id, key_id=key_id, action="read")
    if not access.get("ok"):
        return access

    registry = _load_registry()
    record = (registry.get("keys") or {}).get(key_id)
    if not record:
        return {"ok": False, "error": "key_not_found"}

    # Re-encrypt old + new (rotation drill)
    old_enc = str(record.get("encrypted_value") or "")
    old_plain = decrypt_secret(old_enc) if old_enc else ""
    rotated = rotate_vault_reencrypt([old_plain, new_plaintext.strip()])
    record["encrypted_value"] = rotated[1]
    record["masked_preview"] = mask_secret(new_plaintext.strip())
    record["rotation_count"] = int(record.get("rotation_count") or 0) + 1
    record["updated_at"] = _utcnow()
    _save_registry(registry)

    _append_audit(
        user_id=user_id,
        key_id=key_id,
        action="rotate",
        allowed=True,
        reason="key_rotated",
    )
    return {
        "ok": True,
        "key_id": key_id,
        "rotation_count": record["rotation_count"],
        "masked_preview": record["masked_preview"],
        "plaintext_logged": False,
    }


def list_user_key_status(user_id: int | str) -> dict[str, Any]:
    registry = _load_registry()
    keys = []
    for key_id, row in (registry.get("keys") or {}).items():
        if str(row.get("user_id")) != str(user_id):
            continue
        keys.append(
            {
                "key_id": key_id,
                "label": row.get("label"),
                "exchange": row.get("exchange"),
                "masked_preview": row.get("masked_preview"),
                "scopes": row.get("scopes"),
                "revoked": is_key_revoked(key_id) or bool(row.get("revoked")),
                "rotation_count": row.get("rotation_count", 0),
                "created_at": row.get("created_at"),
                "updated_at": row.get("updated_at"),
            }
        )
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "user_id": str(user_id),
        "keys": keys,
        "count": len(keys),
        "plaintext_exposed": False,
    }


def security_encryption_status() -> dict[str, Any]:
    registry = _load_registry()
    revoked = _load_revocations().get("revoked") or {}
    audit_lines = 0
    if _AUDIT_PATH.is_file():
        audit_lines = sum(1 for _ in _AUDIT_PATH.open(encoding="utf-8"))

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": "API Security Encryption",
        "encryption_at_rest": "fernet_aes128_cbc",
        "kms_recommended": "aws_kms_or_hashicorp_vault",
        "per_user_isolation": True,
        "immediate_revocation": True,
        "audit_log_enabled": True,
        "plaintext_logging": False,
        "keys_registered": len(registry.get("keys") or {}),
        "keys_revoked": len(revoked),
        "audit_events": audit_lines,
        "integrated_features": ["#192"],
        "policy": (
            "All API keys encrypted at rest. Per-user isolation enforced. "
            "Revoked keys denied immediately. No plaintext in logs or persistence."
        ),
        "timestamp": _utcnow(),
    }
