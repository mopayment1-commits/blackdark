"""
Cross-Asset Correlation (#42) — rolling crypto ↔ TradFi relationship analysis.

Portfolio AI / Risk Dashboard backend. NOT Alpha Vantage quote display (#12).
Computes rolling Pearson correlation with window + significance labels.
"""

from __future__ import annotations

import logging
import math
import time
from datetime import UTC, datetime
from typing import Any

import aiohttp

import config
from blackdark.canonical.resolver import resolve_asset

logger = logging.getLogger("BLACKDARK.CrossAssetCorrelation")

DEFAULT_WINDOW = 30
TRADFI_SERIES: dict[str, str] = {
    "SPX": getattr(config, "MACRO_YAHOO_SPX_SYMBOL", "^GSPC"),
    "DXY": getattr(config, "MACRO_YAHOO_DXY_SYMBOL", "DX-Y.NYB"),
    "GOLD": getattr(config, "MACRO_YAHOO_GOLD_SYMBOL", "GC=F"),
    "NDX": "^NDX",
    "VIX": getattr(config, "ORACLE_MACRO_VIX_SYMBOL", "^VIX"),
}
CRYPTO_DEFAULTS = ("BTC", "ETH", "SOL")


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _pct_returns(closes: list[float]) -> list[float]:
    out: list[float] = []
    for i in range(1, len(closes)):
        prev, cur = closes[i - 1], closes[i]
        if prev and prev != 0:
            out.append((cur - prev) / prev)
    return out


def _pearson(x: list[float], y: list[float]) -> float | None:
    n = min(len(x), len(y))
    if n < 3:
        return None
    xs, ys = x[-n:], y[-n:]
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    den_x = math.sqrt(sum((a - mx) ** 2 for a in xs))
    den_y = math.sqrt(sum((b - my) ** 2 for b in ys))
    if den_x == 0 or den_y == 0:
        return None
    return num / (den_x * den_y)


def _significance(correlation: float | None, samples: int) -> dict[str, Any]:
    """Window/significance metadata — honest labels, no fabricated p-values."""
    if correlation is None or samples < 5:
        return {
            "label": "insufficient_data",
            "strength": None,
            "samples": samples,
            "significant": False,
        }
    r = abs(correlation)
    if r >= 0.6:
        strength = "strong"
    elif r >= 0.3:
        strength = "moderate"
    else:
        strength = "weak"
    # Rule-of-thumb: |r|*sqrt(n) > 2 suggests meaningful at n>=30
    t_approx = abs(correlation) * math.sqrt(max(samples - 2, 1) / max(1 - correlation**2, 1e-9))
    significant = samples >= DEFAULT_WINDOW and t_approx >= 1.96
    return {
        "label": strength if significant else f"{strength}_low_confidence",
        "strength": strength,
        "samples": samples,
        "significant": significant,
        "t_stat_approx": round(t_approx, 3),
    }


async def _fetch_yahoo_daily_closes(symbol: str, *, range_days: str = "3mo") -> list[float]:
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    params = {"interval": "1d", "range": range_days}
    timeout = aiohttp.ClientTimeout(total=3.0)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    return []
                payload = await resp.json()
        result = (payload.get("chart") or {}).get("result") or []
        if not result:
            return []
        closes = ((result[0].get("indicators") or {}).get("quote") or [{}])[0].get("close") or []
        return [float(v) for v in closes if v is not None]
    except (aiohttp.ClientError, TypeError, ValueError):
        return []


async def _fetch_crypto_daily_closes(symbol: str, *, limit: int = 90) -> list[float]:
    from market_context import fetch_binance_klines

    pair = f"{symbol.upper()}USDT"
    return await fetch_binance_klines(pair, interval="1d", limit=limit)


async def _series_returns(asset_key: str, *, window: int) -> tuple[list[float], str]:
    key = asset_key.upper()
    if key in CRYPTO_DEFAULTS or resolve_asset(key).found:
        closes = await _fetch_crypto_daily_closes(key, limit=max(window + 5, 60))
        source = "binance_daily"
    else:
        yahoo_sym = TRADFI_SERIES.get(key, key)
        closes = await _fetch_yahoo_daily_closes(yahoo_sym)
        source = "yahoo_daily"
    rets = _pct_returns(closes)
    return rets[-window:], source


