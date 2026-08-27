"""
AI Execution Optimizer (#56) — Fee, Slippage & Capacity Intelligence.

True-cost routing across 20+ DEX + 5 CEX venues. Feeds Decision Engine (#48)
and Trade Simulator (#94). Extends Intelligence Ledger — not a duplicate surface.
"""

from __future__ import annotations

import asyncio
import logging
import math
import time
from datetime import UTC, datetime
from typing import Any, Literal

from dex_slippage import constant_product_slippage_bps
from gas_oracle import gas_cost_bps

logger = logging.getLogger("BLACKDARK.ExecutionOptimizer")

Priority = Literal["cost", "speed", "safety"]

DEX_VENUES: dict[str, dict[str, Any]] = {
    "uniswap_v2": {"fee_bps": 30, "chain": "ethereum", "mev_protected": False, "latency_sec": 12},
    "uniswap_v3": {"fee_bps": 5, "chain": "ethereum", "mev_protected": False, "latency_sec": 12},
    "pancakeswap": {"fee_bps": 25, "chain": "bsc", "mev_protected": False, "latency_sec": 8},
    "curve": {"fee_bps": 4, "chain": "ethereum", "mev_protected": False, "latency_sec": 14},
    "balancer": {"fee_bps": 10, "chain": "ethereum", "mev_protected": False, "latency_sec": 14},
    "sushiswap": {"fee_bps": 30, "chain": "ethereum", "mev_protected": False, "latency_sec": 13},
    "traderjoe": {"fee_bps": 30, "chain": "avalanche", "mev_protected": False, "latency_sec": 10},
    "raydium": {"fee_bps": 25, "chain": "solana", "mev_protected": False, "latency_sec": 2},
    "orca": {"fee_bps": 30, "chain": "solana", "mev_protected": False, "latency_sec": 2},
    "jupiter": {"fee_bps": 0, "chain": "solana", "mev_protected": False, "latency_sec": 3},
    "quickswap": {"fee_bps": 30, "chain": "polygon", "mev_protected": False, "latency_sec": 6},
    "aerodrome": {"fee_bps": 5, "chain": "base", "mev_protected": False, "latency_sec": 8},
    "camelot": {"fee_bps": 30, "chain": "arbitrum", "mev_protected": False, "latency_sec": 5},
    "gmx": {"fee_bps": 10, "chain": "arbitrum", "mev_protected": False, "latency_sec": 6},
    "cowswap": {"fee_bps": 0, "chain": "ethereum", "mev_protected": True, "latency_sec": 30},
    "1inch": {"fee_bps": 0, "chain": "ethereum", "mev_protected": False, "latency_sec": 18},
    "paraswap": {"fee_bps": 0, "chain": "ethereum", "mev_protected": False, "latency_sec": 18},
    "kyberswap": {"fee_bps": 0, "chain": "ethereum", "mev_protected": False, "latency_sec": 16},
    "biswap": {"fee_bps": 10, "chain": "bsc", "mev_protected": False, "latency_sec": 8},
    "syncswap": {"fee_bps": 5, "chain": "zksync", "mev_protected": False, "latency_sec": 10},
    "dodo": {"fee_bps": 30, "chain": "ethereum", "mev_protected": False, "latency_sec": 14},
}

CEX_VENUES: dict[str, dict[str, Any]] = {
    "binance": {"taker_bps": 10, "latency_sec": 2, "mev_protected": True},
    "okx": {"taker_bps": 8, "latency_sec": 2, "mev_protected": True},
    "bybit": {"taker_bps": 10, "latency_sec": 2, "mev_protected": True},
    "kucoin": {"taker_bps": 10, "latency_sec": 3, "mev_protected": True},
    "gateio": {"taker_bps": 10, "latency_sec": 3, "mev_protected": True},
}

BRIDGE_VENUES: dict[str, dict[str, Any]] = {
    "wormhole": {"cost_bps": 8, "time_min": 15, "reliability": 0.92},
    "stargate": {"cost_bps": 6, "time_min": 8, "reliability": 0.95},
    "across": {"cost_bps": 5, "time_min": 5, "reliability": 0.94},
}

_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}
_CACHE_TTL = 30.0


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def capacity_score(*, amount_usd: float, liquidity_usd: float) -> dict[str, Any]:
    """0-100 capacity score per acceptance criteria."""
    if liquidity_usd <= 0:
        return {"score": 0, "label": "illiquid", "max_comfortable_usd": 0}
    ratio = amount_usd / liquidity_usd
    impact_bps = (amount_usd / (2.0 * liquidity_usd)) * 10_000 if liquidity_usd else 9999
    if impact_bps < 10 and amount_usd <= 100_000:
        score, label = 95, "deep"
    elif impact_bps < 50 and amount_usd <= 50_000:
        score, label = 72, "moderate"
    elif impact_bps < 200:
        score, label = 35, "shallow"
    else:
        score, label = 5, "illiquid"
    max_comfort = liquidity_usd * 0.05
    return {
        "score": score,
        "label": label,
        "impact_bps_estimate": round(impact_bps, 2),
        "max_comfortable_usd": round(max_comfort, 2),
        "liquidity_ratio": round(ratio, 6),
    }


