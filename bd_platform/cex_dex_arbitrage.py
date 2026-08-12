"""CEX↔DEX cross-boundary arbitrage — scan + DexScreener + multi-venue."""

from __future__ import annotations

import logging
import os
from datetime import UTC, datetime
from typing import Any

import aiohttp

import config

logger = logging.getLogger("BLACKDARK.CexDexArb")

_GAS_BPS_EST = float(os.getenv("CEX_DEX_GAS_BPS_EST", "35"))
_MIN_NET_BPS = float(os.getenv("CEX_DEX_MIN_NET_BPS", "8"))


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


async def _cex_prices(session: aiohttp.ClientSession, asset: str) -> dict[str, float]:
    out: dict[str, float] = {}
    if not asset.isalnum():
        return out
    pair = f"{asset}USDT"
    if not pair.isalnum():
        return out
    urls = {
        "binance": f"https://api.binance.com/api/v3/ticker/price?symbol={pair}",
        "okx": f"https://www.okx.com/api/v5/market/ticker?instId={asset}-USDT",
    }
    try:
        async with session.get(urls["binance"]) as resp:
            if resp.status == 200:
                data = await resp.json()
                p = float(data.get("price") or 0)
                if p > 0:
                    out["binance"] = p
    except (aiohttp.ClientError, TypeError, ValueError):
        pass
    try:
        async with session.get(urls["okx"]) as resp:
            if resp.status == 200:
                data = await resp.json()
                row = (data.get("data") or [{}])[0]
                p = float(row.get("last") or 0)
                if p > 0:
                    out["okx"] = p
    except (aiohttp.ClientError, TypeError, ValueError):
        pass
    return out


async def _dexscreener_best(
    session: aiohttp.ClientSession,
    asset: str,
    cex_ref: float,
) -> dict[str, Any]:
    if not asset.isalnum():
        return {}
    url = f"https://api.dexscreener.com/latest/dex/search?q={asset}%20USDT"
    headers = {"User-Agent": "BLACKDARK/1.0"}
    try:
        async with session.get(url, headers=headers) as resp:
            if resp.status != 200:
                return {}
            data = await resp.json()
    except aiohttp.ClientError:
        return {}
    pairs = data.get("pairs") or []
    best: dict[str, Any] | None = None
    asset_u = asset.upper()
    for row in pairs:
        candidate = _dexscreener_candidate(row, asset_u, cex_ref, min_liquidity=50_000)
        if candidate is None:
            continue
        if best is None or candidate["liquidity_usd"] > float(best.get("liquidity_usd") or 0):
            best = candidate
    return best or {}


def _dexscreener_candidate(
    row: dict[str, Any],
    asset_u: str,
    cex_ref: float,
    *,
    min_liquidity: float,
) -> dict[str, Any] | None:
    base_sym = str((row.get("baseToken") or {}).get("symbol") or "").upper()
    quote_sym = str((row.get("quoteToken") or {}).get("symbol") or "").upper()
    if base_sym != asset_u and not base_sym.startswith(asset_u):
        return None
    if quote_sym not in {"USDT", "USDC", "USD"}:
        return None
    price = float(row.get("priceUsd") or 0)
    liq = float((row.get("liquidity") or {}).get("usd") or 0)
    if price <= 0 or liq < min_liquidity:
        return None
    if cex_ref > 0 and abs(price - cex_ref) / cex_ref > 0.15:
        return None
    return {
        "venue": row.get("dexId") or "dex",
        "pair": row.get("pairAddress"),
        "chain": row.get("chainId"),
        "price": price,
        "liquidity_usd": liq,
        "url": row.get("url"),
    }


async def _jupiter_quote(session: aiohttp.ClientSession, asset: str) -> dict[str, Any]:
    from dex_fetcher import _jupiter_price

    price = await _jupiter_price(session, asset)
    return {"venue": "jupiter", "price": price}


async def _gmx_price(session: aiohttp.ClientSession, asset: str, cex_ref: float) -> dict[str, Any]:
    """GMX perp mark price via public stats API (Arbitrum)."""
    symbol = f"{asset.upper()}USD"
    url = "https://arbitrum-api.gmxinfra.io/prices/tickers"
    try:
        async with session.get(url) as resp:
            if resp.status != 200:
                return {}
            rows = await resp.json()
            for row in rows or []:
                if str(row.get("tokenSymbol") or "").upper() == symbol.replace("USD", ""):
                    price = float(row.get("maxPrice") or row.get("minPrice") or 0) / 1e30
                    if price <= 0:
                        continue
                    if cex_ref > 0 and abs(price - cex_ref) / cex_ref > 0.15:
                        continue
                    return {"venue": "gmx", "price": price, "liquidity_usd": 1_000_000, "source": "gmx_arbitrum"}
    except (aiohttp.ClientError, TypeError, ValueError):
        pass
    return {}