async def compute_pair_correlation(
    crypto: str,
    tradfi: str,
    *,
    window: int = DEFAULT_WINDOW,
) -> dict[str, Any]:
    crypto_rets, c_src = await _series_returns(crypto, window=window)
    trad_rets, t_src = await _series_returns(tradfi, window=window)
    n = min(len(crypto_rets), len(trad_rets))
    corr = _pearson(crypto_rets, trad_rets)
    sig = _significance(corr, n)
    direction = None
    if corr is not None:
        if corr > 0.15:
            direction = "positive"
        elif corr < -0.15:
            direction = "negative"
        else:
            direction = "neutral"
    return {
        "crypto": crypto.upper(),
        "tradfi": tradfi.upper(),
        "correlation": round(corr, 4) if corr is not None else None,
        "direction": direction,
        "window_days": window,
        "samples": n,
        "significance": sig,
        "sources": {"crypto": c_src, "tradfi": t_src},
    }


async def compute_correlation_matrix(
    *,
    crypto_assets: list[str] | None = None,
    tradfi_assets: list[str] | None = None,
    window: int = DEFAULT_WINDOW,
) -> dict[str, Any]:
    """Rolling correlation matrix — crypto rows × tradfi columns."""
    t0 = time.perf_counter()
    crypto_list = [a.upper() for a in (crypto_assets or list(CRYPTO_DEFAULTS))]
    tradfi_list = [a.upper() for a in (tradfi_assets or list(TRADFI_SERIES.keys()))]
    window = max(7, min(90, window))

    pairs: list[dict[str, Any]] = []
    matrix: dict[str, dict[str, Any]] = {}
    for c in crypto_list:
        matrix[c] = {}
        for t in tradfi_list:
            row = await compute_pair_correlation(c, t, window=window)
            pairs.append(row)
            matrix[c][t] = {
                "correlation": row["correlation"],
                "direction": row["direction"],
                "significance": row["significance"],
            }

    elapsed = time.perf_counter() - t0
    return {
        "ok": True,
        "feature": "#42",
        "surface": "cross_asset_correlation",
        "window_days": window,
        "crypto_assets": crypto_list,
        "tradfi_assets": tradfi_list,
        "matrix": matrix,
        "pairs": pairs,
        "latency_ms": round(elapsed * 1000, 1),
        "sla_met": elapsed <= 3.0,
        "timestamp": _utcnow(),
    }


async def correlation_view_for_asset(asset: str = "BTC", *, window: int = DEFAULT_WINDOW) -> dict[str, Any]:
    """Portfolio AI / Risk Dashboard correlation view for one crypto asset."""
    sym = asset.upper()
    matrix = await compute_correlation_matrix(crypto_assets=[sym], window=window)
    row = (matrix.get("matrix") or {}).get(sym) or {}
    highlights: list[str] = []
    for trad, cell in row.items():
        corr = cell.get("correlation")
        sig = cell.get("significance") or {}
        if corr is None:
            continue
        if sig.get("significant") and abs(corr) >= 0.3:
            dir_word = "positive" if corr > 0 else "negative"
            highlights.append(
                f"{sym} ↔ {trad}: {corr:+.2f} ({sig.get('strength')} {dir_word}, {window}d window)"
            )

    diversification_score = None
    strong_negs = [
        abs(v["correlation"])
        for v in row.values()
        if v.get("correlation") is not None and v["correlation"] < -0.3
    ]
    if strong_negs:
        diversification_score = round(min(10, 5 + sum(strong_negs) * 2), 1)

    return {
        "ok": True,
        "feature": "#42",
        "asset": sym,
        "window_days": window,
        "correlations": row,
        "highlights": highlights or [f"No significant {window}d correlations detected for {sym}"],
        "diversification_score": diversification_score,
        "risk_note": (
            "Higher diversification score suggests macro hedges may offset crypto drawdowns"
            if diversification_score
            else "Limited macro hedge detected from rolling correlations"
        ),
        "matrix": matrix.get("matrix"),
        "latency_ms": matrix.get("latency_ms"),
        "timestamp": _utcnow(),
    }


def portfolio_correlation_enrichment(
  holdings: list[dict[str, Any]],
  *,
  matrix: dict[str, dict[str, dict[str, Any]]] | None,
) -> dict[str, Any]:
    """Extend Portfolio AI with matrix-based concentration insight."""
    if not holdings or not matrix:
        return {"correlation_enriched": False}
    weighted_spx = 0.0
    total = sum(float(h.get("value_usd") or 0) for h in holdings)
    if total <= 0:
        return {"correlation_enriched": False}
    for h in holdings:
        sym = str(h.get("symbol") or h.get("asset") or "").upper()
        w = float(h.get("value_usd") or 0) / total
        spx_corr = (matrix.get(sym) or {}).get("SPX", {}).get("correlation")
        if spx_corr is not None:
            weighted_spx += w * float(spx_corr)
    return {
        "correlation_enriched": True,
        "weighted_spx_correlation": round(weighted_spx, 4),
        "portfolio_macro_beta_note": (
            f"Portfolio weighted SPX correlation {weighted_spx:+.2f} (30d rolling)"
        ),
    }
