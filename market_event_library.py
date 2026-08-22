"""
BLACKDARK — Market Event Library.

Searchable, versioned event knowledge base with attribution and evidence class.
Complements lake `events` category with governed compounding semantics.
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
_MAX_MEMORY = int(getattr(config, "MARKET_EVENT_MAX_MEMORY", 5000))
_PATH = safe_data_file(getattr(config, "MARKET_EVENT_LIBRARY_FILENAME", "market_event_library.jsonl"))
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


def record_market_event(
    *,
    event_name: str,
    category: str,
    symbol: str | None = None,
    severity: str = "info",
    description: str = "",
    metadata: dict[str, Any] | None = None,
    evidence_class: str | None = None,
    source: str | None = None,
) -> dict[str, Any]:
    """Record a governed market event with evidence metadata."""
    cls = evidence_class or infer_evidence_class(source=source or "oracle")
    event_id = f"evt_{uuid4().hex[:16]}"
    row = attach_evidence_metadata(
        {
            "event_id": event_id,
            "event_name": str(event_name),
            "category": str(category),
            "symbol": str(symbol).upper() if symbol else None,
            "severity": str(severity),
            "description": str(description),
            "metadata": metadata or {},
            "recorded_at": _utcnow(),
            "source": source or "market_event_library",
        },
        source=source or "oracle",
    )
    row["evidence_class"] = cls
    with _LOCK:
        _MEMORY[event_id] = row
        while len(_MEMORY) > _MAX_MEMORY:
            oldest = next(iter(_MEMORY))
            _MEMORY.pop(oldest, None)
        _persist(row)
    return dict(row)


def search_events(
    *,
    query: str = "",
    category: str | None = None,
    symbol: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    q = query.lower().strip()
    sym = symbol.upper() if symbol else None
    with _LOCK:
        rows = list(_MEMORY.values())
    if not rows and _PATH.exists():
        try:
            lines = _PATH.read_text(encoding="utf-8").splitlines()[-2000:]
            rows = [json.loads(line) for line in lines if line.strip()]
        except (OSError, json.JSONDecodeError):
            rows = []
    out: list[dict[str, Any]] = []
    for row in reversed(rows):
        if category and str(row.get("category")) != category:
            continue
        if sym and str(row.get("symbol") or "").upper() != sym:
            continue
        if q:
            blob = " ".join(
                str(row.get(k) or "")
                for k in ("event_name", "description", "category", "symbol")
            ).lower()
            if q not in blob:
                continue
        out.append(row)
        if len(out) >= limit:
            break
    return out


def event_library_stats() -> dict[str, Any]:
    with _LOCK:
        rows = list(_MEMORY.values())
    if not rows and _PATH.exists():
        try:
            lines = _PATH.read_text(encoding="utf-8").splitlines()[-500:]
            rows = [json.loads(line) for line in lines if line.strip()]
        except (OSError, json.JSONDecodeError):
            rows = []
    by_category: dict[str, int] = {}
    for row in rows:
        cat = str(row.get("category") or "unknown")
        by_category[cat] = by_category.get(cat, 0) + 1
    return {
        "status": "active",
        "total": len(rows),
        "by_category": by_category,
        "path": str(_PATH),
    }
