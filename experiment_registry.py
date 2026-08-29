"""
BLACKDARK — Model Risk Management: lightweight Experiment Registry.
"""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any

import config

_REGISTRY = config.DATA_DIR / "experiment_registry.jsonl"


def _append(entry: dict[str, Any]) -> dict[str, Any]:
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    with _REGISTRY.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")
    return entry


def register_experiment(
    *,
    name: str,
    hypothesis: str,
    model_id: str,
    owner: str,
    status: str = "planned",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    entry = {
        "experiment_id": f"exp_{uuid.uuid4().hex[:12]}",
        "name": name,
        "hypothesis": hypothesis,
        "model_id": model_id,
        "owner": owner,
        "status": status,
        "registered_at": time.time(),
        "metadata": metadata or {},
    }
    return _append(entry)


def list_experiments(*, limit: int = 100) -> list[dict[str, Any]]:
    if not _REGISTRY.exists():
        return []
    lines = [ln for ln in _REGISTRY.read_text(encoding="utf-8").splitlines() if ln.strip()]
    rows = [json.loads(ln) for ln in lines[-limit:]]
    return list(reversed(rows))


def mrm_summary() -> dict[str, Any]:
    rows = list_experiments(limit=500)
    by_status: dict[str, int] = {}
    for row in rows:
        st = str(row.get("status") or "unknown")
        by_status[st] = by_status.get(st, 0) + 1
    return {
        "registry_path": str(_REGISTRY),
        "total": len(rows),
        "by_status": by_status,
        "experiments": rows[:25],
        "governing_reference": "docs/governing/DATA_PLATFORM_GOVERNING_REFERENCE.md",
    }
