"""Decision calibration ledger (DTS-021, DTS-057–059)."""

from __future__ import annotations

import json
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from decision_truth.methodology import METHODOLOGY_VERSIONS

_LOCK = threading.Lock()
_LEDGER_PATH = Path(__file__).resolve().parents[1] / "data" / "decision_truth_calibration.jsonl"


def record_calibration_bucket(
    *,
    confidence_bucket: str,
    predicted_probability: float,
    realized: bool,
    decision_id: str,
) -> dict[str, Any]:
    row = {
        "recorded_at": datetime.now(UTC).isoformat(),
        "decision_id": decision_id,
        "confidence_bucket": confidence_bucket,
        "predicted_probability": predicted_probability,
        "realized": realized,
        "methodology_version": METHODOLOGY_VERSIONS["calibration"],
    }
    _LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _LOCK:
        with _LEDGER_PATH.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row) + "\n")
    return row


def calibration_summary(*, min_samples: int = 20) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    if _LEDGER_PATH.is_file():
        for line in _LEDGER_PATH.read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    if len(rows) < min_samples:
        return {
            "status": "CALIBRATION_INSUFFICIENT_DATA",
            "sample_count": len(rows),
            "methodology_version": METHODOLOGY_VERSIONS["calibration"],
        }
    realized_rate = sum(1 for r in rows if r.get("realized")) / len(rows)
    return {
        "status": "CALIBRATION_AVAILABLE",
        "sample_count": len(rows),
        "realized_frequency": round(realized_rate, 4),
        "calibration_error": round(abs(realized_rate - 0.5), 4),
        "methodology_version": METHODOLOGY_VERSIONS["calibration"],
    }
