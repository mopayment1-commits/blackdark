"""
Order Flow Intelligence (#85) — silent Decision Engine metric.

Aggressive flow from trades by side/size with trade-side QA validated
against exchange official kline taker volumes. NOT a standalone product surface.
"""

from __future__ import annotations

import logging
import time
from datetime import UTC, datetime
from typing import Any

import aiohttp

from blackdark.ingestion.connector_cache import IngestionCache, cache_key
from blackdark.ingestion.futures_cvd_metric import _classify_taker_qa

logger = logging.getLogger("BLACKDARK.OrderFlowIntel")

SPOT_BASE = "https://api.binance.com"
FUTURES_BASE = "https://fapi.binance.com"
_HEADERS = {"User-Agent": "BLACKDARK/1.0", "Accept": "application/json"}
_PAIR_MAP = {"BTC": "BTCUSDT", "ETH": "ETHUSDT", "SOL": "SOLUSDT", "BNB": "BNBUSDT"}
_CACHE = IngestionCache(default_ttl_sec=120, max_ttl_sec=3600)

_SIZE_BUCKETS = (
    ("retail", 0, 1_000),
    ("medium", 1_000, 10_000),
    ("large", 10_000, 100_000),
    ("whale", 100_000, float("inf")),
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _pair(symbol: str) -> str:
    return _PAIR_MAP.get(symbol.upper(), f"{symbol.upper()}USDT")


def _bucket_label(notional: float) -> str:
    for name, lo, hi in _SIZE_BUCKETS:
        if lo <= notional < hi:
            return name
    return "whale"


def _aggregate_trades(trades: list[dict[str, Any]]) -> dict[str, Any]:
    """Bucket and aggregate aggressive buy/sell from Binance aggTrades."""
    buckets: dict[str, dict[str, float]] = {
        name: {"aggressive_buy_usd": 0.0, "aggressive_sell_usd": 0.0, "count": 0}
        for name, *_ in _SIZE_BUCKETS
    }
    qa_issues: list[str] = []
    aggressive_buy = aggressive_sell = 0.0

    for trade in trades:
        try:
            price = float(trade.get("p") or 0)
            qty = float(trade.get("q") or 0)
        except (TypeError, ValueError):
            qa_issues.append("invalid_price_qty")
            continue
        if price <= 0 or qty <= 0:
            qa_issues.append("non_positive_trade")
            continue
        if "m" not in trade:
            qa_issues.append("missing_maker_flag")
            continue

        notional = price * qty
        label = _bucket_label(notional)
        # m=true → buyer is maker → aggressive seller
        if trade.get("m"):
            aggressive_sell += notional
            buckets[label]["aggressive_sell_usd"] += notional
        else:
            aggressive_buy += notional
            buckets[label]["aggressive_buy_usd"] += notional
        buckets[label]["count"] += 1

    total = aggressive_buy + aggressive_sell
    buy_ratio = aggressive_buy / total if total > 0 else None
    return {
        "aggressive_buy_usd": round(aggressive_buy, 2),
        "aggressive_sell_usd": round(aggressive_sell, 2),
        "aggressive_buy_ratio": round(buy_ratio, 4) if buy_ratio is not None else None,
        "buckets": {
            k: {
                "aggressive_buy_usd": round(v["aggressive_buy_usd"], 2),
                "aggressive_sell_usd": round(v["aggressive_sell_usd"], 2),
                "trade_count": int(v["count"]),
            }
            for k, v in buckets.items()
        },
        "trade_count": len(trades),
        "qa_issues": sorted(set(qa_issues)),
    }


def _cross_validate_kline(
    *,
    agg_buy: float,
    kline_taker_buy_quote: float,
    tolerance: float = 0.25,
) -> dict[str, Any]:
    """Trade-side QA — aggTrades rollup vs official kline taker buy volume."""
    if kline_taker_buy_quote <= 0:
        return {"ok": False, "reason": "zero_kline_taker_buy", "match_valid": False}
    if agg_buy <= 0:
        return {"ok": False, "reason": "zero_agg_buy_sample", "match_valid": False}
    # aggTrades sample may be partial window — allow tolerance, flag if exceeded
    delta = abs(agg_buy - kline_taker_buy_quote) / kline_taker_buy_quote
    match_valid = delta <= tolerance
    return {
        "ok": match_valid,
        "match_valid": match_valid,
        "relative_delta": round(delta, 4),
        "tolerance": tolerance,
        "agg_trades_buy_usd": round(agg_buy, 2),
        "kline_taker_buy_usd": round(kline_taker_buy_quote, 2),
        "note": "partial_sample_allowed" if not match_valid and delta < 0.5 else None,
    }


def _reversal_probability_from_series(series: list[dict[str, Any]]) -> float | None:
    """Historical exhaustion → reversal rate from kline series only (no fabrication)."""
    if len(series) < 12:
        return None
    setups = reversals = 0
    for i in range(3, len(series) - 4):
        window = series[i - 3 : i + 1]
        if not all(float(r.get("taker_buy_ratio") or 0) > 0.65 for r in window):
            continue
        setups += 1
        future = series[i + 1 : i + 5]
        if any(float(r.get("taker_buy_ratio") or 1) < 0.45 for r in future):
            reversals += 1
    if setups < 3:
        return None
    return round(reversals / setups, 3)


async def _fetch_klines(symbol: str, *, interval: str = "1h", limit: int = 24) -> list[list[Any]]:
    pair = _pair(symbol)
    url = f"{FUTURES_BASE}/fapi/v1/klines"
    params = {"symbol": pair, "interval": interval, "limit": min(500, limit)}
    timeout = aiohttp.ClientTimeout(total=3.0)
    async with aiohttp.ClientSession(timeout=timeout, headers=_HEADERS) as session:
        async with session.get(url, params=params) as resp:
            if resp.status != 200:
                return []
            rows = await resp.json()
    return rows if isinstance(rows, list) else []


async def compute_order_flow_intelligence(
    symbol: str = "ETH",
    *,
    interval: str = "1h",
    limit: int = 24,
    agg_limit: int = 500,
) -> dict[str, Any]:
    """Aggressive order flow with trade-side QA (#85)."""
    t0 = time.perf_counter()
    sym = symbol.upper()
    pair = _pair(sym)
    ttl = _CACHE.ttl("ORDER_FLOW_CACHE_TTL_SEC", 120)
    ck = cache_key("order_flow", sym, interval, limit, agg_limit)
    cached = _CACHE.get(ck, ttl=ttl)
    if cached:
        return {**cached, "cache_hit": True}

    klines = await _fetch_klines(sym, interval=interval, limit=limit)
    series: list[dict[str, Any]] = []
    qa_pass = qa_fail = 0
    for row in klines:
        if not isinstance(row, list) or len(row) < 11:
            continue
        volume = float(row[5] or 0)
        taker_buy = float(row[9] or 0)
        qa = _classify_taker_qa(volume=volume, taker_buy=taker_buy)
        if not qa["classification_valid"]:
            qa_fail += 1
            continue
        qa_pass += 1
        series.append(
            {
                "open_time": int(row[0]),
                "taker_buy_ratio": qa["taker_buy_ratio"],
                "volume": volume,
                "taker_buy_quote": float(row[7] or 0),
            }
        )

    agg_resp = await _CACHE.http_get_json(
        f"{SPOT_BASE}/api/v3/aggTrades",
        params={"symbol": pair, "limit": min(1000, agg_limit)},
        timeout_sec=3.0,
        cache_key=cache_key("agg_trades", pair, agg_limit),
        ttl=ttl,
        source_slug="binance_spot",
    )
    trades = agg_resp.get("data") if agg_resp.get("ok") else []
    if not isinstance(trades, list):
        trades = []

    flow = _aggregate_trades(trades)
    cross = {"ok": False, "match_valid": False}
    if series and flow.get("aggressive_buy_usd"):
        cross = _cross_validate_kline(
            agg_buy=float(flow["aggressive_buy_usd"]),
            kline_taker_buy_quote=float(series[-1].get("taker_buy_quote") or 0),
        )

    total_bars = qa_pass + qa_fail
    qa_score = round(qa_pass / total_bars, 3) if total_bars else None
    classification_valid = qa_fail == 0 and cross.get("match_valid", False) and not flow.get("qa_issues")

    bias = "neutral"
    current_ratio = series[-1]["taker_buy_ratio"] if series else None
    if current_ratio is not None:
        if current_ratio > 0.65:
            bias = "aggressive_buyers"
        elif current_ratio < 0.35:
            bias = "aggressive_sellers"
        elif len(series) >= 4:
            prior = [float(r["taker_buy_ratio"]) for r in series[-4:-1]]
            if all(r > 0.65 for r in prior) and current_ratio < 0.52:
                bias = "buy_exhaustion"
            elif all(r < 0.35 for r in prior) and current_ratio > 0.48:
                bias = "sell_exhaustion"

    reversal_prob = _reversal_probability_from_series(series) if classification_valid else None

    headline = None
    if classification_valid and bias == "buy_exhaustion" and reversal_prob is not None:
        headline = (
            f"Order Flow: Aggressive buyers exhausted on {sym} — "
            f"{int(reversal_prob * 100)}% probability of reversal within 4 hours"
        )
    elif classification_valid and bias == "sell_exhaustion" and reversal_prob is not None:
        headline = (
            f"Order Flow: Aggressive sellers exhausted on {sym} — "
            f"{int(reversal_prob * 100)}% probability of bounce within 4 hours"
        )
    elif classification_valid and bias == "aggressive_buyers":
        headline = f"Order Flow: Aggressive buyer dominance on {sym} — trade-side QA passed"
    elif classification_valid and bias == "aggressive_sellers":
        headline = f"Order Flow: Aggressive seller dominance on {sym} — trade-side QA passed"

    elapsed = time.perf_counter() - t0
    result = {
        "ok": qa_pass > 0 and bool(trades),
        "feature": "#85",
        "ingestion_role": "decision_engine_input",
        "symbol": sym,
        "pair": pair,
        "interval": interval,
        "bias": bias,
        "aggressive_flow": flow,
        "order_flow_chart": series[-12:],
        "trade_side_qa": {
            "passed_bars": qa_pass,
            "failed_bars": qa_fail,
            "qa_score": qa_score,
            "classification_valid": classification_valid,
            "kline_cross_validation": cross,
            "agg_trade_issues": flow.get("qa_issues") or [],
        },
        "reversal_probability": reversal_prob,
        "headline": headline,
        "data_state": "LIVE" if classification_valid else ("DEGRADED" if qa_pass > 0 else "MISSING"),
        "missing_not_zero": True,
        "latency_ms": round(elapsed * 1000, 1),
        "sla_met": elapsed <= 3.0,
        "timestamp": _utcnow(),
    }
    _CACHE.set(ck, result)
    return result
