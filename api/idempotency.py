"""Idempotency-Key deduplication for institutional write APIs (D-06)."""

from __future__ import annotations

import json
import threading
import time
from typing import Any

_LOCK = threading.Lock()
_STORE: dict[str, tuple[float, int, dict[str, Any]]] = {}
_TTL_SECONDS = 86400


def _purge() -> None:
    now = time.time()
    expired = [k for k, (ts, _, _) in _STORE.items() if now - ts > _TTL_SECONDS]
    for k in expired:
        _STORE.pop(k, None)


def check_idempotency(key: str | None) -> tuple[bool, dict[str, Any] | None]:
    """Return (is_duplicate, cached_response)."""
    if not key or not key.strip():
        return False, None
    k = key.strip()[:128]
    with _LOCK:
        _purge()
        entry = _STORE.get(k)
        if entry:
            _, status, body = entry
            return True, {"status_code": status, "body": body}
    return False, None


def store_idempotency(key: str | None, status_code: int, body: dict[str, Any]) -> None:
    if not key or not key.strip():
        return
    k = key.strip()[:128]
    with _LOCK:
        _STORE[k] = (time.time(), status_code, body)


def store_size() -> int:
    with _LOCK:
        return len(_STORE)


def idempotent_response(key: str | None, status_code: int, body: dict[str, Any]):
    """Return cached JSONResponse on duplicate key, else store and return body."""
    from fastapi.responses import JSONResponse

    is_dup, cached = check_idempotency(key)
    if is_dup and cached:
        return JSONResponse(status_code=cached["status_code"], content=cached["body"])
    store_idempotency(key, status_code, body)
    return body
