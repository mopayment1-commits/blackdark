"""Strategy marketplace — list/publish trading strategies."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import config


def _path():
    return config.DATA_DIR / "strategy_marketplace.json"


def _load() -> list[dict[str, Any]]:
    p = _path()
    if not p.exists():
        return _default_strategies()
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return _default_strategies()


def _default_strategies() -> list[dict[str, Any]]:
    return [
        {"id": "cross_exchange_v1", "name": "Cross-Exchange Scanner", "tier": "free", "author": "BLACKDARK", "kind": "arbitrage"},
        {"id": "grid_btc_range", "name": "BTC Range Grid", "tier": "free", "author": "BLACKDARK", "kind": "grid"},
        {"id": "oracle_momentum", "name": "Oracle Momentum 24h", "tier": "pro", "author": "BLACKDARK", "kind": "oracle"},
        {"id": "funding_harvest", "name": "Funding Rate Harvest", "tier": "pro", "author": "BLACKDARK", "kind": "derivatives"},
    ]


def list_strategies() -> dict[str, Any]:
    rows = _load()
    return {"strategies": rows, "count": len(rows), "timestamp": datetime.now(timezone.utc).isoformat()}


def publish_strategy(name: str, kind: str, *, tier: str = "community") -> dict[str, Any]:
    rows = _load()
    item = {
        "id": f"str_{len(rows)+1}",
        "name": name,
        "kind": kind,
        "tier": tier,
        "author": "community",
        "published_at": datetime.now(timezone.utc).isoformat(),
    }
    rows.append(item)
    _path().parent.mkdir(parents=True, exist_ok=True)
    _path().write_text(json.dumps(rows, indent=2), encoding="utf-8")
    return item
