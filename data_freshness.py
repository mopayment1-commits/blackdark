"""
BLACKDARK — Data freshness helpers for Oracle / Live book chips.
"""

from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Any


def _age_sec_from_iso_timestamp(ts: Any) -> float | None:
    if ts is None:
        return None
    try:
        if isinstance(ts, (int, float)):
            return max(0.0, time.time() - float(ts))
        raw = str(ts).strip()
        if not raw:
            return None
        if raw.endswith("Z"):
            raw = f"{raw[:-1]}+00:00"
        dt = datetime.fromisoformat(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return max(0.0, time.time() - dt.timestamp())
    except Exception:
        return None


def _book_age_ms(book: dict[str, Any]) -> float | None:
    ms = book.get("freshness_ms") or book.get("stalest_ms")
    if ms is not None:
        return float(ms)
    ts = book.get("ts") or book.get("timestamp")
    age_sec = _age_sec_from_iso_timestamp(ts)
    if age_sec is not None:
        return age_sec * 1000.0
    if ts is not None:
        try:
            return max(0.0, (time.time() - float(ts)) * 1000.0)
        except Exception:
            return None
    return None


def _quote_age_ms_from_hub(exchange: str, symbol: str) -> float | None:
    try:
        from live_book_hub import get_quote_age_ms

        return get_quote_age_ms(exchange, symbol)
    except Exception:
        return None


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
            "label": "",
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
    asset = str(out.get("asset") or out.get("symbol") or "BTC").upper().replace("USDT", "")
    quote_exchange = str(out.get("quote_exchange") or "binance").strip().lower()
    quote_symbol = str(out.get("quote_symbol") or f"{asset}/USDT").strip().upper()
    if ms is None and age is None:
        try:
            from live_book_hub import get_top_of_book

            book = get_top_of_book(quote_exchange, quote_symbol)
            if not isinstance(book, dict):
                book = get_top_of_book(f"{asset}USDT") or get_top_of_book(asset)
            if isinstance(book, dict):
                ms = _book_age_ms(book)
        except Exception:
            pass
    if ms is None and age is None:
        hub_ms = _quote_age_ms_from_hub(quote_exchange, quote_symbol)
        if hub_ms is not None:
            ms = hub_ms
    chip = freshness_chip(freshness_ms=ms, age_sec=age)
    out["data_freshness"] = chip
    out["freshness_ms"] = chip.get("freshness_ms")
    try:
        from data_provenance_score import attach_provenance

        out = attach_provenance(out)
    except Exception:
        pass
    return out
