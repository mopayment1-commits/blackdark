"""
BLACKDARK — Discipline Mirror (Section Z #2).

Private, optional behavioral mirror: did the user follow the Oracle signal?
Personal-only stats — never public. Deepens Portfolio AI / behavioral learning.
"""

from __future__ import annotations

import json
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_PATH = Path("data/discipline_mirror.jsonl")
_LOCK = threading.Lock()


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def record_follow_up(
    *,
    user_key: str,
    asset: str,
    system_action: str,
    followed: bool,
    prediction_id: int | str | None = None,
    opportunity_score: float | None = None,
    note: str | None = None,
) -> dict[str, Any]:
    """Store a private follow-up answer for one user."""
    key = (user_key or "anonymous").strip().lower() or "anonymous"
    row = {
        "id": f"{key}:{_utcnow()}",
        "user_key": key,
        "asset": asset.upper(),
        "system_action": str(system_action or "").upper(),
        "followed": bool(followed),
        "prediction_id": prediction_id,
        "opportunity_score": opportunity_score,
        "note": (note or "")[:240],
        "created_at": _utcnow(),
        "private": True,
    }
    _PATH.parent.mkdir(parents=True, exist_ok=True)
    with _LOCK, _PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, default=str) + "\n")
    return {"ok": True, "id": row["id"], "private": True}


def _outcome_points(system_action: str, label: str | None) -> float | None:
    """Heuristic points when a prediction label is known."""
    if not label or label == "pending":
        return None
    lab = str(label).lower()
    if lab == "correct":
        return 1.0
    if lab == "incorrect":
        return -1.0
    if lab == "partial":
        return 0.25
    return 0.0


def personal_mirror(
    user_key: str,
    *,
    limit: int = 100,
    label_by_id: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Private summary for one user only — optional label map for system-vs-you delta."""
    key = (user_key or "").strip().lower()
    if not key:
        return {"error": "user_key_required", "private": True}
    rows = [r for r in _read_all() if r.get("user_key") == key][-limit:]
    followed = [r for r in rows if r.get("followed")]
    ignored = [r for r in rows if not r.get("followed")]
    labels = label_by_id or {}

    system_score = 0.0
    user_score = 0.0
    scored = 0
    enriched_recent = []
    for r in reversed(rows[-20:]):
        pid = r.get("prediction_id")
        label = labels.get(str(pid)) if pid is not None else None
        sys_pts = _outcome_points(str(r.get("system_action") or ""), label)
        if sys_pts is not None:
            scored += 1
            system_score += sys_pts
            user_score += sys_pts if r.get("followed") else -sys_pts
        enriched_recent.append(
            {
                "asset": r.get("asset"),
                "system_action": r.get("system_action"),
                "followed": r.get("followed"),
                "prediction_id": r.get("prediction_id"),
                "created_at": r.get("created_at"),
                "outcome_label": label or "pending",
            }
        )

    delta = round(system_score - user_score, 2) if scored else None
    return {
        "private": True,
        "user_key": key,
        "total_answers": len(rows),
        "followed_count": len(followed),
        "ignored_count": len(ignored),
        "follow_rate_percent": round(100.0 * len(followed) / len(rows), 1) if rows else 0.0,
        "scored_samples": scored,
        "system_discipline_score": round(system_score, 2),
        "your_behavior_score": round(user_score, 2),
        "delta_system_minus_you": delta,
        "delta_plain_english": (
            f"System-minus-you discipline delta: {delta:+.1f}. "
            "Positive means following the Oracle beat your overrides on resolved samples."
            if delta is not None
            else "Keep answering after signals — delta appears once predictions resolve (24h)."
        ),
        "message": (
            "Private Discipline Mirror — only you can see this. "
            "Compare following the Single-Sentence Oracle vs emotional overrides."
        ),
        "recent": enriched_recent[:12],
        "hero_deepening": "portfolio_ai",
        "compliance": {
            "disclaimer": "Private coaching metrics — not financial advice. Not shown publicly.",
        },
    }


def _read_all() -> list[dict[str, Any]]:
    if not _PATH.exists():
        return []
    out: list[dict[str, Any]] = []
    with _LOCK:
        for line in _PATH.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out
