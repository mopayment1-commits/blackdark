"""Decision history integrity — append-only audit trail (DTS-060)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

METHODOLOGY_VERSION = "dts-p4-history-integrity-1.0"
_HISTORY_PATH = Path(__file__).resolve().parent.parent / "data" / "decision_truth_history.jsonl"


def _utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def record_history_event(
    *,
    previous_state: str | None,
    new_state: str,
    cause: str,
    evidence_delta: dict[str, Any] | None = None,
    methodology_version: str | None = None,
    decision_id: str | None = None,
    correction: bool = False,
) -> dict[str, Any]:
    """Append-only material state change record."""
    row = {
        "previous_state": previous_state,
        "new_state": new_state,
        "timestamp_utc": _utc_now(),
        "cause": cause,
        "evidence_delta": evidence_delta or {},
        "methodology_version": methodology_version or METHODOLOGY_VERSION,
        "decision_id": decision_id,
        "correction": correction,
        "append_only": True,
    }
    _HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _HISTORY_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
    return row


def recent_history(limit: int = 50) -> list[dict[str, Any]]:
    if not _HISTORY_PATH.exists():
        return []
    lines = _HISTORY_PATH.read_text(encoding="utf-8").strip().splitlines()
    return [json.loads(line) for line in lines[-limit:] if line.strip()]
