"""Tamper-evident evidence integrity — DSR-016, D-13."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from blackdark.data_governance._paths import EVIDENCE_MANIFEST_PATH, ensure_governance_dirs


def _hash_chain(prev: str, payload: dict[str, Any]) -> str:
    body = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(f"{prev}|{body}".encode()).hexdigest()


def append_integrity_manifest(
    *,
    producer: str,
    artifact_path: str,
    verification_procedure: str = "sha256_chain_verify",
) -> dict[str, Any]:
    ensure_governance_dirs()
    path = Path(artifact_path)
    if not path.is_absolute():
        path = Path(__file__).resolve().parents[2] / artifact_path
    prev_hash = "0" * 64
    if EVIDENCE_MANIFEST_PATH.exists():
        lines = EVIDENCE_MANIFEST_PATH.read_text(encoding="utf-8").splitlines()
        if lines:
            try:
                prev_hash = json.loads(lines[-1]).get("chain_hash", prev_hash)
            except json.JSONDecodeError:
                pass

    content_hash = hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else "missing"
    entry = {
        "timestamp": datetime.now(UTC).isoformat(),
        "producer": producer,
        "artifact_path": artifact_path,
        "content_hash": content_hash,
        "verification_procedure": verification_procedure,
        "prev_hash": prev_hash,
    }
    entry["chain_hash"] = _hash_chain(prev_hash, entry)
    with EVIDENCE_MANIFEST_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
    return entry


def verify_manifest_chain() -> dict[str, Any]:
    if not EVIDENCE_MANIFEST_PATH.exists():
        return {"valid": True, "records": 0}
    prev = "0" * 64
    records = 0
    broken_at = None
    for line in EVIDENCE_MANIFEST_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        records += 1
        entry = json.loads(line)
        stored = entry.pop("chain_hash", "")
        expected = _hash_chain(prev, entry)
        entry["chain_hash"] = stored
        if stored != expected or entry.get("prev_hash") != prev:
            broken_at = records
            break
        prev = stored
    return {"valid": broken_at is None, "records": records, "broken_at": broken_at}
