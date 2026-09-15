"""Step-Up authentication grants (FDS-12)."""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import time
from pathlib import Path
from typing import Any

_STEP_UP_TTL_SEC = int(os.getenv("STEP_UP_TTL_SEC", "300"))
_GRANTS: dict[str, dict[str, Any]] = {}


def _ledger_path() -> Path:
    root = Path(os.getenv("DATA_DIR") or "data")
    root.mkdir(parents=True, exist_ok=True)
    return root / "step_up_grants.jsonl"


def _grant_key(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def issue_step_up_grant(
    *,
    subject_id: str,
    operation: str,
    purpose: str | None = None,
) -> dict[str, Any]:
    token = secrets.token_urlsafe(32)
    now = time.time()
    grant = {
        "subject_id": subject_id,
        "operation": operation,
        "purpose": purpose or operation,
        "issued_at": now,
        "expires_at": now + _STEP_UP_TTL_SEC,
        "nonce": secrets.token_hex(8),
        "consumed": False,
    }
    _GRANTS[_grant_key(token)] = grant
    with _ledger_path().open("a", encoding="utf-8") as fh:
        fh.write(
            json.dumps(
                {
                    "event": "step_up_issued",
                    "subject_id": subject_id,
                    "operation": operation,
                    "purpose": grant["purpose"],
                    "issued_at": now,
                    "expires_at": grant["expires_at"],
                    "grant_fingerprint": _grant_key(token)[:16],
                }
            )
            + "\n"
        )
    return {
        "step_up_token": token,
        "expires_at": grant["expires_at"],
        "operation": operation,
        "ttl_sec": _STEP_UP_TTL_SEC,
    }


def verify_step_up_grant(
    *,
    token: str | None,
    subject_id: str,
    operation: str,
    consume: bool = True,
) -> bool:
    if not token:
        return False
    key = _grant_key(token.strip())
    grant = _GRANTS.get(key)
    if not grant:
        return False
    now = time.time()
    if grant.get("consumed"):
        return False
    if now >= float(grant.get("expires_at") or 0):
        _GRANTS.pop(key, None)
        return False
    if str(grant.get("subject_id")) != str(subject_id):
        return False
    if str(grant.get("operation")) != str(operation):
        return False
    if consume:
        grant["consumed"] = True
        with _ledger_path().open("a", encoding="utf-8") as fh:
            fh.write(
                json.dumps(
                    {
                        "event": "step_up_consumed",
                        "subject_id": subject_id,
                        "operation": operation,
                        "consumed_at": now,
                        "grant_fingerprint": key[:16],
                    }
                )
                + "\n"
            )
    return True


def step_up_audit_entries(limit: int = 20) -> list[dict[str, Any]]:
    path = _ledger_path()
    if not path.is_file():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    out: list[dict[str, Any]] = []
    for raw in lines[-limit:]:
        try:
            out.append(json.loads(raw))
        except json.JSONDecodeError:
            continue
    return out
