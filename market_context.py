"""
BLACKDARK — Shared market / oracle context (decoupled from HTTP layer).

Used by dashboard, chat, voice, and SSE — no imports from dashboard.py.
"""

from __future__ import annotations

import json
import logging
import os
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any

import aiohttp

import config

# Sonar S1192: duplicated string literals
STR_NO_SIGNIFICANT_WHALE_ACTIVITY = 'No significant whale activity'
logger = logging.getLogger("BLACKDARK.MarketContext")

_HTTP_TIMEOUT = aiohttp.ClientTimeout(total=12)
_HTTP_HEADERS = {
    "User-Agent": "BLACKDARK/1.0 (+https://blackdark.io)",
    "Accept": "application/json",
}


def _coingecko_headers() -> dict[str, str]:
    headers = dict(_HTTP_HEADERS)
    cg_key = os.getenv("COINGECKO_API_KEY", "").strip()
    if cg_key:
        headers["x-cg-demo-api-key"] = cg_key
        headers["x-cg-pro-api-key"] = cg_key
    return headers


async def _rest_get(
    url: str,
    *,
    params: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
    session: aiohttp.ClientSession | None = None,
) -> Any | None:
    try:
        if session is None:
            from aggregator import get_shared_http_session

            session = get_shared_http_session()
        async with session.get(url, params=params, headers=headers) as resp:
            if resp.status != 200:
                logger.debug(
                    "REST price fetch non-200 | url=%s status=%s",
                    str(url).replace("\r", " ").replace("\n", " "),
                    str(resp.status).replace("\r", " ").replace("\n", " "),
                )
                return None
            return await resp.json()
    except (aiohttp.ClientError, TypeError, ValueError):
        return None


def sector_for_asset(asset: str) -> str:
    return config.SECTOR_MAP.get(asset.upper(), "Other")


def normalize_oracle_symbol(symbol: str) -> tuple[str, str]:
    from blackdark.canonical.resolver import resolve_symbol

    asset = resolve_symbol(symbol)
    pair = f"{asset}USDT" if not asset.endswith("USDT") else asset
    if "/" in symbol or symbol.upper().endswith("USDT"):
        cleaned = symbol.upper().strip().replace("/", "").replace("-", "")
        if cleaned.endswith("USDT"):
            pair = cleaned
            asset = resolve_symbol(cleaned[:-4])
    return asset, pair


# CoinGecko IDs for REST fallback when Binance is geo-blocked (common on cloud hosts).
_COINGECKO_IDS: dict[str, str] = {
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
    "POL": "polygon-ecosystem-token",
    "LTC": "litecoin",
    "TRX": "tron",
    "ATOM": "cosmos",
    "UNI": "uniswap",
    "NEAR": "near",
    "APT": "aptos",
    "ARB": "arbitrum",
    "OP": "optimism",
    "SUI": "sui",
    "PEPE": "pepe",
    "SHIB": "shiba-inu",
    "BCH": "bitcoin-cash",
    "FIL": "filecoin",
    "ICP": "internet-computer",
    "ETC": "ethereum-classic",
    "HBAR": "hedera-hashgraph",
    "VET": "vechain",
    "ALGO": "algorand",
    "FTM": "fantom",
    "SAND": "the-sandbox",
    "MANA": "decentraland",
    "AAVE": "aave",
    "MKR": "maker",
    "CRV": "curve-dao-token",
    "RUNE": "thorchain",
    "INJ": "injective-protocol",
    "SEI": "sei-network",
    "TIA": "celestia",
    "STX": "blockstack",
    "IMX": "immutable-x",
    "GRT": "the-graph",
    "RENDER": "render-token",
    "FET": "fetch-ai",
    "WIF": "dogwifcoin",
    "BONK": "bonk",
    "FLOKI": "floki",
}


def _binance_ticker_from_json(data: dict[str, Any], *, source: str) -> dict[str, Any]:
    return {
        "price": float(data["lastPrice"]),
        "change_24h": float(data["priceChangePercent"]),
        "volume": float(data["volume"]),
        "quote_volume": float(data.get("quoteVolume") or 0),
        "source": source,
    }


# Kraken uses non-standard pair names for some assets.
_KRAKEN_PAIRS: dict[str, str] = {
    "BTC": "XBTUSD",
    "DOGE": "XDGUSD",
    "ETH": "ETHUSD",
    "SOL": "SOLUSD",
    "XRP": "XRPUSD",
    "ADA": "ADAUSD",
    "DOT": "DOTUSD",
    "LINK": "LINKUSD",
    "LTC": "LTCUSD",
    "AVAX": "AVAXUSD",
    "ATOM": "ATOMUSD",
    "UNI": "UNIUSD",
    "NEAR": "NEARUSD",
    "APT": "APTUSD",
    "ARB": "ARBUSD",
    "OP": "OPUSD",
    "SUI": "SUIUSD",
    "PEPE": "PEPEUSD",
    "SHIB": "SHIBUSD",
}


