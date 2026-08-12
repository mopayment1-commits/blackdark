"""
BLACKDARK — DeFi arbitrage engine (flash loan, DEX-DEX, bridge, MEV proxy).
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

import aiohttp

import config

# Sonar S1192: duplicated string literals
STR_BLACKDARK_1_0 = 'BLACKDARK/1.0'

logger = logging.getLogger("BLACKDARK.DeFiArbitrage")


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _dex_row_price_liquidity(row: dict[str, Any]) -> tuple[float, float]:
    price = float(row.get("priceUsd") or 0)
    liquidity = float((row.get("liquidity") or {}).get("usd") or 0)
    return price, liquidity


def _best_venue_prices(pairs: list[dict[str, Any]]) -> tuple[float, float, float, float]:
    uni_price = sushi_price = 0.0
    uni_liq = sushi_liq = 0.0
    for row in pairs:
        dex = str(row.get("dexId") or "").lower()
        price, liquidity = _dex_row_price_liquidity(row)
        if price <= 0 or liquidity < 30_000:
            continue
        if "uniswap" in dex and liquidity > uni_liq:
            uni_price, uni_liq = price, liquidity
        elif "sushi" in dex and liquidity > sushi_liq:
            sushi_price, sushi_liq = price, liquidity
    return uni_price, uni_liq, sushi_price, sushi_liq


def _dex_dex_venues(uni_price: float, sushi_price: float) -> tuple[str, str, float, float]:
    buy_venue = "uniswap" if uni_price < sushi_price else "sushiswap"
    sell_venue = "sushiswap" if buy_venue == "uniswap" else "uniswap"
    return buy_venue, sell_venue, min(uni_price, sushi_price), max(uni_price, sushi_price)


async def scan_uniswap_sushiswap_spread(session: aiohttp.ClientSession, asset: str) -> dict[str, Any] | None:
    """Compare Uniswap vs SushiSwap prices for same asset via DexScreener."""
    if not asset.isalnum():
        return None
    url = f"https://api.dexscreener.com/latest/dex/search?q={asset}%20USDT"
    try:
        async with session.get(url, headers={"User-Agent": STR_BLACKDARK_1_0}) as resp:
            if resp.status != 200:
                return None
            data = await resp.json()
    except aiohttp.ClientError:
        return None

    uni_price, _, sushi_price, _ = _best_venue_prices(data.get("pairs") or [])

    if uni_price <= 0 or sushi_price <= 0:
        return None

    spread_bps = abs(uni_price - sushi_price) / min(uni_price, sushi_price) * 10_000
    buy_venue, sell_venue, buy_p, sell_p = _dex_dex_venues(uni_price, sushi_price)

    from gas_oracle import gas_cost_bps

    quote = float(getattr(config, "DEFAULT_QUOTE_AMOUNT", 100))
    gas_bps = await gas_cost_bps("ethereum", quote, hops=2)
    if gas_bps is None:
        # Unknown/stale gas must not invent executable DeFi profitability.
        return None
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
        # Mid-price DexScreener rows lack executable depth → indicative only.
        "profitable": False,
        "executable": False,
        "indicative": True,
        "reject_reason": "defi_depth_not_verified",
        "chain": "ethereum",
        "gas_truth": "live_cached",
    }


async def _find_second_dex_quote(
    session: aiohttp.ClientSession,
    asset: str,
    cex_mid: float,
) -> tuple[float, str]:
    if not asset.isalnum():
        return 0.0, ""
    url = f"https://api.dexscreener.com/latest/dex/tokens/{asset}"
    dex_b_price = 0.0
    dex_b_venue = ""
    try:
        async with session.get(url, headers={"User-Agent": STR_BLACKDARK_1_0}) as resp:
            if resp.status != 200:
                return dex_b_price, dex_b_venue
            data = await resp.json()
    except aiohttp.ClientError:
        return dex_b_price, dex_b_venue

    # Prefer the closest liquid peer — maximizing disagreement invents flash "profit".
    best_dist = None
    for row in data.get("pairs") or []:
        price, liquidity = _dex_row_price_liquidity(row)
        if price <= 0 or liquidity <= 50_000:
            continue
        dist = abs(price - cex_mid)
        if best_dist is None or dist < best_dist:
            best_dist = dist
            dex_b_price = price
            dex_b_venue = row.get("dexId") or "dex"
    return dex_b_price, dex_b_venue


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
    dex_b_price, dex_b_venue = await _find_second_dex_quote(session, asset, cex_mid)
    if dex_b_price <= 0:
        return None

    pa = float(dex_a["price"])
    spread_bps = abs(pa - dex_b_price) / min(pa, dex_b_price) * 10_000
    chain = str(dex_a.get("chain") or "ethereum")
    from gas_oracle import gas_cost_bps

    quote = float(getattr(config, "DEFAULT_QUOTE_AMOUNT", 100))
    gas_bps = await gas_cost_bps(chain, quote, hops=3)
    if gas_bps is None:
        return None
    # Flash-loan protocol fee is venue-specific and not inventoried → fail closed
    # for net/profitability (do not invent Aave 0.09% as authority).
    return {
        "kind": "defi_flash_loan",
        "strategy": "flash_loan_atomic",
        "asset": asset,
        "venue_a": dex_a.get("venue"),
        "venue_b": dex_b_venue,
        "price_a": round(pa, 6),
        "price_b": round(dex_b_price, 6),
        "spread_bps": round(spread_bps, 2),
        "flash_fee_bps": None,
        "gas_bps": round(gas_bps, 2),
        "net_spread_bps": None,
        "profitable": False,
        "executable": False,
        "indicative": True,
        "reject_reason": "flash_loan_protocol_fee_unknown",
        "chain": chain,
        "gas_truth": "live_cached",
        "note": (
            "Indicative flash-loan spread only. Protocol fee not inventoried — "
            "fail closed for executable profitability."
        ),
    }


async def _chain_dex_price(
    session: aiohttp.ClientSession,
    asset: str,
    chain: str,
) -> float:
    if not chain.isalnum():
        return 0.0
    url = f"https://api.dexscreener.com/latest/dex/search?q={asset}%20USDT%20{chain}"
    try:
        async with session.get(url, headers={"User-Agent": STR_BLACKDARK_1_0}) as resp:
            if resp.status != 200:
                return 0.0
            data = await resp.json()
    except aiohttp.ClientError:
        return 0.0

    best_p = best_liq = 0.0
    for row in data.get("pairs") or []:
        chain_id = str(row.get("chainId") or "").lower()
        if chain_id != chain and chain not in chain_id:
            continue
        price, liquidity = _dex_row_price_liquidity(row)
        if price > 0 and liquidity > best_liq:
            best_p, best_liq = price, liquidity
    return best_p


async def scan_bridge_spread(session: aiohttp.ClientSession, asset: str) -> dict[str, Any] | None:
    """Cross-chain bridge spread: ETH mainnet vs BSC vs Arbitrum DEX prices."""
    if not asset.isalnum():
        return None
    chains = ["ethereum", "bsc", "arbitrum"]
    prices: dict[str, float] = {}
    for chain in chains:
        best_p = await _chain_dex_price(session, asset, chain)
        if best_p > 0:
            prices[chain] = best_p

    if len(prices) < 2:
        return None

    buy_chain = min(prices, key=prices.get)
    sell_chain = max(prices, key=prices.get)
    buy_p = prices[buy_chain]
    sell_p = prices[sell_chain]
    spread_bps = (sell_p - buy_p) / buy_p * 10_000

    from gas_oracle import get_swap_gas_usd

    buy_gas = await get_swap_gas_usd(buy_chain, hops=1)
    sell_gas = await get_swap_gas_usd(sell_chain, hops=1)
    if buy_gas is None or sell_gas is None:
        # Unknown/stale gas must not invent executable DeFi profitability.
        return None
    bridge_gas = buy_gas + sell_gas
    # Bridge protocol fee is venue-specific and not inventoried → fail closed
    # for executability (do not invent a flat +$3 bridge fee).
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
        "bridge_protocol_fee_usd": None,
        "net_spread_bps": None,
        "profitable": False,
        "executable": False,
        "reject_reason": "bridge_protocol_fee_unknown",
        "note": (
            "Indicative cross-chain spread only. Bridge protocol fee is not "
            "inventoried — fail closed for executable profitability."
        ),
    }


def _mev_spread_viable(spread_bps: float, slip_bps: float) -> bool:
    return spread_bps >= 15 and slip_bps <= spread_bps * 0.5


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

    if not _mev_spread_viable(spread_bps, slip_bps):
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
        "profitable": False,
        "executable": False,
        "indicative": True,
        "reject_reason": "mev_gas_and_depth_not_verified",
        "note": (
            "Indicative MEV/slippage gap only. No gas/fee truth — fail closed "
            "for executable profitability."
        ),
    }


def _defi_scanners() -> tuple[Any, ...]:
    return (
        scan_uniswap_sushiswap_spread,
        scan_flash_loan_proxy,
        scan_bridge_spread,
        scan_mev_slippage_proxy,
    )


async def _scan_asset_defi_strategies(
    session: aiohttp.ClientSession,
    asset: str,
    quote_usd: float,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for scanner in _defi_scanners():
        try:
            row = await scanner(session, asset)
            if row and row.get("profitable"):
                row["quote_usd"] = quote_usd
                row["estimated_profit_usd"] = round(
                    quote_usd * float(row.get("net_spread_bps") or 0) / 10_000, 2
                )
                rows.append(row)
        except Exception:
            logger.debug("DeFi scanner failed | asset=%s", asset, exc_info=True)
    return rows


async def _scan_cex_dex_defi(quote_usd: float) -> list[dict[str, Any]]:
    from bd_platform.cex_dex_arbitrage import scan_cex_dex_opportunities

    cex_dex = await scan_cex_dex_opportunities(quote_usd=quote_usd)
    return [row for row in cex_dex.get("opportunities") or [] if row.get("profitable")]


async def scan_all_defi_strategies(*, quote_usd: float = 1000) -> dict[str, Any]:
    assets = list(config.WHITELIST_ASSETS)[:10]
    opportunities: list[dict[str, Any]] = []
    timeout = aiohttp.ClientTimeout(total=20)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        for asset in assets:
            opportunities.extend(await _scan_asset_defi_strategies(session, asset, quote_usd))
    opportunities.extend(await _scan_cex_dex_defi(quote_usd))

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
