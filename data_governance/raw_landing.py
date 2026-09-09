"""Raw immutable landing zone — hash + metadata before normalization."""

from __future__ import annotations

import hashlib
import json
import threading
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

_DATA = Path("data/institutional/raw_landing")
_LOCK = threading.Lock()
RETENTION_CLASS = "raw_hot"


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def hash_raw(payload: str | bytes | dict[str, Any]) -> str:
    if isinstance(payload, dict):
        payload = json.dumps(payload, sort_keys=True, default=str)
    if isinstance(payload, str):
        payload = payload.encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def land_raw_record(
    *,
    source_id: str,
    payload: dict[str, Any] | str | bytes,
    source_timestamp: str | None = None,
    schema_version: str = "1.0.0",
    partition: str | None = None,
) -> dict[str, Any]:
    """Persist raw evidence reference (hash + metadata); body stored as JSONL partition."""
    observed_at = _utcnow()
    ingested_at = observed_at
    raw_hash = hash_raw(payload)
    row = {
        "raw_id": f"raw_{uuid4().hex[:16]}",
        "source_id": source_id,
        "raw_payload_hash": raw_hash,
        "source_timestamp": source_timestamp,
        "observed_at": observed_at,
        "ingested_at": ingested_at,
        "schema_version": schema_version,
        "partition": partition or source_id,
        "retention_class": RETENTION_CLASS,
    }
    part = _DATA / f"{row['partition']}.jsonl"
    with _LOCK:
        part.parent.mkdir(parents=True, exist_ok=True)
        with part.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"meta": row, "payload": payload if isinstance(payload, (dict, list)) else str(payload)}, default=str) + "\n")
    return row


def raw_landing_status() -> dict[str, Any]:
    if not _DATA.exists():
        return {"store": str(_DATA), "partitions": 0, "records": 0}
    parts = list(_DATA.glob("*.jsonl"))
    total = sum(1 for p in parts for _ in p.open(encoding="utf-8"))
    return {"store": str(_DATA), "partitions": len(parts), "records": total}
