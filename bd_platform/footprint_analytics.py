"""Footprint / order-flow analytics from live book hub + DB depth."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


async def footprint_snapshot(asset: str = "BTC") -> dict[str, Any]:
    from database import fetch_latest_order_books
    from live_book_hub import get_best_price

    symbol = f"{asset.upper()}/USDT"
    venues = ("binance", "okx", "bybit", "kraken")
    top_rows: list[dict[str, Any]] = []
    for ex in venues:
        row = get_best_price(ex, symbol)
        if not row:
            continue
        spread_bps = ((row["ask"] - row["bid"]) / row["mid"]) * 10_000 if row["mid"] else 0
        top_rows.append({
            "exchange": ex,
            "bid": row["bid"],
            "ask": row["ask"],
            "mid": row["mid"],
            "spread_bps": round(spread_bps, 2),
        })

    books = await fetch_latest_order_books()
    depth_rows: list[dict[str, Any]] = []
    bid_depth = 0.0
    ask_depth = 0.0
    for ex, syms in (books or {}).items():
        book = syms.get(symbol) or syms.get(f"{asset.upper()}USDT")
        if not book:
            continue
        bids = book.get("bids") or []
        asks = book.get("asks") or []
        b5 = sum(float(b[1]) for b in bids[:5])
        a5 = sum(float(a[1]) for a in asks[:5])
        bid_depth += b5
        ask_depth += a5
        imbalance = (b5 - a5) / (b5 + a5) if (b5 + a5) > 0 else 0
        depth_rows.append({
            "exchange": ex,
            "bid_depth_5": round(b5, 4),
            "ask_depth_5": round(a5, 4),
            "imbalance": round(imbalance, 4),
        })

    delta = bid_depth - ask_depth
    return {
        "asset": asset.upper(),
        "timestamp": _utcnow(),
        "top_of_book": top_rows,
        "depth_levels": depth_rows[:8],
        "aggregate_bid_depth_5": round(bid_depth, 4),
        "aggregate_ask_depth_5": round(ask_depth, 4),
        "order_flow_delta": round(delta, 4),
        "type": "multi_venue_footprint",
        "note": "5-level depth imbalance across CEX books",
    }
