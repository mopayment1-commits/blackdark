"""
BLACKDARK — DeFi arbitrage engine (flash loan, DEX-DEX, bridge, MEV proxy).
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

import aiohttp

import config

logger = logging.getLogger("BLACKDARK.DeFiArbitrage")


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


async def scan_uniswap_sushiswap_spread(session: aiohttp.ClientSession, asset: str) -> dict[str, Any] | None:
    """Compare Uniswap vs SushiSwap prices for same asset via DexScreener."""
    url = f"https://api.dexscreener.com/latest/dex/search?q={asset}%20USDT"
    try:
        async with session.get(url, headers={"User-Agent": "BLACKDARK/1.0"}) as resp:
            if resp.status != 200:
                return None
            data = await resp.json()
    except aiohttp.ClientError:
        return None

    uni_price = sushi_price = 0.0
    uni_liq = sushi_liq = 0.0
    for row in data.get("pairs") or []:
        dex = str(row.get("dexId") or "").lower()
        price = float(row.get("priceUsd") or 0)
        liq = float((row.get("liquidity") or {}).get("usd") or 0)
        if price <= 0 or liq < 30_000:
            continue
        if "uniswap" in dex:
            if liq > uni_liq:
                uni_price, uni_liq = price, liq
        elif "sushi" in dex and liq > sushi_liq:
            sushi_price, sushi_liq = price, liq

    if uni_price <= 0 or sushi_price <= 0:
        return None

    spread_bps = abs(uni_price - sushi_price) / min(uni_price, sushi_price) * 10_000
    buy_venue = "uniswap" if uni_price < sushi_price else "sushiswap"
    sell_venue = "sushiswap" if buy_venue == "uniswap" else "uniswap"
    buy_p = min(uni_price, sushi_price)
    sell_p = max(uni_price, sushi_price)

    from gas_oracle import gas_cost_bps

    quote = float(getattr(config, "DEFAULT_QUOTE_AMOUNT", 100))
    gas_bps = await gas_cost_bps("ethereum", quote, hops=2)
    net_bps = spread_bps - gas_bps - 60  # pool fees ~0.6%

    return {
        "kind": "defi_dex_dex",
        "strategy": "uniswap_vs_sushiswap",
        "asset": asset,
        "buy_venue": buy_venue,
        "sell_venue": sell_venue,
        "buy_price": round(buy_p, 6),
        "sell_price": round(sell_p, 6),
        "spread_bps": round(spread_bps, 2),
        "gas_bps": round(gas_bps, 2),
        "net_spread_bps": round(net_bps, 2),
        "profitable": net_bps > 8,
        "chain": "ethereum",
    }


async def scan_flash_loan_proxy(session: aiohttp.ClientSession, asset: str) -> dict[str, Any] | None:
    """
    Flash-loan arb proxy: detect same-asset price gap across DEX venues
    large enough to cover Aave flash fee (0.09%) + gas.
    """
    from bd_platform.cex_dex_arbitrage import _best_dex_quote, _cex_prices

    cex = await _cex_prices(session, asset)
    if not cex:
        return None
    cex_mid = sum(cex.values()) / len(cex)
    dex_a = await _best_dex_quote(session, asset, cex_mid)
    if not dex_a.get("price"):
        return None

    # Second venue search
    url = f"https://api.dexscreener.com/latest/dex/tokens/{asset}"
    dex_b_price = 0.0
    dex_b_venue = ""
    try:
        async with session.get(url, headers={"User-Agent": "BLACKDARK/1.0"}) as resp:
            if resp.status == 200:
                data = await resp.json()
                for row in data.get("pairs") or []:
                    p = float(row.get("priceUsd") or 0)
                    liq = float((row.get("liquidity") or {}).get("usd") or 0)
                    if p > 0 and liq > 50_000 and (
                        dex_b_price == 0 or abs(p - cex_mid) > abs(dex_b_price - cex_mid)
                    ):
                        dex_b_price = p
                        dex_b_venue = row.get("dexId") or "dex"
    except aiohttp.ClientError:
        pass

    if dex_b_price <= 0:
        return None

    pa = float(dex_a["price"])
    spread_bps = abs(pa - dex_b_price) / min(pa, dex_b_price) * 10_000
    chain = str(dex_a.get("chain") or "ethereum")
    from gas_oracle import gas_cost_bps

    quote = float(getattr(config, "DEFAULT_QUOTE_AMOUNT", 100))
    gas_bps = await gas_cost_bps(chain, quote, hops=3)
    flash_fee_bps = 9.0  # Aave 0.09%
    net_bps = spread_bps - gas_bps - flash_fee_bps - 60

    if net_bps < 5:
        return None

    return {
        "kind": "defi_flash_loan",
        "strategy": "flash_loan_atomic",
        "asset": asset,
        "venue_a": dex_a.get("venue"),
        "venue_b": dex_b_venue,
        "price_a": round(pa, 6),
        "price_b": round(dex_b_price, 6),
        "spread_bps": round(spread_bps, 2),
        "flash_fee_bps": flash_fee_bps,
        "gas_bps": round(gas_bps, 2),
        "net_spread_bps": round(net_bps, 2),
        "profitable": net_bps > 8,
        "chain": chain,
        "note": "Atomic flash loan feasible if spread covers 0.09% + gas",
    }


async def scan_bridge_spread(session: aiohttp.ClientSession, asset: str) -> dict[str, Any] | None:
    """Cross-chain bridge spread: ETH mainnet vs BSC vs Arbitrum DEX prices."""
    chains = ["ethereum", "bsc", "arbitrum"]
    prices: dict[str, float] = {}
    for chain in chains:
        url = f"https://api.dexscreener.com/latest/dex/search?q={asset}%20USDT%20{chain}"
        try:
            async with session.get(url, headers={"User-Agent": "BLACKDARK/1.0"}) as resp:
                if resp.status != 200:
                    continue
                data = await resp.json()
                best_p = best_liq = 0.0
                for row in data.get("pairs") or []:
                    if str(row.get("chainId") or "").lower() != chain and chain not in str(row.get("chainId") or "").lower():
                        continue
                    p = float(row.get("priceUsd") or 0)
                    liq = float((row.get("liquidity") or {}).get("usd") or 0)
                    if p > 0 and liq > best_liq:
                        best_p, best_liq = p, liq
                if best_p > 0:
                    prices[chain] = best_p
        except aiohttp.ClientError:
            continue

    if len(prices) < 2:
        return None

    buy_chain = min(prices, key=prices.get)
    sell_chain = max(prices, key=prices.get)
    buy_p = prices[buy_chain]
    sell_p = prices[sell_chain]
    spread_bps = (sell_p - buy_p) / buy_p * 10_000

    from gas_oracle import get_swap_gas_usd

    quote = float(getattr(config, "DEFAULT_QUOTE_AMOUNT", 100))
    bridge_gas = await get_swap_gas_usd(buy_chain, hops=1) + await get_swap_gas_usd(sell_chain, hops=1) + 3.0
    gas_bps = (bridge_gas / quote) * 10_000
    net_bps = spread_bps - gas_bps - 20

    if net_bps < 5:
        return None

    return {
        "kind": "defi_bridge",
        "strategy": "cross_chain_bridge",
        "asset": asset,
        "buy_chain": buy_chain,
        "sell_chain": sell_chain,
        "buy_price": round(buy_p, 6),
        "sell_price": round(sell_p, 6),
        "spread_bps": round(spread_bps, 2),
        "bridge_gas_usd": round(bridge_gas, 2),
        "net_spread_bps": round(net_bps, 2),
        "profitable": net_bps > 10,
    }


async def scan_mev_slippage_proxy(session: aiohttp.ClientSession, asset: str) -> dict[str, Any] | None:
    """MEV/slippage capture proxy — large CEX-DEX gap with high DEX impact potential."""
    from bd_platform.cex_dex_arbitrage import _best_dex_quote, _cex_prices
    from dex_slippage import constant_product_slippage_bps

    cex = await _cex_prices(session, asset)
    if not cex:
        return None
    cex_mid = sum(cex.values()) / len(cex)
    dex = await _best_dex_quote(session, asset, cex_mid)
    if not dex.get("price"):
        return None

    spread_bps = abs(float(dex["price"]) - cex_mid) / cex_mid * 10_000
    liq = float(dex.get("liquidity_usd") or 0)
    quote = float(getattr(config, "DEFAULT_QUOTE_AMOUNT", 100))
    slip_bps = constant_product_slippage_bps(amount_usd=quote, liquidity_usd=liq)

    if spread_bps < 15 or slip_bps > spread_bps * 0.5:
        return None

    return {
        "kind": "defi_mev",
        "strategy": "mev_slippage_capture",
        "asset": asset,
        "cex_mid": round(cex_mid, 6),
        "dex_price": round(float(dex["price"]), 6),
        "spread_bps": round(spread_bps, 2),
        "slippage_bps": round(slip_bps, 2),
        "dex_liquidity_usd": liq,
        "net_spread_bps": round(spread_bps - slip_bps, 2),
        "profitable": spread_bps > slip_bps + 10,
        "note": "MEV opportunity if block builder captures spread before public",
    }


async def scan_all_defi_strategies(*, quote_usd: float = 1000) -> dict[str, Any]:
    assets = list(config.WHITELIST_ASSETS)[:10]
    opportunities: list[dict[str, Any]] = []
    timeout = aiohttp.ClientTimeout(total=20)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        for asset in assets:
            for scanner in (
                scan_uniswap_sushiswap_spread,
                scan_flash_loan_proxy,
                scan_bridge_spread,
                scan_mev_slippage_proxy,
            ):
                try:
                    row = await scanner(session, asset)
                    if row and row.get("profitable"):
                        row["quote_usd"] = quote_usd
                        row["estimated_profit_usd"] = round(
                            quote_usd * float(row.get("net_spread_bps") or 0) / 10_000, 2
                        )
                        opportunities.append(row)
                except Exception:
                    logger.debug("DeFi scanner failed | asset=%s", asset, exc_info=True)

    from bd_platform.cex_dex_arbitrage import scan_cex_dex_opportunities

    cex_dex = await scan_cex_dex_opportunities(quote_usd=quote_usd)
    for row in cex_dex.get("opportunities") or []:
        if row.get("profitable"):
            opportunities.append(row)

    opportunities.sort(key=lambda x: float(x.get("net_spread_bps") or 0), reverse=True)
    return {
        "timestamp": _utcnow(),
        "quote_usd": quote_usd,
        "strategies": ["cex_dex", "uniswap_sushi", "flash_loan", "bridge", "mev"],
        "opportunities": opportunities,
        "count": len(opportunities),
        "profitable_count": sum(1 for o in opportunities if o.get("profitable")),
        "top": opportunities[0] if opportunities else None,
    }


def defi_engine_stats() -> dict[str, Any]:
    from gas_oracle import oracle_stats

    return {"gas_oracle": oracle_stats()}
