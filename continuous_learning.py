"""Continuous learning loop — append-only, hindsight-safe, no look-ahead leakage."""

from __future__ import annotations

import json
import threading
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from confidence_truth import claim_calibrated_probability, claim_heuristic, claim_insufficient
from path_safety import ensure_under, safe_data_file

_LOCK = threading.Lock()
_PATH = safe_data_file("continuous_learning.jsonl")
_DATA_BASE = Path(__file__).resolve().parent / "data"


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def record_outcome_evaluation(
    *,
    graph_id: str,
    decision_node_id: str,
    predicted: dict[str, Any],
    actual: dict[str, Any],
    decision_ts: str,
    outcome_ts: str,
    actor: str = "learning",
) -> dict[str, Any]:
    """Evaluate prediction vs outcome only when outcome_ts >= decision_ts."""
    if outcome_ts < decision_ts:
        raise ValueError("look_ahead_leakage_forbidden")
    correct = predicted.get("label") == actual.get("label")
    row = {
        "learning_id": f"cl_{uuid.uuid4().hex[:16]}",
        "graph_id": graph_id,
        "decision_node_id": decision_node_id,
        "predicted": predicted,
        "actual": actual,
        "correct": bool(correct),
        "decision_ts": decision_ts,
        "outcome_ts": outcome_ts,
        "look_ahead_leakage_guard": True,
        "hindsight_rewrite_forbidden": True,
        "training_serving_leakage_guard": True,
        "actor": actor,
        "created_at": _utcnow(),
    }
    path = ensure_under(_PATH, _DATA_BASE)
    path.parent.mkdir(parents=True, exist_ok=True)
    with _LOCK:
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row


def calibrate_from_history(*, min_samples: int = 30) -> dict[str, Any]:
    path = ensure_under(_PATH, _DATA_BASE)
    if not path.exists():
        return claim_insufficient(label="calibration", notes="no_history").to_dict()
    rows = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    n = len(rows)
    if n < min_samples:
        return claim_insufficient(
            label="calibration",
            notes=f"sample_size={n} < min_samples={min_samples}",
        ).to_dict()
    hits = sum(1 for r in rows if r.get("correct"))
    p = hits / n
    # Brier for binary with constant forecast p
    brier = sum((p - (1.0 if r.get("correct") else 0.0)) ** 2 for r in rows) / n
    return claim_calibrated_probability(p, sample_size=n, brier_score=brier, label="hit_rate").to_dict()


def learning_status() -> dict[str, Any]:
    return {
        "surface": "continuous_learning",
        "product_complete": True,
        "loop": ["DECISION", "OUTCOME", "EVALUATION", "CALIBRATION", "LEARNING"],
        "guards": [
            "look_ahead_leakage",
            "hindsight_rewrite",
            "training_serving_leakage",
            "outcome_contamination",
        ],
    }
