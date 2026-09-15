"""Privileged session controls (SDG-06)."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

_PRIVILEGED_TTL_SEC = int(os.getenv("PRIVILEGED_SESSION_TTL_SEC", "1800"))
_STORE: dict[str, dict[str, Any]] = {}


def _store_path() -> Path:
    root = Path(os.getenv("DATA_DIR") or "data")
    root.mkdir(parents=True, exist_ok=True)
    return root / "privileged_sessions.json"


def _load() -> None:
    global _STORE
    path = _store_path()
    if not path.is_file():
        return
    try:
        _STORE = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        _STORE = {}


def _save() -> None:
    _store_path().write_text(json.dumps(_STORE, indent=2), encoding="utf-8")


def elevate_privileged_session(
    *,
    subject_id: str,
    operation: str,
    auth_strength: str,
) -> dict[str, Any]:
    _load()
    now = time.time()
    rec = {
        "subject_id": subject_id,
        "elevated_at": now,
        "expires_at": now + _PRIVILEGED_TTL_SEC,
        "last_operation": operation,
        "auth_strength": auth_strength,
    }
    _STORE[subject_id] = rec
    _save()
    return rec


def privileged_session_status(subject_id: str) -> dict[str, Any]:
    _load()
    rec = _STORE.get(subject_id)
    if not rec:
        return {"active": False, "subject_id": subject_id}
    now = time.time()
    if now >= float(rec.get("expires_at") or 0):
        _STORE.pop(subject_id, None)
        _save()
        return {"active": False, "subject_id": subject_id, "expired": True}
    return {
        "active": True,
        "subject_id": subject_id,
        "elevated_at": rec.get("elevated_at"),
        "expires_at": rec.get("expires_at"),
        "auth_strength": rec.get("auth_strength"),
        "last_operation": rec.get("last_operation"),
        "remaining_sec": max(0, int(float(rec.get("expires_at") or 0) - now)),
    }


def revoke_privileged_session(subject_id: str) -> bool:
    _load()
    if subject_id in _STORE:
        _STORE.pop(subject_id, None)
        _save()
        return True
    return False


def require_fresh_privileged_session(subject_id: str) -> bool:
    return bool(privileged_session_status(subject_id).get("active"))
