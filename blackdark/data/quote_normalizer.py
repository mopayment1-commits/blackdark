"""
Quote normalization — Feature #90 (silent data layer).

Bid < ask sanity, stale flags, canonical quote stream.
Users see clean signals — not a "Quote Data" product.
"""

from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Any

import config

_QUOTE_MAX_AGE_MS = float(getattr(config, "LIVE_BOOK_MAX_AGE_MS", 500))
_EXEC_MAX_AGE_MS = float(getattr(config, "EXECUTION_MAX_QUOTE_AGE_MS", 300))


def validate_bid_ask_sanity(*, bid: float, ask: float) -> tuple[bool, str]:
    if bid <= 0 or ask <= 0:
        return False, "non_positive_price"
    if bid >= ask:
        return False, "bid_not_lt_ask"
    spread_bps = ((ask - bid) / bid) * 10_000
    if spread_bps > 500:
        return False, "spread_too_wide"
    return True, "ok"


def _canonical_ts(ts_ms: int | None = None) -> dict[str, Any]:
    ms = int(ts_ms or time.time() * 1000)
    return {
        "ts_ms": ms,
        "ts_utc": datetime.fromtimestamp(ms / 1000, tz=UTC).isoformat(),
    }


def quote_stale_flag(
    *,
    received_ts_ms: int,
    exchange_ts_ms: int | None = None,
    max_age_ms: float | None = None,
) -> tuple[bool, float, str]:
    """Return (is_stale, age_ms, reason)."""
    limit = max_age_ms if max_age_ms is not None else _QUOTE_MAX_AGE_MS
    now_ms = int(time.time() * 1000)
    ref = exchange_ts_ms if exchange_ts_ms and exchange_ts_ms > 0 else received_ts_ms
    age = max(0.0, float(now_ms - ref))
    if age > limit:
        return True, age, f"stale:{age:.0f}ms>{limit:.0f}ms"
    if exchange_ts_ms and abs(received_ts_ms - exchange_ts_ms) > limit * 2:
        return True, age, "exchange_clock_skew"
    return False, age, "fresh"


def normalize_quote(
    *,
    exchange: str,
    symbol: str,
    bid: float,
    ask: float,
    bid_qty: float = 0.0,
    ask_qty: float = 0.0,
    exchange_ts_ms: int | None = None,
    received_ts_ms: int | None = None,
    market_type: str = "spot",
) -> dict[str, Any]:
    """Normalize top-of-book quote with sanity + stale metadata."""
    recv = int(received_ts_ms or time.time() * 1000)
    sane, sanity_reason = validate_bid_ask_sanity(bid=bid, ask=ask)
    stale, age_ms, stale_reason = quote_stale_flag(
        received_ts_ms=recv,
        exchange_ts_ms=exchange_ts_ms,
    )
    ts = _canonical_ts(recv)
    mid = (bid + ask) / 2.0 if sane else 0.0
    spread_bps = round(((ask - bid) / bid) * 10_000, 4) if sane and bid > 0 else None

    return {
        "feature": "#90-silent",
        "exchange": exchange.strip().lower(),
        "symbol": symbol.strip().upper(),
        "bid": bid,
        "ask": ask,
        "bid_qty": bid_qty,
        "ask_qty": ask_qty,
        "mid": mid,
        "spread_bps": spread_bps,
        "market_type": market_type,
        "sane": sane,
        "sanity_reason": sanity_reason,
        "stale": stale,
        "stale_reason": stale_reason,
        "age_ms": round(age_ms, 2),
        "executable": sane and not stale,
        "exchange_ts_ms": exchange_ts_ms,
        **ts,
    }


def enrich_book_row(book: dict[str, Any], *, exchange: str, symbol: str) -> dict[str, Any]:
    """Attach quote metadata to an existing live_book_hub row."""
    bids = book.get("bids") or []
    asks = book.get("asks") or []
    if not bids or not asks:
        return {**book, "quote_meta": {"sane": False, "stale": True, "sanity_reason": "empty_book"}}
    bid = float(bids[0][0])
    ask = float(asks[0][0])
    meta = normalize_quote(
        exchange=exchange,
        symbol=symbol,
        bid=bid,
        ask=ask,
        bid_qty=float(bids[0][1]) if len(bids[0]) > 1 else 0,
        ask_qty=float(asks[0][1]) if len(asks[0]) > 1 else 0,
    )
    return {**book, "quote_meta": meta}
