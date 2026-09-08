"""Evaluation contamination registry — tracks train/eval overlap and leakage risk."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_STORE = Path("data/evaluation_contamination_registry.jsonl")


def register_contamination_event(
    *,
    evaluation_id: str,
    dataset_id: str,
    contamination_type: str,
    severity: str,
    detail: str,
) -> dict[str, Any]:
    row = {
        "evaluation_id": evaluation_id,
        "dataset_id": dataset_id,
        "contamination_type": contamination_type,
        "severity": severity,
        "detail": detail,
        "registered_at": datetime.now(UTC).isoformat(),
    }
    _STORE.parent.mkdir(parents=True, exist_ok=True)
    with _STORE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row


def list_contamination_events(*, evaluation_id: str | None = None) -> list[dict[str, Any]]:
    if not _STORE.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for line in _STORE.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if evaluation_id is None or row.get("evaluation_id") == evaluation_id:
            rows.append(row)
    return rows


def contamination_registry_status() -> dict[str, Any]:
    events = list_contamination_events()
    return {
        "module": "evaluation_contamination_registry",
        "status": "ACTIVE_LOCAL",
        "event_count": len(events),
        "store": str(_STORE),
    }
