"""
BLACKDARK — Failure Intelligence Corpus.

Unified queryable failure registry: Truth vetoes, kill events, provenance downgrades,
OOD rejections. Extends kill_rate_board without replacing it.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import config
from cap646.evidence_class import attach_evidence_metadata, infer_evidence_class
from path_safety import ensure_under, safe_data_file

_PATH = safe_data_file(getattr(config, "FAILURE_CORPUS_FILENAME", "failure_corpus.jsonl"))
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


def record_failure(
    *,
    source: str,
    reason: str,
    category: str,
    evidence_class: str | None = None,
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Record a failure intelligence row and mirror to kill_rate_board when applicable."""
    cls = evidence_class or infer_evidence_class(source=source)
    failure_id = f"fail_{uuid4().hex[:16]}"
    row = attach_evidence_metadata(
        {
            "failure_id": failure_id,
            "source": str(source),
            "reason": str(reason),
            "category": str(category),
            "meta": meta or {},
            "recorded_at": _utcnow(),
        },
        source=source,
    )
    row["evidence_class"] = cls
    _persist(row)
    try:
        from kill_rate_board import record_kill

        record_kill(source, reason, meta={"failure_id": failure_id, **(meta or {})})
    except Exception:
        pass
    return row


def search_failures(*, limit: int = 200) -> list[dict[str, Any]]:
    if not _PATH.exists():
        return []
    try:
        lines = _PATH.read_text(encoding="utf-8").splitlines()[-limit:]
    except OSError:
        return []
    out: list[dict[str, Any]] = []
    for line in lines:
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def corpus_stats() -> dict[str, Any]:
    rows = search_failures(limit=5000)
    by_category: dict[str, int] = {}
    by_source: dict[str, int] = {}
    for row in rows:
        cat = str(row.get("category") or "unknown")
        src = str(row.get("source") or "unknown")
        by_category[cat] = by_category.get(cat, 0) + 1
        by_source[src] = by_source.get(src, 0) + 1
    kill_board: dict[str, Any] = {}
    try:
        from kill_rate_board import build_kill_rate_board

        kill_board = build_kill_rate_board()
    except Exception as exc:
        kill_board = {"error": str(exc)}
    return {
        "status": "active",
        "total": len(rows),
        "by_category": by_category,
        "by_source": by_source,
        "kill_rate_board": kill_board,
        "path": str(_PATH),
    }
