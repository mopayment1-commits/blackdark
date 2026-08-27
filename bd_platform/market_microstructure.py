"""
Market Microstructure Intelligence (#74) — silent Decision Engine layer.

Analyzes L2 order books + tick flow for toxicity, spoofing heuristics, liquidity health.
NOT a standalone branded product — feeds #48 Decision Engine and #56 Execution Optimizer.

Uses transparent rule-based detectors (no black-box ML claims).
"""

from __future__ import annotations

import asyncio
import logging
import statistics
import time
from datetime import UTC, datetime
from typing import Any

import aiohttp

from arbitrage_engine import walk_asks, walk_bids
from blackdark.ingestion.connector_cache import IngestionCache, cache_key

logger = logging.getLogger("BLACKDARK.MarketMicrostructure")

SPOT_BASE = "https://api.binance.com"
_HEADERS = {"User-Agent": "BLACKDARK/1.0", "Accept": "application/json"}
_CACHE = IngestionCache(default_ttl_sec=5, max_ttl_sec=60)

# ≥50 liquid spot assets (spot + futures proxy via Binance USDT pairs)
LIQUID_ASSETS: tuple[str, ...] = (
    "BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "DOGE", "AVAX", "DOT", "LINK",
    "MATIC", "POL", "LTC", "BCH", "UNI", "ATOM", "ETC", "FIL", "APT", "ARB",
    "OP", "NEAR", "INJ", "SUI", "SEI", "TIA", "RUNE", "AAVE", "MKR", "CRV",
    "LDO", "PEPE", "WIF", "BONK", "FET", "RENDER", "IMX", "GRT", "SAND",
    "MANA", "AXS", "EGLD", "ALGO", "XLM", "TRX", "ICP", "HBAR", "VET",
    "FTM", "FLOW", "STX", "KAS",
)

_IMPACT_SIZES_USD = (1_000, 10_000, 50_000, 100_000)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _pair(symbol: str) -> str:
    sym = symbol.upper().replace("/USDT", "")
    if sym == "MATIC":
        sym = "POL"
    return f"{sym}USDT"


def _notional_levels(levels: list[list[float]], *, mid: float, pct_band: float = 0.005) -> float:
    total = 0.0
    for price, qty in levels:
        if mid <= 0:
            continue
        if abs(price - mid) / mid <= pct_band:
            total += price * qty
    return total


def order_book_imbalance(bids: list[list[float]], asks: list[list[float]]) -> float | None:
    bid_usd = sum(p * q for p, q in bids[:20])
    ask_usd = sum(p * q for p, q in asks[:20])
    total = bid_usd + ask_usd
    if total <= 0:
        return None
    return round((bid_usd - ask_usd) / total, 4)


def effective_spread_bps(bids: list[list[float]], asks: list[list[float]]) -> float | None:
    if not bids or not asks:
        return None
    best_bid, best_ask = bids[0][0], asks[0][0]
    mid = (best_bid + best_ask) / 2
    if mid <= 0:
        return None
    return round(((best_ask - best_bid) / mid) * 10_000, 3)


