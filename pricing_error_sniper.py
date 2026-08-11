"""
BLACKDARK — Pricing Error Sniper (Plan Point 29).

Detects temporary mispricing when one venue's book diverges sharply from the
cross-venue median during refresh windows (classic exchange update glitch).
"""

from __future__ import annotations

import logging
import statistics
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger("BLACKDARK.PricingErrorSniper")

DEFAULT_DEVIATION_BPS = 35.0
MIN_VENUES = 3


def _utcnow_iso() -> str:
    return datetime.now(UTC).isoformat()


def _clean_venue(venue: dict[str, Any]) -> tuple[float, dict[str, Any]] | None:
    bid = venue.get("best_bid")
    ask = venue.get("best_ask")
    if bid is None or ask is None:
        return None
    try:
        bid_f = float(bid)
        ask_f = float(ask)
    except (TypeError, ValueError):
        return None
    if bid_f <= 0 or ask_f <= 0 or ask_f < bid_f:
        return None
    mid = (bid_f + ask_f) / 2
    return mid, {**venue, "mid": mid, "best_bid": bid_f, "best_ask": ask_f}


def _pricing_opportunity(venue: dict[str, Any], median_mid: float, deviation_bps_actual: float) -> dict[str, Any]:
    mid = float(venue["mid"])
    direction = "underpriced" if mid < median_mid else "overpriced"
    return {
        "kind": "pricing_error",
        "exchange": venue.get("exchange"),
        "direction": direction,
        "venue_mid": round(mid, 6),
        "reference_mid": round(median_mid, 6),
        "deviation_bps": round(deviation_bps_actual, 2),
        "edge_bps": round(deviation_bps_actual, 2),
        "best_bid": round(float(venue["best_bid"]), 6),
        "best_ask": round(float(venue["best_ask"]), 6),
        "timestamp": venue.get("timestamp"),
        "note": (
            f"{venue.get('exchange')} {direction} vs median — "
            "possible stale tick during venue refresh"
        ),
    }


def scan_pricing_errors(
    venues: list[dict[str, Any]],
    *,
    pair: str = "BTC/USDT",
    deviation_bps: float = DEFAULT_DEVIATION_BPS,
) -> dict[str, Any]:
    mids: list[float] = []
    clean: list[dict[str, Any]] = []

    for venue in venues:
        clean_venue = _clean_venue(venue)
        if clean_venue is None:
            continue
        mid, row = clean_venue
        mids.append(mid)
        clean.append(row)

    if len(mids) < MIN_VENUES:
        return {
            "symbol": pair,
            "asset": pair.split("/")[0],
            "opportunities": [],
            "venue_count": len(clean),
            "reason": "insufficient_venues",
            "timestamp": _utcnow_iso(),
        }

    median_mid = statistics.median(mids)
    opportunities: list[dict[str, Any]] = []

    for venue in clean:
        mid = float(venue["mid"])
        deviation_bps_actual = abs(mid - median_mid) / median_mid * 10_000
        if deviation_bps_actual < deviation_bps:
            continue

        opportunities.append(_pricing_opportunity(venue, median_mid, deviation_bps_actual))

    opportunities.sort(key=lambda x: float(x.get("deviation_bps") or 0), reverse=True)
    return {
        "symbol": pair,
        "asset": pair.split("/")[0],
        "reference_mid": round(median_mid, 6),
        "deviation_threshold_bps": deviation_bps,
        "opportunities": opportunities,
        "venue_count": len(clean),
        "timestamp": _utcnow_iso(),
    }


def scan_pricing_errors_from_books(
    books: dict[str, dict[str, dict[str, Any]]],
    pair: str,
    *,
    deviation_bps: float = DEFAULT_DEVIATION_BPS,
) -> dict[str, Any]:
    venues: list[dict[str, Any]] = []
    for exchange_id, symbols in books.items():
        book = symbols.get(pair)
        if not book:
            continue
        bids = book.get("bids") or []
        asks = book.get("asks") or []
        if not bids or not asks:
            continue
        venues.append(
            {
                "exchange": exchange_id,
                "best_bid": bids[0][0],
                "best_ask": asks[0][0],
                "timestamp": book.get("timestamp"),
            }
        )
    return scan_pricing_errors(venues, pair=pair, deviation_bps=deviation_bps)