async def _fetch_binance_host_ticker(
    pair: str,
    host: str,
    *,
    session: aiohttp.ClientSession | None = None,
) -> dict[str, Any] | None:
    url = f"https://{host}/api/v3/ticker/24hr"
    data = await _rest_get(url, params={"symbol": pair}, session=session)
    if not isinstance(data, dict):
        return None
    try:
        return _binance_ticker_from_json(data, source=f"binance:{host}")
    except (KeyError, TypeError, ValueError):
        return None


async def _fetch_coingecko_ticker(
    asset: str,
    *,
    session: aiohttp.ClientSession | None = None,
) -> dict[str, Any] | None:
    from blackdark.ingestion.coingecko_connector import fetch_coingecko_price

    row = await fetch_coingecko_price(asset)
    if not row.get("ok"):
        return None
    return {
        "price": float(row.get("price_usd") or 0),
        "change_24h": float(row.get("change_24h_pct") or 0),
        "volume": 0.0,
        "quote_volume": 0.0,
        "source": row.get("source") or "coingecko",
        "canonical_id": row.get("canonical_id"),
        "fallback": row.get("fallback"),
    }


async def _fetch_coinbase_ticker(
    asset: str,
    *,
    session: aiohttp.ClientSession | None = None,
) -> dict[str, Any] | None:
    url = f"https://api.coinbase.com/v2/prices/{asset.upper()}-USD/spot"
    payload = await _rest_get(url, session=session)
    if not isinstance(payload, dict):
        return None
    try:
        price = float((payload.get("data") or {}).get("amount") or 0)
        if price <= 0:
            return None
        return {
            "price": price,
            "change_24h": 0.0,
            "volume": 0.0,
            "quote_volume": 0.0,
            "source": "coinbase",
        }
    except (KeyError, TypeError, ValueError):
        return None


async def _fetch_kraken_ticker(
    asset: str,
    *,
    session: aiohttp.ClientSession | None = None,
) -> dict[str, Any] | None:
    pair = _KRAKEN_PAIRS.get(asset.upper(), f"{asset.upper()}USD")
    payload = await _rest_get(
        "https://api.kraken.com/0/public/Ticker",
        params={"pair": pair},
        session=session,
    )
    if not isinstance(payload, dict):
        return None
    try:
        result = payload.get("result") or {}
        if not result:
            return None
        row = next(iter(result.values()))
        price = float(row["c"][0])
        if price <= 0:
            return None
        open_today = float(row.get("o") or price)
        change = ((price - open_today) / open_today * 100.0) if open_today else 0.0
        volume = float(row.get("v", [0, 0])[1])
        return {
            "price": price,
            "change_24h": change,
            "volume": volume,
            "quote_volume": 0.0,
            "source": "kraken",
        }
    except (KeyError, TypeError, ValueError, StopIteration):
        return None


async def _fetch_okx_ticker(
    asset: str,
    *,
    session: aiohttp.ClientSession | None = None,
) -> dict[str, Any] | None:
    payload = await _rest_get(
        "https://www.okx.com/api/v5/market/ticker",
        params={"instId": f"{asset.upper()}-USDT"},
        session=session,
    )
    if not isinstance(payload, dict) or str(payload.get("code")) != "0":
        return None
    try:
        row = (payload.get("data") or [{}])[0]
        price = float(row.get("last") or 0)
        if price <= 0:
            return None
        open24 = float(row.get("open24h") or price)
        change = ((price - open24) / open24 * 100.0) if open24 else 0.0
        volume = float(row.get("vol24h") or 0)
        quote_volume = float(row.get("volCcy24h") or 0)
        return {
            "price": price,
            "change_24h": change,
            "volume": volume,
            "quote_volume": quote_volume,
            "source": "okx",
        }
    except (KeyError, TypeError, ValueError, IndexError):
        return None


async def _fetch_bybit_ticker(
    asset: str,
    *,
    session: aiohttp.ClientSession | None = None,
) -> dict[str, Any] | None:
    payload = await _rest_get(
        "https://api.bybit.com/v5/market/tickers",
        params={"category": "spot", "symbol": f"{asset.upper()}USDT"},
        session=session,
    )
    if not isinstance(payload, dict):
        return None
    ret_code = payload.get("retCode")
    if ret_code is None or int(ret_code) != 0:
        return None
    try:
        rows = (payload.get("result") or {}).get("list") or []
        if not rows:
            return None
        row = rows[0]
        price = float(row.get("lastPrice") or 0)
        if price <= 0:
            return None
        change = float(row.get("price24hPcnt") or 0) * 100.0
        volume = float(row.get("volume24h") or 0)
        quote_volume = float(row.get("turnover24h") or 0)
        return {
            "price": price,
            "change_24h": change,
            "volume": volume,
            "quote_volume": quote_volume,
            "source": "bybit",
        }
    except (KeyError, TypeError, ValueError, IndexError):
        return None


