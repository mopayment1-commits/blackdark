"""Raw immutable landing zone (DIG-018, DIG-044)."""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

_LOCK = threading.Lock()
_LANDING = Path(__file__).resolve().parents[1] / "data" / "governance_raw_landing.jsonl"


def record_raw_landing(payload: dict[str, Any], *, surface: str) -> dict[str, Any]:
    row = {
        "surface": surface,
        "source_id": payload.get("source_id") or payload.get("source"),
        "symbol": payload.get("symbol") or payload.get("asset"),
        "immutable": True,
    }
    _LANDING.parent.mkdir(parents=True, exist_ok=True)
    with _LOCK:
        with _LANDING.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, default=str) + "\n")
    return row
