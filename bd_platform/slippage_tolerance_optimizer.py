"""
Slippage Intelligence Module — Features #5 + #17 (unified).

#5  Slippage Tolerance Self-Optimization:
    volatility + liquidity depth + gas → optimal tolerance

#17 Asymmetric Slippage Cost (embedded, not standalone):
    buy vs sell directional cost decomposition from CEX order-book walk
    + AMM pool impact asymmetry

Formula (transparent, auditable):
  optimal_bps = clamp(base + vol_adj + depth_adj + gas_adj, 10, 300)
  asymmetric_spread_bps = |buy_slippage_bps - sell_slippage_bps|
"""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import UTC, datetime
from typing import Any

import aiohttp

from arbitrage_engine import walk_asks, walk_bids
from dex_slippage import constant_product_slippage_bps
from gas_oracle import gas_cost_bps

logger = logging.getLogger("BLACKDARK.SlippageOptimizer")

_MIN_BPS = 10
_MAX_BPS = 300
_DEFAULT_BASE_BPS = 50


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


async def _market_context(asset: str) -> dict[str, Any]:
    """Volatility + liquidity from public APIs (canonical symbol + CoinGecko primary)."""
    from blackdark.canonical.resolver import resolve_symbol

    canonical = resolve_symbol(asset)
    symbol = f"{canonical}USDT"
    if not symbol.isalnum():
        return {}
    timeout = aiohttp.ClientTimeout(total=4)
    vol_pct = 0.0
    liquidity_usd = 0.0
    price = 0.0
    source = "unknown"
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(
                "https://api.binance.com/api/v3/ticker/24hr", params={"symbol": symbol}
            ) as resp:
                if resp.status == 200:
                    row = await resp.json()
                    vol_pct = abs(float(row.get("priceChangePercent") or 0))
                    price = float(row.get("lastPrice") or 0)
                    liquidity_usd = float(row.get("quoteVolume") or 0) * 0.05
                    source = "binance"
    except (aiohttp.ClientError, asyncio.TimeoutError, TimeoutError):
        pass

    if price <= 0:
        try:
            from blackdark.ingestion.coingecko_connector import fetch_coingecko_price

            cg = await fetch_coingecko_price(canonical)
            if cg.get("ok"):
                price = float(cg.get("price_usd") or 0)
                vol_pct = abs(float(cg.get("change_24h_pct") or 0))
                source = "coingecko_canonical"
        except (aiohttp.ClientError, asyncio.TimeoutError, TimeoutError, ImportError):
            pass

    if liquidity_usd <= 0:
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                q = f"{canonical} USDC"
                async with session.get(
                    "https://api.dexscreener.com/latest/dex/search", params={"q": q}
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        pairs = data.get("pairs") or []
                        if pairs:
                            best = max(
                                pairs,
                                key=lambda p: float((p.get("liquidity") or {}).get("usd") or 0),
                            )
                            liquidity_usd = float((best.get("liquidity") or {}).get("usd") or 0)
                            if not price:
                                price = float(best.get("priceUsd") or 0)
                            source = f"{source}+dexscreener" if source != "unknown" else "dexscreener"
        except (aiohttp.ClientError, asyncio.TimeoutError, TimeoutError):
            pass

    return {
        "canonical_symbol": canonical,
        "volatility_24h_pct": vol_pct,
        "liquidity_usd": liquidity_usd,
        "price_usd": price,
        "source": source,
    }


def _volatility_adjustment(vol_pct: float) -> float:
    """Higher vol → wider tolerance. ~0.5% move → +4bps; 5% → +40bps."""
    return min(120.0, vol_pct * 8.0)


def _depth_adjustment(*, amount_usd: float, liquidity_usd: float) -> float:
    """
    Deeper liquidity vs trade size → tighter tolerance (negative adjustment).
    Shallow pool → positive (wider).
    """
    if liquidity_usd <= 0 or amount_usd <= 0:
        return 25.0
    utilization = amount_usd / liquidity_usd
    if utilization > 0.1:
        return min(80.0, utilization * 400)
    return -min(35.0, (1.0 - utilization * 10) * 15)


def _gas_adjustment(gas_bps: float | None) -> float:
    """Higher gas as % of trade → slightly wider to avoid failed swaps."""
    if gas_bps is None:
        return 5.0
    return min(40.0, gas_bps * 0.6)


def _alerts(optimal_bps: float, ctx: dict[str, Any], amount_usd: float) -> list[dict[str, Any]]:
    alerts: list[dict[str, Any]] = []
    vol = float(ctx.get("volatility_24h_pct") or 0)
    liq = float(ctx.get("liquidity_usd") or 0)
    if optimal_bps >= 150:
        alerts.append(
            {
                "level": "high",
                "code": "WIDE_SLIPPAGE",
                "message": f"Optimized tolerance {optimal_bps:.0f}bps — high vol or thin liquidity",
            }
        )
    if vol >= 8:
        alerts.append(
            {
                "level": "medium",
                "code": "HIGH_VOLATILITY",
                "message": f"24h volatility {vol:.1f}% — tolerance widened",
            }
        )
    if liq > 0 and amount_usd > liq * 0.05:
        alerts.append(
            {
                "level": "high",
                "code": "SIZE_VS_DEPTH",
                "message": f"Trade ${amount_usd:,.0f} vs ~${liq:,.0f} liquidity — consider splitting",
            }
        )
    if optimal_bps <= 25:
        alerts.append(
            {
                "level": "low",
                "code": "TIGHT_TOLERANCE",
                "message": f"Tight {optimal_bps:.0f}bps — favorable depth/vol conditions",
            }
        )
    return alerts


async def _fetch_cex_order_book(symbol: str) -> dict[str, Any] | None:
    """Binance spot depth for asymmetric buy/sell slippage walk."""
    pair = f"{symbol.upper()}USDT"
    if not pair.isalnum():
        return None
    timeout = aiohttp.ClientTimeout(total=3)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(
                "https://api.binance.com/api/v3/depth",
                params={"symbol": pair, "limit": 20},
            ) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
                return {
                    "asks": [[float(p), float(q)] for p, q in (data.get("asks") or [])],
                    "bids": [[float(p), float(q)] for p, q in (data.get("bids") or [])],
                }
    except (aiohttp.ClientError, asyncio.TimeoutError, TimeoutError, ValueError):
        return None


def _amm_directional_slippage(
    *, amount_usd: float, liquidity_usd: float, price: float, side: str
) -> float:
    """
    AMM buy/sell asymmetry: selling into pool (more base) vs buying (more quote)
    uses slightly different effective depth utilization.
    """
    if liquidity_usd <= 0 or amount_usd <= 0:
        return 9999.0
    base_slip = constant_product_slippage_bps(
        amount_usd=amount_usd, liquidity_usd=liquidity_usd, fee_bps=30.0
    )
    if side == "buy":
        # Buying base: consume asks side of pool — slightly higher impact
        return round(base_slip * 1.08, 2)
    # Selling base: bid side typically deeper on major pairs
    depth_factor = 0.92 if price > 0 else 1.0
    return round(base_slip * depth_factor, 2)


def _directional_bias(buy_bps: float, sell_bps: float) -> str:
    spread = buy_bps - sell_bps
    if abs(spread) < 5:
        return "balanced"
    return "buy_heavy" if spread > 0 else "sell_heavy"


async def compute_asymmetric_slippage_cost(
    symbol: str = "ETH",
    *,
    amount_usd: float = 10_000.0,
    chain: str = "ethereum",
) -> dict[str, Any]:
    """
    Feature #17 — directional slippage cost vector (buy vs sell).
    Embedded in Slippage Intelligence Module; not a standalone surface.
    """
    t0 = time.perf_counter()
    from blackdark.canonical.resolver import resolve_asset

    resolved = resolve_asset(symbol or "ETH")
    asset = resolved.symbol or str(symbol or "ETH").upper().replace("/USDT", "")
    ctx = await _market_context(asset)
    price = float(ctx.get("price_usd") or 0)
    liq = float(ctx.get("liquidity_usd") or 0)

    book = await _fetch_cex_order_book(asset)
    buy_bps = 0.0
    sell_bps = 0.0
    cex_source = "unavailable"

    if book and price > 0:
        buy_exec = walk_asks(book, amount_usd)
        base_amt = amount_usd / price if price > 0 else 0
        sell_exec = walk_bids(book, base_amt) if base_amt > 0 else None
        if buy_exec:
            buy_bps = round(buy_exec.slippage_bps, 2)
        if sell_exec:
            sell_bps = round(sell_exec.slippage_bps, 2)
        if buy_exec or sell_exec:
            cex_source = "binance_depth"

    amm_buy_bps = _amm_directional_slippage(
        amount_usd=amount_usd, liquidity_usd=max(liq, amount_usd), price=price, side="buy"
    )
    amm_sell_bps = _amm_directional_slippage(
        amount_usd=amount_usd, liquidity_usd=max(liq, amount_usd), price=price, side="sell"
    )

    # Blend CEX + AMM when CEX book unavailable
    if cex_source == "unavailable":
        buy_bps = amm_buy_bps
        sell_bps = amm_sell_bps
        cex_source = "amm_proxy"

    spread_bps = round(abs(buy_bps - sell_bps), 2)
    ratio = round(buy_bps / sell_bps, 3) if sell_bps > 0 else None
    bias = _directional_bias(buy_bps, sell_bps)
    gas_bps = await gas_cost_bps(chain, amount_usd, hops=1)

    alerts: list[dict[str, Any]] = []
    if spread_bps >= 30:
        alerts.append(
            {
                "level": "high",
                "code": "ASYMMETRIC_SPREAD",
                "message": f"Buy/sell slippage spread {spread_bps:.0f}bps — directional bias: {bias}",
            }
        )
    if buy_bps >= 100 or sell_bps >= 100:
        alerts.append(
            {
                "level": "medium",
                "code": "DIRECTIONAL_COST_HIGH",
                "message": f"Buy {buy_bps:.0f}bps / Sell {sell_bps:.0f}bps exceeds comfort zone",
            }
        )

    heavier_side = "buy" if buy_bps >= sell_bps else "sell"
    side_adjustment_bps = round(max(buy_bps, sell_bps) * 0.15, 1)

    return {
        "ok": True,
        "surface": "asymmetric_slippage_cost",
        "module": "slippage_intelligence",
        "asset": asset,
        "canonical_id": resolved.canonical_id if resolved.found else None,
        "chain": chain,
        "amount_usd": amount_usd,
        "buy_slippage_bps": buy_bps,
        "sell_slippage_bps": sell_bps,
        "asymmetry_spread_bps": spread_bps,
        "asymmetry_ratio": ratio,
        "directional_bias": bias,
        "heavier_side": heavier_side,
        "side_tolerance_adjustment_bps": side_adjustment_bps,
        "venues": {
            "cex": {"source": cex_source, "buy_bps": buy_bps, "sell_bps": sell_bps},
            "amm": {"buy_bps": amm_buy_bps, "sell_bps": amm_sell_bps},
        },
        "gas_cost_bps": gas_bps,
        "effective_buy_cost_bps": round(buy_bps + (gas_bps or 0), 2),
        "effective_sell_cost_bps": round(sell_bps + (gas_bps or 0), 2),
        "headline": f"Asymmetric cost: buy {buy_bps:.0f}bps / sell {sell_bps:.0f}bps (spread {spread_bps:.0f}bps)",
        "alerts": alerts,
        "data_state": "LIVE" if ctx else "UNKNOWN",
        "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
        "sla_met": (time.perf_counter() - t0) <= 2.0,
        "timestamp": _utcnow(),
    }


async def optimize_slippage_tolerance(
    symbol: str = "ETH",
    *,
    amount_usd: float = 10_000.0,
    chain: str = "ethereum",
    user_tolerance_bps: int | None = None,
) -> dict[str, Any]:
    """CAP978 Slippage Tolerance Self-Optimization entrypoint."""
    t0 = time.perf_counter()
    from blackdark.canonical.resolver import resolve_asset

    resolved = resolve_asset(symbol or "ETH")
    asset = resolved.symbol or str(symbol or "ETH").upper().replace("/USDT", "")
    base_bps = float(user_tolerance_bps if user_tolerance_bps is not None else _DEFAULT_BASE_BPS)

    ctx = await _market_context(asset)
    vol_pct = float(ctx.get("volatility_24h_pct") or 0)
    liq = float(ctx.get("liquidity_usd") or 0)
    price = float(ctx.get("price_usd") or 0)

    vol_adj = _volatility_adjustment(vol_pct)
    depth_adj = _depth_adjustment(amount_usd=amount_usd, liquidity_usd=liq)
    gas_bps = await gas_cost_bps(chain, amount_usd, hops=1)
    gas_adj = _gas_adjustment(gas_bps)

    raw = base_bps + vol_adj + depth_adj + gas_adj
    optimal_bps = round(max(_MIN_BPS, min(_MAX_BPS, raw)), 1)

    amm_slip = constant_product_slippage_bps(
        amount_usd=amount_usd,
        liquidity_usd=max(liq, amount_usd),
        fee_bps=30.0,
    )

    asymmetric = await compute_asymmetric_slippage_cost(
        asset, amount_usd=amount_usd, chain=chain
    )
    # Widen optimal tolerance on the heavier directional side (#17 → #5)
    side_adj = float(asymmetric.get("side_tolerance_adjustment_bps") or 0)
    if asymmetric.get("directional_bias") != "balanced":
        optimal_bps = round(max(_MIN_BPS, min(_MAX_BPS, optimal_bps + side_adj * 0.5)), 1)

    combined_alerts = _alerts(optimal_bps, ctx, amount_usd) + list(asymmetric.get("alerts") or [])

    result = {
        "ok": True,
        "success": True,
        "surface": "slippage_intelligence_module",
        "module": "slippage_intelligence",
        "features": ["#5_slippage_self_optimization", "#17_asymmetric_slippage_cost"],
        "asset": asset,
        "canonical_id": resolved.canonical_id if resolved.found else None,
        "chain": chain,
        "amount_usd": amount_usd,
        "user_tolerance_bps": user_tolerance_bps,
        "optimal_slippage_bps": optimal_bps,
        "recommended_tolerance_bps": optimal_bps,
        "headline": (
            f"Slippage intelligence: {optimal_bps:.0f}bps tolerance · "
            f"buy {asymmetric.get('buy_slippage_bps', 0):.0f}/"
            f"sell {asymmetric.get('sell_slippage_bps', 0):.0f}bps asymmetric"
        ),
        "optimization": {
            "base_bps": base_bps,
            "volatility_adj_bps": round(vol_adj, 2),
            "liquidity_depth_adj_bps": round(depth_adj, 2),
            "gas_adj_bps": round(gas_adj, 2),
            "asymmetric_adj_bps": round(side_adj * 0.5, 2) if side_adj else 0,
            "formula": "optimal = base + vol + depth + gas + asymmetric_adj (clamped 10–300)",
            "inputs": {
                "volatility_24h_pct": vol_pct,
                "liquidity_usd": liq,
                "gas_cost_bps": gas_bps,
                "amm_impact_bps_estimate": round(amm_slip, 2),
            },
        },
        "asymmetric_slippage": asymmetric,
        "alerts": combined_alerts,
        "data_state": "LIVE" if ctx else "UNKNOWN",
        "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
        "sla_met": (time.perf_counter() - t0) <= 2.0,
        "timestamp": _utcnow(),
    }
    return result
