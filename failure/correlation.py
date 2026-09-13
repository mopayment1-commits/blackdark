"""Opaque correlation identifiers and request context (ERR-004, ERR-043)."""

from __future__ import annotations

import secrets
import uuid
from contextvars import ContextVar
from typing import Any

_CORRELATION_ID: ContextVar[str | None] = ContextVar("bd_correlation_id", default=None)
_SUPPORT_REF: ContextVar[str | None] = ContextVar("bd_support_ref", default=None)


def new_correlation_id() -> str:
    return f"bd-{secrets.token_hex(12)}"


def new_support_reference(correlation_id: str | None = None) -> str:
    base = correlation_id or new_correlation_id()
    return base.replace("bd-", "SR-")[:12].upper()


def set_correlation_id(value: str | None) -> None:
    _CORRELATION_ID.set(value)


def get_correlation_id() -> str | None:
    return _CORRELATION_ID.get()


def require_correlation_id() -> str:
    cid = get_correlation_id()
    if not cid:
        cid = new_correlation_id()
        set_correlation_id(cid)
    return cid


def correlation_context() -> dict[str, str]:
    cid = require_correlation_id()
    ref = _SUPPORT_REF.get() or new_support_reference(cid)
    return {"correlation_id": cid, "support_reference": ref}


def parse_incoming_correlation_id(headers: dict[str, Any] | Any) -> str | None:
    try:
        raw = headers.get("x-correlation-id") or headers.get("X-Correlation-ID")
    except Exception:
        raw = None
    if not raw:
        return None
    val = str(raw).strip()[:64]
    if not val or any(ch in val for ch in ("@", ":", "/")):
        return None
    return val


def is_privacy_safe_identifier(value: str) -> bool:
    lowered = value.lower()
    banned = ("@", "postgres", "redis", "sqlite", "user_id", "email", "secret", "token")
    return not any(b in lowered for b in banned)