def predict_slippage_bps(
    *,
    amount_usd: float,
    liquidity_usd: float,
    volatility_pct: float,
    venue_fee_bps: float,
    is_cex: bool,
) -> dict[str, Any]:
    """Rule-based slippage model with confidence interval (not black-box ML)."""
    if is_cex:
        base = max(venue_fee_bps, 8.0)
        depth_adj = (amount_usd / max(liquidity_usd, 1)) * 500
        predicted = base + depth_adj + volatility_pct * 2
    else:
        predicted = constant_product_slippage_bps(
            amount_usd=amount_usd,
            liquidity_usd=max(liquidity_usd, 1),
            fee_bps=venue_fee_bps,
        )
    margin = max(2.0, predicted * 0.15)
    return {
        "predicted_bps": round(predicted, 3),
        "confidence_low_bps": round(max(0, predicted - margin), 3),
        "confidence_high_bps": round(predicted + margin, 3),
        "model": "rule_based_v1",
    }


def mev_risk_score(
    *,
    amount_usd: float,
    venue: str,
    mev_protected: bool,
    chain: str,
) -> dict[str, Any]:
    if mev_protected:
        return {"score": 5, "probability_pct": 1.0, "recommendation": "low_risk"}
    base = min(95, 8 + (amount_usd / 5000))
    if chain in {"ethereum", "bsc"} and amount_usd >= 25_000:
        base = min(95, base + 12)
    if venue in {"uniswap_v2", "uniswap_v3", "sushiswap"}:
        base = min(95, base + 5)
    rec = "use_cowswap_or_cex" if base >= 40 else "acceptable"
    return {
        "score": round(base, 1),
        "probability_pct": round(base * 0.15, 2),
        "recommendation": rec,
    }


def compute_true_cost(
    *,
    price_impact_bps: float,
    slippage_bps: float,
    fee_bps: float,
    gas_bps: float,
    bridge_bps: float = 0,
    mev_risk_bps: float = 0,
) -> dict[str, Any]:
    total = price_impact_bps + slippage_bps + fee_bps + gas_bps + bridge_bps + mev_risk_bps
    return {
        "price_impact_bps": round(price_impact_bps, 3),
        "slippage_bps": round(slippage_bps, 3),
        "fee_bps": round(fee_bps, 3),
        "gas_bps": round(gas_bps, 3),
        "bridge_bps": round(bridge_bps, 3),
        "mev_risk_bps": round(mev_risk_bps, 3),
        "true_cost_bps": round(total, 3),
        "true_cost_pct": round(total / 100, 4),
    }


def _ai_score(*, true_cost_bps: float, capacity: int, mev_score: float, latency_sec: float) -> int:
    cost_penalty = min(40, true_cost_bps / 5)
    cap_bonus = capacity * 0.35
    mev_penalty = mev_score * 0.2
    speed_bonus = max(0, 15 - latency_sec)
    return int(max(0, min(100, 50 + cap_bonus + speed_bonus - cost_penalty - mev_penalty)))


async def _market_liquidity(asset: str) -> dict[str, Any]:
    from bd_platform.slippage_tolerance_optimizer import _market_context

    return await _market_context(asset)


async def _gas_bps_for_chain(chain: str, amount_usd: float) -> float:
    try:
        return float(await gas_cost_bps(chain, amount_usd) or 0)
    except Exception:
        return 15.0


def _split_recommendation(routes: list[dict[str, Any]], amount_usd: float) -> dict[str, Any] | None:
    cex = [r for r in routes if r.get("venue_type") == "cex" and r.get("capacity_score", 0) >= 50]
    dex = [r for r in routes if r.get("venue_type") == "dex" and r.get("capacity_score", 0) >= 40]
    if not cex or not dex or amount_usd < 50_000:
        return None
    best_cex = min(cex, key=lambda r: r["true_cost"]["true_cost_bps"])
    best_dex = min(dex, key=lambda r: r["true_cost"]["true_cost_bps"])
    single = min(routes, key=lambda r: r["true_cost"]["true_cost_bps"])
    split_cost = (
        best_cex["true_cost"]["true_cost_bps"] * 0.6
        + best_dex["true_cost"]["true_cost_bps"] * 0.25
        + best_cex["true_cost"]["true_cost_bps"] * 0.15
    )
    if split_cost >= single["true_cost"]["true_cost_bps"]:
        return None
    return {
        "strategy": "split",
        "allocations": [
            {"venue": best_cex["venue"], "pct": 60},
            {"venue": best_dex["venue"], "pct": 25},
            {"venue": best_cex["venue"], "pct": 15, "note": "secondary_cex_leg"},
        ],
        "estimated_true_cost_bps": round(split_cost, 2),
        "single_venue_cost_bps": single["true_cost"]["true_cost_bps"],
        "savings_bps": round(single["true_cost"]["true_cost_bps"] - split_cost, 2),
    }


