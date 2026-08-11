"""
BLACKDARK — WebSocket / Redis price provider (no REST).

Serves dashboard charts, market radar, and whale signals from:
  live_book_hub → Redis cache → Kafka-built OHLC buckets
"""

from __future__ import annotations

import logging
from typing import Any

import config
from live_book_hub import get_best_price, get_top_of_book, hub_stats

logger = logging.getLogger("BLACKDARK.WSPriceProvider")

_PRIMARY_VENUE = "binance"
_STABLECOINS = frozenset(
    {"USDC", "USDT", "USD1", "DAI", "FDUSD", "USDE", "USDS", "TUSD", "BUSD", "EURC", "RLUSD", "USDG"}
)


def _symbol(asset: str) -> str:
    cleaned = asset.upper().strip().replace("/", "").replace("-", "")
    if cleaned.endswith("USDT"):
        return f"{cleaned[:-4]}/USDT"
    return f"{cleaned}/USDT"


def _is_stablecoin(asset: str) -> bool:
    return asset.upper() in _STABLECOINS


def _sector_for_asset(asset: str) -> str:
    return config.SECTOR_MAP.get(asset.upper(), "Other")


def _oracle_score(volume: float, change: float) -> int:
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


def _oracle_verdict(score: int, asset: str, price: float) -> tuple[str, str]:
    if _is_stablecoin(asset):
        return "WAIT", f"{asset} is a stablecoin — not a trading opportunity (Score: {score}/100)"
    if score >= 75:
        return "BUY", f"Strong buy signal for {asset} at ${price:,.0f} (Score: {score}/100)"
    if score >= 50:
        return "WAIT", f"Hold {asset} and watch for breakout (Score: {score}/100)"
    return "SELL", f"Weak structure for {asset} at ${price:,.0f} (Score: {score}/100)"


async def get_ticker(asset: str) -> dict[str, Any] | None:
    sym = _symbol(asset)
    row = get_best_price(_PRIMARY_VENUE, sym)
    if row is None:
        try:
            from redis_price_cache import get_best_price as redis_price

            row = await redis_price(_PRIMARY_VENUE, sym)
        except Exception:
            row = None
    if not row:
        return None
    mid = float(row.get("mid") or (row["bid"] + row["ask"]) / 2)
    return {
        "price": mid,
        "change_24h": 0.0,
        "volume": 0.0,
        "quote_volume": 0.0,
        "source": "websocket_live",
    }


async def get_market_overview(limit: int | None = None) -> list[dict[str, Any]]:
    if limit is None:
        limit = config.MARKET_RADAR_LIMIT

    items: list[dict[str, Any]] = []
    for asset in config.tracked_asset_list():
        if _is_stablecoin(asset):
            continue
        sym = _symbol(asset)
        best_mid = 0.0
        for venue in sorted(config.WS_PRICE_VENUES):
            row = get_best_price(venue, sym)
            if row and row.get("mid"):
                best_mid = float(row["mid"])
                break
        if best_mid <= 0:
            continue
        score = _oracle_score(0, 0)
        verdict, _ = _oracle_verdict(score, asset, best_mid)
        items.append(
            {
                "symbol": asset,
                "price": best_mid,
                "change_24h": 0.0,
                "volume_24h": 0.0,
                "score": score,
                "verdict": verdict,
                "sector": _sector_for_asset(asset),
                "source": "websocket_live",
            }
        )

    if len(items) < limit:
        try:
            from redis_price_cache import get_all_books

            books = await get_all_books()
            seen = {i["symbol"] for i in items}
            for symbols in books.values():
                for sym, row in symbols.items():
                    if not sym.endswith("/USDT"):
                        continue
                    asset = sym.replace("/USDT", "")
                    if asset in seen or _is_stablecoin(asset):
                        continue
                    mid = float(row.get("mid") or 0)
                    if mid <= 0:
                        continue
                    score = _oracle_score(0, 0)
                    verdict, _ = _oracle_verdict(score, asset, mid)
                    items.append(
                        {
                            "symbol": asset,
                            "price": mid,
                            "change_24h": 0.0,
                            "volume_24h": 0.0,
                            "score": score,
                            "verdict": verdict,
                            "sector": _sector_for_asset(asset),
                            "source": "redis_cache",
                        }
                    )
                    seen.add(asset)
                    if len(items) >= limit:
                        break
                if len(items) >= limit:
                    break
        except Exception:
            logger.debug("Redis market overview enrichment skipped", exc_info=True)

    return items[:limit]


async def get_klines(asset: str, interval: str = "1h", limit: int = 200) -> list[float]:
    sym = _symbol(asset)
    try:
        from redis_price_cache import get_ohlc_closes

        closes = await get_ohlc_closes(sym, interval=interval, limit=limit)
        if closes:
            return closes
    except Exception:
        logger.debug("Redis OHLC read failed", exc_info=True)

    row = get_best_price(_PRIMARY_VENUE, sym)
    if row and row.get("mid"):
        return [float(row["mid"])] * min(limit, 20)
    return []


async def get_whale_signal(asset: str, _price: float) -> str:
    sym = _symbol(asset)
    threshold_usd = 75_000.0
    large_side: str | None = None
    largest = 0.0

    for venue in sorted(config.WS_PRICE_VENUES):
        full = get_top_of_book(venue, sym) or {}
        bids = full.get("bids") or []
        asks = full.get("asks") or []
        for side, levels in (("buy", bids), ("sell", asks)):
            if not levels:
                continue
            px = float(levels[0][0])
            qty = float(levels[0][1])
            notional = px * qty
            if notional >= threshold_usd and notional > largest:
                largest = notional
                large_side = side

    if large_side == "buy":
        return f"Large aggressive buy detected (~${largest:,.0f}) via WebSocket book"
    if large_side == "sell":
        return f"Large aggressive sell detected (~${largest:,.0f}) via WebSocket book"
    return "No significant whale activity (WS book monitor)"


def provider_stats() -> dict[str, Any]:
    return {
        "mode": "websocket_redis",
        "primary_venue": _PRIMARY_VENUE,
        "venues": sorted(config.WS_PRICE_VENUES),
        "live_book": hub_stats(),
    }
