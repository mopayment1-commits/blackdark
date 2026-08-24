"""Track exchange listing first-seen times for honest lead-time claims."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.ExchangeListingTracker")

_SNAPSHOT_PATH = Path("data/exchange_listing_snapshots.json")


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load() -> dict[str, Any]:
    if not _SNAPSHOT_PATH.exists():
        return {"pairs": {}}
    try:
        return json.loads(_SNAPSHOT_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"pairs": {}}


def _save(data: dict[str, Any]) -> None:
    _SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    _SNAPSHOT_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def record_sightings(exchange: str, symbols: set[str]) -> dict[str, Any]:
    """Record first-seen timestamp per exchange:SYMBOL."""
    data = _load()
    pairs: dict[str, dict[str, Any]] = data.setdefault("pairs", {})
    now = _utcnow()
    newly_seen: list[str] = []
    for sym in symbols:
        key = f"{exchange.lower()}:{sym.upper()}"
        if key not in pairs:
            pairs[key] = {"first_seen": now, "exchange": exchange.lower(), "symbol": sym.upper()}
            newly_seen.append(sym.upper())
    data["updated_at"] = now
    _save(data)
    return {"newly_seen": newly_seen, "total_tracked": len(pairs)}


def lead_time_hours(*, source_exchange: str, symbol: str, target_exchange: str = "binance") -> float | None:
    """Hours between first sighting on source vs target — only when both recorded."""
    data = _load()
    pairs = data.get("pairs") or {}
    src = pairs.get(f"{source_exchange.lower()}:{symbol.upper()}")
    tgt = pairs.get(f"{target_exchange.lower()}:{symbol.upper()}")
    if not src or not tgt:
        return None
    try:
        t0 = datetime.fromisoformat(str(src["first_seen"]).replace("Z", "+00:00"))
        t1 = datetime.fromisoformat(str(tgt["first_seen"]).replace("Z", "+00:00"))
        delta = (t1 - t0).total_seconds() / 3600
        return round(delta, 1) if delta > 0 else None
    except (TypeError, ValueError):
        return None


def not_on_target(symbols: set[str], *, source_exchange: str, target_exchange: str = "binance") -> list[str]:
    """Symbols seen on source but not yet recorded on target exchange."""
    data = _load()
    pairs = data.get("pairs") or {}
    target_seen = {k.split(":", 1)[1] for k in pairs if k.startswith(f"{target_exchange.lower()}:")}
    return sorted(sym for sym in symbols if sym.upper() not in target_seen)
