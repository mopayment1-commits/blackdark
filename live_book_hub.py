"""
BLACKDARK — In-memory top-of-book hub (sub-ms reads).

Fed by exchange WebSocket bookTicker streams — arbitrage scanner reads here first.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any

import config

_books: dict[str, dict[str, dict[str, Any]]] = {}
_last_update_ms: dict[str, float] = {}
_updates_total = 0


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _max_age_ms() -> float:
    return max(50.0, float(getattr(config, "LIVE_BOOK_MAX_AGE_MS", 500)))


def update_top_of_book(
    exchange: str,
    symbol: str,
    *,
    bid: float,
    bid_qty: float,
    ask: float,
    ask_qty: float,
    market_type: str = "spot",
) -> None:
    global _updates_total
    if bid <= 0 or ask <= 0:
        return
    exchange_id = exchange.strip().lower()
    sym = symbol.strip().upper()
    ts = _utcnow_iso()
    _books.setdefault(exchange_id, {})[sym] = {
        "bids": [[bid, bid_qty]],
        "asks": [[ask, ask_qty]],
        "timestamp": ts,
        "market_type": market_type,
        "symbol": sym,
    }
    _last_update_ms[f"{exchange_id}|{sym}"] = time.monotonic() * 1000.0
    _updates_total += 1


def get_live_books_if_fresh(*, max_age_ms: float | None = None) -> tuple[dict[str, dict[str, dict[str, Any]]], float] | None:
    """Return books if at least 2 venues have fresh data."""
    if not _books:
        return None

    limit = max_age_ms if max_age_ms is not None else _max_age_ms()
    now_ms = time.monotonic() * 1000.0
    fresh_exchanges = 0
    worst_age_ms = 0.0

    for exchange_id, symbols in _books.items():
        exchange_fresh = False
        for symbol in symbols:
            key = f"{exchange_id}|{symbol}"
            last = _last_update_ms.get(key, 0.0)
            if last <= 0:
                continue
            age = now_ms - last
            if age <= limit:
                exchange_fresh = True
                worst_age_ms = max(worst_age_ms, age)
        if exchange_fresh:
            fresh_exchanges += 1

    if fresh_exchanges < 2:
        return None

    return dict(_books), worst_age_ms


def get_best_price(exchange: str, symbol: str) -> dict[str, float] | None:
    book = (_books.get(exchange.lower()) or {}).get(symbol.upper())
    if not book:
        return None
    bids = book.get("bids") or []
    asks = book.get("asks") or []
    if not bids or not asks:
        return None
    return {
        "bid": float(bids[0][0]),
        "ask": float(asks[0][0]),
        "mid": (float(bids[0][0]) + float(asks[0][0])) / 2.0,
    }


def get_quote_age_ms(exchange: str, symbol: str) -> float | None:
    """Age of the latest top-of-book update for exchange/symbol in milliseconds."""
    key = f"{exchange.strip().lower()}|{symbol.strip().upper()}"
    last = _last_update_ms.get(key, 0.0)
    if last <= 0:
        return None
    return max(0.0, time.monotonic() * 1000.0 - last)


def is_quote_fresh(
    exchange: str,
    symbol: str,
    *,
    max_age_ms: float | None = None,
) -> bool:
    age = get_quote_age_ms(exchange, symbol)
    if age is None:
        return False
    limit = max_age_ms if max_age_ms is not None else _max_age_ms()
    return age <= limit


def hub_stats() -> dict[str, Any]:
    now_ms = time.monotonic() * 1000.0
    ages: list[float] = []
    for key, last in _last_update_ms.items():
        if last > 0:
            ages.append(now_ms - last)

    return {
        "enabled": getattr(config, "EXCHANGE_WS_ENABLED", True),
        "exchanges": sorted(_books.keys()),
        "symbol_count": sum(len(v) for v in _books.values()),
        "updates_total": _updates_total,
        "max_age_ms": _max_age_ms(),
        "freshness_ms": round(min(ages), 1) if ages else None,
        "stalest_ms": round(max(ages), 1) if ages else None,
    }


def _adapt_redis_row(symbol: str, row: dict[str, Any]) -> dict[str, Any] | None:
    """Convert Redis top-of-book payload into arb engine book shape."""
    try:
        bid = float(row.get("bid") or 0)
        ask = float(row.get("ask") or 0)
        bid_qty = float(row.get("bid_qty") or 0) or 1.0
        ask_qty = float(row.get("ask_qty") or 0) or 1.0
    except (TypeError, ValueError):
        return None
    if bid <= 0 or ask <= 0:
        return None
    ts = row.get("ts_ms")
    timestamp = _utcnow_iso()
    if ts:
        try:
            from datetime import datetime, timezone

            timestamp = datetime.fromtimestamp(float(ts) / 1000.0, tz=timezone.utc).isoformat()
        except (TypeError, ValueError, OSError):
            pass
    return {
        "bids": [[bid, bid_qty]],
        "asks": [[ask, ask_qty]],
        "timestamp": timestamp,
        "market_type": "spot",
        "symbol": symbol.upper(),
        "source": "redis_shared",
    }


async def get_shared_books_if_fresh(
    *,
    max_age_ms: float | None = None,
) -> tuple[dict[str, dict[str, dict[str, Any]]], float] | None:
    """
    Cross-replica shared books from Redis price cache.
    Used when the local in-memory hub is cold (other worker owns the WS feed).
    """
    try:
        from redis_price_cache import get_all_books
    except Exception:
        return None

    raw = await get_all_books()
    if not raw:
        return None

    limit = max_age_ms if max_age_ms is not None else max(_max_age_ms(), 1500.0)
    # Redis TTL is seconds-scale; allow a slightly looser freshness window than local hub.
    limit = max(limit, float(getattr(config, "REDIS_BOOK_MAX_AGE_MS", 2500)))
    now_ms = time.time() * 1000.0
    adapted: dict[str, dict[str, dict[str, Any]]] = {}
    fresh_exchanges = 0
    worst_age_ms = 0.0

    for exchange_id, symbols in raw.items():
        exchange_fresh = False
        for symbol, row in (symbols or {}).items():
            if not isinstance(row, dict):
                continue
            ts_ms = float(row.get("ts_ms") or 0)
            if ts_ms <= 0:
                continue
            age = now_ms - ts_ms
            if age < 0:
                age = 0.0
            if age > limit:
                continue
            book = _adapt_redis_row(str(symbol), row)
            if book is None:
                continue
            adapted.setdefault(str(exchange_id).lower(), {})[str(symbol).upper()] = book
            # Warm local hub so subsequent reads stay sub-ms on this replica.
            try:
                update_top_of_book(
                    str(exchange_id),
                    str(symbol),
                    bid=float(book["bids"][0][0]),
                    bid_qty=float(book["bids"][0][1]),
                    ask=float(book["asks"][0][0]),
                    ask_qty=float(book["asks"][0][1]),
                )
            except Exception:
                pass
            exchange_fresh = True
            worst_age_ms = max(worst_age_ms, age)
        if exchange_fresh:
            fresh_exchanges += 1

    if fresh_exchanges < 2 or not adapted:
        return None
    return adapted, worst_age_ms