def vpin_proxy(trades: list[dict[str, Any]], *, buckets: int = 10) -> dict[str, Any]:
    """Volume-synchronized informed-trading probability proxy from trade signs."""
    if len(trades) < buckets * 5:
        return {"vpin": None, "sample_trades": len(trades), "model": "insufficient_data"}
    chunk = max(5, len(trades) // buckets)
    imbalances: list[float] = []
    for i in range(0, len(trades) - chunk + 1, chunk):
        window = trades[i : i + chunk]
        buy_v = sell_v = 0.0
        for t in window:
            try:
                px = float(t.get("p") or 0)
                qty = float(t.get("q") or 0)
            except (TypeError, ValueError):
                continue
            vol = px * qty
            if t.get("m"):
                sell_v += vol
            else:
                buy_v += vol
        total = buy_v + sell_v
        if total > 0:
            imbalances.append(abs(buy_v - sell_v) / total)
    if not imbalances:
        return {"vpin": None, "sample_trades": len(trades), "model": "no_volume"}
    vpin = statistics.mean(imbalances)
    return {
        "vpin": round(vpin, 4),
        "buckets": len(imbalances),
        "sample_trades": len(trades),
        "model": "volume_bucket_proxy_v1",
    }


def spoofing_detection_score(
    bids: list[list[float]],
    asks: list[list[float]],
    *,
    prior_bids: list[list[float]] | None = None,
    prior_asks: list[list[float]] | None = None,
) -> dict[str, Any]:
    """
    Heuristic spoofing score (0-100) — large off-touch walls + disappearance between snapshots.
    Honest: rule-based, not trained RF/XGBoost.
    """
    if not bids or not asks:
        return {"score": 0, "confidence": 0, "alerts": []}
    mid = (bids[0][0] + asks[0][0]) / 2
    alerts: list[dict[str, Any]] = []
    sizes = [p * q for p, q in bids[:15] + asks[:15]]
    median = statistics.median(sizes) if sizes else 0

    def _wall_scan(levels: list[list[float]], side: str) -> float:
        score = 0.0
        for price, qty in levels[1:12]:
            dist = abs(price - mid) / mid if mid else 0
            notional = price * qty
            if dist > 0.003 and median > 0 and notional > median * 4:
                score += min(25, (notional / median) * 3)
                alerts.append(
                    {
                        "side": side,
                        "price": price,
                        "notional_usd": round(notional, 2),
                        "distance_pct": round(dist * 100, 3),
                        "pattern": "off_touch_large_wall",
                    }
                )
        return score

    score = _wall_scan(bids, "bid") + _wall_scan(asks, "ask")

    if prior_bids and prior_asks:
        prev_map = {(round(p, 8), "bid"): p * q for p, q in prior_bids[1:15]}
        prev_map.update({(round(p, 8), "ask"): p * q for p, q in prior_asks[1:15]})
        curr_keys = {(round(p, 8), "bid") for p, _ in bids[1:15]} | {(round(p, 8), "ask") for p, _ in asks[1:15]}
        vanished = [k for k, v in prev_map.items() if v > (median * 5) and k not in curr_keys]
        if vanished:
            score += min(40, len(vanished) * 15)
            alerts.append(
                {
                    "pattern": "wall_cancelled",
                    "vanished_levels": len(vanished),
                    "message": "Large off-touch liquidity removed without trade print",
                }
            )

    score = min(100, round(score, 1))
    confidence = min(95, 50 + score * 0.4) if score >= 40 else round(score * 0.6, 1)
    return {"score": score, "confidence": confidence, "alerts": alerts[:5], "model": "rule_based_v1"}


def liquidity_health_score(
    bids: list[list[float]],
    asks: list[list[float]],
    *,
    spread_bps: float | None,
) -> dict[str, Any]:
    if not bids or not asks:
        return {"score": 0, "label": "missing_book"}
    mid = (bids[0][0] + asks[0][0]) / 2
    depth = _notional_levels(bids, mid=mid) + _notional_levels(asks, mid=mid)
    spread = spread_bps if spread_bps is not None else 999
    depth_score = min(50, (depth / 500_000) * 50) if depth else 0
    spread_score = max(0, 50 - spread * 2)
    score = int(max(0, min(100, depth_score + spread_score)))
    label = "healthy" if score >= 70 else "moderate" if score >= 45 else "stressed"
    return {
        "score": score,
        "label": label,
        "depth_usd_50bps": round(depth, 2),
        "spread_bps": spread_bps,
    }


def toxicity_regime(
    *,
    vpin: float | None,
    spoofing_score: float,
    obi: float | None,
    health: int,
) -> str:
    if spoofing_score >= 70:
        return "manipulation_detected"
    if vpin is not None and vpin >= 0.75:
        return "high_toxicity"
    if spoofing_score >= 40 or (vpin is not None and vpin >= 0.55) or health < 40:
        return "caution"
    if obi is not None and abs(obi) > 0.65 and vpin is not None and vpin >= 0.45:
        return "high_toxicity"
    return "normal"


def market_impact_curve(book: dict[str, Any], *, price: float) -> list[dict[str, Any]]:
    curve: list[dict[str, Any]] = []
    for usd in _IMPACT_SIZES_USD:
        buy = walk_asks(book, usd)
        sell_base = usd / price if price > 0 else 0
        sell = walk_bids(book, sell_base) if sell_base > 0 else None
        curve.append(
            {
                "size_usd": usd,
                "buy_slippage_bps": round(buy.slippage_bps, 2) if buy else None,
                "sell_slippage_bps": round(sell.slippage_bps, 2) if sell else None,
            }
        )
    return curve


async def _fetch_depth(symbol: str, *, limit: int = 100) -> dict[str, Any] | None:
    pair = _pair(symbol)
    if not pair.isalnum():
        return None
    resp = await _CACHE.http_get_json(
        f"{SPOT_BASE}/api/v3/depth",
        params={"symbol": pair, "limit": limit},
        timeout_sec=0.5,
        cache_key=cache_key("ms_depth", pair, limit),
        ttl=5,
        source_slug="binance_spot",
    )
    if not resp.get("ok"):
        return None
    data = resp.get("data") or {}
    return {
        "bids": [[float(p), float(q)] for p, q in (data.get("bids") or [])],
        "asks": [[float(p), float(q)] for p, q in (data.get("asks") or [])],
    }


async def _fetch_agg_trades(symbol: str, *, limit: int = 500) -> list[dict[str, Any]]:
    pair = _pair(symbol)
    resp = await _CACHE.http_get_json(
        f"{SPOT_BASE}/api/v3/aggTrades",
        params={"symbol": pair, "limit": min(1000, limit)},
        timeout_sec=0.5,
        cache_key=cache_key("ms_agg", pair, limit),
        ttl=5,
        source_slug="binance_spot",
    )
    if not resp.get("ok"):
        return []
    data = resp.get("data")
    return data if isinstance(data, list) else []


async def analyze_market_microstructure(
    symbol: str = "ETH",
    *,
    amount_usd: float = 10_000.0,
    include_replay_hint: bool = True,
) -> dict[str, Any]:
    """Full microstructure analysis — target processing ≤500ms."""
    t0 = time.perf_counter()
    sym = symbol.upper().replace("/USDT", "")
    if sym not in LIQUID_ASSETS and sym != "MATIC":
        pass  # still attempt — pair resolver handles

    book1 = await _fetch_depth(sym)
    await asyncio.sleep(0.15)
    book2 = await _fetch_depth(sym)
    trades = await _fetch_agg_trades(sym)

    book = book2 or book1
    if not book or not book.get("bids") or not book.get("asks"):
        elapsed = time.perf_counter() - t0
        return {
            "ok": False,
            "feature": "#74",
            "asset": sym,
            "error": "order_book_unavailable",
            "latency_ms": round(elapsed * 1000, 1),
            "timestamp": _utcnow(),
        }

    bids, asks = book["bids"], book["asks"]
    mid = (bids[0][0] + asks[0][0]) / 2
    spread_bps = effective_spread_bps(bids, asks)
    obi = order_book_imbalance(bids, asks)
    vpin = vpin_proxy(trades)
    spoof = spoofing_detection_score(
        bids,
        asks,
        prior_bids=(book1 or {}).get("bids"),
        prior_asks=(book1 or {}).get("asks"),
    )
    health = liquidity_health_score(bids, asks, spread_bps=spread_bps)
    regime = toxicity_regime(
        vpin=vpin.get("vpin"),
        spoofing_score=float(spoof["score"]),
        obi=obi,
        health=int(health["score"]),
    )
    impact = market_impact_curve(book, price=mid)

    buy_exec = walk_asks(book, amount_usd)
    opt_rec = {
        "recommended_split": amount_usd >= 50_000,
        "expected_slippage_bps": round(buy_exec.slippage_bps, 2) if buy_exec else None,
        "venue": "binance_spot",
        "note": "Use #56 execution optimizer for multi-venue routing",
    }

    headline = None
    if regime == "manipulation_detected":
        headline = f"Microstructure: Spoofing pattern detected on {sym} — avoid market orders"
    elif regime == "high_toxicity":
        headline = f"Microstructure: High toxicity on {sym} — widen limits or reduce size"
    elif health["score"] >= 80:
        headline = f"Microstructure: {sym} liquidity healthy (score {health['score']}/100)"

    elapsed = time.perf_counter() - t0
    return {
        "ok": True,
        "feature": "#74",
        "surface": "market_microstructure",
        "asset": sym,
        "liquidity_health_score": health["score"],
        "liquidity_health": health,
        "toxicity_regime": regime,
        "spoofing": spoof,
        "features": {
            "order_book_imbalance": obi,
            "effective_spread_bps": spread_bps,
            "vpin": vpin,
            "order_flow_imbalance_proxy": obi,
            "cancellation_toxicity_proxy": round(float(spoof["score"]) * 0.4, 2),
        },
        "market_impact_curve": impact,
        "optimal_execution": opt_rec,
        "order_book_heatmap": {
            "bids_top10": bids[:10],
            "asks_top10": asks[:10],
            "mid_price": round(mid, 6),
            "toxicity_color": regime,
        },
        "headline": headline,
        "supported_assets_count": len(LIQUID_ASSETS),
        "historical_replay_mode": include_replay_hint,
        "latency_ms": round(elapsed * 1000, 1),
        "sla_met": elapsed <= 0.5,
        "refresh_sec": 5,
        "timestamp": _utcnow(),
    }


async def microstructure_for_decision_engine(symbol: str = "ETH") -> dict[str, Any]:
    """Compact #74 payload for Decision Engine (#48)."""
    row = await analyze_market_microstructure(symbol, amount_usd=10_000)
    if not row.get("ok"):
        return {"ok": False, "feature": "#74", "error": row.get("error")}
    regime = row.get("toxicity_regime")
    risk_delta = 0.0
    if regime == "manipulation_detected":
        risk_delta = 2.0
    elif regime == "high_toxicity":
        risk_delta = 1.2
    elif regime == "caution":
        risk_delta = 0.5
    return {
        "ok": True,
        "feature": "#74",
        "asset": row.get("asset"),
        "liquidity_health_score": row.get("liquidity_health_score"),
        "toxicity_regime": regime,
        "spoofing_score": (row.get("spoofing") or {}).get("score"),
        "risk_score_delta": risk_delta,
        "headline": row.get("headline"),
        "latency_ms": row.get("latency_ms"),
    }


def market_microstructure_status() -> dict[str, Any]:
    return {
        "ok": True,
        "feature": "#74",
        "supported_assets": len(LIQUID_ASSETS),
        "cache_ttl_sec": 5,
        "detectors": ["vpin_proxy", "obi", "spoofing_heuristic", "liquidity_health"],
        "integrations": ["#48_decision_engine", "#56_execution_optimizer", "#85_order_flow"],
        "model_disclaimer": "Rule-based v1 — no black-box ML",
        "timestamp": _utcnow(),
    }
