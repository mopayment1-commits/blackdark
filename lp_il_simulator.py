"""
BLACKDARK — Impermanent Loss Live Simulator (CAP978 ID 954).

Constant-product AMM (Uniswap v2 style) 50/50 pool math with live
DexScreener + DeFiLlama yield data. No placeholder prices.
"""

from __future__ import annotations

import asyncio
import json
import logging
import math
import time
from datetime import UTC, datetime
from typing import Any

import aiohttp

from path_safety import assert_url_path_safe, safe_url_segment

logger = logging.getLogger("BLACKDARK.LPIL")

_HEADERS = {"User-Agent": "BLACKDARK/1.0", "Accept": "application/json"}
_POOL_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}
_CACHE_TTL = 45.0


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def compute_impermanent_loss_pct(price_ratio: float) -> float:
    """
    IL for 50/50 constant-product pool.

    price_ratio = exit_price / entry_price (token A vs stable quote).
    Returns negative fraction (e.g. -0.057 for -5.7%).
    """
    if price_ratio <= 0:
        return 0.0
    if abs(price_ratio - 1.0) < 1e-12:
        return 0.0
    return (2.0 * math.sqrt(price_ratio) / (1.0 + price_ratio)) - 1.0


def hodl_value_ratio(price_ratio: float) -> float:
    """HODL value / initial deposit for 50/50 ETH/stable-style pool."""
    return (1.0 + price_ratio) / 2.0


def lp_value_ratio(price_ratio: float) -> float:
    """LP value / initial deposit."""
    return 2.0 * math.sqrt(price_ratio) / (1.0 + price_ratio)


def simulate_lp_position(
    *,
    amount_usd: float,
    entry_price: float,
    exit_price: float,
    fee_apy_pct: float = 0.0,
    horizon_days: float = 30.0,
) -> dict[str, Any]:
    """Simulate LP vs HODL with optional fee income from pool APY."""
    if amount_usd <= 0 or entry_price <= 0 or exit_price <= 0:
        return {
            "ok": False,
            "error": "amount_usd, entry_price, exit_price must be positive",
            "data_state": "MISSING",
        }

    ratio = exit_price / entry_price
    il_pct = compute_impermanent_loss_pct(ratio)
    lp_ratio = lp_value_ratio(ratio)
    hodl_ratio = hodl_value_ratio(ratio)

    lp_value_usd = amount_usd * lp_ratio
    hodl_value_usd = amount_usd * hodl_ratio
    fee_income_usd = amount_usd * (fee_apy_pct / 100.0) * (horizon_days / 365.0)
    net_lp_usd = lp_value_usd + fee_income_usd
    net_vs_hodl_usd = net_lp_usd - hodl_value_usd
    net_vs_hodl_pct = (net_lp_usd / hodl_value_usd - 1.0) * 100.0 if hodl_value_usd else 0.0

    price_change_pct = (ratio - 1.0) * 100.0
    alerts: list[dict[str, Any]] = []
    if il_pct <= -0.10:
        alerts.append(
            {
                "level": "high",
                "code": "IL_SEVERE",
                "message": f"Impermanent loss {il_pct * 100:.1f}% exceeds 10% threshold",
            }
        )
    elif il_pct <= -0.05:
        alerts.append(
            {
                "level": "medium",
                "code": "IL_ELEVATED",
                "message": f"Impermanent loss {il_pct * 100:.1f}% exceeds 5% threshold",
            }
        )
    if net_vs_hodl_usd < 0 and abs(net_vs_hodl_usd) > amount_usd * 0.02:
        alerts.append(
            {
                "level": "warn",
                "code": "LP_UNDERPERFORMS_HODL",
                "message": f"LP net ${net_vs_hodl_usd:,.0f} below HODL after fees",
            }
        )

    curve = _il_curve_points()
    return {
        "ok": True,
        "data_state": "LIVE",
        "pool_type": "constant_product_50_50",
        "amount_usd": round(amount_usd, 2),
        "entry_price": entry_price,
        "exit_price": exit_price,
        "price_ratio": round(ratio, 6),
        "price_change_pct": round(price_change_pct, 2),
        "impermanent_loss_pct": round(il_pct * 100, 4),
        "lp_value_usd": round(lp_value_usd, 2),
        "hodl_value_usd": round(hodl_value_usd, 2),
        "fee_income_usd": round(fee_income_usd, 2),
        "fee_apy_pct": fee_apy_pct,
        "horizon_days": horizon_days,
        "net_lp_usd": round(net_lp_usd, 2),
        "net_vs_hodl_usd": round(net_vs_hodl_usd, 2),
        "net_vs_hodl_pct": round(net_vs_hodl_pct, 4),
        "il_curve": curve,
        "alerts": alerts,
        "formula": "IL = 2√r/(1+r) − 1; r = exit/entry",
        "accuracy_note": "Standard v2 full-range 50/50; excludes gas, IL in concentrated ranges",
    }


