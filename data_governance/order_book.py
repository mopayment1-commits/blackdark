"""Order book integrity — sequence gaps, stale depth, resync policy."""

from __future__ import annotations

from typing import Any


def evaluate_order_book_integrity(book: dict[str, Any] | None) -> dict[str, Any]:
    if not book:
        return {"integrity_ok": False, "reason": "missing_book", "sequence_gaps": [], "stale": True}
    bid = book.get("bid") or book.get("best_bid")
    ask = book.get("ask") or book.get("best_ask")
    crossed = bid and ask and float(bid) >= float(ask)
    age_ms = book.get("freshness_ms") or book.get("stalest_ms")
    stale = age_ms is None or float(age_ms) > 5000
    seq_gap = bool(book.get("sequence_gap"))
    return {
        "integrity_ok": not crossed and not stale and not seq_gap,
        "crossed_book": crossed,
        "stale_depth": stale,
        "sequence_gap": seq_gap,
        "freshness_ms": age_ms,
        "resync_required": seq_gap or crossed,
    }


def order_book_from_live(symbol: str) -> dict[str, Any]:
    try:
        from live_book_hub import get_top_of_book

        asset = symbol.upper().replace("USDT", "")
        book = get_top_of_book(f"{asset}USDT") or get_top_of_book(asset) or {}
        return evaluate_order_book_integrity(book)
    except Exception:
        return evaluate_order_book_integrity(None)
