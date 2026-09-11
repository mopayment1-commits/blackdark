"""Append-only decision outcome ledger (DTS-022 MVP)."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from decision_truth.contract import DecisionContract

_LEDGER_PATH = Path(__file__).resolve().parent.parent / "data" / "decision_truth_ledger.jsonl"
_BUFFER: list[dict[str, Any]] = []


def record_outcome(contract: DecisionContract) -> dict[str, Any]:
    row = {
        "recorded_at": time.time(),
        "symbol": contract.symbol,
        "decision_state": contract.decision_state.value,
        "methodology_version": contract.methodology_version,
        "contract": contract.to_dict(),
    }
    _BUFFER.append(row)
    _LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _LEDGER_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
    return row


def recent_outcomes(limit: int = 50) -> list[dict[str, Any]]:
    if not _LEDGER_PATH.exists():
        return list(_BUFFER[-limit:])
    lines = _LEDGER_PATH.read_text(encoding="utf-8").strip().splitlines()
    rows = [json.loads(line) for line in lines[-limit:] if line.strip()]
    return rows
