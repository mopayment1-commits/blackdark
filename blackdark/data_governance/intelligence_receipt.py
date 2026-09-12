"""Intelligence Receipts — DSR-008, D-06."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from blackdark.data_governance._paths import RECEIPTS_PATH, ensure_governance_dirs
from blackdark.data_governance.lineage import inherit_evidence_origin


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _hash_payload(payload: dict[str, Any]) -> str:
    body = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(body.encode()).hexdigest()


def issue_intelligence_receipt(
    *,
    artifact_type: str,
    artifact_id: str,
    source_snapshot_hash: str | None = None,
    transform: str | None = None,
    feature_versions: dict[str, str] | None = None,
    model_version: str | None = None,
    rule_config_version: str | None = None,
    output: dict[str, Any] | None = None,
    evidence_class: str | None = None,
    source: str | None = None,
) -> dict[str, Any]:
    """Issue verifiable intelligence receipt for Signal/Prediction/Decision."""
    ensure_governance_dirs()
    origin = inherit_evidence_origin(parent_class=evidence_class, source=source, transform=transform)
    receipt_core = {
        "receipt_id": f"rcpt_{uuid4().hex[:16]}",
        "artifact_type": artifact_type,
        "artifact_id": artifact_id,
        "issued_at": _utcnow(),
        "source_snapshot_hash": source_snapshot_hash,
        "transform": transform,
        "feature_versions": feature_versions or {},
        "model_version": model_version,
        "rule_config_version": rule_config_version,
        "output_summary": {k: output[k] for k in list((output or {}).keys())[:10]} if output else {},
        **origin,
    }
    receipt_core["evidence_hash"] = _hash_payload(receipt_core)
    RECEIPTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with RECEIPTS_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(receipt_core, ensure_ascii=False, default=str) + "\n")
    return receipt_core


def verify_receipt(receipt: dict[str, Any]) -> tuple[bool, str]:
    stored = receipt.get("evidence_hash")
    if not stored:
        return False, "missing_evidence_hash"
    copy = dict(receipt)
    copy.pop("evidence_hash", None)
    expected = _hash_payload(copy)
    if stored != expected:
        return False, "hash_mismatch"
    return True, "ok"
