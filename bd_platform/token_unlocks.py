"""Token unlocks — free tier: known schedule + CoinGecko supply pressure.

#703+#704+#707+#708 merged into bd_platform.token_unlock_intelligence_engine (Sprint 2).
Free tier endpoint retained for backward compatibility.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import aiohttp

logger = logging.getLogger("BLACKDARK.TokenUnlocks")


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_known() -> list[dict[str, Any]]:
    path = Path(__file__).resolve().parent.parent / "data" / "known_unlocks.json"
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


async def _coingecko_supply_pressure(limit: int = 20) -> list[dict[str, Any]]:
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": min(limit, 50),
        "page": 1,
        "sparkline": "false",
    }
    timeout = aiohttp.ClientTimeout(total=15)
    rows: list[dict[str, Any]] = []
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session, session.get(url, params=params) as resp:
            if resp.status != 200:
                return rows
            data = await resp.json()
        for coin in data:
            mcap = float(coin.get("market_cap") or 0)
            circ = float(coin.get("circulating_supply") or 0)
            total = float(coin.get("total_supply") or 0)
            if total <= 0 or circ <= 0:
                continue
            locked_pct = round((total - circ) / total * 100, 1)
            if locked_pct < 5:
                continue
            rows.append({
                "asset": str(coin.get("symbol", "")).upper(),
                "name": coin.get("name"),
                "locked_supply_pct": locked_pct,
                "market_cap_usd": mcap,
                "type": "supply_pressure",
                "source": "coingecko_free",
            })
    except (aiohttp.ClientError, TypeError, ValueError):
        logger.debug("CoinGecko supply pressure fetch failed")
    rows.sort(key=lambda x: x.get("locked_supply_pct", 0), reverse=True)
    return rows[:limit]


async def unlock_calendar(*, limit: int = 30) -> dict[str, Any]:
    known = _load_known()
    known.sort(key=lambda x: x.get("unlock_date", ""))
    supply = await _coingecko_supply_pressure(limit=min(limit, 15))

    return {
        "source": "free_tier_composite",
        "timestamp": _utcnow(),
        "scheduled_unlocks": known[:limit],
        "supply_pressure": supply,
        "count": len(known) + len(supply),
        "note": "Scheduled unlocks from public vesting calendars + CoinGecko locked-supply metric (no paid API)",
        "references": ["TokenUnlocks", "CryptoRank", "CoinGecko"],
    }