async def _fetch_cryptocompare_ticker(
    asset: str,
    *,
    session: aiohttp.ClientSession | None = None,
) -> dict[str, Any] | None:
    payload = await _rest_get(
        "https://min-api.cryptocompare.com/data/pricemultifull",
        params={"fsyms": asset.upper(), "tsyms": "USD"},
        session=session,
    )
    if not isinstance(payload, dict):
        return None
    try:
        raw = payload.get("RAW") or {}
        row = (raw.get(asset.upper()) or {}).get("USD") or {}
        price = float(row.get("PRICE") or 0)
        if price <= 0:
            return None
        change = float(row.get("CHANGEPCT24HOUR") or 0)
        volume = float(row.get("VOLUME24HOUR") or 0)
        quote_volume = float(row.get("VOLUME24HOURTO") or 0)
        return {
            "price": price,
            "change_24h": change,
            "volume": volume,
            "quote_volume": quote_volume,
            "source": "cryptocompare",
        }
    except (KeyError, TypeError, ValueError):
        return None


_REST_PRICE_FALLBACKS: tuple[
    Callable[..., Awaitable[dict[str, Any] | None]],
    ...,
] = (
    _fetch_kraken_ticker,
    _fetch_okx_ticker,
    _fetch_bybit_ticker,
    _fetch_coingecko_ticker,
    _fetch_coinbase_ticker,
    _fetch_cryptocompare_ticker,
)


def _safe_asset_label(asset: str) -> str:
    allowed = {str(a).upper() for a in (getattr(config, "WHITELIST_ASSETS", None) or [])}
    asset_upper = str(asset).upper()
    return asset_upper if asset_upper in allowed else "other"


async def _ws_ticker_if_enabled(asset: str) -> dict[str, Any] | None:
    if not config.PRICE_FEED_WS_ONLY:
        return None
    from live_book_hub import get_live_books_if_fresh

    fresh = get_live_books_if_fresh()
    if not fresh:
        return None
    from ws_price_provider import get_ticker

    ws_row = await get_ticker(asset)
    if ws_row is not None:
        ws_row.setdefault("source", "websocket_live")
    return ws_row


async def _primary_rest_ticker(
    pair: str,
    session: aiohttp.ClientSession,
) -> dict[str, Any] | None:
    for host in ("api.binance.com", "data-api.binance.vision", "api.binance.us"):
        row = await _fetch_binance_host_ticker(pair, host, session=session)
        if row is not None:
            return row
    return None


def _log_price_fallback(asset: str, source: str) -> None:
    source_label = source if source.replace("_", "").isalnum() else "unknown"
    logger.info(
        "Price REST fallback | asset=%s source=%s",
        _safe_asset_label(asset).replace("\r", " ").replace("\n", " "),
        str(source_label).replace("\r", " ").replace("\n", " "),
    )


async def _fallback_rest_ticker(
    asset: str,
    session: aiohttp.ClientSession,
) -> dict[str, Any] | None:
    for fallback in _REST_PRICE_FALLBACKS:
        row = await fallback(asset, session=session)
        if row is None:
            continue
        _log_price_fallback(asset, str(row.get("source") or "unknown"))
        return row
    return None


async def fetch_binance_ticker(pair: str) -> dict | None:
    """Live spot ticker — WS when fresh, else multi-source REST (Railway/cloud safe)."""
    asset = pair.replace("USDT", "").upper()

    ws_row = await _ws_ticker_if_enabled(asset)
    if ws_row is not None:
        return ws_row

    from aggregator import get_shared_http_session

    session = get_shared_http_session()
    row = await _primary_rest_ticker(pair, session)
    if row is not None:
        return row
    row = await _fallback_rest_ticker(asset, session)
    if row is not None:
        return row

    logger.warning("All price sources failed | asset=%s", _safe_asset_label(asset).replace("\r", " ").replace("\n", " "))
    return None


async def _probe_binance_hosts(
    pair: str,
    session: aiohttp.ClientSession,
) -> dict[str, Any]:
    checks: dict[str, Any] = {}
    for host in ("api.binance.com", "data-api.binance.vision", "api.binance.us"):
        row = await _fetch_binance_host_ticker(pair, host, session=session)
        checks[host] = {"ok": row is not None, "source": row.get("source") if row else None}
    return checks


async def _probe_rest_fallbacks(
    asset: str,
    session: aiohttp.ClientSession,
) -> dict[str, Any]:
    checks: dict[str, Any] = {}
    for name, fetcher in (
        ("kraken", _fetch_kraken_ticker),
        ("okx", _fetch_okx_ticker),
        ("bybit", _fetch_bybit_ticker),
        ("coingecko", _fetch_coingecko_ticker),
        ("coinbase", _fetch_coinbase_ticker),
        ("cryptocompare", _fetch_cryptocompare_ticker),
    ):
        row = await fetcher(asset, session=session)
        checks[name] = {"ok": row is not None, "source": row.get("source") if row else None}
    return checks


