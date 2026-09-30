"""Persist WebAuthn credentials (Launch-57 phishing-resistant auth)."""

from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any

_LOCK = threading.Lock()


def _path() -> Path:
    root = Path(os.getenv("DATA_DIR") or "data")
    root.mkdir(parents=True, exist_ok=True)
    return root / "webauthn_credentials.json"


def _load() -> dict[str, list[dict[str, Any]]]:
    path = _path()
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8") or "{}")
    except json.JSONDecodeError:
        return {}


def _save(data: dict[str, list[dict[str, Any]]]) -> None:
    _path().write_text(json.dumps(data, indent=2), encoding="utf-8")


def list_credentials(user_id: int) -> list[dict[str, Any]]:
    with _LOCK:
        return list(_load().get(str(user_id), []))


def add_credential(user_id: int, credential: dict[str, Any]) -> dict[str, Any]:
    with _LOCK:
        data = _load()
        key = str(user_id)
        rows = data.get(key, [])
        cred_id = credential.get("credential_id")
        rows = [r for r in rows if r.get("credential_id") != cred_id]
        rows.append(credential)
        data[key] = rows
        _save(data)
    return credential


def find_credential(user_id: int, credential_id: str) -> dict[str, Any] | None:
    for row in list_credentials(user_id):
        if row.get("credential_id") == credential_id:
            return row
    return None


def user_ids_with_credential_id(credential_id: str) -> list[int]:
    out: list[int] = []
    with _LOCK:
        data = _load()
    for uid, rows in data.items():
        for row in rows:
            if row.get("credential_id") == credential_id:
                try:
                    out.append(int(uid))
                except ValueError:
                    continue
    return out
