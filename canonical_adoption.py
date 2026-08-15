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
    normalize_chain,
    normalize_symbol,
    normalize_venue,
)

# Production surfaces that MUST call adopt_* before domain logic.
CRITICAL_PATHS: tuple[str, ...] = (
    "aggregator",
    "price_stream",
    "arbitrage_engine",
    "funding",
    "cex_dex",
    "onchain",
    "whale",
    "portfolio",
    "risk",
    "decision",
    "execution",
    "oms",
    "streaming",
    "news_macro",
    "b2b",
    "ui_super_terminal",
)

_ADOPTION_AUDIT: dict[str, int] = {p: 0 for p in CRITICAL_PATHS}


def _mark(path: str) -> None:
    if path in _ADOPTION_AUDIT:
        _ADOPTION_AUDIT[path] += 1


def adopt_venue(venue: str) -> str:
    return normalize_venue(venue)


def adopt_symbol(symbol: str) -> str:
    return normalize_symbol(symbol)


def adopt_chain(chain: str) -> str:
    return normalize_chain(chain)


def adopt_order_books(
    order_books: dict[str, dict[str, dict[str, Any]]],
    *,
    source: str = "order_books",
    provider_timestamp: Any | None = None,
    path: str = "arbitrage_engine",
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
    _mark(path)
    return out


def adopt_funding_rates(
    funding_rates: dict[str, dict[str, dict[str, Any]]],
    *,
    source: str = "funding_rates",
    path: str = "funding",
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
    _mark(path)
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
    path: str = "price_stream",
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
    _mark(path)
    return {
        **datum.payload,
        "freshness_class": datum.provenance.freshness_class.value,
        "provenance": datum.provenance.to_dict(),
    }


def adopt_market_snapshot(
    *,
    exchange: str,
    symbol: str,
    price: float,
    bids: list[Any],
    asks: list[Any],
    timestamp: Any,
    volume: float | None = None,
    market_type: str = "spot",
    source: str = "aggregator",
) -> dict[str, Any]:
    """Canonicalize aggregator/hot-storage market snapshots before persistence."""
    v = adopt_venue(exchange)
    s = adopt_symbol(symbol)
    if price is None or float(price) <= 0:
        raise ValueError("snapshot_price_invalid")
    if not bids or not asks:
        raise ValueError("snapshot_book_empty")
    best_bid = float(bids[0][0]) if isinstance(bids[0], (list, tuple)) else float(bids[0])
    best_ask = float(asks[0][0]) if isinstance(asks[0], (list, tuple)) else float(asks[0])
    bid_qty = float(bids[0][1]) if isinstance(bids[0], (list, tuple)) and len(bids[0]) > 1 else None
    ask_qty = float(asks[0][1]) if isinstance(asks[0], (list, tuple)) and len(asks[0]) > 1 else None
    quote = adopt_tick_quote(
        venue=v,
        symbol=s,
        bid=best_bid,
        ask=best_ask,
        source=source,
        provider_timestamp=timestamp,
        bid_qty=bid_qty,
        ask_qty=ask_qty,
        require_live=False,
        path="aggregator",
    )
    books = adopt_order_books(
        {v: {s: {"bids": bids, "asks": asks, "venue": v, "symbol": s}}},
        source=source,
        provider_timestamp=timestamp,
        path="aggregator",
    )
    ingest(
        entity_type=EntityType.MARKET,
        id=f"{v}:{s}:{market_type}",
        payload={
            "venue": v,
            "symbol": s,
            "price": float(price),
            "volume": float(volume) if volume is not None else None,
            "market_type": market_type,
            "quote": quote,
        },
        source=source,
        provider_timestamp=timestamp,
        max_live_age_sec=5.0,
        max_degraded_age_sec=30.0,
    )
    return {
        "exchange": v,
        "symbol": s,
        "price": float(price),
        "volume": float(volume) if volume is not None else None,
        "bids": bids,
        "asks": asks,
        "market_type": market_type,
        "timestamp": timestamp,
        "canonical_quote": quote,
        "canonical_books": books,
        "freshness_class": quote.get("freshness_class"),
    }


def adopt_funding_snapshot(
    *,
    exchange: str,
    symbol: str,
    funding_rate: float,
    timestamp: Any,
    next_funding_time: Any = None,
    source: str = "aggregator_funding",
) -> dict[str, Any]:
    v = adopt_venue(exchange)
    s = adopt_symbol(symbol)
    row = {
        "funding_rate": float(funding_rate),
        "timestamp": timestamp,
        "next_funding_time": next_funding_time,
    }
    adopted = adopt_funding_rates({v: {s: row}}, source=source, path="aggregator")
    return adopted[v][s]


def adopt_onchain_flows(
    flows: list[dict[str, Any]],
    *,
    source: str = "onchain_tracker",
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for flow in flows:
        row = dict(flow)
        asset = row.get("asset") or row.get("symbol")
        if asset:
            try:
                row["asset"] = adopt_symbol(str(asset) if "/" in str(asset) else f"{asset}/USDT").split("/")[0]
                row["symbol"] = adopt_symbol(f"{row['asset']}/USDT")
            except ValueError:
                row["asset"] = str(asset).strip().upper()
                row["symbol"] = row["asset"]
        if row.get("chain"):
            row["chain"] = adopt_chain(str(row["chain"]))
        ingest(
            entity_type=EntityType.WALLET if row.get("wallet") else EntityType.ASSET,
            id=str(row.get("id") or row.get("tx_hash") or f"onchain:{row.get('asset')}:{len(out)}"),
            payload=row,
            source=source,
            provider_timestamp=row.get("timestamp") or datetime.now(UTC),
            require_provider_ts=False,
            max_live_age_sec=120.0,
            max_degraded_age_sec=900.0,
        )
        out.append(row)
    _mark("onchain")
    return out


def adopt_positions(
    positions: list[dict[str, Any]],
    *,
    source: str = "portfolio",
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for p in positions:
        row = dict(p)
        if row.get("venue"):
            row["venue"] = adopt_venue(str(row["venue"]))
        asset = row.get("asset") or row.get("symbol")
        if asset:
            try:
                if "/" in str(asset):
                    row["symbol"] = adopt_symbol(str(asset))
                    row["asset"] = row["symbol"].split("/")[0]
                else:
                    row["asset"] = str(asset).strip().upper()
                    row["symbol"] = adopt_symbol(f"{row['asset']}/USDT")
            except ValueError:
                row["asset"] = str(asset).strip().upper()
        ingest(
            entity_type=EntityType.POSITION,
            id=str(row.get("position_id") or f"{row.get('asset')}:{row.get('side')}:{len(out)}"),
            payload=row,
            source=source,
            provider_timestamp=row.get("timestamp") or datetime.now(UTC),
            require_provider_ts=False,
            max_live_age_sec=60.0,
            max_degraded_age_sec=600.0,
        )
        out.append(row)
    _mark("portfolio")
    return out


def adopt_risk_report(report: dict[str, Any], *, source: str = "risk") -> dict[str, Any]:
    row = dict(report)
    if row.get("symbol"):
        try:
            row["symbol"] = adopt_symbol(str(row["symbol"]))
        except ValueError:
            pass
    if row.get("venue"):
        row["venue"] = adopt_venue(str(row["venue"]))
    ingest(
        entity_type=EntityType.RISK,
        id=str(row.get("id") or f"risk:{row.get('kind')}:{row.get('symbol') or 'na'}"),
        payload=row,
        source=source,
        provider_timestamp=datetime.now(UTC),
        require_provider_ts=False,
        max_live_age_sec=30.0,
        max_degraded_age_sec=300.0,
    )
    _mark("risk")
    return row


def adopt_decision_market_state(market_state: dict[str, Any], *, source: str = "decision") -> dict[str, Any]:
    row = dict(market_state)
    if row.get("symbol"):
        row["symbol"] = adopt_symbol(str(row["symbol"]))
    if row.get("venue"):
        row["venue"] = adopt_venue(str(row["venue"]))
    ingest(
        entity_type=EntityType.DECISION,
        id=str(row.get("id") or f"market:{row.get('symbol') or 'unknown'}"),
        payload=row,
        source=source,
        provider_timestamp=row.get("timestamp") or datetime.now(UTC),
        require_provider_ts=False,
        max_live_age_sec=30.0,
        max_degraded_age_sec=300.0,
    )
    _mark("decision")
    return row


def adopt_oms_intent(
    *,
    venue: str,
    symbol: str,
    side: str,
    quantity: float,
    source: str = "oms",
) -> dict[str, Any]:
    v = adopt_venue(venue)
    s = adopt_symbol(symbol)
    payload = {"venue": v, "symbol": s, "side": side.lower(), "quantity": float(quantity)}
    ingest(
        entity_type=EntityType.EXECUTION,
        id=f"oms_intent:{v}:{s}:{side}:{quantity}",
        payload=payload,
        source=source,
        provider_timestamp=datetime.now(UTC),
        require_provider_ts=False,
        max_live_age_sec=5.0,
        max_degraded_age_sec=60.0,
    )
    _mark("oms")
    return payload


def reset_adoption_audit_for_tests() -> None:
    for k in _ADOPTION_AUDIT:
        _ADOPTION_AUDIT[k] = 0


def adoption_audit() -> dict[str, Any]:
    return {
        "critical_paths": list(CRITICAL_PATHS),
        "counts": dict(_ADOPTION_AUDIT),
        "paths_touched": sorted(k for k, v in _ADOPTION_AUDIT.items() if v > 0),
        "bypass_forbidden": True,
    }


def adoption_status() -> dict[str, Any]:
    return {
        "surface": "canonical_adoption",
        "product_complete": False,
        "critical_paths": list(CRITICAL_PATHS),
        "bypass_forbidden": True,
        "stale_as_live_forbidden": True,
        "freshness_classes": [f.value for f in FreshnessClass],
        "audit": adoption_audit(),
        "note": "Critical paths must call adopt_* before financial/decision logic.",
    }
