"""
BLACKDARK — CoinGecko CEX Proxy (Phase B2 fallback).

For regional / small CEX venues without CCXT support — public exchange tickers API.
Honest synthetic_mid only (1-level). Rate-limited with global mid failover on 404/429.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any, Literal

import aiohttp

logger = logging.getLogger("BLACKDARK.CoinGeckoCEX")

MarketType = Literal["spot", "cross", "perpetual"]

# BLACKDARK id → CoinGecko exchange id (validated against /exchanges/list where possible)
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
    "hotcoin": "hotcoin_global",
    "zoomex": "zoomex",
    "coinstore": "coinstore",
    "bkex": "bkex",
    "coinsquare": "coinsquare",
    "paribu": "paribu",
    # korbit/valr/buda removed — served by native_regional_cex_fetcher (real L2).
    "rain": "rain",
    "coinmena": "coinmena",
    "bitoasis": "bitoasis",
    "orangex": "orangex",
    "biconomy": "biconomy",
    "bifinance": "bifinance",
    "binance_tr": "binance_tr",
    "cryptocom_us": "crypto_com",
    "gemini_uk": "gemini",
    "ascendex": "ascendex",
    "probit": "probit",
    "tokocrypto": "toko_crypto",
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

# Shared public API throttle (CoinGecko free tier ~10–30 rpm).
_CG_LOCK = asyncio.Lock()
_CG_NEXT_OK_AT = 0.0
_CG_MIN_INTERVAL_SEC = 1.35


def _utcnow_iso() -> str:
    return datetime.now(UTC).isoformat()


def _synthetic_book(mid: float, *, depth: float = 1.0) -> tuple[list[list[float]], list[list[float]]]:
    spread = max(mid * 0.0006, 0.01)
    return (
        [[round(mid - spread, 8), depth]],
        [[round(mid + spread, 8), depth]],
    )


async def _throttle() -> None:
    global _CG_NEXT_OK_AT
    async with _CG_LOCK:
        now = time.monotonic()
        wait = _CG_NEXT_OK_AT - now
        if wait > 0:
            await asyncio.sleep(wait)
        _CG_NEXT_OK_AT = time.monotonic() + _CG_MIN_INTERVAL_SEC


async def _fetch_json(
    session: aiohttp.ClientSession,
    url: str,
    *,
    retries: int = 3,
    **kwargs: Any,
) -> Any:
    last_status = 0
    for attempt in range(max(1, retries)):
        await _throttle()
        async with session.get(url, **kwargs) as resp:
            last_status = resp.status
            if resp.status == 200:
                return await resp.json()
            if resp.status == 429:
                # Exponential backoff under rate limit.
                await asyncio.sleep(1.5 * (2**attempt))
                continue
            if resp.status == 404:
                raise ValueError(f"HTTP 404 for {url}")
            body = (await resp.text())[:120]
            raise ValueError(f"HTTP {resp.status} for {url}: {body}")
    raise ValueError(f"HTTP {last_status} for {url}")


def _coingecko_exchange_id(exchange_id: str) -> str:
    mapped_ex = COINGECKO_EXCHANGE_MAP.get(exchange_id)
    if mapped_ex is not None:
        return mapped_ex  # constant allowlist entry
    cg_exchange = str(exchange_id)
    if not cg_exchange.replace("_", "").isalnum():
        raise ValueError(f"Unsafe CoinGecko exchange id | exchange={exchange_id}")
    return cg_exchange


def _ticker_price_volume(tickers: list[Any], asset: str) -> tuple[float | None, float]:
    for row in tickers:
        base = str(row.get("base") or "").upper()
        target = str(row.get("target") or "").upper()
        if base == asset and target in {"USDT", "USD", "USDC"}:
            return float(row.get("last") or 0), float(row.get("volume") or 0)
    return None, 0.0


async def _global_price_volume(
    session: aiohttp.ClientSession,
    coin_id: str,
) -> tuple[float, float]:
    global_url = "https://api.coingecko.com/api/v3/simple/price"
    payload = await _fetch_json(
        session,
        global_url,
        params={"ids": coin_id, "vs_currencies": "usd", "include_24hr_vol": "true"},
        retries=4,
    )
    coin = payload.get(coin_id) or {}
    return float(coin.get("usd") or 0), float(coin.get("usd_24h_vol") or 0)


def _market_snapshots(
    *,
    exchange_id: str,
    symbol: str,
    price: float,
    volume: float,
    market_type: MarketType,
) -> tuple[Any, Any]:
    from aggregator import OrderBookSnapshot, TickerSnapshot

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


async def fetch_coingecko_cex_market(
    session: aiohttp.ClientSession | None,
    symbol: str,
    market_type: MarketType,
    *,
    exchange_id: str,
) -> tuple[Any, Any]:
    if market_type == "perpetual":
        raise ValueError(f"CoinGecko proxy is spot-only | exchange={exchange_id}")

    asset = symbol.split("/")[0].upper()
    coin_id = ASSET_TO_COINGECKO.get(asset, asset.lower())
    cg_exchange = _coingecko_exchange_id(exchange_id)

    timeout = aiohttp.ClientTimeout(total=20)
    close_session = session is None
    if session is None:
        session = aiohttp.ClientSession(timeout=timeout)

    try:
        price: float | None = None
        volume = 0.0
        try:
            url = f"https://api.coingecko.com/api/v3/exchanges/{cg_exchange}/tickers"
            payload = await _fetch_json(
                session,
                url,
                params={"coin_ids": coin_id, "include_exchange_logo": "false"},
                retries=3,
            )
            tickers = payload.get("tickers") or []
            price, volume = _ticker_price_volume(tickers, asset)
        except ValueError as exc:
            # Dead / renamed CG ids and rate-limit exhaustion → global mid (synthetic only).
            logger.info("coingecko_exchange_failover | %s | %s", exchange_id, exc)
            price = None

        if not price or price <= 0:
            price, volume = await _global_price_volume(session, coin_id)
        if price <= 0:
            raise ValueError(f"No price for {asset} on {exchange_id}")

        return _market_snapshots(
            exchange_id=exchange_id,
            symbol=symbol,
            price=price,
            volume=volume,
            market_type=market_type,
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
