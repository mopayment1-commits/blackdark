"""Backup retention, expiry, deletion verification (SDG-15)."""

from __future__ import annotations

import json
import os
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Literal

BackupState = Literal["CREATED", "RETENTION_WINDOW", "EXPIRED", "DELETED", "VERIFIED", "FAILED", "LEGAL_HOLD"]

_DEFAULT_RETENTION_DAYS = 30


def backup_retention_days() -> int:
    raw = os.getenv("BACKUP_RETENTION_DAYS", str(_DEFAULT_RETENTION_DAYS))
    try:
        days = int(raw)
    except ValueError:
        days = _DEFAULT_RETENTION_DAYS
    return max(1, days)


def _evidence_path() -> Path:
    base = Path(os.getenv("DATA_DIR", "data"))
    return base / "backup_lifecycle_evidence.jsonl"


def _append_evidence(record: dict[str, Any]) -> None:
    path = _evidence_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, sort_keys=True) + "\n")


def record_backup_creation(
    *,
    backup_path: str,
    policy_class: str = "database_full",
    sha256: str = "",
    legal_hold: bool = False,
) -> dict[str, Any]:
    """Record CREATE → RETENTION_WINDOW with machine evidence."""
    created_at = datetime.now(UTC)
    retention_days = backup_retention_days()
    expiry_at = created_at + timedelta(days=retention_days)
    record = {
        "event": "backup_created",
        "backup_path": backup_path,
        "policy_class": policy_class,
        "policy_version": "fds-backup-v1",
        "created_at": created_at.isoformat(),
        "created_ts": created_at.timestamp(),
        "retention_days": retention_days,
        "expiry_at": expiry_at.isoformat(),
        "expiry_ts": expiry_at.timestamp(),
        "sha256": sha256,
        "state": "RETENTION_WINDOW" if not legal_hold else "LEGAL_HOLD",
        "legal_hold": legal_hold,
        "verification_result": None,
        "deletion_result": None,
    }
    _append_evidence(record)
    return record


def _load_records() -> list[dict[str, Any]]:
    path = _evidence_path()
    if not path.is_file():
        return []
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def process_expired_backups(backup_dir: str | Path | None = None) -> list[dict[str, Any]]:
    """Transition RETENTION_WINDOW → EXPIRED → DELETE/CRYPTO-ERASE → VERIFY."""
    base = Path(backup_dir or os.getenv("BACKUP_DIR", "data/backups"))
    now = time.time()
    results: list[dict[str, Any]] = []
    for rec in _load_records():
        if rec.get("event") != "backup_created":
            continue
        if rec.get("legal_hold"):
            continue
        if rec.get("state") in {"DELETED", "VERIFIED"}:
            continue
        expiry_ts = float(rec.get("expiry_ts") or 0)
        backup_name = Path(str(rec.get("backup_path", ""))).name
        gz = base / backup_name if backup_name else None
        if now < expiry_ts:
            results.append({**rec, "processed_state": rec.get("state")})
            continue
        outcome: dict[str, Any] = {
            "event": "backup_expiry_processed",
            "backup_path": rec.get("backup_path"),
            "policy_class": rec.get("policy_class"),
            "expiry_at": rec.get("expiry_at"),
            "processed_at": datetime.now(UTC).isoformat(),
            "state": "EXPIRED",
        }
        if gz and gz.is_file():
            try:
                gz.unlink()
                meta = base / backup_name.replace(".sql.gz", ".sha256")
                if meta.is_file():
                    meta.unlink()
                outcome["deletion_result"] = "deleted"
                outcome["state"] = "DELETED"
            except OSError as exc:
                outcome["deletion_result"] = "failed"
                outcome["state"] = "FAILED"
                outcome["failure_reason"] = str(exc)
        else:
            outcome["deletion_result"] = "already_absent"
            outcome["state"] = "DELETED"
        verify = verify_backup_deletion(str(rec.get("backup_path", "")))
        outcome["verification_result"] = verify.get("verified")
        outcome["state"] = "VERIFIED" if verify.get("verified") else "FAILED"
        _append_evidence(outcome)
        results.append(outcome)
    return results


def verify_backup_deletion(backup_path: str) -> dict[str, Any]:
    """Verify backup file absent after expiry deletion."""
    path = Path(backup_path)
    if not path.is_absolute():
        path = Path(os.getenv("BACKUP_DIR", "data/backups")) / path.name
    verified = not path.is_file()
    record = {
        "event": "backup_deletion_verified",
        "backup_path": str(path),
        "verified": verified,
        "verified_at": datetime.now(UTC).isoformat(),
        "failure_state": None if verified else "file_still_present",
    }
    _append_evidence(record)
    return record


def backup_lifecycle_status() -> dict[str, Any]:
    records = _load_records()
    return {
        "retention_days": backup_retention_days(),
        "evidence_path": str(_evidence_path()),
        "record_count": len(records),
        "states_supported": ["CREATED", "RETENTION_WINDOW", "EXPIRED", "DELETED", "VERIFIED", "FAILED", "LEGAL_HOLD"],
    }
