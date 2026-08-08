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
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.OracleAuditChain")

CHAIN_PATH = Path(os.getenv("ORACLE_AUDIT_CHAIN_PATH", "data/oracle_audit_chain.jsonl"))
_APPEND_LOCK = threading.Lock()


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash_record(payload: dict[str, Any], prev_hash: str) -> str:
    body = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(f"{prev_hash}|{body}".encode()).hexdigest()


def _read_last_hash() -> str:
    if not CHAIN_PATH.exists():
        return "0" * 64
    last_line = ""
    with CHAIN_PATH.open("r", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                last_line = line
    if not last_line:
        return "0" * 64
    try:
        return json.loads(last_line).get("chain_hash", "0" * 64)
    except json.JSONDecodeError:
        return "0" * 64


def append_prediction_record(record: dict[str, Any]) -> dict[str, Any]:
    """Append tamper-evident record to hash chain (Redis distributed lock + local lock)."""
    from redis_coord import distributed_lock

    with distributed_lock("oracle_audit_chain", ttl_sec=8, wait_sec=3.0) as got_dist:
        # Always also take process lock — nested safety for same-worker races.
        with _APPEND_LOCK:
            if not got_dist:
                logger.warning(
                    "oracle audit chain append without distributed lock — "
                    "multi-replica integrity may race until Redis is available"
                )
            CHAIN_PATH.parent.mkdir(parents=True, exist_ok=True)
            prev = _read_last_hash()
            entry = {
                "seq": _count_records() + 1,
                "timestamp": _utcnow_iso(),
                "prev_hash": prev,
                **record,
                "lock_mode": "redis" if got_dist else "process_local",
            }
            entry["chain_hash"] = _hash_record(entry, prev)
            with CHAIN_PATH.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry, default=str) + "\n")
                fh.flush()
                try:
                    os.fsync(fh.fileno())
                except OSError:
                    pass
            return entry


def _count_records() -> int:
    if not CHAIN_PATH.exists():
        return 0
    count = 0
    with CHAIN_PATH.open("r", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                count += 1
    return count


def verify_chain() -> dict[str, Any]:
    """Verify integrity of entire chain."""
    if not CHAIN_PATH.exists():
        return {"valid": True, "records": 0, "message": "empty chain"}

    prev_hash = "0" * 64
    records = 0
    broken_at: int | None = None

    with CHAIN_PATH.open("r", encoding="utf-8") as fh:
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
        "chain_path": str(CHAIN_PATH),
    }


def chain_summary(*, limit: int = 20) -> dict[str, Any]:
    verify = verify_chain()
    recent: list[dict[str, Any]] = []
    if CHAIN_PATH.exists():
        with CHAIN_PATH.open("r", encoding="utf-8") as fh:
            lines = [l for l in fh if l.strip()]
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
