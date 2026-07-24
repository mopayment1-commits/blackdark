"""
BLACKDARK — Live Opportunity Duration Tracker (Plan Point 25).

Tracks how long profitable arbitrage signals persist before disappearing.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("BLACKDARK.OpportunityTracker")

_ACTIVE: dict[str, dict[str, Any]] = {}
_HISTORY: list[dict[str, Any]] = []
_MAX_HISTORY = 200


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _fingerprint(opp: dict[str, Any]) -> str:
    key = "|".join(
        [
            str(opp.get("kind") or ""),
            str(opp.get("asset") or opp.get("symbol") or ""),
            str(opp.get("path") or ""),
            str(opp.get("buy_exchange") or opp.get("buy_venue") or ""),
            str(opp.get("sell_exchange") or opp.get("sell_venue") or ""),
        ]
    )
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


def _parse_ts(value: str | None) -> float | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def touch_opportunity(opp: dict[str, Any]) -> dict[str, Any]:
    """Register or refresh an opportunity; returns duration metadata."""
    fp = _fingerprint(opp)
    now = time.time()
    profit = float(opp.get("net_profit_usdt") or 0)

    if fp not in _ACTIVE:
        _ACTIVE[fp] = {
            "fingerprint": fp,
            "kind": opp.get("kind"),
            "asset": opp.get("asset") or opp.get("symbol"),
            "first_seen_ts": now,
            "last_seen_ts": now,
            "first_seen": _utcnow_iso(),
            "last_seen": _utcnow_iso(),
            "peak_profit_usdt": profit,
            "sightings": 1,
        }
    else:
        row = _ACTIVE[fp]
        row["last_seen_ts"] = now
        row["last_seen"] = _utcnow_iso()
        row["sightings"] = int(row.get("sightings") or 0) + 1
        row["peak_profit_usdt"] = max(float(row.get("peak_profit_usdt") or 0), profit)

    row = _ACTIVE[fp]
    duration_sec = max(0.0, now - float(row["first_seen_ts"]))
    row["duration_seconds"] = round(duration_sec, 1)
    row["duration_label"] = _format_duration(duration_sec)
    return dict(row)


def _format_duration(seconds: float) -> str:
    if seconds < 60:
        return f"{int(seconds)}s"
    if seconds < 3600:
        return f"{int(seconds // 60)}m {int(seconds % 60)}s"
    return f"{int(seconds // 3600)}h {int((seconds % 3600) // 60)}m"


def sync_scan_opportunities(opportunities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Annotate scan results with live duration; expire stale entries."""
    seen: set[str] = set()
    enriched: list[dict[str, Any]] = []

    for opp in opportunities:
        meta = touch_opportunity(opp)
        seen.add(meta["fingerprint"])
        merged = dict(opp)
        merged["live_duration_seconds"] = meta["duration_seconds"]
        merged["live_duration_label"] = meta["duration_label"]
        merged["first_seen"] = meta["first_seen"]
        merged["sightings"] = meta["sightings"]
        enriched.append(merged)

    _expire_missing(seen)
    return enriched


def _expire_missing(current_fps: set[str], *, ttl_seconds: float = 45.0) -> None:
    now = time.time()
    expired: list[str] = []
    for fp, row in _ACTIVE.items():
        if fp in current_fps:
            continue
        last_seen = float(row.get("last_seen_ts") or now)
        if now - last_seen >= ttl_seconds:
            expired.append(fp)

    for fp in expired:
        row = _ACTIVE.pop(fp, None)
        if row:
            _HISTORY.insert(0, row)
            if len(_HISTORY) > _MAX_HISTORY:
                del _HISTORY[_MAX_HISTORY:]


def get_active_durations(limit: int = 20) -> list[dict[str, Any]]:
    rows = sorted(
        _ACTIVE.values(),
        key=lambda r: float(r.get("duration_seconds") or 0),
        reverse=True,
    )
    return rows[:limit]


def get_duration_history(limit: int = 20) -> list[dict[str, Any]]:
    return _HISTORY[:limit]


def export_state() -> dict[str, Any]:
    return {
        "active_count": len(_ACTIVE),
        "active": get_active_durations(50),
        "recent_expired": get_duration_history(20),
        "timestamp": _utcnow_iso(),
    }