def _il_curve_points() -> list[dict[str, float]]:
    points = []
    for pct in range(-80, 81, 5):
        r = 1.0 + pct / 100.0
        if r <= 0:
            continue
        points.append(
            {
                "price_change_pct": float(pct),
                "il_pct": round(compute_impermanent_loss_pct(r) * 100, 3),
            }
        )
    return points


def il_vulnerability_score(
    symbol: str = "ETH-USDC",
    *,
    volatility_30d_pct: float | None = None,
    liquidity_usd: float | None = None,
    fee_apy_pct: float | None = None,
    tvl_usd: float | None = None,
) -> dict[str, Any]:
    """CAP978 ID 934 — score 0-100 (higher = more IL risk)."""
    vol = float(volatility_30d_pct or 40.0)
    liq = float(liquidity_usd or 1_000_000.0)
    apy = float(fee_apy_pct or 5.0)
    tvl = float(tvl_usd or liq)

    vol_score = min(100.0, vol * 1.5)
    depth_score = max(0.0, 100.0 - math.log10(max(liq, 10_000)) * 15)
    fee_offset = min(30.0, apy * 2.0)
    tvl_score = max(0.0, 50.0 - math.log10(max(tvl, 100_000)) * 8)

    raw = (vol_score * 0.45 + depth_score * 0.35 + tvl_score * 0.20) - fee_offset
    score = int(max(0, min(100, round(raw))))

    if score >= 70:
        band = "high"
    elif score >= 40:
        band = "medium"
    else:
        band = "low"

    return {
        "success": True,
        "capability_id": 934,
        "symbol": symbol.upper(),
        "il_vulnerability_score": score,
        "risk_band": band,
        "components": {
            "volatility_30d_pct": vol,
            "liquidity_usd": liq,
            "fee_apy_pct": apy,
            "tvl_usd": tvl,
        },
        "timestamp": _utcnow(),
        "data_state": "LIVE" if liquidity_usd else "UNKNOWN",
    }


async def _get_json(url: str, *, params: dict | None = None) -> Any:
    timeout = aiohttp.ClientTimeout(total=8)
    safe_url = assert_url_path_safe(url)
    async with aiohttp.ClientSession(timeout=timeout, headers=_HEADERS) as session:
        async with session.get(safe_url, params=params) as resp:
            if resp.status != 200:
                return None
            return await resp.json()


async def fetch_live_pools(query: str = "ETH USDC", *, limit: int = 15) -> dict[str, Any]:
    """DexScreener search for LP pools with liquidity."""
    q = "".join(c for c in (query or "ETH USDC").strip()[:80] if c.isprintable()) or "ETH USDC"
    cache_key = f"pools:{q}:{limit}"
    cached = _POOL_CACHE.get(cache_key)
    if cached and time.time() - cached[0] < _CACHE_TTL:
        return cached[1]

    data = await _get_json("https://api.dexscreener.com/latest/dex/search", params={"q": q})
    pairs = (data or {}).get("pairs") or []
    pools: list[dict[str, Any]] = []
    for row in pairs[:50]:
        liq = float((row.get("liquidity") or {}).get("usd") or 0)
        if liq < 50_000:
            continue
        base = row.get("baseToken") or {}
        quote = row.get("quoteToken") or {}
        price_usd = float(row.get("priceUsd") or 0)
        pools.append(
            {
                "pair_address": row.get("pairAddress"),
                "dex": row.get("dexId"),
                "chain": row.get("chainId"),
                "base_symbol": base.get("symbol"),
                "quote_symbol": quote.get("symbol"),
                "price_usd": price_usd,
                "liquidity_usd": liq,
                "volume_24h_usd": float((row.get("volume") or {}).get("h24") or 0),
                "price_change_24h_pct": float((row.get("priceChange") or {}).get("h24") or 0),
                "url": row.get("url"),
            }
        )
    pools.sort(key=lambda p: p["liquidity_usd"], reverse=True)
    pools = pools[:limit]

    result = {
        "source": "dexscreener",
        "query": q,
        "timestamp": _utcnow(),
        "count": len(pools),
        "pools": pools,
        "data_state": "LIVE" if pools else "MISSING",
    }
    _POOL_CACHE[cache_key] = (time.time(), result)
    return result


async def _match_defillama_apy(symbol_a: str, symbol_b: str, dex: str | None) -> float | None:
    data = await _get_json("https://yields.llama.fi/pools")
    pools = (data or {}).get("data") or []
    sym = f"{symbol_a}-{symbol_b}".upper()
    sym_rev = f"{symbol_b}-{symbol_a}".upper()
    best_apy: float | None = None
    dex_l = (dex or "").lower()
    for row in pools:
        pool_sym = str(row.get("symbol") or "").upper()
        project = str(row.get("project") or "").lower()
        if sym not in pool_sym and sym_rev not in pool_sym:
            continue
        if dex_l and dex_l not in project:
            continue
        apy = float(row.get("apy") or 0)
        if apy > 0 and (best_apy is None or apy > best_apy):
            best_apy = apy
    return best_apy