async def _oneinch_spot(session: aiohttp.ClientSession, asset: str, cex_ref: float) -> dict[str, Any]:
    """1inch spot indicative price via DexScreener 1inch pools."""
    if not asset.isalnum():
        return {}
    url = f"https://api.dexscreener.com/latest/dex/search?q=1inch%20{asset}%20USDT"
    try:
        async with session.get(url, headers={"User-Agent": "BLACKDARK/1.0"}) as resp:
            if resp.status != 200:
                return {}
            data = await resp.json()
    except aiohttp.ClientError:
        return {}
    for row in data.get("pairs") or []:
        candidate = _oneinch_candidate(row, cex_ref)
        if candidate is not None:
            return candidate
    return {}


def _oneinch_candidate(row: dict[str, Any], cex_ref: float) -> dict[str, Any] | None:
    dex_id = str(row.get("dexId") or "").lower()
    if "1inch" not in dex_id and dex_id not in {"uniswap", "sushiswap"}:
        return None
    price = float(row.get("priceUsd") or 0)
    liq = float((row.get("liquidity") or {}).get("usd") or 0)
    if price <= 0 or liq < 30_000:
        return None
    if cex_ref > 0 and abs(price - cex_ref) / cex_ref > 0.15:
        return None
    return {
        "venue": "1inch",
        "price": price,
        "liquidity_usd": liq,
        "source": "dexscreener_1inch",
        "url": row.get("url"),
    }


async def _best_dex_quote(
    session: aiohttp.ClientSession,
    asset: str,
    cex_ref: float,
) -> dict[str, Any]:
    """Pick best DEX quote among DexScreener, Jupiter, GMX, 1inch."""
    candidates: list[dict[str, Any]] = []
    dex_row = await _dexscreener_best(session, asset, cex_ref)
    if dex_row.get("price"):
        candidates.append(dex_row)
    for fetch in (_jupiter_quote, _gmx_price, _oneinch_spot):
        try:
            if fetch is _jupiter_quote:
                row = await fetch(session, asset)
            else:
                row = await fetch(session, asset, cex_ref)
            if row.get("price"):
                candidates.append(row)
        except TypeError:
            continue
    if not candidates:
        return {}
    return max(candidates, key=lambda r: float(r.get("liquidity_usd") or 0))


def _best_cex(prices: dict[str, float], *, side: str) -> tuple[str, float]:
    if not prices:
        return "binance", 0.0
    venue = min(prices, key=prices.get) if side == "buy" else max(prices, key=prices.get)
    return venue, prices[venue]


def _execution_feasibility(net_bps: float, liq_usd: float, quote_usd: float) -> str:
    if net_bps < _MIN_NET_BPS:
        return "below_threshold"
    if liq_usd < quote_usd * 2:
        return "low_dex_liquidity"
    if net_bps >= 25 and liq_usd >= quote_usd * 5:
        return "high"
    if net_bps >= 12:
        return "medium"
    return "partial"


def _indicative_fee_bps(buy_venue: str, sell_venue: str) -> float | None:
    """Indicative fee haircut via fee_matrix — None when either venue fee unknown."""
    from fee_matrix import taker_fee

    buy_rate = taker_fee(str(buy_venue or ""))
    sell_rate = taker_fee(str(sell_venue or ""))
    if buy_rate is None or sell_rate is None:
        return None
    return (float(buy_rate) + float(sell_rate)) * 10_000 + _GAS_BPS_EST


async def _cex_dex_opportunity_for_asset(
    session: aiohttp.ClientSession,
    asset: str,
    quote_usd: float,
) -> dict[str, Any] | None:
    cex_map = await _cex_prices(session, asset)
    if not cex_map:
        return None
    cex_mid = sum(cex_map.values()) / len(cex_map)
    dex_row = await _best_dex_quote(session, asset, cex_mid)
    dex_price = float(dex_row.get("price") or 0)
    if dex_price <= 0:
        return None

    cex_low_v, cex_low = _best_cex(cex_map, side="buy")
    cex_high_v, cex_high = _best_cex(cex_map, side="sell")
    buy_venue, buy_price, sell_venue, sell_price = _cex_dex_route(
        cex_mid,
        dex_price,
        dex_row,
        cex_low_v,
        cex_low,
        cex_high_v,
        cex_high,
    )
    spread_bps = ((sell_price - buy_price) / buy_price) * 10_000 if buy_price else 0
    if abs(spread_bps) > 500:
        return None
    # Mid-price path is indicative-only; fee estimate from fee_matrix (not DEFAULT_TAKER_FEE).
    fee_bps = _indicative_fee_bps(buy_venue, sell_venue)
    if fee_bps is None:
        return None
    net_bps = spread_bps - fee_bps
    if abs(net_bps) < _MIN_NET_BPS:
        return None
    return _cex_dex_row(
        asset,
        cex_map,
        cex_mid,
        dex_row,
        buy_venue,
        buy_price,
        sell_venue,
        sell_price,
        spread_bps,
        net_bps,
        quote_usd,
        fee_bps,
    )


def _cex_dex_route(
    cex_mid: float,
    dex_price: float,
    dex_row: dict[str, Any],
    cex_low_v: str,
    cex_low: float,
    cex_high_v: str,
    cex_high: float,
) -> tuple[str, float, str, float]:
    if cex_mid > dex_price:
        return dex_row.get("venue", "dex"), dex_price, cex_high_v, cex_high
    return cex_low_v, cex_low, dex_row.get("venue", "dex"), dex_price


