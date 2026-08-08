"""Statistical pairs trading — z-score spread on correlated assets."""

from __future__ import annotations

import math
from datetime import UTC, datetime
from typing import Any

import aiohttp

DEFAULT_PAIRS: tuple[tuple[str, str], ...] = (
    ("BTC", "ETH"),
    ("ETH", "SOL"),
    ("BNB", "ETH"),
    ("BTC", "BNB"),
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


async def _fetch_closes(session: aiohttp.ClientSession, asset: str, *, limit: int = 60) -> list[float]:
    pair = f"{asset}USDT"
    url = f"https://api.binance.com/api/v3/klines?symbol={pair}&interval=1h&limit={limit}"
    try:
        async with session.get(url) as resp:
            if resp.status != 200:
                return []
            rows = await resp.json()
            return [float(r[4]) for r in rows if len(r) > 4]
    except (aiohttp.ClientError, TypeError, ValueError):
        return []


def _zscore(series: list[float]) -> float | None:
    if len(series) < 10:
        return None
    mean = sum(series) / len(series)
    var = sum((x - mean) ** 2 for x in series) / len(series)
    if var <= 0:
        return None
    return (series[-1] - mean) / math.sqrt(var)


def _spread_z(closes_a: list[float], closes_b: list[float]) -> float | None:
    n = min(len(closes_a), len(closes_b))
    if n < 15:
        return None
    ratios = [closes_a[i] / closes_b[i] for i in range(-n, 0) if closes_b[i] > 0]
    return _zscore(ratios)


def _signal_from_z(z: float | None, *, entry: float = 2.0, exit_z: float = 0.5) -> str:
    if z is None:
        return "insufficient_data"
    if z >= entry:
        return "short_spread"
    if z <= -entry:
        return "long_spread"
    if abs(z) <= exit_z:
        return "flat"
    return "hold"


async def scan_pairs(*, pairs: tuple[tuple[str, str], ...] = DEFAULT_PAIRS) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    timeout = aiohttp.ClientTimeout(total=20)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        for asset_a, asset_b in pairs:
            ca = await _fetch_closes(session, asset_a)
            cb = await _fetch_closes(session, asset_b)
            z = _spread_z(ca, cb)
            signal = _signal_from_z(z)
            ratio = ca[-1] / cb[-1] if ca and cb and cb[-1] > 0 else None
            results.append(
                {
                    "pair": f"{asset_a}/{asset_b}",
                    "asset_a": asset_a,
                    "asset_b": asset_b,
                    "ratio": round(ratio, 6) if ratio else None,
                    "z_score": round(z, 3) if z is not None else None,
                    "signal": signal,
                    "method": "log-ratio z-score · 1h klines",
                    "actionable": signal in {"long_spread", "short_spread"},
                }
            )

    actionable = [r for r in results if r["actionable"]]
    return {
        "timestamp": _utcnow(),
        "pairs_scanned": len(results),
        "actionable_count": len(actionable),
        "results": results,
        "top": actionable[0] if actionable else None,
        "disclaimer": "Statistical pairs proxy — not cointegration-tested for live capital.",
    }
