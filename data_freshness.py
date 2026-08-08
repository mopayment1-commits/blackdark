"""
BLACKDARK — Data freshness helpers for Oracle / Live book chips.
"""

from __future__ import annotations

import time
from typing import Any


def freshness_chip(
    *,
    freshness_ms: float | None = None,
    age_sec: float | None = None,
    max_fresh_ms: float = 2000.0,
    max_ok_ms: float = 15000.0,
) -> dict[str, Any]:
    ms: float | None = None
    if freshness_ms is not None:
        ms = float(freshness_ms)
    elif age_sec is not None:
        ms = float(age_sec) * 1000.0
    if ms is None:
        return {
            "label": "Live · age unknown",
            "state": "unknown",
            "freshness_ms": None,
            "age_sec": None,
        }
    age = round(ms / 1000.0, 2)
    if ms <= max_fresh_ms:
        state = "fresh"
        label = f"Live · {age:.1f}s ago"
    elif ms <= max_ok_ms:
        state = "ok"
        label = f"Live · {age:.1f}s ago"
    else:
        state = "stale"
        label = f"Stale · {age:.1f}s ago"
    return {
        "label": label,
        "state": state,
        "freshness_ms": round(ms, 1),
        "age_sec": age,
        "as_of_unix": time.time() - (ms / 1000.0),
    }


def attach_oracle_freshness(payload: dict[str, Any]) -> dict[str, Any]:
    """Best-effort attach freshness from live book / payload fields."""
    out = dict(payload)
    ms = out.get("freshness_ms")
    age = out.get("data_age_sec") or out.get("quote_age_sec")
    if ms is None and age is None:
        try:
            from live_book_hub import get_top_of_book

            asset = str(out.get("asset") or out.get("symbol") or "BTC").upper().replace("USDT", "")
            book = get_top_of_book(f"{asset}USDT") or get_top_of_book(asset)
            if isinstance(book, dict):
                ms = book.get("freshness_ms") or book.get("stalest_ms")
                if ms is None and book.get("ts"):
                    age = max(0.0, time.time() - float(book["ts"]))
        except Exception:
            pass
    chip = freshness_chip(freshness_ms=ms, age_sec=age)
    out["data_freshness"] = chip
    out["freshness_ms"] = chip.get("freshness_ms")
    return out
