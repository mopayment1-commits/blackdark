"""Advanced on-chain / macro metrics — MVRV Z, NUPL, Puell, SOPR, HODL, S2F, VaR/CVaR, Monte Carlo."""

from __future__ import annotations

import math
import random
from datetime import UTC, datetime
from typing import Any

import aiohttp

_SUPPLY = {"BTC": 19_800_000, "ETH": 120_000_000}


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


_ALLOWED_INTERVALS = {"1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "3d", "1w", "1M"}


async def _klines(asset: str, *, interval: str = "1d", limit: int = 365) -> list[float]:
    pair = f"{asset}USDT"
    if not pair.isalnum():
        return []
    if interval not in _ALLOWED_INTERVALS:
        interval = "1d"
    url = f"https://api.binance.com/api/v3/klines?symbol={pair}&interval={interval}&limit={limit}"
    timeout = aiohttp.ClientTimeout(total=15)
    async with aiohttp.ClientSession(timeout=timeout) as session, session.get(url) as resp:
        if resp.status != 200:
            return []
        rows = await resp.json()
        return [float(r[4]) for r in rows if len(r) > 4]


def _sma(values: list[float], period: int) -> float | None:
    if len(values) < period:
        return None
    return sum(values[-period:]) / period


def _std(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    return math.sqrt(sum((x - mean) ** 2 for x in values) / len(values))


def _var_cvar(returns: list[float], *, confidence: float = 0.95, notional: float = 10_000) -> dict[str, float]:
    if len(returns) < 10:
        return {"var_usd": 0.0, "cvar_usd": 0.0, "confidence": confidence}
    sorted_r = sorted(returns)
    idx = max(0, int((1 - confidence) * len(sorted_r)) - 1)
    var_r = sorted_r[idx]
    tail = sorted_r[: idx + 1] or [var_r]
    cvar_r = sum(tail) / len(tail)
    return {
        "var_usd": round(abs(var_r * notional), 2),
        "cvar_usd": round(abs(cvar_r * notional), 2),
        "confidence": confidence,
    }


def _monte_carlo(closes: list[float], *, days: int = 30, simulations: int = 500) -> dict[str, Any]:
    if len(closes) < 20:
        return {"error": "insufficient_data"}
    rets = [(closes[i] - closes[i - 1]) / closes[i - 1] for i in range(1, len(closes))]
    mu = sum(rets) / len(rets)
    sigma = _std(rets)
    start = closes[-1]
    finals: list[float] = []
    for _ in range(simulations):
        price = start
        for _ in range(days):
            shock = random.gauss(mu, sigma)
            price *= 1 + shock
        finals.append(price)
    finals.sort()
    p5 = finals[int(0.05 * len(finals))]
    p50 = finals[int(0.50 * len(finals))]
    p95 = finals[int(0.95 * len(finals))]
    return {
        "horizon_days": days,
        "simulations": simulations,
        "current_price": round(start, 2),
        "p5": round(p5, 2),
        "p50": round(p50, 2),
        "p95": round(p95, 2),
        "method": "GBM bootstrap on daily returns",
    }


def _band_signal(value: float, *, low: float, high: float, low_label: str, high_label: str) -> str:
    if value > high:
        return high_label
    if value < low:
        return low_label
    return "neutral"


def _mvrv_history(closes: list[float]) -> list[float]:
    return [
        closes[i] / (_sma(closes[: i + 1], min(200, i + 1)) or closes[i])
        for i in range(200, len(closes))
    ]


def _hodl_waves(closes: list[float], price: float) -> dict[str, Any]:
    short_hold = sum(closes[-7:]) / 7 if len(closes) >= 7 else price
    long_hold = sum(closes[-90:]) / 90 if len(closes) >= 90 else price
    return {
        "short_term_7d_avg": round(short_hold, 2),
        "long_term_90d_avg": round(long_hold, 2),
        "accumulation_signal": short_hold < long_hold,
    }


def _advanced_proxies(closes: list[float], price: float) -> dict[str, float]:
    sma30 = _sma(closes, 30)
    realized = _sma(closes, min(200, len(closes)))
    mvrv = price / realized if realized and realized > 0 else 1.0
    mvrv_hist = _mvrv_history(closes)
    mvrv_z = (mvrv - (sum(mvrv_hist) / len(mvrv_hist))) / (_std(mvrv_hist) or 1) if mvrv_hist else 0.0
    return {
        "mvrv": mvrv,
        "mvrv_z": mvrv_z,
        "sopr": price / sma30 if sma30 and sma30 > 0 else 1.0,
        "nupl": (price - (realized or price)) / price if price > 0 else 0.0,
        "puell": price / (_sma(closes, 365) or price) if len(closes) >= 30 else 1.0,
    }


async def compute_advanced_metrics(asset: str = "BTC", *, notional: float = 10_000) -> dict[str, Any]:
    asset = asset.upper()
    closes = await _klines(asset, limit=365)
    if not closes:
        return {"asset": asset, "error": "market_data_unavailable", "timestamp": _utcnow()}

    price = closes[-1]
    proxies = _advanced_proxies(closes, price)
    supply = _SUPPLY.get(asset, 100_000_000)
    s2f = supply / max(1.0, supply * 0.02)
    rets = [(closes[i] - closes[i - 1]) / closes[i - 1] for i in range(1, len(closes))]
    risk = _var_cvar(rets, notional=notional)
    mc = _monte_carlo(closes)

    return {
        "asset": asset,
        "price": round(price, 2),
        "timestamp": _utcnow(),
        "mvrv": {
            "ratio": round(proxies["mvrv"], 3),
            "z_score": round(proxies["mvrv_z"], 3),
            "signal": _band_signal(
                proxies["mvrv_z"],
                low=-1,
                high=2,
                low_label="undervalued",
                high_label="overheated",
            ),
        },
        "nupl_proxy": {
            "value": round(proxies["nupl"], 4),
            "signal": _band_signal(proxies["nupl"], low=0, high=0.5, low_label="capitulation", high_label="euphoria"),
        },
        "puell_proxy": {
            "ratio": round(proxies["puell"], 3),
            "signal": _band_signal(
                proxies["puell"],
                low=0.5,
                high=1.2,
                low_label="miner_stress",
                high_label="miner_profit",
            ),
        },
        "sopr_proxy": {
            "ratio": round(proxies["sopr"], 3),
            "signal": _band_signal(
                proxies["sopr"],
                low=0.95,
                high=1.05,
                low_label="capitulation",
                high_label="profit_taking",
            ),
        },
        "hodl_waves": _hodl_waves(closes, price),
        "s2f_proxy": {"ratio": round(s2f, 2), "note": "Supply/annual-issuance proxy"},
        "var_cvar": risk,
        "monte_carlo": mc,
        "disclaimer": "Proxies from price/volume unless Glassnode/Santiment API configured.",
    }