async def probe_price_sources(symbol: str = "BTC") -> dict[str, Any]:
    """Ops diagnostic — which price APIs respond from this host (Railway DD)."""
    asset, pair = normalize_oracle_symbol(symbol)
    checks: dict[str, Any] = {}
    from aggregator import get_shared_http_session

    session = get_shared_http_session()
    checks.update(await _probe_binance_hosts(pair, session))
    checks.update(await _probe_rest_fallbacks(asset, session))
    resolved = await fetch_binance_ticker(pair)
    return {
        "symbol": asset,
        "pair": pair,
        "price_feed_ws_only": config.PRICE_FEED_WS_ONLY,
        "checks": checks,
        "resolved": resolved is not None,
        "resolved_source": (resolved or {}).get("source"),
        "resolved_price": (resolved or {}).get("price"),
        "timestamp": datetime.now(UTC).isoformat(),
    }


def _market_overview_item(row: dict[str, Any]) -> dict[str, Any] | None:
    symbol = row.get("symbol", "")
    if not symbol.endswith("USDT"):
        return None
    asset = symbol[:-4]
    if is_stablecoin(asset):
        return None
    try:
        quote_volume = float(row.get("quoteVolume") or 0)
        change = float(row.get("priceChangePercent") or 0)
        price = float(row.get("lastPrice") or 0)
    except (TypeError, ValueError):
        return None
    if quote_volume < 10_000_000:
        return None
    score = oracle_score(quote_volume, change)
    verdict, _ = oracle_verdict(score, asset, price)
    return {
        "symbol": asset,
        "price": price,
        "change_24h": change,
        "volume_24h": quote_volume,
        "score": score,
        "verdict": verdict,
        "sector": sector_for_asset(asset),
    }


def _prioritized_market_overview(
    by_symbol: dict[str, dict],
    all_candidates: list[dict],
    limit: int,
) -> list[dict]:
    priority: list[dict] = []
    seen: set[str] = set()
    for asset in config.tracked_asset_list():
        if asset in by_symbol:
            priority.append(by_symbol[asset])
            seen.add(asset)
    for candidate in all_candidates:
        if len(priority) >= limit:
            break
        if candidate["symbol"] in seen:
            continue
        priority.append(candidate)
        seen.add(candidate["symbol"])
    return priority[:limit]


_BINANCE_REST_HOSTS = ("api.binance.com", "data-api.binance.vision", "api.binance.us")


async def _fetch_binance_24hr_rows(
    session: aiohttp.ClientSession,
    host: str,
) -> list[dict[str, Any]] | None:
    url = f"https://{host}/api/v3/ticker/24hr"
    try:
        async with session.get(url) as resp:
            if resp.status != 200:
                return None
            rows = await resp.json()
    except (aiohttp.ClientError, TypeError, ValueError):
        return None
    return rows if isinstance(rows, list) else None


def _overview_from_24hr_rows(rows: list[dict[str, Any]], limit: int) -> list[dict]:
    by_symbol: dict[str, dict] = {}
    all_candidates: list[dict] = []
    for row in rows:
        item = _market_overview_item(row)
        if item is None:
            continue
        by_symbol[item["symbol"]] = item
        all_candidates.append(item)
    all_candidates.sort(key=lambda x: x["volume_24h"], reverse=True)
    return _prioritized_market_overview(by_symbol, all_candidates, limit)


async def _overview_from_tracked_tickers(limit: int) -> list[dict]:
    """Last-resort radar: resolve each tracked asset via the multi-host ticker."""
    out: list[dict] = []
    for asset in config.tracked_asset_list()[: max(1, limit)]:
        row = await fetch_binance_ticker(f"{asset}USDT")
        if not row or not row.get("price"):
            continue
        price = float(row["price"])
        change = float(row.get("change_24h") or 0)
        quote_volume = float(row.get("quote_volume") or 0)
        score = oracle_score(quote_volume, change)
        verdict, _ = oracle_verdict(score, asset, price)
        out.append(
            {
                "symbol": asset,
                "price": price,
                "change_24h": change,
                "volume_24h": quote_volume,
                "score": score,
                "verdict": verdict,
                "sector": sector_for_asset(asset),
            }
        )
    return out


async def fetch_binance_market_overview_pack(limit: int | None = None) -> dict[str, Any]:
    """Radar pack with honest source. Never claims Binance Live when the book is empty."""
    if limit is None:
        limit = config.MARKET_RADAR_LIMIT
    if config.PRICE_FEED_WS_ONLY:
        from ws_price_provider import get_market_overview

        assets = await get_market_overview(limit)
        return {
            "assets": assets,
            "data_source": "websocket_live" if assets else "websocket_empty",
            "source_host": None,
        }

    from aggregator import get_shared_http_session

    session = get_shared_http_session()
    for host in _BINANCE_REST_HOSTS:
        rows = await _fetch_binance_24hr_rows(session, host)
        if not rows:
            continue
        assets = _overview_from_24hr_rows(rows, limit)
        if assets:
            return {
                "assets": assets,
                "data_source": f"binance:{host}",
                "source_host": host,
            }

    assets = await _overview_from_tracked_tickers(limit)
    return {
        "assets": assets,
        "data_source": "multi_source_ticker" if assets else "unavailable",
        "source_host": None,
    }


