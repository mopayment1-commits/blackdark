"""
CoinPaprika public REST API (no API key) — spot tickers and daily OHLCV.

https://api.coinpaprika.com/v1/
"""

from __future__ import annotations

import logging
import time
from collections import deque
from typing import Any

import aiohttp

from config import COINPAPRIKA_CACHE_TTL_SEC, COINPAPRIKA_RPS_LIMIT

logger = logging.getLogger("BLACKDARK.CoinPaprika")

_BASE = "https://api.coinpaprika.com/v1"
_TIMEOUT = aiohttp.ClientTimeout(total=14)
_HEADERS = {
    "User-Agent": "BLACKDARK/1.0 (+https://blackdark.io)",
    "Accept": "application/json",
}

_CACHE: dict[str, tuple[float, Any]] = {}
_RPS_TIMES: deque[float] = deque(maxlen=COINPAPRIKA_RPS_LIMIT * 2)
_COIN_ID_MAP: tuple[float, dict[str, str]] | None = None
_COIN_ID_MAP_TTL = 6 * 3600.0


def _pair_asset(pair: str) -> str:
    cleaned = (pair or "").upper().strip().replace("/", "").replace("-", "")
    if cleaned.endswith("USDT"):
        return cleaned[:-4]
    if cleaned.endswith("USD"):
        return cleaned[:-3]
    return cleaned


def _try_consume_rps() -> bool:
    now = time.time()
    while _RPS_TIMES and now - _RPS_TIMES[0] > 1.0:
        _RPS_TIMES.popleft()
    if len(_RPS_TIMES) >= COINPAPRIKA_RPS_LIMIT:
        return False
    _RPS_TIMES.append(now)
    return True


def _cache_get(key: str) -> Any | None:
    row = _CACHE.get(key)
    if not row:
        return None
    ts, val = row
    if time.time() - ts > COINPAPRIKA_CACHE_TTL_SEC:
        return None
    return val


def _cache_set(key: str, val: Any) -> None:
    _CACHE[key] = (time.time(), val)


async def _get_json(
    session: aiohttp.ClientSession,
    path: str,
    *,
    consume_rps: bool = True,
) -> Any | None:
    if consume_rps and not _try_consume_rps():
        logger.debug("CoinPaprika RPS limit reached")
        return None
    url = f"{_BASE}{path}"
    try:
        async with session.get(url, headers=_HEADERS) as resp:
            if resp.status != 200:
                logger.debug("CoinPaprika HTTP %s %s", resp.status, path)
                return None
            return await resp.json()
    except (aiohttp.ClientError, TypeError, ValueError):
        return None


async def _load_coin_id_map(session: aiohttp.ClientSession) -> dict[str, str]:
    global _COIN_ID_MAP
    now = time.time()
    if _COIN_ID_MAP and now - _COIN_ID_MAP[0] < _COIN_ID_MAP_TTL:
        return _COIN_ID_MAP[1]
    data = await _get_json(session, "/coins", consume_rps=True)
    best: dict[str, tuple[int, str]] = {}
    if isinstance(data, list):
        for coin in data:
            if not isinstance(coin, dict) or not coin.get("is_active", True):
                continue
            sym = str(coin.get("symbol") or "").upper()
            cid = coin.get("id")
            if not sym or not cid:
                continue
            rank = int(coin.get("rank") or 999_999)
            prev = best.get(sym)
            if prev is None or rank < prev[0]:
                best[sym] = (rank, str(cid))
    mapping = {sym: cid for sym, (_rank, cid) in best.items()}
    _COIN_ID_MAP = (now, mapping)
    return mapping


async def resolve_coin_id(asset: str, *, session: aiohttp.ClientSession) -> str | None:
    sym = (asset or "").upper().strip()
    if not sym:
        return None
    mapping = await _load_coin_id_map(session)
    return mapping.get(sym)


