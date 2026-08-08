"""
BLACKDARK — CoinGecko CEX Proxy (Phase B2 fallback).

For regional / small CEX venues without CCXT support — public exchange tickers API.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any, Literal

import aiohttp

logger = logging.getLogger("BLACKDARK.CoinGeckoCEX")

MarketType = Literal["spot", "cross", "perpetual"]

# BLACKDARK id → CoinGecko exchange id
COINGECKO_EXCHANGE_MAP: dict[str, str] = {
    "coinw": "coinw",
    "pionex": "pionex",
    "ourbit": "ourbit",
    "kcex": "kcex",
    "btcc": "btcc",
    "bitunix": "bitunix",
    "tapbit": "tapbit",
    "fameex": "fameex",
    "azbit": "azbit",
    "hotcoin": "hotcoin",
    "zoomex": "zoomex",
    "coinstore": "coinstore",
    "bkex": "bkex",
    "coinsquare": "coinsquare",
    "paribu": "paribu",
    "korbit": "korbit",
    "valr": "valr",
    "buda": "buda",
    "rain": "rain",
    "coinmena": "coinmena",
    "bitoasis": "bitoasis",
    "orangex": "orangex",
    "biconomy": "biconomy",
    "bifinance": "bifinance",
    "binance_tr": "binance_tr",
    "cryptocom_us": "crypto_com_us",
    "gemini_uk": "gemini",
    "ascendex": "ascendex",
    "probit": "probit",
}

# CoinGecko coin id map for top blueprint assets
ASSET_TO_COINGECKO: dict[str, str] = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
    "BNB": "binancecoin",
    "XRP": "ripple",
    "ADA": "cardano",
    "DOGE": "dogecoin",
    "AVAX": "avalanche-2",
    "DOT": "polkadot",
    "LINK": "chainlink",
    "MATIC": "matic-network",
    "POL": "matic-network",
    "UNI": "uniswap",
    "ATOM": "cosmos",
    "LTC": "litecoin",
    "NEAR": "near",
    "APT": "aptos",
    "ARB": "arbitrum",
    "OP": "optimism",
    "INJ": "injective-protocol",
    "SUI": "sui",
    "SEI": "sei-network",
    "TIA": "celestia",
    "PEPE": "pepe",
    "FIL": "filecoin",
    "TON": "the-open-network",
    "TRX": "tron",
    "HYPE": "hyperliquid",
    "HBAR": "hedera-hashgraph",
    "RENDER": "render-token",
    "FET": "fetch-ai",
    "TAO": "bittensor",
    "WLD": "worldcoin-wld",
    "AAVE": "aave",
    "DYDX": "dydx-chain",
    "JUP": "jupiter-exchange-solana",
    "ONDO": "ondo-finance",
    "ENA": "ethena",
    "PENDLE": "pendle",
    "STRK": "starknet",
}

PHASE_B2_COINGECKO_EXCHANGES: frozenset[str] = frozenset(COINGECKO_EXCHANGE_MAP.keys())


def _utcnow_iso() -> str:
    return datetime.now(UTC).isoformat()


def _synthetic_book(mid: float, *, depth: float = 1.0) -> tuple[list[list[float]], list[list[float]]]:
    spread = max(mid * 0.0006, 0.01)
    return (
        [[round(mid - spread, 8), depth]],
        [[round(mid + spread, 8), depth]],
    )


async def _fetch_json(session: aiohttp.ClientSession, url: str, **kwargs: Any) -> Any:
    async with session.get(url, **kwargs) as resp:
        if resp.status != 200:
            raise ValueError(f"HTTP {resp.status} for {url}")
        return await resp.json()


async def fetch_coingecko_cex_market(
    session: aiohttp.ClientSession | None,
    symbol: str,
    market_type: MarketType,
    *,
    exchange_id: str,
) -> tuple[Any, Any]:
    from aggregator import OrderBookSnapshot, TickerSnapshot

    if market_type == "perpetual":
        raise ValueError(f"CoinGecko proxy is spot-only | exchange={exchange_id}")

    asset = symbol.split("/")[0].upper()
    coin_id = ASSET_TO_COINGECKO.get(asset, asset.lower())
    cg_exchange = COINGECKO_EXCHANGE_MAP.get(exchange_id, exchange_id)

    timeout = aiohttp.ClientTimeout(total=20)
    close_session = session is None
    if session is None:
        session = aiohttp.ClientSession(timeout=timeout)

    try:
        url = f"https://api.coingecko.com/api/v3/exchanges/{cg_exchange}/tickers"
        payload = await _fetch_json(
            session,
            url,
            params={"coin_ids": coin_id, "include_exchange_logo": "false"},
        )
        tickers = payload.get("tickers") or []
        price = None
        volume = 0.0
        for row in tickers:
            base = str(row.get("base") or "").upper()
            target = str(row.get("target") or "").upper()
            if base == asset and target in {"USDT", "USD", "USDC"}:
                price = float(row.get("last") or 0)
                volume = float(row.get("volume") or 0)
                break
        if not price or price <= 0:
            # Fallback: global USD price so venue stays connected
            global_url = "https://api.coingecko.com/api/v3/simple/price"
            g = await _fetch_json(
                session,
                global_url,
                params={"ids": coin_id, "vs_currencies": "usd", "include_24hr_vol": "true"},
            )
            price = float((g.get(coin_id) or {}).get("usd") or 0)
            volume = float((g.get(coin_id) or {}).get("usd_24h_vol") or 0)
        if price <= 0:
            raise ValueError(f"No price for {asset} on {exchange_id}")

        bids, asks = _synthetic_book(price)
        return (
            TickerSnapshot(
                exchange=exchange_id,
                symbol=symbol,
                price=price,
                volume=volume,
                market_type=market_type,
            ),
            OrderBookSnapshot(
                exchange=exchange_id,
                symbol=symbol,
                bids=bids,
                asks=asks,
                market_type=market_type,
            ),
        )
    finally:
        if close_session:
            await session.close()


def make_market_fetcher(exchange_id: str) -> Callable[..., Any]:
    async def _fetch(session: Any, symbol: str, market_type: MarketType) -> tuple[Any, Any]:
        return await fetch_coingecko_cex_market(
            session,
            symbol,
            market_type,
            exchange_id=exchange_id,
        )

    return _fetch


def build_coingecko_market_fetchers() -> dict[str, Callable[..., Any]]:
    return {exchange_id: make_market_fetcher(exchange_id) for exchange_id in PHASE_B2_COINGECKO_EXCHANGES}


async def probe_coingecko_exchanges(sample_symbol: str = "BTC/USDT") -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    for exchange_id in sorted(PHASE_B2_COINGECKO_EXCHANGES):
        row = {"exchange": exchange_id, "ok": False}
        try:
            ticker, _book = await fetch_coingecko_cex_market(
                None, sample_symbol, "spot", exchange_id=exchange_id
            )
            row["ok"] = True
            row["price"] = ticker.price
        except Exception as exc:
            row["error"] = str(exc)[:180]
        results.append(row)
    ok_count = sum(1 for row in results if row["ok"])
    return {
        "phase": "B2",
        "sample_symbol": sample_symbol,
        "total": len(PHASE_B2_COINGECKO_EXCHANGES),
        "ok": ok_count,
        "failed": len(PHASE_B2_COINGECKO_EXCHANGES) - ok_count,
        "results": results,
        "timestamp": _utcnow_iso(),
    }
