"""Shared helpers for institutional compounding phases 2–8."""

from __future__ import annotations

import hmac
import json
from datetime import UTC, datetime
from typing import Any

from audit_registry import _sign_payload_dict, hash_payload


def utcnow() -> str:
    return datetime.now(UTC).isoformat()


def dumps_json(data: Any) -> str:
    return json.dumps(data or {}, ensure_ascii=False, sort_keys=True, default=str)


def loads_json(raw: str | None, default: Any = None) -> Any:
    if not raw:
        return default if default is not None else {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return default if default is not None else {}


def _sign_fields(row: dict[str, Any], fields: tuple[str, ...]) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for key in fields:
        val = row.get(key)
        if key.endswith("_json") and not isinstance(val, str):
            val = dumps_json(val)
        payload[key] = val
    return payload


def row_signature(row: dict[str, Any], fields: tuple[str, ...]) -> str:
    return _sign_payload_dict(_sign_fields(row, fields))


def verify_row_signature(row: dict[str, Any], fields: tuple[str, ...]) -> bool:
    sig = str(row.get("signature") or "")
    if not sig:
        return False
    expected = _sign_payload_dict(_sign_fields(row, fields))
    return hmac.compare_digest(sig, expected)