async def fetch_binance_market_overview(limit: int | None = None) -> list[dict]:
    """Tracked assets from WebSocket/Redis, then Binance host failover, then tickers."""
    pack = await fetch_binance_market_overview_pack(limit)
    return list(pack.get("assets") or [])


async def fetch_live_whale_signal(pair: str, price: float) -> str:
    """Detect large book activity from WebSocket feeds (no REST aggTrades)."""
    if config.PRICE_FEED_WS_ONLY:
        from ws_price_provider import get_whale_signal

        asset = pair.replace("USDT", "")
        return get_whale_signal(asset, price)
    if not pair.isalnum():
        return STR_NO_SIGNIFICANT_WHALE_ACTIVITY
    url = f"https://api.binance.com/api/v3/aggTrades?symbol={pair}&limit=200"
    threshold_usd = 75_000
    try:
        from aggregator import get_shared_http_session

        session = get_shared_http_session()
        async with session.get(url) as resp:
            if resp.status != 200:
                return STR_NO_SIGNIFICANT_WHALE_ACTIVITY
            trades = await resp.json()
    except (aiohttp.ClientError, TypeError, ValueError):
        return STR_NO_SIGNIFICANT_WHALE_ACTIVITY

    buy_blocks, sell_blocks, max_notional = _whale_trade_blocks(trades, threshold_usd)
    return _whale_trade_message(buy_blocks, sell_blocks, max_notional, threshold_usd)


def _whale_trade_blocks(trades: list[dict[str, Any]], threshold_usd: float) -> tuple[int, int, float]:
    buy_blocks = 0
    sell_blocks = 0
    max_notional = 0.0
    for trade in trades:
        notional = _trade_notional(trade)
        if notional < threshold_usd:
            continue
        max_notional = max(max_notional, notional)
        # m=true -> buyer is maker -> aggressive seller; m=false -> aggressive buyer
        if trade.get("m"):
            sell_blocks += 1
        else:
            buy_blocks += 1
    return buy_blocks, sell_blocks, max_notional


def _trade_notional(trade: dict[str, Any]) -> float:
    try:
        return float(trade["q"]) * float(trade["p"])
    except (KeyError, TypeError, ValueError):
        return 0.0


def _whale_trade_message(
    buy_blocks: int,
    sell_blocks: int,
    max_notional: float,
    threshold_usd: float,
) -> str:
    if buy_blocks >= 3 and buy_blocks > sell_blocks:
        return f"Whale accumulation detected — {buy_blocks} large buy blocks (max ${max_notional:,.0f})"
    if sell_blocks >= 3 and sell_blocks > buy_blocks:
        return f"Whale distribution detected — {sell_blocks} large sell blocks (max ${max_notional:,.0f})"
    if buy_blocks or sell_blocks:
        return f"Mixed whale activity — {buy_blocks} buys / {sell_blocks} sells above ${threshold_usd:,.0f}"
    return "No significant whale activity in recent trades"


def oracle_score(volume: float, change: float) -> int:
    score = 50
    if volume > 1_000_000_000:
        score += 20
    elif volume > 100_000_000:
        score += 15
    elif volume > 10_000_000:
        score += 10
    if 0 < change < 3:
        score += 20
    elif 3 <= change < 8:
        score += 15
    elif 8 <= change < 15:
        score += 5
    elif change >= 15:
        score -= 15
    elif -3 < change <= 0:
        score -= 5
    elif -8 < change <= -3:
        score -= 15
    elif change <= -8:
        score -= 25
    return max(0, min(100, score))


_STABLECOINS = frozenset(
    {"USDC", "USDT", "USD1", "DAI", "FDUSD", "USDE", "USDS", "TUSD", "BUSD", "EURC", "RLUSD", "USDG"}
)


def is_stablecoin(asset: str) -> bool:
    return asset.upper() in _STABLECOINS


def oracle_verdict(score: int, asset: str, price: float) -> tuple[str, str]:
    from regulatory_compliance_guard import compliant_verdict_description, to_public_verdict

    if is_stablecoin(asset):
        v = to_public_verdict("WAIT")
        return v, f"{asset} is a stablecoin — analytics only, not a trading opportunity (Score: {score}/100)"
    if score >= 75:
        return to_public_verdict("BUY"), compliant_verdict_description(asset, score, price, "BUY")
    if score >= 50:
        return to_public_verdict("WAIT"), compliant_verdict_description(asset, score, price, "WAIT")
    if score >= 30:
        return to_public_verdict("CAUTION"), compliant_verdict_description(asset, score, price, "CAUTION")
    return to_public_verdict("SELL"), compliant_verdict_description(asset, score, price, "SELL")


def oracle_sentiment(change: float) -> str:
    if change > 2:
        return "Bullish"
    if change < -2:
        return "Bearish"
    return "Neutral"


def fear_greed_index(change: float, quote_volume: float) -> tuple[int, str]:
    fg = min(100, max(0, int(50 + change * 2 + (quote_volume / 1e9) * 10)))
    if fg > 75:
        label = "Extreme Greed"
    elif fg > 55:
        label = "Greed"
    elif fg > 45:
        label = "Neutral"
    elif fg > 25:
        label = "Fear"
    else:
        label = "Extreme Fear"
    return fg, label


