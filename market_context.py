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
    owns_session = session is None
    try:
        if owns_session:
            session = aiohttp.ClientSession(timeout=_HTTP_TIMEOUT, headers=_HTTP_HEADERS)
        assert session is not None
        async with session.get(url, params=params, headers=headers) as resp:
            if resp.status != 200:
                logger.debug(
                    "REST price fetch non-200 | url=%s status=%s",
                    str(url).replace("\r", " ").replace("\n", " "),
                    str(resp.status).replace("\r", " ").replace("\n", " "),
                )
                return None
            return await resp.json()
    except (aiohttp.ClientError, json.JSONDecodeError, TypeError, ValueError):
        return None
    finally:
        if owns_session and session is not None:
            await session.close()


def sector_for_asset(asset: str) -> str:
    return config.SECTOR_MAP.get(asset.upper(), "Other")


def normalize_oracle_symbol(symbol: str) -> tuple[str, str]:
    cleaned = symbol.upper().strip().replace("/", "").replace("-", "")
    if cleaned.endswith("USDT"):
        return cleaned[:-4], cleaned
    return cleaned, f"{cleaned}USDT"


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
    cg_id = _COINGECKO_IDS.get(asset.upper())
    if not cg_id:
        return None
    url = "https://api.coingecko.com/api/v3/simple/price"
    data = await _rest_get(
        url,
        params={
            "ids": cg_id,
            "vs_currencies": "usd",
            "include_24hr_change": "true",
        },
        headers=_coingecko_headers(),
        session=session,
    )
    if not isinstance(data, dict):
        return None
    try:
        row = data.get(cg_id) or {}
        price = float(row.get("usd") or 0)
        if price <= 0:
            return None
        return {
            "price": price,
            "change_24h": float(row.get("usd_24h_change") or 0),
            "volume": 0.0,
            "quote_volume": 0.0,
            "source": "coingecko",
        }
    except (KeyError, TypeError, ValueError):
        return None


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


async def fetch_binance_ticker(pair: str) -> dict | None:
    """Live spot ticker — WS when fresh, else multi-source REST (Railway/cloud safe)."""
    asset = pair.replace("USDT", "").upper()

    if config.PRICE_FEED_WS_ONLY:
        from live_book_hub import get_live_books_if_fresh

        fresh = get_live_books_if_fresh()
        if fresh:
            from ws_price_provider import get_ticker

            ws_row = await get_ticker(asset)
            if ws_row is not None:
                ws_row.setdefault("source", "websocket_live")
                return ws_row

    async with aiohttp.ClientSession(timeout=_HTTP_TIMEOUT, headers=_HTTP_HEADERS) as session:
        for host in ("api.binance.com", "data-api.binance.vision", "api.binance.us"):
            row = await _fetch_binance_host_ticker(pair, host, session=session)
            if row is not None:
                return row

        for fallback in _REST_PRICE_FALLBACKS:
            row = await fallback(asset, session=session)
            if row is not None:
                allowed = {str(a).upper() for a in (getattr(config, "WHITELIST_ASSETS", None) or [])}
                asset_label = str(asset).upper() if str(asset).upper() in allowed else "other"
                source_raw = str(row.get("source") or "unknown")
                source_label = source_raw if source_raw.replace("_", "").isalnum() else "unknown"
                logger.info(
                    "Price REST fallback | asset=%s source=%s",
                    str(asset_label).replace("\r", " ").replace("\n", " "),
                    str(source_label).replace("\r", " ").replace("\n", " "),
                )
                return row

    allowed = {str(a).upper() for a in (getattr(config, "WHITELIST_ASSETS", None) or [])}
    asset_label = str(asset).upper() if str(asset).upper() in allowed else "other"
    logger.warning("All price sources failed | asset=%s", str(asset_label).replace("\r", " ").replace("\n", " "))
    return None


async def probe_price_sources(symbol: str = "BTC") -> dict[str, Any]:
    """Ops diagnostic — which price APIs respond from this host (Railway DD)."""
    asset, pair = normalize_oracle_symbol(symbol)
    checks: dict[str, Any] = {}
    async with aiohttp.ClientSession(timeout=_HTTP_TIMEOUT, headers=_HTTP_HEADERS) as session:
        for host in ("api.binance.com", "data-api.binance.vision", "api.binance.us"):
            row = await _fetch_binance_host_ticker(pair, host, session=session)
            checks[host] = {"ok": row is not None, "source": row.get("source") if row else None}
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


