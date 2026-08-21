"""
BLACKDARK — Unified Decision Ledger.

Links prediction → decision certificate → user exposure → outcome in one queryable store.
Extends oracle_predictions + decision_certificate without duplicating prediction storage.
"""

from __future__ import annotations

import json
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import config
from cap646.evidence_class import attach_evidence_metadata, infer_evidence_class
from path_safety import ensure_under, safe_data_file

_LOCK = threading.Lock()
_MEMORY: dict[str, dict[str, Any]] = {}
_MAX_MEMORY = int(getattr(config, "DECISION_LEDGER_MAX_MEMORY", 5000))
_PATH = safe_data_file(getattr(config, "DECISION_LEDGER_FILENAME", "decision_ledger.jsonl"))
_DATA_BASE = Path(__file__).resolve().parent / "data"


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _persist(row: dict[str, Any]) -> None:
    try:
        path = ensure_under(_PATH, _DATA_BASE)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:  # NOSONAR pythonsecurity:S2083
            fh.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
    except OSError:
        pass


def record_decision(
    *,
    prediction_id: str,
    decision_action: str,
    symbol: str,
    certificate_hash: str | None = None,
    model_version: str | None = None,
    exposure_id: str | None = None,
    outcome_id: str | None = None,
    evidence_class: str | None = None,
    source: str | None = None,
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Append a decision ledger row with evidence metadata."""
    cls = evidence_class or infer_evidence_class(source=source or "oracle")
    decision_id = f"dec_{uuid4().hex[:16]}"
    row = attach_evidence_metadata(
        {
            "decision_id": decision_id,
            "prediction_id": str(prediction_id),
            "decision_action": str(decision_action),
            "symbol": str(symbol).upper(),
            "certificate_hash": certificate_hash,
            "model_version": model_version,
            "exposure_id": exposure_id,
            "outcome_id": outcome_id,
            "source": source or "decision_ledger",
            "meta": meta or {},
            "created_at": _utcnow(),
            "updated_at": _utcnow(),
        },
        source=source or "oracle",
    )
    row["evidence_class"] = cls
    with _LOCK:
        _MEMORY[decision_id] = row
        while len(_MEMORY) > _MAX_MEMORY:
            oldest = next(iter(_MEMORY))
            _MEMORY.pop(oldest, None)
        _persist(row)
    return dict(row)


def link_exposure(decision_id: str, exposure_id: str) -> dict[str, Any] | None:
    with _LOCK:
        row = _MEMORY.get(decision_id)
        if not row:
            return None
        row = dict(row)
        row["exposure_id"] = exposure_id
        row["updated_at"] = _utcnow()
        _MEMORY[decision_id] = row
        _persist(row)
        return row


def link_outcome(decision_id: str, outcome_id: str) -> dict[str, Any] | None:
    with _LOCK:
        row = _MEMORY.get(decision_id)
        if not row:
            return None
        row = dict(row)
        row["outcome_id"] = outcome_id
        row["updated_at"] = _utcnow()
        _MEMORY[decision_id] = row
        _persist(row)
        return row


def get_decision(decision_id: str) -> dict[str, Any] | None:
    with _LOCK:
        return dict(_MEMORY[decision_id]) if decision_id in _MEMORY else None


def ledger_stats() -> dict[str, Any]:
    with _LOCK:
        rows = list(_MEMORY.values())
    if not rows and _PATH.exists():
        try:
            lines = _PATH.read_text(encoding="utf-8").splitlines()[-500:]
            rows = [json.loads(line) for line in lines if line.strip()]
        except (OSError, json.JSONDecodeError):
            rows = []
    by_class: dict[str, int] = {}
    linked_outcomes = 0
    linked_exposure = 0
    for row in rows:
        cls = str(row.get("evidence_class") or "unknown")
        by_class[cls] = by_class.get(cls, 0) + 1
        if row.get("outcome_id"):
            linked_outcomes += 1
        if row.get("exposure_id"):
            linked_exposure += 1
    return {
        "status": "active",
        "total": len(rows),
        "linked_outcomes": linked_outcomes,
        "linked_exposure": linked_exposure,
        "by_evidence_class": by_class,
        "path": str(_PATH),
    }
