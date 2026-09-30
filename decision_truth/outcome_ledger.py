"""Pre-Registered Outcome Ledger (DTS-022) — append-only."""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

METHODOLOGY_VERSION = "dts-p4-outcome-ledger-1.0"
_PREREG_PATH = Path(__file__).resolve().parent.parent / "data" / "decision_truth_preregister.jsonl"
_OUTCOME_PATH = Path(__file__).resolve().parent.parent / "data" / "decision_truth_outcomes.jsonl"
_BUFFER: dict[str, dict[str, Any]] = {}


def _utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _append(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")


def _hash_snapshot(snapshot: dict[str, Any]) -> str:
    payload = json.dumps(snapshot, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def pre_register_decision(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Record decision before outcome is known."""
    decision_id = str(snapshot.get("decision_id") or f"dt_{uuid.uuid4().hex[:16]}")
    row = {
        "record_type": "PRE_REGISTERED",
        "decision_id": decision_id,
        "registered_at": _utc_now(),
        "registered_at_ts": time.time(),
        "symbol": snapshot.get("symbol"),
        "horizon": snapshot.get("time_horizon") or snapshot.get("horizon"),
        "decision_state": snapshot.get("decision_state"),
        "confidence": snapshot.get("confidence") or snapshot.get("confidence_percent"),
        "uncertainty": snapshot.get("uncertainty"),
        "methodology_version": snapshot.get("methodology_version") or METHODOLOGY_VERSION,
        "methodology_versions": snapshot.get("methodology_versions"),
        "invalidation_condition": snapshot.get("invalidation_condition"),
        "evidence_class": snapshot.get("evidence_class"),
        "assumptions": snapshot.get("assumptions") or {},
        "evidence_snapshot_hash": _hash_snapshot(snapshot),
        "contract_excerpt": {
            "decision_state": snapshot.get("decision_state"),
            "grade": snapshot.get("grade"),
            "why_not": snapshot.get("why_not"),
        },
    }
    _BUFFER[decision_id] = row
    _append(_PREREG_PATH, row)
    return row


def record_outcome_observed(
    decision_id: str,
    *,
    realized_outcome: dict[str, Any],
    evaluation_result: str | None = None,
    calibration_impact: dict[str, Any] | None = None,
    correction_state: str | None = None,
) -> dict[str, Any]:
    """Append outcome only when pre-registration exists."""
    if decision_id not in _BUFFER and not _has_preregistration(decision_id):
        raise ValueError("outcome_without_preregistration_denied")

    row = {
        "record_type": "OUTCOME_OBSERVED",
        "decision_id": decision_id,
        "observed_at": _utc_now(),
        "realized_outcome": realized_outcome,
        "evaluation_result": evaluation_result,
        "calibration_impact": calibration_impact,
        "correction_state": correction_state,
        "methodology_version": METHODOLOGY_VERSION,
    }
    _append(_OUTCOME_PATH, row)
    return row


def _has_preregistration(decision_id: str) -> bool:
    if not _PREREG_PATH.exists():
        return False
    for line in _PREREG_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("decision_id") == decision_id and row.get("record_type") == "PRE_REGISTERED":
            _BUFFER[decision_id] = row
            return True
    return False


def get_preregistration(decision_id: str) -> dict[str, Any] | None:
    if decision_id in _BUFFER:
        return _BUFFER[decision_id]
    return None if not _has_preregistration(decision_id) else _BUFFER.get(decision_id)
