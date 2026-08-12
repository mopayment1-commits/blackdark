"""Canonical Truth Bus — sole production path for sensitive computations.

LIVE DATA → CANONICAL → consumers (Risk / Decision / Whale / Execution / Terminal)

Production consumers must call `require_live_books` / `require_canonical_quote`.
Synthetic / fabricated L2 sizes are forbidden on production execution paths.
"""

from __future__ import annotations

import asyncio
import threading
from datetime import UTC, datetime
from typing import Any

from canonical_adoption import adopt_order_books, adoption_audit
from canonical_data_layer import EntityType, FreshnessClass, get_datum, reset_store_for_tests

_LOCK = threading.RLock()
_LAST_REFRESH: dict[str, Any] = {"at": None, "venues": [], "ok": False}
_BOOKS: dict[str, dict[str, dict[str, Any]]] = {}
_FUNDING: dict[str, dict[str, dict[str, Any]]] = {}


def _run(coro: Any) -> Any:
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                return pool.submit(asyncio.run, coro).result(timeout=45)
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


def _book_from_probe(probe: dict[str, Any], *, symbol: str) -> dict[str, Any] | None:
    if not (probe.get("ok") and probe.get("live")):
        return None
    bids = probe.get("bids") or []
    asks = probe.get("asks") or []
    if not bids or not asks:
        return None
    if probe.get("fabricated_depth"):
        return None
    if probe.get("depth_source") not in {"venue_l2", "venue_tob"}:
        return None
    # Institutional consumers require multi-level L2 when available; TOB alone is marked.
    return {
        "bids": [[float(p), float(q)] for p, q in bids],
        "asks": [[float(p), float(q)] for p, q in asks],
        "venue": probe["venue"],
        "symbol": symbol,
        "depth_source": probe.get("depth_source"),
        "fabricated_depth": False,
        "source": probe.get("source"),
    }


async def _fetch_venue_perp_and_funding(
    venue: str,
    symbol: str,
    session: Any,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """Pull venue perpetual book + funding via aggregator (real sizes / rates)."""
    from aggregator import FUNDING_FETCHERS, MARKET_FETCHERS

    market_fn = MARKET_FETCHERS.get(venue)
    funding_fn = FUNDING_FETCHERS.get(venue)
    if market_fn is None or funding_fn is None:
        return None, None
    try:
        _ticker, book = await market_fn(session, symbol, "perpetual")
        funding = await funding_fn(session, symbol)
    except Exception:
        return None, None

    perp = None
    if book and getattr(book, "bids", None) and getattr(book, "asks", None):
        perp = {
            "bids": [[float(p), float(q)] for p, q in book.bids],
            "asks": [[float(p), float(q)] for p, q in book.asks],
            "venue": venue,
            "symbol": f"{symbol}@perpetual",
            "market_type": "perpetual",
            "depth_source": "venue_l2",
            "fabricated_depth": False,
            "source": f"{venue}_public_perp_books",
        }
    fund = None
    if funding is not None:
        fund = {
            "funding_rate": float(funding.funding_rate),
            "next_funding_time": getattr(funding, "next_funding_time", None),
            "venue": venue,
            "symbol": symbol,
            "source": f"{venue}_public_funding",
            "timestamp": datetime.now(UTC).isoformat(),
            "synthetic": False,
        }
    return perp, fund


async def _fetch_multi_venue_perp_funding(symbol: str) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]], list[str]]:
    """OKX + Bybit public perpetual/funding (Kraken is spot-only — excluded)."""
    import aiohttp

    perps: dict[str, dict[str, Any]] = {}
    funds: dict[str, dict[str, Any]] = {}
    venues_ok: list[str] = []
    timeout = aiohttp.ClientTimeout(total=15)
    # Prefer venues with public perp+funding reachable in restricted regions.
    # Bybit/Binance often 403/451 here; OKX/Gate/Bitget/KuCoin typically work.
    async with aiohttp.ClientSession(timeout=timeout) as session:
        for venue in ("okx", "gateio", "bitget", "kucoin", "bybit"):
            perp, fund = await _fetch_venue_perp_and_funding(venue, symbol, session)
            if perp:
                perps[venue] = perp
            if fund:
                funds[venue] = fund
            if perp and fund:
                venues_ok.append(venue)
    return perps, funds, venues_ok