def oracle_confidence(score: int, change: float, quote_volume: float) -> int:
    return min(100, max(50, int(score * 0.8 + abs(change) * 2 + (quote_volume / 1e9) * 5)))


def risk_level(score: int) -> str:
    if score > 75:
        return "Low"
    if score > 55:
        return "Medium"
    if score > 40:
        return "High"
    return "Extreme"


def whale_alert_message(quote_volume: float, change: float) -> str:
    if quote_volume > 50_000_000:
        return "Whale accumulation detected — high volume inflow"
    if quote_volume > 10_000_000:
        return "Moderate whale interest"
    if change < -5:
        return "Whale distribution detected — large sell pressure"
    return STR_NO_SIGNIFICANT_WHALE_ACTIVITY


def oracle_action(score: int, price: float, support: float, resistance: float) -> str:
    from regulatory_compliance_guard import compliant_action_text

    return compliant_action_text(score, price, support, resistance)


def oracle_narrative(
    asset: str,
    change: float,
    quote_volume: float,
    score: int,
    sentiment: str,
    fear_greed: str,
    confidence: int,
    trend_direction: str,
    risk_level: str,
    support: float,
    resistance: float,
    action: str,
    market_summary: str,
) -> str:
    if is_stablecoin(asset):
        return f"{asset} is pegged — hold for stability, not for trading gains."

    if change > 2:
        direction = "surging"
    elif change > 0:
        direction = "rising"
    else:
        direction = "falling"
    if quote_volume > 50_000_000:
        whale_phrase = "massive whale inflow"
    elif quote_volume > 10_000_000:
        whale_phrase = "moderate interest"
    else:
        whale_phrase = "low activity"
    if score >= 70:
        signal = "strong bullish analytics"
    elif score >= 55:
        signal = "bullish analytics"
    elif score >= 40:
        signal = "neutral analytics"
    else:
        signal = "bearish analytics"
    return (
        f"Analytics summary: {action} — {market_summary} — "
        f"{risk_level} Risk — {trend_direction} — {asset} is {direction} {change:+.2f}% "
        f"with {whale_phrase} — Support: ${support:,.0f} | Resistance: ${resistance:,.0f} — "
        f"{sentiment} sentiment — {signal} — "
        f"Confidence: {confidence}% — {fear_greed} — Not investment advice."
    )


def timestamp_human(now: datetime | None = None) -> str:
    ts = now or datetime.now(UTC)
    return ts.strftime("%B %d, %Y at %I:%M %p UTC")


def _oracle_response_score(
    asset: str,
    quote_volume: float,
    change: float,
    unified: dict[str, Any] | None,
) -> int:
    score = int((unified or {}).get("opportunity_score") or oracle_score(quote_volume, change))
    return min(score, 55) if is_stablecoin(asset) else score


def _oracle_response_verdict(
    asset: str,
    price: float,
    score: int,
    unified: dict[str, Any] | None,
) -> tuple[str, str]:
    verdict, oracle_text = oracle_verdict(score, asset, price)
    if not unified or not unified.get("verdict"):
        return verdict, oracle_text
    from regulatory_compliance_guard import compliant_verdict_description, to_public_verdict

    public_verdict = to_public_verdict(str(unified["verdict"]))
    public_text = compliant_verdict_description(asset, score, price, str(unified["verdict"]))
    return public_verdict, public_text


def _volatility_label(change: float) -> str:
    if abs(change) < 2:
        return "Low"
    if abs(change) < 5:
        return "Medium"
    return "High"


def _attach_unified_oracle_fields(payload: dict[str, Any], unified: dict[str, Any] | None) -> None:
    if not unified:
        return
    payload["unified_engine"] = unified.get("engine", "unified_multimodal_v1")
    payload["market_regime"] = unified.get("market_regime")
    payload["dimension_weights"] = unified.get("dimension_weights")
    payload["modal_breakdown"] = unified.get("modal_breakdown")
    payload["base_score"] = unified.get("base_score")
    payload["ml"] = unified.get("ml")
    conflict = _unified_dimension_conflict(unified)
    if conflict is not None:
        payload["dimension_conflict"] = conflict


def _unified_dimension_conflict(unified: dict[str, Any]) -> dict[str, Any] | None:
    conflict_meta = unified.get("dimension_conflict")
    if isinstance(conflict_meta, dict) and _is_actionable_conflict(conflict_meta):
        return conflict_meta
    conflicts = (unified.get("modal_breakdown") or {}).get("conflicts")
    if conflicts and conflicts.get("severity") != "none":
        return conflicts
    return None


def _is_actionable_conflict(conflict_meta: dict[str, Any]) -> bool:
    return bool(
        conflict_meta.get("veto")
        or conflict_meta.get("abstain")
        or conflict_meta.get("severity") not in (None, "none")
    )


