"""Tamper-evident audit signing with key rotation (FDS-16)."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
from typing import Any

from secrets_crypto.production_policy import is_production_crypto_env

_DEV_DEFAULT = "blackdark-audit-dev-sign"
_KEY_VERSION_ENV = "AUDIT_SIGNING_KEY_VERSION"
_KEYS: dict[int, str] = {}


def _load_keys() -> dict[int, str]:
    global _KEYS
    if _KEYS:
        return _KEYS
    current = (os.getenv("AUDIT_SIGNING_KEY") or "").strip()
    if not current:
        if is_production_crypto_env():
            raise RuntimeError("AUDIT_SIGNING_KEY_required_in_production")
        current = _DEV_DEFAULT
    version = int(os.getenv(_KEY_VERSION_ENV, "1") or "1")
    _KEYS[version] = current
    previous = (os.getenv("AUDIT_SIGNING_KEY_PREVIOUS") or "").strip()
    if previous:
        _KEYS[max(1, version - 1)] = previous
    return _KEYS


def current_signing_key_version() -> int:
    return int(os.getenv(_KEY_VERSION_ENV, "1") or "1")


def signing_key_material(version: int | None = None) -> tuple[str, int]:
    keys = _load_keys()
    ver = version or current_signing_key_version()
    key = keys.get(ver)
    if not key:
        raise RuntimeError(f"audit_signing_key_version_missing:{ver}")
    if key == _DEV_DEFAULT and is_production_crypto_env():
        raise RuntimeError("audit_dev_signing_key_forbidden_in_production")
    return key, ver


def canonical_payload(record: dict[str, Any]) -> dict[str, Any]:
    if "decision_id" in record:
        context = record.get("context")
        prediction = record.get("prediction")
        return {
            "decision_id": record.get("decision_id"),
            "context": context if isinstance(context, str) else json.dumps(context or {}, sort_keys=True, default=str),
            "prediction": prediction if isinstance(prediction, str) else json.dumps(prediction or {}, sort_keys=True, default=str),
            "confidence": float(record.get("confidence") or 0),
            "timestamp": record.get("timestamp"),
            "outcome": record.get("outcome"),
            "version": int(record.get("version") or 1),
        }
    meta = record.get("metadata_json")
    if meta is None and "metadata" in record:
        meta = json.dumps(record.get("metadata") or {}, ensure_ascii=False, sort_keys=True, default=str)
    return {
        "timestamp": record.get("timestamp"),
        "actor": record.get("actor"),
        "action": record.get("action"),
        "payload_hash": record.get("payload_hash"),
        "outcome": record.get("outcome"),
        "request_method": record.get("request_method"),
        "request_path": record.get("request_path"),
        "metadata_json": meta or "{}",
        "signing_key_version": int(record.get("signing_key_version") or current_signing_key_version()),
    }


def sign_record(record: dict[str, Any]) -> tuple[str, int]:
    key, version = signing_key_material()
    payload = canonical_payload({**record, "signing_key_version": version})
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()
    signature = hmac.new(key.encode(), raw, hashlib.sha256).hexdigest()
    return signature, version


def verify_record_signature(record: dict[str, Any]) -> bool:
    sig = str(record.get("signature") or "")
    if not sig:
        return False
    version = int(record.get("signing_key_version") or current_signing_key_version())
    try:
        key, _ = signing_key_material(version)
    except RuntimeError:
        return False
    payload = canonical_payload(record)
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()
    expected = hmac.new(key.encode(), raw, hashlib.sha256).hexdigest()
    return hmac.compare_digest(sig, expected)


def tamper_check(record: dict[str, Any]) -> dict[str, Any]:
    valid = verify_record_signature(record)
    return {
        "signature_valid": valid,
        "signing_key_version": record.get("signing_key_version"),
        "tamper_detected": not valid,
    }
