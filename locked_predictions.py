"""
BLACKDARK — Locked Predictions (Section Z #1 / Glass Box cadence).

Sealed, time-stamped forecasts before major market events; revealed after.
Deepens Decision Certificate + Public Accuracy Ledger — not a seventh hero.
"""

from __future__ import annotations

import hashlib
import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_PATH = Path("data/locked_predictions.jsonl")
_LOCK = threading.Lock()


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _seal_hash(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def lock_prediction(
    *,
    event_name: str,
    asset: str,
    direction: str,
    rationale: str,
    unlock_at: str,
    opportunity_score: float | None = None,
    prediction_id: int | str | None = None,
) -> dict[str, Any]:
    """Create a sealed locked prediction (public metadata only until unlock)."""
    sealed_body = {
        "event_name": event_name,
        "asset": asset.upper(),
        "direction": direction,
        "rationale": rationale,
        "opportunity_score": opportunity_score,
        "prediction_id": prediction_id,
        "locked_at": _utcnow(),
        "unlock_at": unlock_at,
    }
    row = {
        "id": _seal_hash(sealed_body)[:16],
        "event_name": event_name,
        "asset": asset.upper(),
        "locked_at": sealed_body["locked_at"],
        "unlock_at": unlock_at,
        "seal_hash": _seal_hash(sealed_body),
        "status": "locked",
        "revealed": False,
        # Keep sealed payload encrypted-by-omission until unlock (stored for reveal).
        "_sealed": sealed_body,
    }
    _PATH.parent.mkdir(parents=True, exist_ok=True)
    with _LOCK:
        with _PATH.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, default=str) + "\n")
    return public_view(row)


def public_view(row: dict[str, Any]) -> dict[str, Any]:
    """Strip sealed internals unless unlocked."""
    unlocked = bool(row.get("revealed")) or _is_past(row.get("unlock_at"))
    out = {
        "id": row.get("id"),
        "event_name": row.get("event_name"),
        "asset": row.get("asset"),
        "locked_at": row.get("locked_at"),
        "unlock_at": row.get("unlock_at"),
        "seal_hash": row.get("seal_hash"),
        "status": "unlocked" if unlocked else "locked",
        "revealed": unlocked,
    }
    if unlocked:
        sealed = row.get("_sealed") or {}
        out["direction"] = sealed.get("direction")
        out["rationale"] = sealed.get("rationale")
        out["opportunity_score"] = sealed.get("opportunity_score")
        out["prediction_id"] = sealed.get("prediction_id")
    else:
        out["teaser"] = "Sealed Decision Certificate — direction hidden until unlock time."
    return out


def _is_past(iso_ts: str | None) -> bool:
    if not iso_ts:
        return False
    try:
        ts = datetime.fromisoformat(str(iso_ts).replace("Z", "+00:00"))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) >= ts
    except Exception:
        return False


def list_locked_predictions(*, limit: int = 20) -> list[dict[str, Any]]:
    rows = _read_all()
    # Auto-reveal when unlock time passed
    changed = False
    for row in rows:
        if not row.get("revealed") and _is_past(row.get("unlock_at")):
            row["revealed"] = True
            row["status"] = "unlocked"
            changed = True
    if changed:
        _rewrite(rows)
    views = [public_view(r) for r in rows]
    views.sort(key=lambda r: str(r.get("locked_at") or ""), reverse=True)
    return views[: max(1, min(limit, 100))]


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


def _rewrite(rows: list[dict[str, Any]]) -> None:
    _PATH.parent.mkdir(parents=True, exist_ok=True)
    with _LOCK:
        with _PATH.open("w", encoding="utf-8") as fh:
            for row in rows:
                fh.write(json.dumps(row, default=str) + "\n")


def glass_box_status() -> dict[str, Any]:
    rows = list_locked_predictions(limit=50)
    locked = sum(1 for r in rows if r.get("status") == "locked")
    unlocked = sum(1 for r in rows if r.get("status") == "unlocked")
    return {
        "feature": "locked_predictions",
        "hero_deepening": ["decision_certificate", "public_accuracy_ledger"],
        "total": len(rows),
        "locked": locked,
        "unlocked": unlocked,
        "launch_narrative": "glass_box_challenge",
        "public_page_hint": "/oracle-accuracy#locked",
    }