def build_full_oracle_response(
    asset: str,
    price: float,
    volume: float,
    quote_volume: float,
    change: float,
    *,
    whale_alert: str | None = None,
    unified: dict[str, Any] | None = None,
) -> dict:
    score = _oracle_response_score(asset, quote_volume, change, unified)
    verdict, oracle_text = _oracle_response_verdict(asset, price, score, unified)
    sentiment = oracle_sentiment(change)
    fg_score, fear_greed = fear_greed_index(change, quote_volume)
    confidence = int((unified or {}).get("confidence") or oracle_confidence(score, change, quote_volume))
    trend_dir = trend_direction(change)
    risk = risk_level(score)
    support = round(price * 0.97, -2)
    resistance = round(price * 1.03, -2)
    prediction_low = round(price * (1 + (change / 100) * 0.5), -2)
    prediction_high = round(price * (1 + (change / 100) * 1.5), -2)
    volatility = _volatility_label(change)
    liquidity, _ = liquidity_label(quote_volume)
    market_summary = f"Market: {sentiment} | Volatility: {volatility} | Liquidity: {liquidity}"
    action = oracle_action(score, price, support, resistance)
    whale_alert = whale_alert or whale_alert_message(quote_volume, change)
    narrative = oracle_narrative(
        asset,
        change,
        quote_volume,
        score,
        sentiment,
        fear_greed,
        confidence,
        trend_dir,
        risk,
        support,
        resistance,
        action,
        market_summary,
    )
    now = datetime.now(UTC)

    payload = {
        "symbol": asset,
        "price": price,
        "change_24h": change,
        "volume": volume,
        "volume_24h": quote_volume,
        "opportunity_score": score,
        "verdict": verdict,
        "oracle": oracle_text,
        "fear_greed": fear_greed,
        "fear_greed_score": fg_score,
        "support": support,
        "resistance": resistance,
        "next_24h_low": prediction_low,
        "next_24h_high": prediction_high,
        "trend_direction": trend_dir,
        "confidence": confidence,
        "action": action,
        "market_summary": market_summary,
        "risk_level": risk,
        "sentiment": sentiment,
        "narrative": narrative,
        "whale_alert": whale_alert,
        "data_source": "Binance Live API | Unified Multi-Modal AI Engine",
        "timestamp_human": timestamp_human(now),
        "timestamp": now.isoformat(),
        "disclaimer": "Not financial advice. Do your own research (DYOR).",
    }
    _attach_unified_oracle_fields(payload, unified)
    return payload


def trend_direction(change: float) -> str:
    if change > 2:
        return "Uptrend"
    if change < -2:
        return "Downtrend"
    return "Sideways"


def liquidity_label(quote_volume: float) -> tuple[str, int]:
    if quote_volume > 500_000_000:
        return "High", 92
    if quote_volume > 50_000_000:
        return "Medium", 68
    return "Low", 38


def compute_ema(values: list[float], period: int) -> float | None:
    if len(values) < period:
        return None
    multiplier = 2 / (period + 1)
    ema = sum(values[:period]) / period
    for value in values[period:]:
        ema = value * multiplier + ema * (1 - multiplier)
    return ema


def compute_rsi(closes: list[float], period: int = 14) -> float | None:
    if len(closes) < period + 1:
        return None
    gains: list[float] = []
    losses: list[float] = []
    for idx in range(1, len(closes)):
        delta = closes[idx] - closes[idx - 1]
        gains.append(max(delta, 0.0))
        losses.append(max(-delta, 0.0))
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 1)


def rsi_signal_label(rsi: float) -> str:
    if rsi >= 70:
        return "Overbought"
    if rsi >= 55:
        return "Bullish momentum"
    if rsi >= 45:
        return "Neutral"
    if rsi >= 30:
        return "Bearish momentum"
    return "Oversold"


def macd_trend_label(closes: list[float]) -> str:
    if len(closes) < 26:
        return "Insufficient candle data"
    ema12 = compute_ema(closes, 12)
    ema26 = compute_ema(closes, 26)
    if ema12 is None or ema26 is None:
        return "Insufficient candle data"
    macd = ema12 - ema26
    prev_closes = closes[:-1]
    prev_ema12 = compute_ema(prev_closes, 12)
    prev_ema26 = compute_ema(prev_closes, 26)
    if prev_ema12 is None or prev_ema26 is None:
        return "MACD consolidating"
    prev_macd = prev_ema12 - prev_ema26
    if macd > 0 and macd > prev_macd:
        return "Bullish crossover — momentum rising"
    if macd < 0 and macd < prev_macd:
        return "Bearish crossover — momentum falling"
    if macd > prev_macd:
        return "MACD turning up — early bullish shift"
    if macd < prev_macd:
        return "MACD turning down — early bearish shift"
    return "MACD flat — consolidation phase"


