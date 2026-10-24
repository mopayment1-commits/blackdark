"""
CoinMarketCap Basic (pro-api) — commercial-friendly fallback & market metadata.

Requires COINMARKETCAP_API_KEY (Basic plan). No key → helpers return None / [].
"""

from __future__ import annotations

import logging
from typing import Any

import aiohttp

import config

logger = logging.getLogger("BLACKDARK.CoinMarketCap")

_BASE = "https://pro-api.coinmarketcap.com/v1"
_TIMEOUT = aiohttp.ClientTimeout(total=14)
_HEADERS_BASE = {
    "User-Agent": "BLACKDARK/1.0 (+https://blackdark.io)",
    "Accept": "application/json",
}


def _api_key() -> str:
    return (getattr(config, "COINMARKETCAP_API_KEY", None) or "").strip()


def is_configured() -> bool:
    return bool(_api_key())


def _auth_headers() -> dict[str, str] | None:
    key = _api_key()
    if not key:
        return None
    return {**_HEADERS_BASE, "X-CMC_PRO_API_KEY": key}


async def _get_json(
    path: str,
    *,
    params: dict[str, str | int] | None = None,
    session: aiohttp.ClientSession | None = None,
) -> dict[str, Any] | None:
    headers = _auth_headers()
    if not headers:
        return None
    url = f"{_BASE}{path}"
    owns = session is None
    if owns:
        session = aiohttp.ClientSession(timeout=_TIMEOUT)
    try:
        assert session is not None
        async with session.get(url, params=params, headers=headers) as resp:
            if resp.status != 200:
                logger.debug("CMC HTTP %s for %s", resp.status, path)
                return None
            payload = await resp.json()
            return payload if isinstance(payload, dict) else None
    except (aiohttp.ClientError, TypeError, ValueError):
        return None
    finally:
        if owns and session is not None:
            await session.close()


def _row_from_quote_payload(payload: dict[str, Any], asset: str) -> dict[str, Any] | None:
    data = payload.get("data")
    if not isinstance(data, dict):
        return None
    want = asset.upper().strip()
    for entries in data.values():
        rows = entries if isinstance(entries, list) else [entries]
        for row in rows:
            if not isinstance(row, dict):
                continue
            if str(row.get("symbol") or "").upper() != want:
                continue
            quote = (row.get("quote") or {}).get("USD") or {}
            try:
                price = float(quote.get("price") or 0)
                if price <= 0:
                    return None
                change = float(quote.get("percent_change_24h") or 0)
                quote_volume = float(quote.get("volume_24h") or 0)
                market_cap = float(quote.get("market_cap") or 0)
            except (TypeError, ValueError):
                return None
            last_updated = quote.get("last_updated")
            out: dict[str, Any] = {
                "price": price,
                "change_24h": change,
                "volume": quote_volume / price if price else 0.0,
                "quote_volume": quote_volume,
                "market_cap_usd": market_cap,
                "cmc_rank": row.get("cmc_rank"),
                "source": "coinmarketcap",
            }
            if last_updated:
                out["event_time"] = last_updated
            return out
    return None


async def fetch_spot_ticker(
    asset: str,
    *,
    session: aiohttp.ClientSession | None = None,
) -> dict[str, Any] | None:
    """Quotes/latest — price, 24h %, volume, market cap (USD)."""
    sym = (asset or "").upper().strip()
    if not sym or not is_configured():
        return None
    payload = await _get_json(
        "/cryptocurrency/quotes/latest",
        params={"symbol": sym, "convert": "USD"},
        session=session,
    )
    if not payload:
        return None
    return _row_from_quote_payload(payload, sym)


async def fetch_listings_latest(
    limit: int = 100,
    *,
    session: aiohttp.ClientSession | None = None,
) -> list[dict[str, Any]]:
    """Listings/latest — rank, symbol, price, market cap, volume."""
    if not is_configured():
        return []
    lim = max(1, min(int(limit), 500))
    payload = await _get_json(
        "/cryptocurrency/listings/latest",
        params={"limit": lim, "convert": "USD"},
        session=session,
    )
    if not payload:
        return []
    out: list[dict[str, Any]] = []
    for row in payload.get("data") or []:
        if not isinstance(row, dict):
            continue
        sym = str(row.get("symbol") or "").upper()
        usd = (row.get("quote") or {}).get("USD") or {}
        try:
            out.append(
                {
                    "id": row.get("id"),
                    "symbol": sym,
                    "name": row.get("name"),
                    "cmc_rank": row.get("cmc_rank"),
                    "price_usd": float(usd.get("price") or 0),
                    "market_cap_usd": float(usd.get("market_cap") or 0),
                    "volume_24h_usd": float(usd.get("volume_24h") or 0),
                    "percent_change_24h": float(usd.get("percent_change_24h") or 0),
                    "source": "coinmarketcap",
                }
            )
        except (TypeError, ValueError):
            continue
    return out


async def enrich_market_with_cmc_metadata(
    market: dict[str, Any],
    asset: str,
    *,
    session: aiohttp.ClientSession | None = None,
) -> dict[str, Any]:
    """Attach market_cap / cmc_rank from CMC without replacing Binance price."""
    if not market or not is_configured():
        return market
    if market.get("market_cap_usd") and market.get("cmc_rank"):
        return market
    row = await fetch_spot_ticker(asset, session=session)
    if not row:
        return market
    out = dict(market)
    if not out.get("market_cap_usd"):
        out["market_cap_usd"] = row.get("market_cap_usd")
    if not out.get("cmc_rank"):
        out["cmc_rank"] = row.get("cmc_rank")
    out.setdefault("cmc_attribution", "coinmarketcap")
    return out
