"""
BLACKDARK — Stale price guard (Latency Arbitrage protection).

Rejects quotes older than EXECUTION_MAX_QUOTE_AGE_MS before scan alerts or live orders.
Target: no execution on WS data older than ~300ms (HFT arb window).
"""

from __future__ import annotations

from typing import Any

import config
from live_book_hub import get_quote_age_ms, hub_stats, is_quote_fresh


def max_quote_age_ms(*, for_execution: bool = False) -> float:
    if for_execution:
        return float(getattr(config, "EXECUTION_MAX_QUOTE_AGE_MS", 300))
    return float(getattr(config, "FAST_SCAN_MAX_QUOTE_AGE_MS", getattr(config, "LIVE_BOOK_MAX_AGE_MS", 300)))


def guard_enabled() -> bool:
    return getattr(config, "STALE_PRICE_GUARD_ENABLED", True)


def validate_venue_quote(exchange: str, symbol: str, *, for_execution: bool = False) -> tuple[bool, float | None, str]:
    """Return (fresh, age_ms, reason)."""
    if not guard_enabled():
        return True, get_quote_age_ms(exchange, symbol), "guard_disabled"

    limit = max_quote_age_ms(for_execution=for_execution)
    age = get_quote_age_ms(exchange, symbol)
    if age is None:
        return False, None, f"no_quote:{exchange}:{symbol}"
    if age > limit:
        return False, age, f"stale_quote:{exchange}:{symbol}:{age:.0f}ms>{limit:.0f}ms"
    return True, age, "ok"


def _normalized_symbol(opportunity: dict[str, Any]) -> str:
    symbol = str(opportunity.get("symbol") or f"{opportunity.get('asset', 'BTC')}/USDT")
    if not symbol.endswith("/USDT"):
        symbol = f"{symbol.replace('/USDT', '')}/USDT"
    return symbol


def _opportunity_legs(opportunity: dict[str, Any], symbol: str, kind: str) -> list[tuple[str, str]] | None:
    legs: list[tuple[str, str]] = []
    if kind in {"cross_exchange", "fast_cross", "stream_cross_exchange", "cex_dex"}:
        buy = str(opportunity.get("buy_exchange") or opportunity.get("buy_venue") or "")
        sell = str(opportunity.get("sell_exchange") or opportunity.get("sell_venue") or "")
        if buy:
            legs.append((buy, symbol))
        if sell:
            legs.append((sell, symbol))
        return legs
    if kind == "triangular":
        ex = str(opportunity.get("exchange") or "binance")
        return [(ex, str(leg_sym)) for leg_sym, _side in opportunity.get("legs") or []]
    return None


def _venue_scan_passes(asset: str, *, for_execution: bool) -> bool:
    sym = f"{asset}/USDT"
    return any(
        is_quote_fresh(venue, sym, max_age_ms=max_quote_age_ms(for_execution=for_execution))
        for venue in getattr(config, "WS_PRICE_VENUES", ())
    )


def _quote_age_details(legs: list[tuple[str, str]], *, for_execution: bool) -> tuple[list[dict[str, Any]], dict[str, float]]:
    stale: list[dict[str, Any]] = []
    fresh_ages: dict[str, float] = {}
    for exchange, sym in legs:
        ok, age, reason = validate_venue_quote(exchange, sym, for_execution=for_execution)
        if not ok:
            stale.append({"exchange": exchange, "symbol": sym, "age_ms": age, "reason": reason})
        elif age is not None:
            fresh_ages[f"{exchange}|{sym}"] = round(age, 2)
    return stale, fresh_ages


def validate_opportunity_quotes(opportunity: dict[str, Any], *, for_execution: bool = False) -> tuple[bool, dict[str, Any]]:
    """
    Validate all exchange legs referenced by an opportunity.
    Returns (allowed, detail).
    """
    if not guard_enabled():
        return True, {"guard": "disabled"}

    kind = str(opportunity.get("kind") or "")
    symbol = _normalized_symbol(opportunity)
    legs = _opportunity_legs(opportunity, symbol, kind)
    if legs is None:
        asset = str(opportunity.get("asset") or "BTC")
        if _venue_scan_passes(asset, for_execution=for_execution):
            return True, {"guard": "ok", "kind": kind, "note": "venue_scan_pass"}
        legs = []

    if not legs:
        return True, {"guard": "ok", "kind": kind, "note": "no_legs_to_check"}

    stale, fresh_ages = _quote_age_details(legs, for_execution=for_execution)

    if stale:
        return False, {
            "guard": "blocked",
            "reason": "stale_prices",
            "max_age_ms": max_quote_age_ms(for_execution=for_execution),
            "stale_legs": stale,
            "fresh_ages_ms": fresh_ages,
        }

    worst = max(fresh_ages.values()) if fresh_ages else 0.0
    return True, {
        "guard": "ok",
        "max_age_ms": max_quote_age_ms(for_execution=for_execution),
        "worst_age_ms": worst,
        "fresh_ages_ms": fresh_ages,
    }


def stale_guard_status() -> dict[str, Any]:
    stats = hub_stats()
    limit = max_quote_age_ms(for_execution=True)
    return {
        "enabled": guard_enabled(),
        "execution_max_age_ms": limit,
        "fast_scan_max_age_ms": max_quote_age_ms(for_execution=False),
        "live_book_max_age_ms": float(getattr(config, "LIVE_BOOK_MAX_AGE_MS", 300)),
        "hub": stats,
        "policy": (
            "Quotes older than limit are rejected before alerts and live execution. "
            "WS-only ingestion; REST blocked in PRICE_FEED_WS_ONLY mode."
        ),
    }
