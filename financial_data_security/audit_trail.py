"""Tamper-evident financial security audit trail."""

from __future__ import annotations

import hashlib
import json
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

_DATA = Path("data/institutional/financial_security_audit.jsonl")
_LOCK = threading.Lock()
_LAST_HASH = "genesis"


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_last_hash() -> str:
    if not _DATA.is_file():
        return "genesis"
    prev = "genesis"
    for line in _DATA.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        prev = row.get("entry_hash", prev)
    return prev


def record_financial_audit(
    *,
    actor: str,
    action: str,
    resource: str,
    result: str,
    auth_strength: str = "standard",
    policy_decision: str = "allow",
    tenant: str | None = None,
    correlation_id: str | None = None,
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    global _LAST_HASH
    _LAST_HASH = _load_last_hash()
    row = {
        "audit_id": f"fds_{uuid4().hex[:16]}",
        "actor": actor,
        "action": action,
        "resource": resource,
        "timestamp": _utcnow(),
        "tenant": tenant,
        "auth_strength": auth_strength,
        "policy_decision": policy_decision,
        "result": result,
        "correlation_id": correlation_id,
        "meta": meta or {},
        "prev_hash": _LAST_HASH,
    }
    digest = hashlib.sha256(json.dumps(row, sort_keys=True, default=str).encode()).hexdigest()
    row["entry_hash"] = digest
    with _LOCK:
        _DATA.parent.mkdir(parents=True, exist_ok=True)
        with _DATA.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, default=str) + "\n")
        _LAST_HASH = digest
    return row


def verify_audit_chain(*, limit: int = 500) -> dict[str, Any]:
    if not _DATA.is_file():
        return {"rows": 0, "chain_valid": True, "store": str(_DATA)}
    prev = "genesis"
    rows = 0
    valid = True
    for line in _DATA.read_text(encoding="utf-8").splitlines()[-limit:]:
        if not line.strip():
            continue
        row = json.loads(line)
        rows += 1
        if row.get("prev_hash") != prev:
            valid = False
            break
        check = dict(row)
        entry_hash = check.pop("entry_hash")
        calc = hashlib.sha256(json.dumps(check, sort_keys=True, default=str).encode()).hexdigest()
        if calc != entry_hash:
            valid = False
            break
        prev = entry_hash
    return {"rows": rows, "chain_valid": valid, "store": str(_DATA)}