async def refresh_live_truth(*, symbol: str = "BTC/USDT") -> dict[str, Any]:
    """Pull public live venue L2 (+ multi-venue perp/funding) into canonical books."""
    from live_data_truth_probe import (
        prove_multi_venue_live,
        probe_kraken_depth,
        probe_okx_book,
    )

    proof = await prove_multi_venue_live()
    books: dict[str, dict[str, dict[str, Any]]] = {}
    quotes: list[dict[str, Any]] = []
    funding: dict[str, dict[str, dict[str, Any]]] = {}
    depth_meta: dict[str, Any] = {"fabricated_rejected": True, "venues_l2": [], "perp_venues": []}

    okx = await probe_okx_book("BTC-USDT", depth=20)
    okx_book = _book_from_probe(okx, symbol=symbol)
    if okx_book:
        books.setdefault("okx", {})[symbol] = okx_book
        quotes.append(okx)
        if okx_book.get("depth_source") == "venue_l2":
            depth_meta["venues_l2"].append("okx")

    kr = await probe_kraken_depth("XBTUSDT", depth=25)
    kr_book = _book_from_probe(kr, symbol=symbol)
    if kr_book:
        books.setdefault("kraken", {})[symbol] = kr_book
        quotes.append(kr)
        if kr_book.get("depth_source") == "venue_l2":
            depth_meta["venues_l2"].append("kraken")

    perps, funds, perp_venues = await _fetch_multi_venue_perp_funding(symbol)
    for venue, perp in perps.items():
        books.setdefault(venue, {})[f"{symbol}@perpetual"] = perp
    for venue, fund in funds.items():
        funding.setdefault(venue, {})[symbol] = fund
    depth_meta["perp_venues"] = list(perp_venues)
    depth_meta["funding_venues"] = sorted(funds.keys())

    # Fetch spot L2 for perp venues missing spot so Super Terminal can pair spot+perp.
    missing_spot = [v for v in perps if symbol not in books.get(v, {})]
    if missing_spot:
        try:
            import aiohttp

            from aggregator import MARKET_FETCHERS

            timeout = aiohttp.ClientTimeout(total=12)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                for venue in missing_spot:
                    fn = MARKET_FETCHERS.get(venue)
                    if not fn:
                        continue
                    try:
                        _t, book = await fn(session, symbol, "spot")
                    except Exception:
                        continue
                    if book and book.bids and book.asks:
                        books.setdefault(venue, {})[symbol] = {
                            "bids": [[float(p), float(q)] for p, q in book.bids],
                            "asks": [[float(p), float(q)] for p, q in book.asks],
                            "venue": venue,
                            "symbol": symbol,
                            "depth_source": "venue_l2",
                            "fabricated_depth": False,
                            "source": f"{venue}_public_spot_books",
                        }
                        depth_meta["venues_l2"].append(venue)
        except Exception:
            pass

    adopted: dict[str, Any] = {}
    if books:
        adopted = adopt_order_books(books, source="canonical_truth_bus", path="streaming")

    l2_ok = len(depth_meta["venues_l2"]) >= 1
    with _LOCK:
        _BOOKS.clear()
        _BOOKS.update(adopted or books)
        _FUNDING.clear()
        _FUNDING.update(funding)
        _LAST_REFRESH.update(
            {
                "at": datetime.now(UTC).isoformat(),
                "venues": sorted(_BOOKS.keys()),
                "ok": bool(_BOOKS) and l2_ok and bool(proof.get("ok") or quotes),
                "proof": proof,
                "quote_count": len(quotes),
                "live_count": sum(1 for q in quotes if q.get("live")),
                "l2_venues": sorted(set(depth_meta["venues_l2"])),
                "fabricated_depth": False,
                "perp_present": bool(perps),
                "funding_present": bool(funds),
                "perp_venues": list(perp_venues),
                "funding_venues": sorted(funds.keys()),
                "depth_meta": depth_meta,
            }
        )
    return {
        "ok": _LAST_REFRESH["ok"],
        "venues": list(_LAST_REFRESH["venues"]),
        "l2_venues": list(_LAST_REFRESH.get("l2_venues") or []),
        "perp_venues": list(_LAST_REFRESH.get("perp_venues") or []),
        "books": {v: list(syms.keys()) for v, syms in _BOOKS.items()},
        "funding_venues": sorted(funding.keys()),
        "proof": proof,
        "canonical_adoption": adoption_audit(),
        "fabricated_depth": False,
        "refreshed_at": _LAST_REFRESH["at"],
    }


