"""
BLACKDARK — Feed Lag Arbitrage Scanner (Points 29 & 31).

Detects temporary mispricing when a slow venue's book is stale vs fast venues.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger("BLACKDARK.FeedLagScanner")

FAST_EXCHANGES = {"binance", "okx", "bybit", "bitget", "mexc", "bingx", "cryptocom", "htx"}
SLOW_EXCHANGES = {"kraken", "kucoin", "gateio", "coinbase"}
DEFAULT_LAG_THRESHOLD_SEC = 3.0
DEFAULT_EDGE_BPS = 8.0


def _utcnow_iso() -> str:
    return datetime.now(UTC).isoformat()


def _parse_ts(value: str | None) -> float | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value).timestamp()
    except ValueError:
        return None


def _top_bid(book: dict[str, Any]) -> float | None:
    bids = book.get("bids") or []
    return float(bids[0][0]) if bids else None


def _top_ask(book: dict[str, Any]) -> float | None:
    asks = book.get("asks") or []
    return float(asks[0][0]) if asks else None


def _venue_row(exchange_id: str, book: dict[str, Any]) -> dict[str, Any] | None:
    bid = _top_bid(book)
    ask = _top_ask(book)
    if bid is None or ask is None:
        return None
    ts = _parse_ts(book.get("timestamp"))
    return {
        "exchange": exchange_id,
        "best_bid": bid,
        "best_ask": ask,
        "mid": (bid + ask) / 2,
        "timestamp": book.get("timestamp"),
        "timestamp_epoch": ts,
        "speed_tier": "fast" if exchange_id in FAST_EXCHANGES else "slow",
    }


def _feed_lag_opportunity(slow: dict[str, Any], ref_mid: float, lag_sec: float, *, reverse: bool) -> dict[str, Any]:
    if reverse:
        edge_bps = (slow["best_bid"] - ref_mid) / ref_mid * 10_000
        return {
            "kind": "feed_lag",
            "direction": "buy_fast_sell_slow",
            "slow_exchange": slow["exchange"],
            "reference_mid": round(ref_mid, 6),
            "slow_bid": round(slow["best_bid"], 6),
            "edge_bps": round(edge_bps, 2),
            "lag_seconds": round(lag_sec, 2),
            "note": "Slow venue bid above fast reference — possible stale book",
        }
    edge_bps = (ref_mid - slow["best_ask"]) / ref_mid * 10_000
    return {
        "kind": "feed_lag",
        "direction": "buy_slow_sell_fast",
        "slow_exchange": slow["exchange"],
        "reference_mid": round(ref_mid, 6),
        "slow_ask": round(slow["best_ask"], 6),
        "edge_bps": round(edge_bps, 2),
        "lag_seconds": round(lag_sec, 2),
        "note": "Slow venue ask below fast reference — possible stale book",
    }


def _venues_from_books(books: dict[str, dict[str, dict[str, Any]]], pair: str) -> list[dict[str, Any]]:
    venues: list[dict[str, Any]] = []
    for exchange_id, symbols in books.items():
        book = symbols.get(pair)
        if not book:
            continue
        row = _venue_row(exchange_id, book)
        if row is not None:
            venues.append(row)
    return venues


def _append_feed_lag_opportunity(
    opportunities: list[dict[str, Any]],
    slow: dict[str, Any],
    ref_mid: float,
    lag_sec: float,
    min_edge_bps: float,
) -> None:
    edge_bps = (ref_mid - slow["best_ask"]) / ref_mid * 10_000
    reverse_edge_bps = (slow["best_bid"] - ref_mid) / ref_mid * 10_000
    if edge_bps >= min_edge_bps:
        opportunities.append(_feed_lag_opportunity(slow, ref_mid, lag_sec, reverse=False))
    elif reverse_edge_bps >= min_edge_bps:
        opportunities.append(_feed_lag_opportunity(slow, ref_mid, lag_sec, reverse=True))


def scan_feed_lag_from_books(
    books: dict[str, dict[str, dict[str, Any]]],
    pair: str,
    *,
    lag_threshold_sec: float = DEFAULT_LAG_THRESHOLD_SEC,
    min_edge_bps: float = DEFAULT_EDGE_BPS,
) -> dict[str, Any]:
    venues = _venues_from_books(books, pair)

    fast_refs = [v for v in venues if v["speed_tier"] == "fast" and v["timestamp_epoch"]]
    slow_refs = [v for v in venues if v["speed_tier"] == "slow" and v["timestamp_epoch"]]

    opportunities: list[dict[str, Any]] = []
    if not fast_refs or not slow_refs:
        return {
            "symbol": pair,
            "opportunities": [],
            "venue_count": len(venues),
            "timestamp": _utcnow_iso(),
        }

    ref_mid = sum(v["mid"] for v in fast_refs) / len(fast_refs)
    ref_ts = max(v["timestamp_epoch"] for v in fast_refs if v["timestamp_epoch"])

    for slow in slow_refs:
        lag_sec = ref_ts - float(slow["timestamp_epoch"] or ref_ts)
        if lag_sec < lag_threshold_sec:
            continue

        _append_feed_lag_opportunity(opportunities, slow, ref_mid, lag_sec, min_edge_bps)

    opportunities.sort(key=lambda x: float(x.get("edge_bps") or 0), reverse=True)
    return {
        "symbol": pair,
        "asset": pair.split("/")[0],
        "reference_mid": round(ref_mid, 6),
        "lag_threshold_seconds": lag_threshold_sec,
        "min_edge_bps": min_edge_bps,
        "opportunities": opportunities,
        "venue_count": len(venues),
        "timestamp": _utcnow_iso(),
    }


def scan_feed_lag_from_venues(
    venues: list[dict[str, Any]],
    pair: str = "BTC/USDT",
    *,
    lag_threshold_sec: float = DEFAULT_LAG_THRESHOLD_SEC,
    min_edge_bps: float = DEFAULT_EDGE_BPS,
) -> dict[str, Any]:
    books: dict[str, dict[str, dict[str, Any]]] = {}
    for venue in venues:
        exchange = str(venue.get("exchange") or "")
        if not exchange:
            continue
        books.setdefault(exchange, {})[pair] = {
            "bids": [[venue.get("best_bid"), 1]],
            "asks": [[venue.get("best_ask"), 1]],
            "timestamp": venue.get("timestamp"),
        }
    return scan_feed_lag_from_books(
        books,
        pair,
        lag_threshold_sec=lag_threshold_sec,
        min_edge_bps=min_edge_bps,
    )
