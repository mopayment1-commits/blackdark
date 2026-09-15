"""Secret rotation and revocation lifecycle (SDG-03)."""

from __future__ import annotations

import json
import os
import secrets
import time
from pathlib import Path
from typing import Any, Literal

SecretState = Literal["created", "active", "rotated", "revoked", "expired"]

_LEDGER: dict[str, dict[str, Any]] = {}


def _ledger_path() -> Path:
    root = Path(os.getenv("DATA_DIR") or "data")
    root.mkdir(parents=True, exist_ok=True)
    return root / "secret_lifecycle_evidence.jsonl"


def _append_event(event: dict[str, Any]) -> None:
    with _ledger_path().open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event) + "\n")


def create_secret_version(
    *,
    secret_id: str,
    secret_type: str,
    value: str,
    actor: str,
) -> dict[str, Any]:
    version = secrets.token_hex(8)
    rec = {
        "secret_id": secret_id,
        "secret_type": secret_type,
        "version": version,
        "state": "created",
        "created_at": time.time(),
        "created_by": actor,
        "activated_at": None,
        "revoked_at": None,
        "expires_at": None,
        "previous_version": (_LEDGER.get(secret_id) or {}).get("version"),
    }
    stored = {**rec, "value": value}
    _LEDGER[secret_id] = stored
    _append_event({"event": "secret_created", **rec, "actor": actor})
    return stored


def activate_secret_version(secret_id: str, *, actor: str) -> dict[str, Any]:
    rec = _LEDGER.get(secret_id)
    if not rec:
        raise ValueError("secret_not_found")
    rec["state"] = "active"
    rec["activated_at"] = time.time()
    _append_event({"event": "secret_activated", "secret_id": secret_id, "version": rec["version"], "actor": actor})
    return rec


def rotate_secret(secret_id: str, *, new_value: str, actor: str, grace_versions: int = 1) -> dict[str, Any]:
    current = _LEDGER.get(secret_id)
    if not current or current.get("state") == "revoked":
        raise ValueError("secret_not_active")
    previous_version = current.get("version")
    new_rec = create_secret_version(
        secret_id=secret_id,
        secret_type=str(current.get("secret_type") or "generic"),
        value=new_value,
        actor=actor,
    )
    new_rec["state"] = "active"
    new_rec["activated_at"] = time.time()
    new_rec["rotated_from"] = previous_version
    new_rec["grace_versions"] = grace_versions
    new_rec["value"] = new_value
    _LEDGER[secret_id] = new_rec
    _append_event(
        {
            "event": "secret_rotated",
            "secret_id": secret_id,
            "version": new_rec["version"],
            "previous_version": previous_version,
            "actor": actor,
        }
    )
    return new_rec


def revoke_secret(secret_id: str, *, actor: str, reason: str = "") -> dict[str, Any]:
    rec = _LEDGER.get(secret_id)
    if not rec:
        raise ValueError("secret_not_found")
    rec["state"] = "revoked"
    rec["revoked_at"] = time.time()
    rec["revoke_reason"] = reason
    _append_event(
        {
            "event": "secret_revoked",
            "secret_id": secret_id,
            "version": rec.get("version"),
            "actor": actor,
            "reason": reason,
        }
    )
    return rec


def get_secret_version(secret_id: str) -> dict[str, Any] | None:
    rec = _LEDGER.get(secret_id)
    if not rec or rec.get("state") == "revoked":
        return None
    return rec


def lifecycle_status() -> dict[str, Any]:
    return {
        "tracked_secrets": len(_LEDGER),
        "evidence_path": str(_ledger_path()),
        "states": sorted({str(r.get("state")) for r in _LEDGER.values()}),
    }


def lifecycle_events(limit: int = 50) -> list[dict[str, Any]]:
    path = _ledger_path()
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        try:
            rows.append(json.loads(raw))
        except json.JSONDecodeError:
            continue
    return rows[-limit:]
