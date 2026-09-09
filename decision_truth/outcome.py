"""Pre-registered outcome ledger — append-only (DTS-022, DTS-058)."""

from __future__ import annotations

import json
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from decision_truth.methodology import METHODOLOGY_VERSIONS

_LOCK = threading.Lock()
_LEDGER_PATH = Path(__file__).resolve().parents[1] / "data" / "decision_truth_outcomes.jsonl"


def pre_register_outcome(
    *,
    decision_id: str,
    prediction: str,
    confidence: float,
    horizon: str,
    invalidation_condition: str,
    evidence_class: str,
    methodology_versions: dict[str, str],
) -> dict[str, Any]:
    row = {
        "outcome_id": f"out-{uuid4().hex[:12]}",
        "registered_at": datetime.now(UTC).isoformat(),
        "decision_id": decision_id,
        "prediction": prediction,
        "confidence": confidence,
        "horizon": horizon,
        "invalidation_condition": invalidation_condition,
        "evidence_class": evidence_class,
        "methodology_versions": methodology_versions,
        "realized_outcome": None,
        "resolved_at": None,
    }
    _LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _LOCK:
        with _LEDGER_PATH.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row) + "\n")
    return row


def append_realized_outcome(outcome_id: str, *, realized: Any, calibration_impact: Any = None) -> dict[str, Any] | None:
    if not _LEDGER_PATH.is_file():
        return None
    lines = _LEDGER_PATH.read_text(encoding="utf-8").splitlines()
    updated: dict[str, Any] | None = None
    out_lines: list[str] = []
    for line in lines:
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("outcome_id") == outcome_id and row.get("realized_outcome") is None:
            row["realized_outcome"] = realized
            row["resolved_at"] = datetime.now(UTC).isoformat()
            row["calibration_impact"] = calibration_impact
            updated = row
        out_lines.append(json.dumps(row))
    if updated:
        with _LOCK:
            _LEDGER_PATH.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    return updated
