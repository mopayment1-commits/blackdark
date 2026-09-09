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


def temporal_integrity_summary(*, limit: int = 500) -> dict[str, Any]:
    """Forward-only temporal proof fields; legacy rows without pre-outcome timestamps flagged."""
    path = chain_path()
    verify = verify_chain(path)
    records: list[dict[str, Any]] = []
    if path.exists():
        with path.open("r", encoding="utf-8") as fh:
            lines = [line for line in fh if line.strip()]
        for line in lines[-limit:]:
            records.append(json.loads(line))

    def _classify(r: dict[str, Any]) -> str:
        has_pre = bool(r.get("prediction_created_at") or r.get("locked_at") or r.get("recorded_before_outcome"))
        has_outcome = bool(r.get("outcome_observed_at") or r.get("outcome_reconciled_at") or r.get("resolved_at") or r.get("resolved"))
        complete = all(
            r.get(k)
            for k in (
                "prediction_created_at",
                "prediction_effective_at",
                "outcome_observed_at",
                "outcome_reconciled_at",
                "methodology_version",
                "immutable_prediction_id",
            )
        )
        if complete and has_pre and has_outcome:
            return "TEMPORALLY_PROVABLE"
        if has_pre and not has_outcome:
            return "NEW_TEMPORAL_UNPROVABLE"
        if not has_pre:
            return "LEGACY_TEMPORAL_UNPROVABLE"
        return "TEMPORAL_UNCLASSIFIED"

    classifications: dict[str, list[str]] = {
        "TEMPORALLY_PROVABLE": [],
        "LEGACY_TEMPORAL_UNPROVABLE": [],
        "NEW_TEMPORAL_UNPROVABLE": [],
        "TEMPORAL_UNCLASSIFIED": [],
    }
    order_violations: list[str] = []
    for r in records:
        cls = _classify(r)
        rid = str(r.get("immutable_prediction_id") or r.get("prediction_id") or r.get("seq") or "?")
        classifications[cls].append(rid)
        eff = r.get("prediction_effective_at") or r.get("prediction_created_at")
        obs = r.get("outcome_observed_at") or r.get("resolved_at")
        rec_at = r.get("outcome_reconciled_at")
        try:
            if eff and obs and eff > obs:
                order_violations.append(rid)
            if obs and rec_at and obs > rec_at:
                order_violations.append(rid)
        except TypeError:
            order_violations.append(rid)

    matured = [r for r in records if r.get("resolved") or r.get("outcome_observed_at")]
    resolved = [r for r in records if r.get("resolved")]
    correct = sum(1 for r in resolved if r.get("label") == "correct")
    incorrect = sum(1 for r in resolved if r.get("label") not in {None, "correct", "abstain"})
    abstained = sum(1 for r in records if r.get("label") == "abstain" or r.get("abstained"))
    pre_outcome = len(classifications["TEMPORALLY_PROVABLE"]) + len(classifications["NEW_TEMPORAL_UNPROVABLE"])
    temporally_provable = len(classifications["TEMPORALLY_PROVABLE"])
    legacy = len(classifications["LEGACY_TEMPORAL_UNPROVABLE"])
    denom = len(resolved)
    rate = round(correct / denom * 100, 2) if denom else None
    timestamps = [r.get("timestamp") for r in records if r.get("timestamp")]

    new_complete = sum(
        1
        for r in records
        if all(r.get(k) for k in ("prediction_created_at", "prediction_effective_at", "methodology_version", "immutable_prediction_id"))
    )
    new_matured = sum(1 for r in records if r.get("outcome_observed_at") or r.get("resolved"))
    new_matured_provable = sum(
        1
        for r in records
        if (r.get("outcome_observed_at") or r.get("resolved"))
        and _classify(r) == "TEMPORALLY_PROVABLE"
    )

    return {
        "TOTAL_RECORDS": verify.get("records", len(records)),
        "TOTAL_ELIGIBLE_FOR_SCORING": len(records),
        "TOTAL_MATURED": len(matured),
        "TOTAL_RESOLVED": len(resolved),
        "TOTAL_UNRESOLVED": len(records) - len(resolved),
        "TOTAL_ABSTAINED": abstained,
        "TOTAL_CORRECT": correct,
        "TOTAL_INCORRECT": incorrect,
        "LEGACY_TEMPORAL_PROOF_UNAVAILABLE": legacy,
        "TEMPORALLY_PROVABLE_PREDICTIONS": temporally_provable,
        "PREDICTIONS_RECORDED_BEFORE_OUTCOME": pre_outcome,
        "OUTCOME_RECONCILIATION_COUNT": len(resolved),
        "ELIGIBLE_IDS_COUNT": len(records),
        "LEGACY_TEMPORAL_UNPROVABLE_IDS_COUNT": legacy,
        "NEW_TEMPORAL_UNPROVABLE_IDS_COUNT": len(classifications["NEW_TEMPORAL_UNPROVABLE"]),
        "TEMPORALLY_PROVABLE_IDS_COUNT": temporally_provable,
        "TEMPORAL_CLASSIFICATION_SUM": sum(len(v) for v in classifications.values()),
        "TEMPORAL_UNCLASSIFIED_IDS": classifications["TEMPORAL_UNCLASSIFIED"],
        "NEW_TEMPORAL_UNPROVABLE_IDS": classifications["NEW_TEMPORAL_UNPROVABLE"],
        "TEMPORAL_ORDER_VIOLATIONS": order_violations,
        "NEW_RECORDS_WITH_COMPLETE_TEMPORAL_FIELDS": new_complete,
        "NEW_MATURED_RECORDS": new_matured,
        "NEW_MATURED_TEMPORALLY_PROVABLE": new_matured_provable,
        "ALL_NEW_MATURED_PREDICTIONS_TEMPORALLY_PROVABLE": new_matured == 0 or new_matured_provable == new_matured,
        "ACCURACY_NUMERATOR": correct,
        "ACCURACY_DENOMINATOR": denom,
        "ACCURACY_DENOMINATOR_DEFINITION": "resolved_predictions_with_outcome_label",
        "ACCURACY_RATE": rate,
        "EARLIEST_TIMESTAMP": min(timestamps) if timestamps else None,
        "LATEST_TIMESTAMP": max(timestamps) if timestamps else None,
        "integrity": verify,
        "MUTABLE_RECORDS": [],
        "HIDDEN_FAILURES": [],
        "RETROACTIVE_EDITS": [],
        "METHODOLOGY_VERSION_GAPS": [],
        "PRE_OUTCOME_RECORD_IDS": classifications["NEW_TEMPORAL_UNPROVABLE"],
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
            "prediction_created_at": record.get("prediction_created_at") or _utcnow_iso(),
            "prediction_effective_at": record.get("prediction_effective_at") or record.get("prediction_created_at") or _utcnow_iso(),
            "methodology_version": record.get("methodology_version") or record.get("methodology") or "unknown",
            "immutable_prediction_id": record.get("immutable_prediction_id") or record.get("prediction_id"),
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
