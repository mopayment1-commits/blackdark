"""
BLACKDARK — User Exposure Log.

Records what decision/signal was shown to which user/tier/surface and when.
Required for Decision→Outcome attribution and PRODUCTION_VERIFIED evidence paths.
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
_MAX_MEMORY = int(getattr(config, "USER_EXPOSURE_MAX_MEMORY", 10000))
_PATH = safe_data_file(getattr(config, "USER_EXPOSURE_FILENAME", "user_exposure_log.jsonl"))
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


def record_user_exposure(
    *,
    user_id: str,
    tier: str,
    surface: str,
    decision_id: str | None = None,
    prediction_id: str | None = None,
    symbol: str | None = None,
    evidence_class: str | None = None,
    source: str | None = None,
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Record a user-facing exposure event with evidence class."""
    cls = evidence_class or infer_evidence_class(source=source or "oracle")
    exposure_id = f"exp_{uuid4().hex[:16]}"
    row = attach_evidence_metadata(
        {
            "exposure_id": exposure_id,
            "user_id": str(user_id),
            "tier": str(tier),
            "surface": str(surface),
            "decision_id": decision_id,
            "prediction_id": prediction_id,
            "symbol": str(symbol).upper() if symbol else None,
            "shown_at": _utcnow(),
            "source": source or "user_exposure_log",
            "meta": meta or {},
        },
        source=source or "oracle",
    )
    row["evidence_class"] = cls
    with _LOCK:
        _MEMORY[exposure_id] = row
        while len(_MEMORY) > _MAX_MEMORY:
            oldest = next(iter(_MEMORY))
            _MEMORY.pop(oldest, None)
        _persist(row)
    return dict(row)


def exposure_stats() -> dict[str, Any]:
    with _LOCK:
        rows = list(_MEMORY.values())
    if not rows and _PATH.exists():
        try:
            lines = _PATH.read_text(encoding="utf-8").splitlines()[-500:]
            rows = [json.loads(line) for line in lines if line.strip()]
        except (OSError, json.JSONDecodeError):
            rows = []
    by_surface: dict[str, int] = {}
    by_tier: dict[str, int] = {}
    for row in rows:
        surf = str(row.get("surface") or "unknown")
        tier = str(row.get("tier") or "unknown")
        by_surface[surf] = by_surface.get(surf, 0) + 1
        by_tier[tier] = by_tier.get(tier, 0) + 1
    return {
        "status": "active",
        "total": len(rows),
        "by_surface": by_surface,
        "by_tier": by_tier,
        "path": str(_PATH),
    }
