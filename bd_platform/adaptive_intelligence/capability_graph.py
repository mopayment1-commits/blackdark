"""Typed Capability Graph — catalog-derived edges without implied causality."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_CATALOG = Path("docs/cap646/CAP646_CATALOG.json")


def build_capability_graph(*, track: str | None = None, limit: int = 200) -> dict[str, Any]:
    rows = json.loads(_CATALOG.read_text(encoding="utf-8"))
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    by_track: dict[str, list[int]] = {}
    for row in rows:
        if track and row.get("track") != track:
            continue
        cid = int(row["id"])
        nodes.append(
            {
                "id": cid,
                "label": row["capability"],
                "track": row.get("track"),
            }
        )
        by_track.setdefault(str(row.get("track")), []).append(cid)
        if len(nodes) >= limit:
            break
    for track_key, ids in by_track.items():
        ids = sorted(ids)
        for a, b in zip(ids, ids[1:]):
            edges.append(
                {
                    "from": a,
                    "to": b,
                    "type": "same_track_adjacency",
                    "causal": False,
                }
            )
    return {
        "nodes": nodes,
        "edges": edges,
        "disclaimer": "Adjacency only — edges do not imply causality",
        "track_filter": track,
    }