def refresh_live_truth_sync(*, symbol: str = "BTC/USDT") -> dict[str, Any]:
    return _run(refresh_live_truth(symbol=symbol))


def get_live_books(*, require_live: bool = True, symbol: str = "BTC/USDT") -> dict[str, dict[str, dict[str, Any]]]:
    """Return canonical live books; refresh if empty. Fail closed if require_live and none."""
    with _LOCK:
        empty = not _BOOKS
    if empty:
        refresh_live_truth_sync(symbol=symbol)
    with _LOCK:
        books = {v: dict(syms) for v, syms in _BOOKS.items()}
        meta = dict(_LAST_REFRESH)
    if require_live and not books:
        raise ValueError("live_books_unavailable_fail_closed")
    if require_live and not meta.get("ok"):
        raise ValueError("live_truth_stale_or_unavailable")
    if require_live and meta.get("fabricated_depth"):
        raise ValueError("fabricated_depth_forbidden")
    return books


def get_live_funding(*, require_live: bool = True, symbol: str = "BTC/USDT") -> dict[str, dict[str, dict[str, Any]]]:
    with _LOCK:
        empty_books = not _BOOKS
        funding = {v: dict(syms) for v, syms in _FUNDING.items()}
    if empty_books or not funding:
        refresh_live_truth_sync(symbol=symbol)
        with _LOCK:
            funding = {v: dict(syms) for v, syms in _FUNDING.items()}
    if require_live and not funding:
        raise ValueError("live_funding_unavailable_fail_closed")
    return funding


def require_canonical_quote(*, venue: str, symbol: str) -> dict[str, Any]:
    from canonical_adoption import adopt_symbol, adopt_venue

    v = adopt_venue(venue)
    s = adopt_symbol(symbol)
    datum = get_datum(EntityType.QUOTE, f"{v}:{s}")
    if datum is None:
        raise ValueError(f"canonical_quote_missing:{v}:{s}")
    if datum.provenance.freshness_class is not FreshnessClass.LIVE:
        raise ValueError(f"canonical_quote_not_live:{datum.provenance.freshness_class.value}")
    return {**datum.payload, "provenance": datum.provenance.to_dict()}


def production_books_or_raise(symbol: str = "BTC/USDT") -> dict[str, dict[str, dict[str, Any]]]:
    """Alias for production consumers — never returns synthetic books."""
    return get_live_books(require_live=True, symbol=symbol)


def book_notional_depth_usd(book: dict[str, Any], *, side: str = "bid", levels: int = 10) -> float:
    key = "bids" if side in {"bid", "bids", "buy"} else "asks"
    total = 0.0
    for p, q in (book.get(key) or [])[:levels]:
        total += float(p) * float(q)
    return total


def bus_status() -> dict[str, Any]:
    with _LOCK:
        meta = dict(_LAST_REFRESH)
        venues = list(_BOOKS.keys())
        funding_venues = list(_FUNDING.keys())
    return {
        "surface": "canonical_truth_bus",
        "last_refresh": meta,
        "venues_cached": venues,
        "funding_venues": funding_venues,
        "bypass_forbidden": True,
        "synthetic_forbidden_on_production": True,
        "fabricated_depth_forbidden": True,
        "pipeline": "LIVE→CANONICAL→RISK→DECISION→EXECUTION→UI/API",
        "verified_complete": False,
        "implementation_class": "PARTIAL",
        "product_complete": False,
    }


def reset_bus_for_tests() -> None:
    with _LOCK:
        _BOOKS.clear()
        _FUNDING.clear()
        _LAST_REFRESH.update({"at": None, "venues": [], "ok": False, "fabricated_depth": False})
    reset_store_for_tests()
