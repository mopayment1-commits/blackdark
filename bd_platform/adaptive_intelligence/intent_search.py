"""Intent search — deterministic capability discovery from user goal text."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

_CATALOG = Path("docs/cap646/CAP646_CATALOG.json")


def _load_catalog() -> list[dict[str, Any]]:
    return json.loads(_CATALOG.read_text(encoding="utf-8"))


def search_intent(query: str, *, limit: int = 8) -> dict[str, Any]:
    q = re.sub(r"[^a-z0-9\s]+", " ", query.lower()).strip()
    tokens = [t for t in q.split() if len(t) > 2]
    if not tokens:
        return {"query": query, "matches": [], "abstain": True, "reason": "empty_query"}
    rows = _load_catalog()
    scored: list[tuple[float, dict[str, Any]]] = []
    for row in rows:
        hay = f"{row.get('capability','')} {row.get('track_name','')}".lower()
        score = sum(1 for t in tokens if t in hay)
        if score:
            scored.append((score, row))
    scored.sort(key=lambda x: (-x[0], x[1]["id"]))
    matches = [
        {
            "capability_id": r["id"],
            "capability": r["capability"],
            "track": r.get("track"),
            "relevance_score": s,
        }
        for s, r in scored[:limit]
    ]
    return {
        "query": query,
        "matches": matches,
        "abstain": not matches,
        "reason": None if matches else "no_catalog_match",
        "doctrine": "deterministic_first",
    }
