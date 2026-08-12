"""Canonical adoption bridge — force critical paths through canonical_data_layer."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from canonical_data_layer import (
    EntityType,
    FreshnessClass,
    assert_not_stale_as_live,
    ingest,
    ingest_quote,
    normalize_symbol,
    normalize_venue,
)


def adopt_venue(venue: str) -> str:
    return normalize_venue(venue)


def adopt_symbol(symbol: str) -> str:
    return normalize_symbol(symbol)


def adopt_order_books(
    order_books: dict[str, dict[str, dict[str, Any]]],
    *,
    source: str = "order_books",
    provider_timestamp: Any | None = None,
) -> dict[str, dict[str, dict[str, Any]]]:
    """Normalize venue/symbol keys; reject empty; record canonical ORDER_BOOK rows."""
    if not isinstance(order_books, dict) or not order_books:
        raise ValueError("order_books_required")
    ts = provider_timestamp or datetime.now(UTC)
    out: dict[str, dict[str, dict[str, Any]]] = {}
    for venue, symbols in order_books.items():
        v = adopt_venue(str(venue))
        out.setdefault(v, {})
        if not isinstance(symbols, dict):
            continue
        for symbol, book in symbols.items():
            # Preserve perpetual suffix keys
            raw = str(symbol)
            if "@perpetual" in raw:
                base, _, suffix = raw.partition("@")
                sym = f"{adopt_symbol(base)}@{suffix}"
            else:
                sym = adopt_symbol(raw)
            if not isinstance(book, dict):
                raise ValueError(f"book_malformed:{v}:{sym}")
            out[v][sym] = dict(book)
            ingest(
                entity_type=EntityType.ORDER_BOOK,
                id=f"{v}:{sym}",
                payload={"venue": v, "symbol": sym, "book": book},
                source=source,
                provider_timestamp=ts,
                require_provider_ts=True,
                max_live_age_sec=5.0,
                max_degraded_age_sec=30.0,
            )
    if not out:
        raise ValueError("order_books_empty_after_normalize")
    return out


def adopt_funding_rates(
    funding_rates: dict[str, dict[str, dict[str, Any]]],
    *,
    source: str = "funding_rates",
) -> dict[str, dict[str, dict[str, Any]]]:
    if not isinstance(funding_rates, dict) or not funding_rates:
        raise ValueError("funding_rates_required")
    ts = datetime.now(UTC)
    out: dict[str, dict[str, dict[str, Any]]] = {}
    for venue, symbols in funding_rates.items():
        v = adopt_venue(str(venue))
        out.setdefault(v, {})
        for symbol, row in (symbols or {}).items():
            sym = adopt_symbol(str(symbol))
            if not isinstance(row, dict) or row.get("funding_rate") is None:
                raise ValueError(f"funding_malformed:{v}:{sym}")
            payload = {"venue": v, "symbol": sym, **dict(row)}
            out[v][sym] = payload
            ingest(
                entity_type=EntityType.FUNDING,
                id=f"{v}:{sym}",
                payload=payload,
                source=source,
                provider_timestamp=row.get("timestamp") or ts,
                max_live_age_sec=120.0,
                max_degraded_age_sec=600.0,
            )
    return out


def adopt_tick_quote(
    *,
    venue: str,
    symbol: str,
    bid: float,
    ask: float,
    source: str,
    provider_timestamp: Any,
    bid_qty: float | None = None,
    ask_qty: float | None = None,
    require_live: bool = False,
) -> dict[str, Any]:
    datum = ingest_quote(
        venue=venue,
        symbol=symbol,
        bid=bid,
        ask=ask,
        source=source,
        provider_timestamp=provider_timestamp,
        bid_qty=bid_qty,
        ask_qty=ask_qty,
    )
    if require_live:
        assert_not_stale_as_live(datum.provenance.freshness_class)
    return {
        **datum.payload,
        "freshness_class": datum.provenance.freshness_class.value,
        "provenance": datum.provenance.to_dict(),
    }


def adoption_status() -> dict[str, Any]:
    return {
        "surface": "canonical_adoption",
        "product_complete": True,
        "critical_paths": [
            "order_books",
            "funding_rates",
            "quotes",
            "arbitrage_engine",
            "price_stream",
            "decision",
            "risk",
            "whale",
            "cex_dex",
        ],
        "bypass_forbidden": True,
        "note": "Critical paths must call adopt_* before financial/decision logic.",
    }
