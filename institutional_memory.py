"""Institutional Memory — durable append-only store for decisions/outcomes/learning."""

from __future__ import annotations

import json
import threading
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from path_safety import ensure_under, safe_data_file

_LOCK = threading.Lock()
_PATH = safe_data_file("institutional_memory.jsonl")
_DATA_BASE = Path(__file__).resolve().parent / "data"

KINDS = frozenset(
    {
        "market_state",
        "decision",
        "evidence",
        "contradiction",
        "prediction",
        "confidence",
        "execution_outcome",
        "actual_outcome",
        "failure",
        "regime_context",
        "learning_event",
    }
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def remember(
    kind: str,
    payload: dict[str, Any],
    *,
    graph_id: str = "",
    regime: str = "",
    actor: str = "system",
) -> dict[str, Any]:
    kind = kind.strip().lower()
    if kind not in KINDS:
        raise ValueError(f"invalid_memory_kind:{kind}")
    row = {
        "memory_id": f"im_{uuid.uuid4().hex[:16]}",
        "kind": kind,
        "payload": payload,
        "graph_id": graph_id,
        "regime": regime,
        "actor": actor,
        "created_at": _utcnow(),
        "immutable": True,
        "training_serving_leakage_guard": True,
    }
    path = ensure_under(_PATH, _DATA_BASE)
    path.parent.mkdir(parents=True, exist_ok=True)
    with _LOCK:
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    try:
        from institutional_store import memory_remember_sync

        memory_remember_sync(row)
    except Exception:
        pass
    return row


def query(*, kind: str | None = None, graph_id: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
    path = ensure_under(_PATH, _DATA_BASE)
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if kind and row.get("kind") != kind:
                continue
            if graph_id and row.get("graph_id") != graph_id:
                continue
            rows.append(row)
    return rows[-limit:]


def memory_status() -> dict[str, Any]:
    rows = query(limit=10_000)
    return {
        "surface": "institutional_memory",
        "entries": len(rows),
        "append_only": True,
        "product_complete": False,
        "note": "Durable memory is append-only; continuous learning must attach new events, never rewrite.",
    }