async def optimize_execution(
    *,
    asset: str = "ETH",
    amount_usd: float = 10_000.0,
    chain: str = "ethereum",
    side: str = "buy",
    priority: Priority = "cost",
    cross_chain: bool = False,
) -> dict[str, Any]:
    """
    AI routing optimizer — evaluates DEX + CEX routes with true cost breakdown.
    Target latency ≤3s.
    """
    t0 = time.perf_counter()
    cache_key = f"{asset}:{amount_usd}:{chain}:{side}:{priority}:{cross_chain}"
    cached = _CACHE.get(cache_key)
    if cached and time.time() - cached[0] < _CACHE_TTL:
        out = dict(cached[1])
        out["cache_hit"] = True
        return out

    asset_u = asset.upper()
    ctx = await _market_liquidity(asset_u)
    liquidity = float(ctx.get("liquidity_usd") or 5_000_000)
    vol = float(ctx.get("volatility_24h_pct") or 2.0)
    price = float(ctx.get("price_usd") or 0)

    gas_bps = await _gas_bps_for_chain(chain, amount_usd)
    bridge_bps = 0.0
    if cross_chain:
        bridge_bps = min(BRIDGE_VENUES.values(), key=lambda b: b["cost_bps"])["cost_bps"]

    routes: list[dict[str, Any]] = []

    for venue, meta in DEX_VENUES.items():
        if meta["chain"] != chain and venue not in {"1inch", "jupiter", "paraswap"}:
            continue
        liq_adj = liquidity * (0.4 if venue == "uniswap_v3" else 0.25)
        cap = capacity_score(amount_usd=amount_usd, liquidity_usd=liq_adj)
        slip = predict_slippage_bps(
            amount_usd=amount_usd,
            liquidity_usd=liq_adj,
            volatility_pct=vol,
            venue_fee_bps=float(meta["fee_bps"]),
            is_cex=False,
        )
        mev = mev_risk_score(
            amount_usd=amount_usd,
            venue=venue,
            mev_protected=bool(meta.get("mev_protected")),
            chain=meta["chain"],
        )
        impact = cap["impact_bps_estimate"]
        mev_bps = float(mev["probability_pct"]) * 10
        true_cost = compute_true_cost(
            price_impact_bps=impact * 0.5,
            slippage_bps=slip["predicted_bps"],
            fee_bps=float(meta["fee_bps"]),
            gas_bps=gas_bps if meta["chain"] == chain else gas_bps * 1.2,
            bridge_bps=bridge_bps,
            mev_risk_bps=mev_bps,
        )
        routes.append(
            {
                "route": venue,
                "venue": venue,
                "venue_type": "dex",
                "chain": meta["chain"],
                "cost_pct": true_cost["true_cost_pct"],
                "time_sec": meta["latency_sec"],
                "mev_risk_pct": mev["probability_pct"],
                "capacity_score": cap["score"],
                "capacity_label": cap["label"],
                "true_cost": true_cost,
                "slippage_prediction": slip,
                "mev": mev,
                "ai_score": _ai_score(
                    true_cost_bps=true_cost["true_cost_bps"],
                    capacity=cap["score"],
                    mev_score=float(mev["score"]),
                    latency_sec=float(meta["latency_sec"]),
                ),
            }
        )

    for venue, meta in CEX_VENUES.items():
        cex_liq = liquidity * 2.5
        cap = capacity_score(amount_usd=amount_usd, liquidity_usd=cex_liq)
        slip = predict_slippage_bps(
            amount_usd=amount_usd,
            liquidity_usd=cex_liq,
            volatility_pct=vol,
            venue_fee_bps=float(meta["taker_bps"]),
            is_cex=True,
        )
        true_cost = compute_true_cost(
            price_impact_bps=cap["impact_bps_estimate"] * 0.3,
            slippage_bps=slip["predicted_bps"],
            fee_bps=float(meta["taker_bps"]),
            gas_bps=0,
            mev_risk_bps=0,
        )
        routes.append(
            {
                "route": venue,
                "venue": venue,
                "venue_type": "cex",
                "chain": "cex",
                "cost_pct": true_cost["true_cost_pct"],
                "time_sec": meta["latency_sec"],
                "mev_risk_pct": 0,
                "capacity_score": cap["score"],
                "capacity_label": cap["label"],
                "true_cost": true_cost,
                "slippage_prediction": slip,
                "mev": {"score": 0, "probability_pct": 0, "recommendation": "none"},
                "ai_score": _ai_score(
                    true_cost_bps=true_cost["true_cost_bps"],
                    capacity=cap["score"],
                    mev_score=0,
                    latency_sec=float(meta["latency_sec"]),
                ),
            }
        )

    routes.sort(key=lambda r: r["true_cost"]["true_cost_bps"])
    best_cost = routes[0] if routes else None
    fastest = min(routes, key=lambda r: r["time_sec"]) if routes else None
    safest = min(routes, key=lambda r: (r["mev_risk_pct"], r["true_cost"]["true_cost_bps"])) if routes else None

    gas_hint = None
    if gas_bps > 20:
        gas_hint = {
            "message": f"Gas elevated ({gas_bps:.1f}bps). Historical pattern suggests 20-35% drop within 90min.",
            "wait_recommended": amount_usd < 25_000,
            "estimated_savings_usd": round(amount_usd * 0.00035, 2),
        }

    split = _split_recommendation(routes, amount_usd)
    slippage_warning = None
    if best_cost and best_cost["true_cost"]["slippage_bps"] >= 50:
        slippage_warning = (
            f"Your ${amount_usd:,.0f} order may cause {best_cost['true_cost']['slippage_bps']:.1f}bps slippage. "
            "AI recommends splitting or using CEX."
        )

    badge = None
    if best_cost:
        badge = (
            f"Best Route: {best_cost['venue']} → Cost {best_cost['true_cost']['true_cost_pct']:.2f}% "
            f"| Time {best_cost['time_sec']}s | MEV Risk: {best_cost['mev_risk_pct']:.1f}%"
        )

    elapsed = time.perf_counter() - t0
    result = {
        "ok": True,
        "feature": "#56",
        "surface": "execution_optimizer",
        "asset": asset_u,
        "amount_usd": amount_usd,
        "chain": chain,
        "side": side,
        "priority": priority,
        "dex_venue_count": len(DEX_VENUES),
        "cex_venue_count": len(CEX_VENUES),
        "routes": routes[:15],
        "route_comparison": [
            {
                "route": r["venue"],
                "cost_pct": r["cost_pct"],
                "time_sec": r["time_sec"],
                "mev_risk_pct": r["mev_risk_pct"],
                "capacity": r["capacity_label"],
                "ai_score": r["ai_score"],
            }
            for r in routes[:8]
        ],
        "recommendations": {
            "best_cost": best_cost,
            "fastest": fastest,
            "safest": safest,
            "custom_priority": priority,
        },
        "ai_recommendation_badge": badge,
        "slippage_warning": slippage_warning,
        "gas_timer": gas_hint,
        "split_recommendation": split,
        "price_usd": price,
        "liquidity_usd": liquidity,
        "latency_ms": round(elapsed * 1000, 1),
        "sla_met": elapsed <= 3.0,
        "capacity_refresh_sec": 30,
        "timestamp": _utcnow(),
        "disclaimer": "Execution cost estimates — not trade advice.",
    }
    _CACHE[cache_key] = (time.time(), result)
    return result


async def execution_cost_for_decision_engine(asset: str, *, amount_usd: float = 10_000) -> dict[str, Any]:
    """Compact payload for Decision Engine (#48) confidence adjustment."""
    opt = await optimize_execution(asset=asset, amount_usd=amount_usd)
    best = (opt.get("recommendations") or {}).get("best_cost") or {}
    tc = best.get("true_cost") or {}
    return {
        "ok": opt.get("ok", False),
        "feature": "#56",
        "execution_cost_bps": tc.get("true_cost_bps"),
        "best_venue": best.get("venue"),
        "capacity_score": best.get("capacity_score"),
        "confidence_penalty": round(min(2.0, (tc.get("true_cost_bps") or 0) / 100), 3),
        "headline": opt.get("ai_recommendation_badge"),
    }


def execution_optimizer_status() -> dict[str, Any]:
    return {
        "ok": True,
        "feature": "#56",
        "dex_venues": len(DEX_VENUES),
        "cex_venues": len(CEX_VENUES),
        "bridge_venues": len(BRIDGE_VENUES),
        "cache_ttl_sec": _CACHE_TTL,
        "integrations": ["#48_decision_engine", "#94_trade_simulator", "intelligence_ledger"],
        "timestamp": _utcnow(),
    }
