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


def _norm_symbol(symbol: str) -> list[str]:
    """Return lookup candidates (BTC/USDT and BTCUSDT forms)."""
    raw = symbol.strip().upper().replace("-", "/")
    cands = [raw]
    compact = raw.replace("/", "")
    if compact not in cands:
        cands.append(compact)
    if compact.endswith("USDT") and "/" not in raw:
        cands.append(f"{compact[:-4]}/USDT")
    return cands


def get_top_of_book(
    exchange_or_symbol: str,
    symbol: str | None = None,
) -> dict[str, Any] | None:
    """Return full top-of-book row.

    Supports:
      get_top_of_book("binance", "BTC/USDT")
      get_top_of_book("BTCUSDT")  # search all venues
    """
    if symbol is None:
        for _ex, books in _books.items():
            for cand in _norm_symbol(exchange_or_symbol):
                row = books.get(cand)
                if row:
                    return dict(row)
        return None

    ex = exchange_or_symbol.strip().lower()
    books = _books.get(ex) or {}
    for cand in _norm_symbol(symbol):
        row = books.get(cand)
        if row:
            return dict(row)
    return None


def get_best_price(exchange: str, symbol: str) -> dict[str, float] | None:
    book = get_top_of_book(exchange, symbol)
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
