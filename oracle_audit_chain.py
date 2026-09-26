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
import time
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

try:
    import fcntl
except ImportError:  # pragma: no cover — non-Unix
    fcntl = None  # type: ignore[assignment]

logger = logging.getLogger("BLACKDARK.OracleAuditChain")

# Mutable module attribute so tests may monkeypatch.setattr(chain, "CHAIN_PATH", path).
# Production readers should prefer chain_path() which also honors live env overrides.
CHAIN_PATH = Path(os.getenv("ORACLE_AUDIT_CHAIN_PATH", "data/oracle_audit_chain.jsonl"))
_APPEND_LOCK = threading.Lock()
_VERIFY_CACHE_LOCK = threading.Lock()
_VERIFY_CACHE: dict[str, Any] | None = None
_VERIFY_CACHE_KEY: tuple[int, int] | None = None
_VERIFY_CACHE_AT: float = 0.0


def _chain_file_fingerprint(path: Path) -> tuple[int, int]:
    try:
        st = path.stat()
        return (st.st_mtime_ns, st.st_size)
    except OSError:
        return (0, 0)


def invalidate_verify_chain_cache() -> None:
    global _VERIFY_CACHE, _VERIFY_CACHE_KEY, _VERIFY_CACHE_AT
    with _VERIFY_CACHE_LOCK:
        _VERIFY_CACHE = None
        _VERIFY_CACHE_KEY = None
        _VERIFY_CACHE_AT = 0.0


def _verify_chain_uncached(chain: Path) -> dict[str, Any]:
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

    out: dict[str, Any] = {
        "valid": broken_at is None,
        "records": records,
        "broken_at_seq": broken_at,
        "chain_path": str(chain),
    }
    if broken_at is not None:
        out["integrity_failure_reason"] = (
            f"Record seq={broken_at} has prev_hash or chain_hash mismatch "
            "(tamper, corruption, or concurrent append race)."
        )
    return out


@contextmanager
def _chain_file_lock(path: Path):
    """Cross-process exclusive lock for append / repair (multi-worker safe)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = path.with_suffix(path.suffix + ".lock")
    with lock_path.open("a+", encoding="utf-8") as lock_fh:
        if fcntl is not None:
            fcntl.flock(lock_fh.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            if fcntl is not None:
                fcntl.flock(lock_fh.fileno(), fcntl.LOCK_UN)


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
    """Verify integrity of entire chain (short TTL + file fingerprint cache)."""
    chain = path or chain_path()
    ttl = float(os.getenv("ORACLE_CHAIN_VERIFY_CACHE_SEC", "45"))
    fp = _chain_file_fingerprint(chain)
    now = time.monotonic()
    global _VERIFY_CACHE, _VERIFY_CACHE_KEY, _VERIFY_CACHE_AT
    with _VERIFY_CACHE_LOCK:
        if (
            _VERIFY_CACHE is not None
            and _VERIFY_CACHE_KEY == fp
            and (now - _VERIFY_CACHE_AT) < ttl
        ):
            return dict(_VERIFY_CACHE)
    out = _verify_chain_uncached(chain)
    with _VERIFY_CACHE_LOCK:
        _VERIFY_CACHE = dict(out)
        _VERIFY_CACHE_KEY = fp
        _VERIFY_CACHE_AT = now
    return out


def repair_tip_prev_hash_race(path: Path | None = None) -> dict[str, Any]:
    """
    Re-link the final record when only prev_hash is stale (common multi-worker race).

    Does not rewrite historical payloads; recomputes tip chain_hash after fixing prev_hash.
    """
    chain = path or chain_path()
    before = verify_chain(chain)
    if before.get("valid"):
        return {"repaired": False, "action": "none", "verify": before}
    broken = before.get("broken_at_seq")
    if not chain.exists() or broken is None:
        return {"repaired": False, "action": "none", "verify": before}

    with _chain_file_lock(chain):
        lines = [line for line in chain.read_text(encoding="utf-8").splitlines() if line.strip()]
        if broken != len(lines):
            return {
                "repaired": False,
                "action": "refused_not_tip_break",
                "verify": verify_chain(chain),
                "note": "Break is not at chain tip — manual investigation required.",
            }
        prev_entry = json.loads(lines[-2]) if len(lines) >= 2 else None
        tip = json.loads(lines[-1])
        expected_prev = prev_entry.get("chain_hash", "0" * 64) if prev_entry else "0" * 64
        if tip.get("prev_hash") == expected_prev:
            return {"repaired": False, "action": "none", "verify": verify_chain(chain)}

        stale_prev = tip.get("prev_hash")
        tip["prev_hash"] = expected_prev
        tip.pop("chain_hash", None)
        tip["chain_hash"] = _hash_record(tip, expected_prev)
        lines[-1] = json.dumps(tip, default=str)
        chain.write_text("\n".join(lines) + "\n", encoding="utf-8")
        invalidate_verify_chain_cache()
        after = verify_chain(chain)
        return {
            "repaired": after.get("valid") is True,
            "action": "relink_tip_prev_hash",
            "broken_at_seq_before": broken,
            "stale_prev_hash": stale_prev,
            "correct_prev_hash": expected_prev,
            "new_tip_hash": tip.get("chain_hash"),
            "verify": after,
        }


def append_prediction_record(record: dict[str, Any]) -> dict[str, Any]:
    """Append tamper-evident record to hash chain (process-local lock).

    Fail closed if the existing chain is already broken — never extend a
    tampered or corrupted audit log.
    """
    with _APPEND_LOCK:
        path = chain_path()
        with _chain_file_lock(path):
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
            invalidate_verify_chain_cache()
            return entry


def read_recent_chain_records(limit: int = 20) -> list[dict[str, Any]]:
    """Tail of chain without integrity scan (for public lookups)."""
    path = chain_path()
    if not path.exists():
        return []
    lines: list[str] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                lines.append(line)
    return [json.loads(line) for line in lines[-limit:]]


def chain_summary(*, limit: int = 20) -> dict[str, Any]:
    path = chain_path()
    verify = verify_chain(path)
    recent = read_recent_chain_records(limit)

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