def ema_position_label(price: float, closes: list[float]) -> str:
    ema50 = compute_ema(closes, 50) if len(closes) >= 50 else None
    ema200 = compute_ema(closes, 200) if len(closes) >= 200 else compute_ema(closes, min(len(closes), 100))
    if ema50 is None:
        return "Insufficient EMA data"
    above50 = price >= ema50
    if ema200 is None:
        return "Price above 50 EMA" if above50 else "Price below 50 EMA"
    above200 = price >= ema200
    if above50 and above200:
        return "Price trading above 50 & 200 EMA — bullish structure"
    if above50 and not above200:
        return "Price above 50 EMA, below 200 EMA — recovery attempt"
    if not above50 and above200:
        return "Price below 50 EMA, holding 200 EMA — pullback zone"
    return "Price below key EMAs — downtrend structure"


_ALLOWED_KLINE_INTERVALS = {
    "1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "3d", "1w", "1M",
}


async def fetch_binance_klines(pair: str, interval: str = "1h", limit: int = 200) -> list[float]:
    if config.PRICE_FEED_WS_ONLY:
        from ws_price_provider import get_klines

        asset = pair.replace("USDT", "")
        return await get_klines(asset, interval=interval, limit=limit)
    if not pair.isalnum():
        return []
    if interval not in _ALLOWED_KLINE_INTERVALS:
        interval = "1h"
    # Prefer Vision/US first — same Railway egress pattern as fetch_binance_ticker.
    hosts = ("data-api.binance.vision", "api.binance.us", "api.binance.com")
    try:
        from aggregator import get_shared_http_session

        session = get_shared_http_session()
        for host in hosts:
            url = f"https://{host}/api/v3/klines?symbol={pair}&interval={interval}&limit={limit}"
            try:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        continue
                    rows = await resp.json()
                closes = [float(row[4]) for row in rows if isinstance(row, list) and len(row) > 4]
                if closes:
                    return closes
            except (aiohttp.ClientError, TypeError, ValueError):
                continue
    except (aiohttp.ClientError, TypeError, ValueError):
        return []
    return []


def parse_alert_metadata(row: dict) -> dict:
    raw = row.get("metadata_json")
    if not raw:
        return row if row.get("pattern") else {}
    try:
        return json.loads(raw) if isinstance(raw, str) else dict(raw)
    except (TypeError, json.JSONDecodeError):
        return {}


def normalize_whale_alert_row(alert: dict) -> dict:
    if alert.get("metadata_json") is not None or alert.get("flow_type"):
        return alert
    meta = {
        "pattern": alert.get("pattern"),
        "liquidity_exchange": alert.get("liquidity_exchange"),
        "manipulation_score": alert.get("manipulation_score"),
        "volume_spike_ratio": alert.get("volume_spike_ratio"),
        "liquidity_drop_ratio": alert.get("liquidity_drop_ratio"),
        "iceberg_trade_count": alert.get("iceberg_trade_count"),
    }
    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "flow_type": "manipulation_alert",
        "exchange": alert.get("volume_exchange"),
        "symbol": alert.get("symbol"),
        "asset": alert.get("asset"),
        "sector": alert.get("sector"),
        "side": alert.get("side"),
        "notional_usd": alert.get("volume_usd"),
        "metadata_json": json.dumps({k: v for k, v in meta.items() if v is not None}),
    }


def whale_alerts_for_asset(alerts: list[dict], asset: str) -> list[dict]:
    target = asset.upper()
    matched: list[dict] = []
    for alert in alerts:
        row = normalize_whale_alert_row(alert)
        if str(row.get("asset") or "").upper() == target:
            matched.append(row)
    return matched


async def fetch_cvvd_whale_context(refresh: bool = False) -> dict:
    from whale_tracker import (
        get_latest_institutional_context,
        persist_manipulation_alerts,
        scan_whale_trades,
    )

    context = await get_latest_institutional_context()
    alerts = [normalize_whale_alert_row(a) for a in context.get("whale_alerts", [])]
    sector_flows = context.get("sector_flows", [])

    if refresh or not alerts:
        live = await scan_whale_trades()
        if live:
            await persist_manipulation_alerts(live)
            alerts = [normalize_whale_alert_row(a.model_dump()) for a in live]
            context = await get_latest_institutional_context()
            sector_flows = context.get("sector_flows", [])

    return {
        "whale_alerts": alerts,
        "sector_flows": sector_flows,
        "live_scan": refresh or not context.get("whale_alerts"),
    }


async def fetch_cvvd_whale_alert(asset: str, pair: str, price: float) -> str:
    context = await fetch_cvvd_whale_context(refresh=False)
    asset_alerts = whale_alerts_for_asset(context["whale_alerts"], asset)
    if asset_alerts:
        top = asset_alerts[0]
        meta = parse_alert_metadata(top)
        pattern = str(meta.get("pattern") or "cross_venue_manipulation").replace("_", " ")
        score = float(meta.get("manipulation_score") or 0)
        notional = float(top.get("notional_usd") or 0)
        side = str(top.get("side") or "unknown")
        exchange = str(top.get("exchange") or meta.get("volume_exchange") or "multi-venue").upper()
        return (
            f"CVVD {pattern} on {exchange} — {side} side — "
            f"${notional:,.0f} volume — manipulation score {score:.0f}/100"
        )

    return await fetch_live_whale_signal(pair, price)