def _parse_pair_symbol(symbol: str) -> tuple[str, str]:
    s = str(symbol or "ETH-USDC").upper().replace("/", "-")
    parts = [p for p in s.split("-") if p]
    if len(parts) >= 2:
        return parts[0], parts[1]
    return parts[0] if parts else "ETH", "USDC"


async def simulate_lp_live(
    symbol: str = "ETH-USDC",
    *,
    token_a: str | None = None,
    token_b: str | None = None,
    amount_usd: float = 10_000.0,
    price_change_pct: float | None = None,
    horizon_days: float = 30.0,
    pair_address: str | None = None,
) -> dict[str, Any]:
    """Live IL simulation using DexScreener pool + DeFiLlama APY."""
    if token_a is None or token_b is None:
        token_a, token_b = _parse_pair_symbol(symbol)
    t0 = time.perf_counter()
    query = f"{token_a} {token_b}"
    pools_task = fetch_live_pools(query)
    pools_data = await pools_task
    pools = pools_data.get("pools") or []

    if not pools:
        return {
            "ok": False,
            "data_state": "MISSING",
            "error": f"No live pools found for {query}",
            "query": query,
            "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
        }

    pool = pools[0]
    if pair_address:
        for p in pools:
            if p.get("pair_address") == pair_address:
                pool = p
                break

    entry_price = float(pool.get("price_usd") or 0)
    if entry_price <= 0:
        return {
            "ok": False,
            "data_state": "MISSING",
            "error": "Pool price unavailable",
            "pool": pool,
        }

    change = price_change_pct
    if change is None:
        change = float(pool.get("price_change_24h_pct") or 0)

    exit_price = entry_price * (1.0 + change / 100.0)
    fee_apy = await _match_defillama_apy(
        token_a, token_b, str(pool.get("dex") or "")
    )
    fee_apy_pct = fee_apy if fee_apy is not None else 0.0

    sim = simulate_lp_position(
        amount_usd=amount_usd,
        entry_price=entry_price,
        exit_price=exit_price,
        fee_apy_pct=fee_apy_pct,
        horizon_days=horizon_days,
    )
    vuln = il_vulnerability_score(
        symbol=f"{token_a}-{token_b}",
        volatility_30d_pct=abs(change) * 3,
        liquidity_usd=pool.get("liquidity_usd"),
        fee_apy_pct=fee_apy_pct,
        tvl_usd=pool.get("liquidity_usd"),
    )

    latency_ms = round((time.perf_counter() - t0) * 1000, 1)
    headline = (
        f"IL {sim['impermanent_loss_pct']:+.2f}% · "
        f"Net vs HODL ${sim['net_vs_hodl_usd']:+,.0f}"
    )

    return {
        "ok": True,
        "success": True,
        "capability_id": 954,
        "surface": "impermanent_loss_live_simulator",
        "headline": headline,
        "token_a": token_a.upper(),
        "token_b": token_b.upper(),
        "pool": pool,
        "simulation": sim,
        "vulnerability": vuln,
        "sources": ["dexscreener", "defillama_yields"],
        "timestamp": _utcnow(),
        "latency_ms": latency_ms,
        "sla_met": latency_ms <= 2000,
        "data_state": "LIVE",
        "disclaimer": "Educational simulator — not financial advice. v2 50/50 full-range model.",
    }


async def lp_front_payload(symbol: str = "ETH-USDC", *, token_a: str | None = None, token_b: str | None = None) -> dict[str, Any]:
    """CAP978 ID 975 — UI bootstrap payload."""
    if token_a is None or token_b is None:
        token_a, token_b = _parse_pair_symbol(symbol)
    pools, live = await asyncio.gather(
        fetch_live_pools(f"{token_a} {token_b}"),
        simulate_lp_live(token_a=token_a, token_b=token_b, amount_usd=10_000),
    )
    return {
        "success": True,
        "capability_id": 975,
        "surface": "decentralized_liquidity_pool_front",
        "ui_route": "/il-simulator",
        "api_base": "/api/platform/defi/il",
        "default_pair": {"token_a": token_a.upper(), "token_b": token_b.upper()},
        "pools": pools,
        "live_preview": live,
        "timestamp": _utcnow(),
    }


async def persist_simulation(result: dict[str, Any]) -> int | None:
    """Store simulation in simulation_logs."""
    try:
        from database import insert_simulation_log

        sim = result.get("simulation") or result
        asset = f"{result.get('token_a', 'LP')}-{result.get('token_b', 'USD')}"
        pnl = float(sim.get("net_vs_hodl_usd") or 0)
        return await insert_simulation_log("lp_il", asset, json.dumps(result, default=str), pnl)
    except Exception:
        logger.exception("Failed to persist IL simulation")
        return None
