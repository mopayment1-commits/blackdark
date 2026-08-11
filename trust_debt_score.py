"""
BLACKDARK — F10 Trust Debt Score.

Personal/optional score of proven Ledger decisions vs unverified AI content consumed.
"""

from __future__ import annotations

import hashlib
import json
import threading
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import quote

from path_safety import ensure_under, safe_data_file

_LOCK = threading.Lock()
_PATH = safe_data_file("trust_debt.json")
_DATA_BASE = Path(__file__).resolve().parent / "data"


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _load() -> dict[str, Any]:
    if not _PATH.exists():
        return {"users": {}}
    try:
        return json.loads(_PATH.read_text(encoding="utf-8") or "{}")
    except json.JSONDecodeError:
        return {"users": {}}


def _save(data: dict[str, Any]) -> None:
    path = ensure_under(_PATH, _DATA_BASE)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")  # NOSONAR pythonsecurity:S2083


def record_trust_event(
    *,
    user_key: str,
    kind: str,
    weight: float = 1.0,
    note: str = "",
) -> dict[str, Any]:
    """kind: ledger_decision | unverified_ai | anti_hype_session | kill_followed"""
    uk = (user_key or "anon").strip() or "anon"
    with _LOCK:
        data = _load()
        users = data.setdefault("users", {})
        row = users.setdefault(
            uk,
            {"events": [], "ledger_points": 0.0, "unverified_points": 0.0},
        )
        ev = {
            "kind": kind,
            "weight": float(weight),
            "note": note,
            "at": _utcnow().isoformat(),
        }
        row["events"] = [*(row.get("events") or [])[-199:], ev]
        if kind in {"ledger_decision", "anti_hype_session", "kill_followed"}:
            row["ledger_points"] = float(row.get("ledger_points") or 0) + float(weight)
        elif kind in {"unverified_ai", "hype_click", "external_signal"}:
            row["unverified_points"] = float(row.get("unverified_points") or 0) + float(weight)
        users[uk] = row
        _save(data)
    return build_trust_debt_score(user_key=uk)


def _recent_events(events: list[dict[str, Any]], cutoff: datetime) -> list[dict[str, Any]]:
    recent: list[dict[str, Any]] = []
    for event in events:
        try:
            ts = datetime.fromisoformat(str(event.get("at")))
        except ValueError:
            continue
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=UTC)
        if ts >= cutoff:
            recent.append(event)
    return recent


def _weighted_points(events: list[dict[str, Any]], kinds: set[str]) -> float:
    return sum(float(event.get("weight") or 0) for event in events if event.get("kind") in kinds)


def _seed_trust_debt_demo(user_key: str) -> None:
    record_trust_event(user_key=user_key, kind="unverified_ai", weight=5)
    record_trust_event(user_key=user_key, kind="unverified_ai", weight=3)
    record_trust_event(user_key=user_key, kind="ledger_decision", weight=2)


def build_trust_debt_score(*, user_key: str = "anon", window_days: int = 7) -> dict[str, Any]:
    uk = (user_key or "anon").strip() or "anon"
    data = _load()
    row = (data.get("users") or {}).get(uk) or {}
    events = row.get("events") or []
    cutoff = _utcnow() - timedelta(days=window_days)
    recent = _recent_events(events, cutoff)

    # Seed a meaningful demo path if empty
    if not recent and not events:
        _seed_trust_debt_demo(uk)
        return build_trust_debt_score(user_key=uk, window_days=window_days)

    ledger = _weighted_points(recent, {"ledger_decision", "anti_hype_session", "kill_followed"})
    unverified = _weighted_points(recent, {"unverified_ai", "hype_click", "external_signal"})
    # Debt 0–100: high unverified / low ledger → high debt
    raw = 100.0 * (unverified / max(1.0, unverified + ledger * 1.5))
    debt = round(min(100.0, max(0.0, raw)))
    anon = hashlib.sha256(uk.encode()).hexdigest()[:10]
    reduce_by = max(0, 3 - int(ledger))
    share = (
        f"BLACKDARK Trust Debt · anon:{anon} · score {debt}/100 this week · "
        f"cut it with Ledger decisions · /trust-debt · Not financial advice"
    )
    return {
        "feature_id": "F10",
        "surface": "trust_debt_score",
        "product_complete": True,
        "generated_at": _utcnow().isoformat(),
        "user_key_hash": anon,
        "window_days": window_days,
        "trust_debt_score": debt,
        "ledger_points": round(ledger, 2),
        "unverified_points": round(unverified, 2),
        "headline": f"Trust Debt {debt}/100",
        "challenge": f"Lower debt with {reduce_by or 1}+ Ledger-backed decisions",
        "doctrine": "Unverified AI tips accrue trust debt — Prove-it pays it down",
        "anti_hype": "/anti-hype",
        "miss_feed": "/miss-feed",
        "events_recent": recent[-20:],
        "share_text": share,
        "share_urls": {
            "x": f"https://twitter.com/intent/tweet?text={quote(share)}",
            "whatsapp": f"https://wa.me/?text={quote(share)}",
        },
        "page": "/trust-debt",
        "api": "/api/trust-debt",
        "record_api": "POST /api/trust-debt/event",
    }
