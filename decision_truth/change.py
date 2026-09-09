"""Decision change detector (DTS-023, DTS-060)."""

from __future__ import annotations

import json
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from decision_truth.methodology import METHODOLOGY_VERSIONS

_LOCK = threading.Lock()
_HISTORY_PATH = Path(__file__).resolve().parents[1] / "data" / "decision_truth_history.jsonl"


def detect_change(
    *,
    decision_id: str,
    previous_state: str,
    new_state: str,
    changed_inputs: dict[str, Any],
    materiality: str = "medium",
    reason: str = "",
    evidence_delta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if previous_state == new_state:
        return {"changed": False, "decision_id": decision_id}
    row = {
        "recorded_at": datetime.now(UTC).isoformat(),
        "decision_id": decision_id,
        "previous_state": previous_state,
        "new_state": new_state,
        "changed_inputs": changed_inputs,
        "materiality": materiality,
        "reason": reason,
        "evidence_delta": evidence_delta or {},
        "methodology_version": METHODOLOGY_VERSIONS["change_detector"],
    }
    _HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _LOCK:
        with _HISTORY_PATH.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row) + "\n")
    return {"changed": True, **row}
