"""
BLACKDARK — DEX Market Fetcher (Phase C).

On-chain / aggregator price feeds for 20 DEX venues.
Uses venue-native public APIs where available, DeFiLlama as fallback.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Callable, Literal

import aiohttp

import config

logger = logging.getLogger("BLACKDARK.DEXFetcher")

MarketType = Literal["spot", "cross", "perpetual"]

DEX_VENUES: frozenset[str] = frozenset(
    {
        "uniswap_v3",
        "pancakeswap",
        "raydium",
        "jupiter",
        "orca",
        "curve",
        "balancer",
        "sushiswap",
        "traderjoe",
        "quickswap",
        "spookyswap",
        "camelot",
        "aerodrome",
        "syncswap",
        "cetus",
        "stonfi",
        "dedust",
        "vvs",
        "osmosis",
        "thorchain",
    }
)

# Solana mint addresses for blueprint assets (wrapped where needed)
SOLANA_MINTS: dict[str, str] = {
    "BTC": "3NZ9JMVBmGAqocybic2c7LQCJScmgsAZ6vQqTDzcqmJh",
    "ETH": "7vfCXTUXx5WJV5JADk17DUJ4ksgau7utNKj4b963voxs",
    "SOL": "So11111111111111111111111111111111111111112",
    "USDT": "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",
}

ASSET_COINGECKO: dict[str, str] = {
    "BTC": "coingecko:bitcoin",
    "ETH": "coingecko:ethereum",
    "SOL": "coingecko:solana",
    "BNB": "coingecko:binancecoin",
    "XRP": "coingecko:ripple",
    "ADA": "coingecko:cardano",
    "AVAX": "coingecko:avalanche-2",
    "DOT": "coingecko:polkadot",
    "LINK": "coingecko:chainlink",
    "UNI": "coingecko:uniswap",
    "ATOM": "coingecko:cosmos",
    "NEAR": "coingecko:near",
    "APT": "coingecko:aptos",
    "ARB": "coingecko:arbitrum",
    "OP": "coingecko:optimism",
    "SUI": "coingecko:sui",
    "SEI": "coingecko:sei-network",
    "INJ": "coingecko:injective-protocol",
    "TIA": "coingecko:celestia",
    "FIL": "coingecko:filecoin",
    "DOGE": "coingecko:dogecoin",
    "LTC": "coingecko:litecoin",
}


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _synthetic_book(mid: float) -> tuple[list[list[float]], list[list[float]]]:
    spread = max(mid * 0.001, 0.05)
    return (
        [[round(mid - spread, 8), 2.0]],
        [[round(mid + spread, 8), 2.0]],
    )


async def _fetch_json(
    session: aiohttp.ClientSession,
    url: str,
    *,
    method: str = "GET",
    json_body: dict | None = None,
    params: dict | None = None,
) -> Any:
    if method == "POST":
        async with session.post(url, json=json_body) as resp:
            resp.raise_for_status()
            return await resp.json()
    async with session.get(url, params=params) as resp:
        resp.raise_for_status()
        return await resp.json()


async def _defillama_price(session: aiohttp.ClientSession, asset: str) -> float:
    key = ASSET_COINGECKO.get(asset.upper())
    if not key:
        raise ValueError(f"No DeFiLlama key for {asset}")
    url = f"https://coins.llama.fi/prices/current/{key}"
    payload = await _fetch_json(session, url)
    coins = payload.get("coins") or {}
    row = coins.get(key) or {}
    price = float(row.get("price") or 0)
    if price <= 0:
        raise ValueError(f"DeFiLlama price unavailable for {asset}")
    return price


async def _jupiter_price(session: aiohttp.ClientSession, asset: str) -> float:
    mint = SOLANA_MINTS.get(asset.upper())
    if not mint:
        return await _defillama_price(session, asset)
    for base in ("https://lite-api.jup.ag/price/v3", "https://api.jup.ag/price/v3"):
        try:
            payload = await _fetch_json(session, base, params={"ids": mint})
            row = payload.get(mint) or {}
            if isinstance(row, dict):
                price = float(row.get("usdPrice") or row.get("price") or 0)
                if price > 0:
                    return price
        except (aiohttp.ClientError, TypeError, ValueError):
            continue
    return await _defillama_price(session, asset)


async def _raydium_price(session: aiohttp.ClientSession, asset: str) -> float:
    mint = SOLANA_MINTS.get(asset.upper())
    if not mint:
        return await _defillama_price(session, asset)
    url = "https://api-v3.raydium.io/mint/price"
    payload = await _fetch_json(session, url, params={"mints": mint})
    data = payload.get("data") or payload
    if isinstance(data, dict):
        price = float(data.get(mint) or data.get("price") or 0)
        if price > 0:
            return price
    return await _jupiter_price(session, asset)


async def _orca_price(session: aiohttp.ClientSession, asset: str) -> float:
    return await _jupiter_price(session, asset)


async def _thorchain_price(session: aiohttp.ClientSession, asset: str) -> float:
    asset = asset.upper()
    try:
        if asset in {"BTC", "ETH", "BNB", "AVAX", "ATOM", "LTC", "BCH", "DOGE"}:
            url = "https://midgard.ninerealms.com/v2/pools"
            payload = await _fetch_json(session, url)
            for pool in payload:
                if pool.get("status") != "available":
                    continue
                asset_pool = str(pool.get("asset") or "")
                if asset_pool.startswith(f"{asset}."):
                    price_rune = float(pool.get("assetPrice") or 0)
                    if price_rune > 0:
                        return await _defillama_price(session, asset)
    except (aiohttp.ClientError, TypeError, ValueError, OSError):
        pass
    return await _defillama_price(session, asset)


async def _osmosis_price(session: aiohttp.ClientSession, asset: str) -> float:
    return await _defillama_price(session, asset)


async def _fetch_dex_mid(
    session: aiohttp.ClientSession,
    exchange_id: str,
    asset: str,
) -> float:
    ex = exchange_id.lower()
    if ex in {"jupiter", "jupiter_perps"}:
        return await _jupiter_price(session, asset)
    if ex == "raydium":
        return await _raydium_price(session, asset)
    if ex == "orca":
        return await _orca_price(session, asset)
    if ex == "thorchain":
        return await _thorchain_price(session, asset)
    if ex == "osmosis":
        return await _osmosis_price(session, asset)
    # EVM / multi-chain DEX — DeFiLlama USD (chain-agnostic pool price)
    return await _defillama_price(session, asset)


async def fetch_dex_market(
    session: aiohttp.ClientSession | None,
    symbol: str,
    market_type: MarketType,
    *,
    exchange_id: str,
) -> tuple[Any, Any]:
    from aggregator import OrderBookSnapshot, TickerSnapshot

    if market_type == "perpetual":
        raise ValueError(f"DEX venue is spot-only | exchange={exchange_id}")

    asset = symbol.split("/")[0].upper()
    timeout = aiohttp.ClientTimeout(total=25)
    close_session = session is None
    if session is None:
        session = aiohttp.ClientSession(timeout=timeout)

    try:
        price = await _fetch_dex_mid(session, exchange_id, asset)
        bids, asks = _synthetic_book(price)
        return (
            TickerSnapshot(
                exchange=exchange_id,
                symbol=symbol,
                price=price,
                volume=0.0,
                market_type="spot",
            ),
            OrderBookSnapshot(
                exchange=exchange_id,
                symbol=symbol,
                bids=bids,
                asks=asks,
                market_type="spot",
            ),
        )
    finally:
        if close_session:
            await session.close()


def make_market_fetcher(exchange_id: str) -> Callable[..., Any]:
    async def _fetch(sess: Any, symbol: str, market_type: MarketType) -> tuple[Any, Any]:
        return await fetch_dex_market(sess, symbol, market_type, exchange_id=exchange_id)

    return _fetch


def build_dex_market_fetchers() -> dict[str, Callable[..., Any]]:
    return {venue_id: make_market_fetcher(venue_id) for venue_id in DEX_VENUES}


def symbols_for_dex(spot_symbols: list[str]) -> list[str]:
    limit = max(5, int(getattr(config, "DEX_SYMBOL_LIMIT", 15)))
    core = set(config.WHITELIST_ASSETS)
    core_syms = [s for s in spot_symbols if s.split("/")[0] in core]
    rest = [s for s in spot_symbols if s.split("/")[0] not in core]
    return core_syms + rest[: max(0, limit - len(core_syms))]


async def probe_dex_venues(sample_symbol: str = "BTC/USDT") -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    for venue_id in sorted(DEX_VENUES):
        row = {"exchange": venue_id, "ok": False}
        try:
            ticker, _book = await fetch_dex_market(None, sample_symbol, "spot", exchange_id=venue_id)
            row["ok"] = True
            row["price"] = ticker.price
        except Exception as exc:
            row["error"] = str(exc)[:180]
        results.append(row)
    ok_count = sum(1 for row in results if row["ok"])
    return {
        "phase": "C",
        "sample_symbol": sample_symbol,
        "total": len(DEX_VENUES),
        "ok": ok_count,
        "failed": len(DEX_VENUES) - ok_count,
        "results": results,
    }
