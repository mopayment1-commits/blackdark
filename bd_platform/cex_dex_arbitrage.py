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
        logger.debug("rl nudge skipped", exc_info=True)
    try:
        async with session.get(urls["okx"]) as resp:
            if resp.status == 200:
                data = await resp.json()
                row = (data.get("data") or [{}])[0]
                p = float(row.get("last") or 0)
                if p > 0:
                    out["okx"] = p
    except (aiohttp.ClientError, TypeError, ValueError):
        logger.debug("rl nudge skipped", exc_info=True)
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
        base_sym = str((row.get("baseToken") or {}).get("symbol") or "").upper()
        quote_sym = str((row.get("quoteToken") or {}).get("symbol") or "").upper()
        if base_sym != asset_u and not base_sym.startswith(asset_u):
            continue
        if quote_sym not in {"USDT", "USDC", "USD"}:
            continue
        liq = float((row.get("liquidity") or {}).get("usd") or 0)
        price = float(row.get("priceUsd") or 0)
        if price <= 0 or liq < 50_000:
            continue
        if cex_ref > 0:
            deviation = abs(price - cex_ref) / cex_ref
            if deviation > 0.15:
                continue
        if best is None or liq > float((best.get("liquidity") or {}).get("usd") or 0):
            best = {
                "venue": row.get("dexId") or "dex",
                "pair": row.get("pairAddress"),
                "chain": row.get("chainId"),
                "price": price,
                "liquidity_usd": liq,
                "url": row.get("url"),
            }
    return best or {}


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
        logger.debug("optional operation skipped", exc_info=True)
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
        dex_id = str(row.get("dexId") or "").lower()
        if "1inch" not in dex_id and dex_id not in {"uniswap", "sushiswap"}:
            continue
        price = float(row.get("priceUsd") or 0)
        liq = float((row.get("liquidity") or {}).get("usd") or 0)
        if price <= 0 or liq < 30_000:
            continue
        if cex_ref > 0 and abs(price - cex_ref) / cex_ref > 0.15:
            continue
        return {
            "venue": "1inch",
            "price": price,
            "liquidity_usd": liq,
            "source": "dexscreener_1inch",
            "url": row.get("url"),
        }
    return {}


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
            logger.debug("optional operation skipped", exc_info=True)
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


async def scan_cex_dex_opportunities(*, quote_usd: float = 1000) -> dict[str, Any]:
    assets = list(config.WHITELIST_ASSETS)[:12]
    opportunities: list[dict[str, Any]] = []
    timeout = aiohttp.ClientTimeout(total=15)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        for asset in assets:
            cex_map = await _cex_prices(session, asset)
            if not cex_map:
                continue
            cex_mid = sum(cex_map.values()) / len(cex_map)
            dex_row = await _best_dex_quote(session, asset, cex_mid)
            if not dex_row.get("price"):
                continue
            dex_price = float(dex_row.get("price") or 0)
            if dex_price <= 0:
                continue

            cex_low_v, cex_low = _best_cex(cex_map, side="buy")
            cex_high_v, cex_high = _best_cex(cex_map, side="sell")

            if cex_mid > dex_price:
                buy_venue, buy_price = dex_row.get("venue", "dex"), dex_price
                sell_venue, sell_price = cex_high_v, cex_high
            else:
                buy_venue, buy_price = cex_low_v, cex_low
                sell_venue, sell_price = dex_row.get("venue", "dex"), dex_price

            spread_bps = ((sell_price - buy_price) / buy_price) * 10_000 if buy_price else 0
            if abs(spread_bps) > 500:
                continue
            fee_bps = float(config.DEFAULT_TAKER_FEE) * 2 * 10_000 + _GAS_BPS_EST
            net_bps = spread_bps - fee_bps
            liq = float(dex_row.get("liquidity_usd") or 0)
            est_profit = quote_usd * (net_bps / 10_000) if net_bps > 0 else 0

            if abs(net_bps) < _MIN_NET_BPS:
                continue

            opportunities.append(
                {
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
                    "net_spread_bps": round(net_bps, 2),
                    "estimated_profit_usd": round(est_profit, 2),
                    "quote_usd": quote_usd,
                    "profitable": net_bps > 0,
                    "execution_feasibility": _execution_feasibility(net_bps, liq, quote_usd),
                    "why": (
                        f"Buy {asset} on {buy_venue} @ ${buy_price:,.2f}, "
                        f"sell on {sell_venue} @ ${sell_price:,.2f} — net {net_bps:.1f} bps after fees/gas"
                    ),
                    "kind": "cex_dex",
                }
            )

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
