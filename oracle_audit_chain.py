"""
BLACKDARK — Immutable Oracle Track Record (Buyer Requirement #4).

Append-only hash chain for predictions — tamper-evident audit trail.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.OracleAuditChain")

# Mutable module attribute so tests may monkeypatch.setattr(chain, "CHAIN_PATH", path).
# Production readers should prefer chain_path() which also honors live env overrides.
CHAIN_PATH = Path(os.getenv("ORACLE_AUDIT_CHAIN_PATH", "data/oracle_audit_chain.jsonl"))
_APPEND_LOCK = threading.Lock()


def chain_path() -> Path:
    """Active chain path (module CHAIN_PATH — monkeypatchable for tests)."""
    return CHAIN_PATH


def _utcnow_iso() -> str:
    return datetime.now(UTC).isoformat()


def _hash_record(payload: dict[str, Any], prev_hash: str) -> str:
    body = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(f"{prev_hash}|{body}".encode()).hexdigest()


def _read_last_hash(path: Path) -> str:
    if not path.exists():
        return "0" * 64
    last_line = ""
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                last_line = line
    if not last_line:
        return "0" * 64
    try:
        return json.loads(last_line).get("chain_hash", "0" * 64)
    except json.JSONDecodeError:
        return "0" * 64


def _count_records(path: Path) -> int:
    if not path.exists():
        return 0
    count = 0
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                count += 1
    return count


def verify_chain(path: Path | None = None) -> dict[str, Any]:
    """Verify integrity of entire chain."""
    chain = path or chain_path()
    if not chain.exists():
        return {"valid": True, "records": 0, "message": "empty chain", "chain_path": str(chain)}

    prev_hash = "0" * 64
    records = 0
    broken_at: int | None = None

    with chain.open("r", encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            records += 1
            entry = json.loads(line)
            stored = entry.pop("chain_hash", "")
            expected = _hash_record(entry, prev_hash)
            entry["chain_hash"] = stored
            if stored != expected or entry.get("prev_hash") != prev_hash:
                broken_at = records
                break
            prev_hash = stored

    return {
        "valid": broken_at is None,
        "records": records,
        "broken_at_seq": broken_at,
        "chain_path": str(chain),
    }


def append_prediction_record(record: dict[str, Any]) -> dict[str, Any]:
    """Append tamper-evident record to hash chain (process-local lock).

    Fail closed if the existing chain is already broken — never extend a
    tampered or corrupted audit log.
    """
    with _APPEND_LOCK:
        path = chain_path()
        integrity = verify_chain(path)
        if not integrity.get("valid"):
            logger.error(
                "oracle_audit_chain_integrity_failed broken_at=%s path=%s",
                integrity.get("broken_at_seq"),
                str(path),
            )
            raise RuntimeError("oracle_audit_chain_integrity_failed")
        path.parent.mkdir(parents=True, exist_ok=True)
        prev = _read_last_hash(path)
        entry = {
            "seq": _count_records(path) + 1,
            "timestamp": _utcnow_iso(),
            "prev_hash": prev,
            **record,
        }
        entry["chain_hash"] = _hash_record(entry, prev)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, default=str) + "\n")
            fh.flush()
            try:
                os.fsync(fh.fileno())
            except OSError:
                pass
        return entry


def chain_summary(*, limit: int = 20) -> dict[str, Any]:
    path = chain_path()
    verify = verify_chain(path)
    recent: list[dict[str, Any]] = []
    if path.exists():
        with path.open("r", encoding="utf-8") as fh:
            lines = [line for line in fh if line.strip()]
        for line in lines[-limit:]:
            recent.append(json.loads(line))

    resolved = [r for r in recent if r.get("resolved")]
    correct = sum(1 for r in resolved if r.get("label") == "correct")
    hit_rate = round(correct / len(resolved) * 100, 2) if resolved else 0.0

    return {
        "integrity": verify,
        "total_records": verify["records"],
        "recent_hit_rate_percent": hit_rate,
        "recent_records": recent,
        "target_accuracy_band": "65-70%",
        "note": "Chain is append-only SHA-256 linked — tamper-evident for due diligence.",
    }