def _ticker_from_paprika(data: dict[str, Any], *, coin_id: str) -> dict[str, Any] | None:
    try:
        quotes = data.get("quotes") or {}
        usd = quotes.get("USD") if isinstance(quotes.get("USD"), dict) else {}
        price = float(usd.get("price") or 0)
        if price <= 0:
            return None
        change = float(usd.get("percent_change_24h") or 0)
        quote_volume = float(usd.get("volume_24h") or 0)
        volume = quote_volume / price if price > 0 else 0.0
        row: dict[str, Any] = {
            "price": price,
            "change_24h": round(change, 4),
            "volume": volume,
            "quote_volume": quote_volume,
            "market_cap_usd": float(usd.get("market_cap") or 0) or None,
            "source": "coinpaprika",
            "coinpaprika_id": coin_id,
            "last_updated": data.get("last_updated"),
        }
        if data.get("beta_value") is not None:
            row["beta_value"] = data.get("beta_value")
        return row
    except (KeyError, TypeError, ValueError):
        return None


async def fetch_ticker_for_asset(
    asset: str,
    *,
    session: aiohttp.ClientSession | None = None,
) -> dict[str, Any] | None:
    sym = (asset or "").upper().strip()
    if not sym:
        return None
    cache_key = f"ticker:{sym}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached
    owns = session is None
    if owns:
        session = aiohttp.ClientSession(timeout=_TIMEOUT)
    try:
        assert session is not None
        coin_id = await resolve_coin_id(sym, session=session)
        if not coin_id:
            return None
        data = await _get_json(session, f"/tickers/{coin_id}")
        if not isinstance(data, dict):
            return None
        row = _ticker_from_paprika(data, coin_id=coin_id)
        if row:
            _cache_set(cache_key, row)
        return row
    finally:
        if owns:
            await session.close()


async def fetch_ohlcv_latest(
    asset: str,
    *,
    session: aiohttp.ClientSession | None = None,
) -> list[dict[str, Any]]:
    """Latest daily OHLCV candle (public plan)."""
    sym = (asset or "").upper().strip()
    if not sym:
        return []
    cache_key = f"ohlcv:{sym}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached
    owns = session is None
    if owns:
        session = aiohttp.ClientSession(timeout=_TIMEOUT)
    try:
        assert session is not None
        coin_id = await resolve_coin_id(sym, session=session)
        if not coin_id:
            return []
        data = await _get_json(session, f"/coins/{coin_id}/ohlcv/latest")
        if not isinstance(data, list):
            return []
        rows: list[dict[str, Any]] = []
        for candle in data[:7]:
            if not isinstance(candle, dict):
                continue
            rows.append(
                {
                    "time_open": candle.get("time_open"),
                    "time_close": candle.get("time_close"),
                    "open": candle.get("open"),
                    "high": candle.get("high"),
                    "low": candle.get("low"),
                    "close": candle.get("close"),
                    "volume": candle.get("volume"),
                    "market_cap": candle.get("market_cap"),
                }
            )
        _cache_set(cache_key, rows)
        return rows
    finally:
        if owns:
            await session.close()


async def fetch_public_spot_market(pair: str) -> dict[str, Any] | None:
    """Spot snapshot for Oracle — ticker + optional daily OHLCV history."""
    asset = _pair_asset(pair)
    if not asset:
        return None
    async with aiohttp.ClientSession(timeout=_TIMEOUT) as session:
        ticker = await fetch_ticker_for_asset(asset, session=session)
        if ticker is None:
            return None
        ohlcv = await fetch_ohlcv_latest(asset, session=session)
        out = dict(ticker)
        if ohlcv:
            out["price_history_daily"] = ohlcv
            out["price_history_source"] = "coinpaprika_ohlcv_latest"
        return out


def usage_stats() -> dict[str, Any]:
    return {
        "configured": True,
        "no_api_key": True,
        "rps_limit": COINPAPRIKA_RPS_LIMIT,
        "cache_ttl_sec": COINPAPRIKA_CACHE_TTL_SEC,
        "attribution": "Data: CoinPaprika",
    }