def _cex_dex_row(
    asset: str,
    cex_map: dict[str, float],
    cex_mid: float,
    dex_row: dict[str, Any],
    buy_venue: str,
    buy_price: float,
    sell_venue: str,
    sell_price: float,
    spread_bps: float,
    net_bps: float,
    quote_usd: float,
    fee_bps: float | None = None,
    *,
    cex_l2_walk_verified: bool = False,
) -> dict[str, Any]:
    dex_price = float(dex_row.get("price") or 0)
    liq = float(dex_row.get("liquidity_usd") or 0)
    # Depth-aware executability: require verified CEX L2 book walk + DEX liquidity + known fees.
    # Mid/pool-only paths remain INDICATIVE forever (fail closed for executable).
    # fee_bps default None — never invent unknown fees as 0.0 / free.
    cex_l2_verified = bool(cex_l2_walk_verified)
    fees_known = fee_bps is not None
    depth_ok = (
        cex_l2_verified
        and liq >= max(quote_usd * 3.0, 1.0)
        and fees_known
    )
    # Conservative impact haircut when only pool liquidity is known (no L2 walk).
    impact_bps = min(75.0, (quote_usd / liq) * 10_000 * 0.35) if liq > 0 else None
    executable = bool(
        depth_ok
        and impact_bps is not None
        and fees_known
        and (net_bps - float(impact_bps)) > 0
        and quote_usd > 0
    )
    adj_net = (net_bps - float(impact_bps)) if impact_bps is not None else None
    est_profit = (
        quote_usd * (adj_net / 10_000)
        if executable and adj_net is not None and adj_net > 0
        else None
    )
    return {
        "asset": asset,
        "cex_prices": {k: round(v, 6) for k, v in cex_map.items()},
        "cex_price": round(cex_mid, 6),
        "dex_price": round(dex_price, 6),
        "dex_venue": dex_row.get("venue"),
        "dex_liquidity_usd": round(liq, 0),
        "dex_pair_url": dex_row.get("url"),
        "buy_venue": buy_venue,
        "sell_venue": sell_venue,
        "buy_price": round(buy_price, 6),
        "sell_price": round(sell_price, 6),
        "spread_bps": round(spread_bps, 2),
        "indicative_fee_bps": round(fee_bps, 2) if fee_bps is not None else None,
        "impact_bps_estimate": round(impact_bps, 2) if impact_bps is not None else None,
        "net_spread_bps": round(net_bps, 2),
        "net_executable_spread_bps": round(adj_net, 2) if adj_net is not None else None,
        "indicative_estimated_profit_usd": round(quote_usd * (net_bps / 10_000), 2) if net_bps > 0 else 0,
        "estimated_profit_usd": round(est_profit, 2) if executable and est_profit is not None else None,
        "net_executable_profit_usdt": round(est_profit, 2) if executable and est_profit is not None else None,
        "quote_usd": quote_usd,
        "topline_positive": net_bps > 0,
        "profitable": bool(executable and est_profit and est_profit > 0),
        "executable": executable,
        "indicative": not executable,
        "indicative_reason": (
            ""
            if executable
            else (
                "fee_unknown"
                if not fees_known
                else (
                    "cex_l2_walk_required"
                    if not cex_l2_verified
                    else "cex_dex_insufficient_depth_or_impact"
                )
            )
        ),
        "depth_verified": depth_ok,
        "cex_l2_walk_verified": cex_l2_verified,
        "fees_known": fees_known,
        "smart_contract_risk_required": True,
        "execution_feasibility": _execution_feasibility(net_bps, liq, quote_usd),
        "why": (
            f"Buy {asset} on {buy_venue} @ ${buy_price:,.2f}, "
            f"sell on {sell_venue} @ ${sell_price:,.2f} — "
            + (
                f"executable {adj_net:.1f} bps after fees+gas+impact"
                if executable and adj_net is not None
                else f"indicative {net_bps:.1f} bps (not executable without verified depth)"
            )
        ),
        "kind": "cex_dex",
    }


async def scan_cex_dex_opportunities(*, quote_usd: float = 1000) -> dict[str, Any]:
    assets = list(config.WHITELIST_ASSETS)[:12]
    opportunities: list[dict[str, Any]] = []
    timeout = aiohttp.ClientTimeout(total=15)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        for asset in assets:
            opportunity = await _cex_dex_opportunity_for_asset(session, asset, quote_usd)
            if opportunity is not None:
                opportunities.append(opportunity)

    opportunities.sort(key=lambda x: x["net_spread_bps"], reverse=True)
    return {
        "timestamp": _utcnow(),
        "quote_usd": quote_usd,
        "opportunities": opportunities,
        "count": len(opportunities),
        "profitable_count": sum(1 for o in opportunities if o["profitable"]),
        "top": opportunities[0] if opportunities else None,
        "data_sources": ["Binance", "OKX", "DexScreener", "Jupiter", "GMX", "1inch"],
        "execution_endpoint": "/api/platform/arb/cex-dex/execute",
    }
