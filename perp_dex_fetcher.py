"""
BLACKDARK — Perp DEX Market Fetcher (Phase D).

Dedicated APIs for on-chain perpetual venues (Hyperliquid, dYdX, GMX, …).
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any, Literal

import aiohttp

import config

logger = logging.getLogger("BLACKDARK.PerpDEXFetcher")

MarketType = Literal["spot", "cross", "perpetual"]

PERP_DEX_VENUES: frozenset[str] = frozenset(
    {
        "hyperliquid",
        "dydx",
        "gmx",
        "apex",
        "gains",
        "kwenta",
        "drift",
        "mux",
        "synthetix",
        "jupiter_perps",
    }
)

# Map blueprint asset → venue symbol suffix
PERP_SYMBOLS: dict[str, str] = {
    "BTC": "BTC",
    "ETH": "ETH",
    "SOL": "SOL",
    "BNB": "BNB",
    "XRP": "XRP",
    "ADA": "ADA",
    "AVAX": "AVAX",
    "DOT": "DOT",
    "LINK": "LINK",
    "UNI": "UNI",
    "ATOM": "ATOM",
    "LTC": "LTC",
    "NEAR": "NEAR",
    "APT": "APT",
    "ARB": "ARB",
    "OP": "OP",
    "INJ": "INJ",
    "SUI": "SUI",
    "SEI": "SEI",
    "TIA": "TIA",
    "FIL": "FIL",
    "DOGE": "DOGE",
    "DYDX": "DYDX",
}


def _utcnow_iso() -> str:
    return datetime.now(UTC).isoformat()


def _synthetic_book(mid: float) -> tuple[list[list[float]], list[list[float]]]:
    spread = max(mid * 0.0008, 0.05)
    return (
        [[round(mid - spread, 8), 3.0]],
        [[round(mid + spread, 8), 3.0]],
    )


async def _fetch_json(
    session: aiohttp.ClientSession,
    url: str,
    *,
    method: str = "GET",
    json_body: dict | None = None,
) -> Any:
    if method == "POST":
        async with session.post(url, json=json_body) as resp:
            resp.raise_for_status()
            return await resp.json()
    async with session.get(url) as resp:
        resp.raise_for_status()
        return await resp.json()


async def _hyperliquid_mid(session: aiohttp.ClientSession, asset: str) -> tuple[float, float]:
    payload = await _fetch_json(
        session,
        "https://api.hyperliquid.xyz/info",
        method="POST",
        json_body={"type": "allMids"},
    )
    sym = PERP_SYMBOLS.get(asset.upper(), asset.upper())
    price = float(payload.get(sym) or 0)
    if price <= 0:
        raise ValueError(f"Hyperliquid mid missing for {asset}")
    funding_payload = await _fetch_json(
        session,
        "https://api.hyperliquid.xyz/info",
        method="POST",
        json_body={"type": "metaAndAssetCtxs"},
    )
    funding_rate = 0.0
    try:
        contexts = funding_payload[1]
        universe = funding_payload[0].get("universe") or []
        idx = next(i for i, u in enumerate(universe) if u.get("name") == sym)
        funding_rate = float(contexts[idx].get("funding") or 0)
    except (StopIteration, IndexError, TypeError, ValueError):
        pass
    return price, funding_rate


async def _dydx_mid(session: aiohttp.ClientSession, asset: str) -> tuple[float, float]:
    sym = PERP_SYMBOLS.get(asset.upper(), asset.upper())
    url = "https://indexer.dydx.trade/v4/perpetualMarkets"
    payload = await _fetch_json(session, url)
    markets = payload.get("markets") or {}
    row = markets.get(f"{sym}-USD") or markets.get(f"{sym}-USDT") or {}
    price = float(row.get("oraclePrice") or row.get("price") or 0)
    funding = float(row.get("nextFundingRate") or 0)
    if price <= 0:
        raise ValueError(f"dYdX price missing for {asset}")
    return price, funding


def _gmx_row_price(row: dict[str, Any], symbol: str) -> float | None:
    if str(row.get("tokenSymbol") or "").upper() != symbol:
        return None
    price = float(row.get("minPrice") or row.get("maxPrice") or 0) / 1e30
    if price <= 0:
        price = float(row.get("price") or 0)
    return price if price > 0 else None


async def _gmx_mid(session: aiohttp.ClientSession, asset: str) -> tuple[float, float]:
    sym = PERP_SYMBOLS.get(asset.upper(), asset.upper())
    for base in (
        "https://arbitrum-api.gmxinfra.io/prices/tickers",
        "https://avalanche-api.gmxinfra.io/prices/tickers",
    ):
        try:
            rows = await _fetch_json(session, base)
            for row in rows:
                price = _gmx_row_price(row, sym)
                if price is not None:
                    return price, 0.0
        except (aiohttp.ClientError, TypeError, ValueError):
            continue
    raise ValueError(f"GMX price missing for {asset}")


async def _drift_mid(session: aiohttp.ClientSession, asset: str) -> tuple[float, float]:
    # Drift mainnet API — market list
    # Fallback: use Jupiter perp or defillama
    from dex_fetcher import _defillama_price

    price = await _defillama_price(session, asset)
    return price, 0.0


async def _generic_perp_mid(session: aiohttp.ClientSession, asset: str) -> tuple[float, float]:
    from dex_fetcher import _defillama_price

    return await _defillama_price(session, asset), 0.0


async def _fetch_perp_mid(
    session: aiohttp.ClientSession,
    exchange_id: str,
    asset: str,
) -> tuple[float, float]:
    ex = exchange_id.lower()
    if ex == "hyperliquid":
        return await _hyperliquid_mid(session, asset)
    if ex == "dydx":
        return await _dydx_mid(session, asset)
    if ex == "gmx":
        return await _gmx_mid(session, asset)
    if ex == "drift":
        return await _drift_mid(session, asset)
    if ex == "jupiter_perps":
        from dex_fetcher import _jupiter_price

        return await _jupiter_price(session, asset), 0.0
    return await _generic_perp_mid(session, asset)


async def fetch_perp_dex_market(
    session: aiohttp.ClientSession | None,
    symbol: str,
    market_type: MarketType,
    *,
    exchange_id: str,
) -> tuple[Any, Any]:
    from aggregator import OrderBookSnapshot, TickerSnapshot

    asset = symbol.split("/")[0].upper()
    timeout = aiohttp.ClientTimeout(total=25)
    close_session = session is None
    if session is None:
        session = aiohttp.ClientSession(timeout=timeout)

    try:
        price, _funding = await _fetch_perp_mid(session, exchange_id, asset)
        bids, asks = _synthetic_book(price)
        mtype: MarketType = "perpetual" if market_type == "perpetual" else "spot"
        return (
            TickerSnapshot(
                exchange=exchange_id,
                symbol=symbol,
                price=price,
                volume=0.0,
                market_type=mtype,
            ),
            OrderBookSnapshot(
                exchange=exchange_id,
                symbol=symbol,
                bids=bids,
                asks=asks,
                market_type=mtype,
            ),
        )
    finally:
        if close_session:
            await session.close()


async def fetch_perp_dex_funding(
    session: aiohttp.ClientSession | None,
    symbol: str,
    *,
    exchange_id: str,
) -> Any:
    from aggregator import FundingSnapshot

    asset = symbol.split("/")[0].upper()
    timeout = aiohttp.ClientTimeout(total=25)
    close_session = session is None
    if session is None:
        session = aiohttp.ClientSession(timeout=timeout)
    try:
        _price, funding_rate = await _fetch_perp_mid(session, exchange_id, asset)
        return FundingSnapshot(
            exchange=exchange_id,
            symbol=symbol,
            funding_rate=funding_rate,
            next_funding_time=None,
        )
    finally:
        if close_session:
            await session.close()


def make_market_fetcher(exchange_id: str) -> Callable[..., Any]:
    async def _fetch(sess: Any, symbol: str, market_type: MarketType) -> tuple[Any, Any]:
        return await fetch_perp_dex_market(sess, symbol, market_type, exchange_id=exchange_id)

    return _fetch


def make_funding_fetcher(exchange_id: str) -> Callable[..., Any]:
    async def _fetch(sess: Any, symbol: str) -> Any:
        return await fetch_perp_dex_funding(sess, symbol, exchange_id=exchange_id)

    return _fetch


def build_perp_market_fetchers() -> dict[str, Callable[..., Any]]:
    return {venue_id: make_market_fetcher(venue_id) for venue_id in PERP_DEX_VENUES}


def build_perp_funding_fetchers() -> dict[str, Callable[..., Any]]:
    return {venue_id: make_funding_fetcher(venue_id) for venue_id in PERP_DEX_VENUES}


def symbols_for_perp(spot_symbols: list[str]) -> list[str]:
    limit = max(5, int(getattr(config, "PERP_DEX_SYMBOL_LIMIT", 15)))
    core = set(config.WHITELIST_ASSETS)
    core_syms = [s for s in spot_symbols if s.split("/")[0] in core]
    rest = [s for s in spot_symbols if s.split("/")[0] not in core]
    return core_syms + rest[: max(0, limit - len(core_syms))]


async def probe_perp_dex_venues(sample_symbol: str = "BTC/USDT") -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    for venue_id in sorted(PERP_DEX_VENUES):
        row = {"exchange": venue_id, "ok": False}
        try:
            ticker, _book = await fetch_perp_dex_market(
                None, sample_symbol, "perpetual", exchange_id=venue_id
            )
            row["ok"] = True
            row["price"] = ticker.price
        except Exception as exc:
            row["error"] = str(exc)[:180]
        results.append(row)
    ok_count = sum(1 for row in results if row["ok"])
    return {
        "phase": "D",
        "sample_symbol": sample_symbol,
        "total": len(PERP_DEX_VENUES),
        "ok": ok_count,
        "failed": len(PERP_DEX_VENUES) - ok_count,
        "results": results,
    }