async def fetch_binance_market_overview(limit: int | None = None) -> list[dict]:
    """Tracked assets from WebSocket/Redis — no REST when WS-only."""
    if config.PRICE_FEED_WS_ONLY:
        from ws_price_provider import get_market_overview

        return await get_market_overview(limit)
    if limit is None:
        limit = config.MARKET_RADAR_LIMIT
    url = "https://api.binance.com/api/v3/ticker/24hr"
    try:
        timeout = aiohttp.ClientTimeout(total=15)
        async with aiohttp.ClientSession(timeout=timeout) as session, session.get(url) as resp:
            if resp.status != 200:
                return []
            rows = await resp.json()
    except (aiohttp.ClientError, TypeError, ValueError):
        return []

    by_symbol: dict[str, dict] = {}
    all_candidates: list[dict] = []
    for row in rows:
        symbol = row.get("symbol", "")
        if not symbol.endswith("USDT"):
            continue
        asset = symbol[:-4]
        if is_stablecoin(asset):
            continue
        try:
            quote_volume = float(row.get("quoteVolume") or 0)
            change = float(row.get("priceChangePercent") or 0)
            price = float(row.get("lastPrice") or 0)
        except (TypeError, ValueError):
            continue
        if quote_volume < 10_000_000:
            continue
        score = oracle_score(quote_volume, change)
        verdict, _ = oracle_verdict(score, asset, price)
        item = {
            "symbol": asset,
            "price": price,
            "change_24h": change,
            "volume_24h": quote_volume,
            "score": score,
            "verdict": verdict,
            "sector": sector_for_asset(asset),
        }
        by_symbol[asset] = item
        all_candidates.append(item)

    all_candidates.sort(key=lambda x: x["volume_24h"], reverse=True)
    priority: list[dict] = []
    seen: set[str] = set()
    for asset in config.tracked_asset_list():
        if asset in by_symbol:
            priority.append(by_symbol[asset])
            seen.add(asset)
    for candidate in all_candidates:
        if len(priority) >= limit:
            break
        if candidate["symbol"] not in seen:
            priority.append(candidate)
            seen.add(candidate["symbol"])
    return priority[:limit]


async def fetch_live_whale_signal(pair: str, price: float) -> str:
    """Detect large book activity from WebSocket feeds (no REST aggTrades)."""
    if config.PRICE_FEED_WS_ONLY:
        from ws_price_provider import get_whale_signal

        asset = pair.replace("USDT", "")
        return await get_whale_signal(asset, price)
    if not pair.isalnum():
        return "No significant whale activity"
    url = f"https://api.binance.com/api/v3/aggTrades?symbol={pair}&limit=200"
    threshold_usd = 75_000
    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session, session.get(url) as resp:
            if resp.status != 200:
                return "No significant whale activity"
            trades = await resp.json()
    except (aiohttp.ClientError, TypeError, ValueError):
        return "No significant whale activity"

    buy_blocks = 0
    sell_blocks = 0
    max_notional = 0.0
    for trade in trades:
        try:
            qty = float(trade["q"])
            trade_price = float(trade["p"])
            notional = qty * trade_price
        except (KeyError, TypeError, ValueError):
            continue
        if notional < threshold_usd:
            continue
        max_notional = max(max_notional, notional)
        # m=true → buyer is maker → aggressive seller; m=false → aggressive buyer
        if trade.get("m"):
            sell_blocks += 1
        else:
            buy_blocks += 1

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
    return "No significant whale activity"


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

    direction = "surging" if change > 2 else "rising" if change > 0 else "falling"
    whale_phrase = (
        "massive whale inflow"
        if quote_volume > 50_000_000
        else "moderate interest"
        if quote_volume > 10_000_000
        else "low activity"
    )
    signal = (
        "strong bullish analytics"
        if score >= 70
        else "bullish analytics"
        if score >= 55
        else "neutral analytics"
        if score >= 40
        else "bearish analytics"
    )
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
    score = int((unified or {}).get("opportunity_score") or oracle_score(quote_volume, change))
    if is_stablecoin(asset):
        score = min(score, 55)
    verdict, oracle_text = oracle_verdict(score, asset, price)
    if unified and unified.get("verdict"):
        from regulatory_compliance_guard import compliant_verdict_description, to_public_verdict

        verdict = to_public_verdict(str(unified["verdict"]))
        oracle_text = compliant_verdict_description(asset, score, price, str(unified["verdict"]))

    sentiment = oracle_sentiment(change)
    fg_score, fear_greed = fear_greed_index(change, quote_volume)
    confidence = int((unified or {}).get("confidence") or oracle_confidence(score, change, quote_volume))
    trend_dir = trend_direction(change)
    risk = risk_level(score)
    support = round(price * 0.97, -2)
    resistance = round(price * 1.03, -2)
    prediction_low = round(price * (1 + (change / 100) * 0.5), -2)
    prediction_high = round(price * (1 + (change / 100) * 1.5), -2)
    volatility = "Low" if abs(change) < 2 else "Medium" if abs(change) < 5 else "High"
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
    if unified:
        payload["unified_engine"] = unified.get("engine", "unified_multimodal_v1")
        payload["market_regime"] = unified.get("market_regime")
        payload["dimension_weights"] = unified.get("dimension_weights")
        payload["modal_breakdown"] = unified.get("modal_breakdown")
        payload["base_score"] = unified.get("base_score")
        payload["ml"] = unified.get("ml")
        # Prefer guard meta (veto/abstain) from finalize_unified_score; fall back to modal conflicts.
        conflict_meta = unified.get("dimension_conflict")
        if isinstance(conflict_meta, dict) and (
            conflict_meta.get("veto")
            or conflict_meta.get("abstain")
            or conflict_meta.get("severity") not in (None, "none")
        ):
            payload["dimension_conflict"] = conflict_meta
        else:
            conflicts = (unified.get("modal_breakdown") or {}).get("conflicts")
            if conflicts and conflicts.get("severity") != "none":
                payload["dimension_conflict"] = conflicts
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
    url = f"https://api.binance.com/api/v3/klines?symbol={pair}&interval={interval}&limit={limit}"
    try:
        timeout = aiohttp.ClientTimeout(total=12)
        async with aiohttp.ClientSession(timeout=timeout) as session, session.get(url) as resp:
            if resp.status != 200:
                return []
            rows = await resp.json()
        return [float(row[4]) for row in rows if isinstance(row, list) and len(row) > 4]
    except (aiohttp.ClientError, TypeError, ValueError):
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
