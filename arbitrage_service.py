"""
BLACKDARK — Arbitrage API service (Wave 3).

Live cross-exchange, triangular, spot-futures basis, and funding scans
for the dashboard with exchange comparison and alert hooks.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import UTC, datetime
from typing import Any, Literal

import aiohttp

import config
from ai_oracle import explain_opportunity
from arbitrage_engine import (
    calculate_cross_exchange_arbitrage,
    calculate_funding_arbitrage_with_institutional_context,
    calculate_spot_futures_premium,
    calculate_triangular_arbitrage,
)
from whale_tracker import get_latest_institutional_context

logger = logging.getLogger("BLACKDARK.ArbitrageService")

OpportunityKind = Literal["cross_exchange", "triangular", "spot_futures", "funding"]

_DURATION_LABELS: dict[str, str] = {
    "cross_exchange": "5–15 min (withdrawal)",
    "triangular": "< 30 sec (same venue)",
    "spot_futures": "1–5 min",
    "funding": "8 h (funding interval)",
}


def _utcnow_iso() -> str:
    return datetime.now(UTC).isoformat()


def _asset_from_symbol(symbol: str) -> str:
    return symbol.split("/")[0].upper()


def _execution_feasibility(net_profit: float, slippage_bps: float) -> str:
    if net_profit <= 0:
        return "not_executable"
    if slippage_bps <= 25:
        return "full"
    if slippage_bps <= 75:
        return "partial"
    return "risky"


def _latency_tier(source: str, data_age_sec: float) -> str:
    if source == "websocket_live":
        return "millisecond"
    if data_age_sec <= 2:
        return "sub_second"
    return "slow"


def _top_bid(book: dict[str, Any]) -> float | None:
    bids = book.get("bids") or []
    return float(bids[0][0]) if bids else None


def _top_ask(book: dict[str, Any]) -> float | None:
    asks = book.get("asks") or []
    return float(asks[0][0]) if asks else None


def _live_exchange_ids(native_exchanges: set[str], fast: bool) -> list[str]:
    fast_exchanges = getattr(config, "FAST_LIVE_EXCHANGES", config.WHITELIST_EXCHANGES)
    return sorted(
        ex
        for ex in native_exchanges
        if ex in config.WHITELIST_EXCHANGES and (not fast or ex in fast_exchanges)
    )


def _queue_live_fetches(
    *,
    session: aiohttp.ClientSession,
    exchange_ids: list[str],
    spot_symbols: list[str],
    perp_symbols: list[str],
    market_fetchers: dict[str, Any],
    funding_fetchers: dict[str, Any],
    spot_only_exchanges: set[str],
    symbols_for_exchange,
    perp_symbols_for_exchange,
) -> tuple[list[asyncio.Task[Any]], list[tuple[str, str, str]]]:
    tasks: list[asyncio.Task[Any]] = []
    meta: list[tuple[str, str, str]] = []
    for exchange_id in exchange_ids:
        market_fetcher = market_fetchers.get(exchange_id)
        funding_fetcher = funding_fetchers.get(exchange_id)
        if market_fetcher is None:
            continue

        for symbol in symbols_for_exchange(exchange_id, spot_symbols):
            tasks.append(asyncio.create_task(market_fetcher(session, symbol, "spot")))
            meta.append((exchange_id, symbol, "spot"))

        for symbol in perp_symbols_for_exchange(exchange_id, perp_symbols):
            if exchange_id in spot_only_exchanges:
                continue
            tasks.append(asyncio.create_task(market_fetcher(session, symbol, "perpetual")))
            meta.append((exchange_id, f"{symbol}@perpetual", "perpetual"))
            if funding_fetcher is not None:
                tasks.append(asyncio.create_task(funding_fetcher(session, symbol)))
                meta.append((exchange_id, symbol, "funding"))
    return tasks, meta


async def _wait_for_live_fetches(tasks: list[asyncio.Task[Any]], deadline: float) -> None:
    pending = set(tasks)
    loop = asyncio.get_running_loop()
    deadline_at = loop.time() + deadline
    while pending and loop.time() < deadline_at:
        done, pending = await asyncio.wait(
            pending,
            timeout=max(0.05, deadline_at - loop.time()),
            return_when=asyncio.FIRST_COMPLETED,
        )
        if not done:
            break
    for task in pending:
        task.cancel()
    if pending:
        await asyncio.gather(*pending, return_exceptions=True)


def _record_live_fetch_result(
    *,
    books: dict[str, dict[str, dict[str, Any]]],
    funding: dict[str, dict[str, dict[str, Any]]],
    task: asyncio.Task[Any],
    meta: tuple[str, str, str],
    timestamp: str,
) -> None:
    exchange_id, key, kind = meta
    if task.cancelled():
        return
    try:
        result = task.result()
    except Exception as exc:
        logger.debug("Live fetch failed | %s %s %s | %s", exchange_id, key, kind, exc)
        return

    if kind == "funding":
        funding.setdefault(exchange_id, {})[key.replace("@perpetual", "")] = {
            "funding_rate": float(result.funding_rate),
            "next_funding_time": result.next_funding_time,
            "timestamp": timestamp,
        }
        return

    _ticker, order_book = result
    books.setdefault(exchange_id, {})[key] = {
        "bids": order_book.bids,
        "asks": order_book.asks,
        "timestamp": timestamp,
        "market_type": kind if kind != "spot" else "spot",
        "symbol": key.replace("@perpetual", ""),
    }


async def fetch_live_market_snapshots(*, fast: bool = True) -> tuple[dict[str, dict[str, dict[str, Any]]], dict[str, dict[str, dict[str, Any]]]]:
    """Fast live refresh — native venues × whitelist assets (not 21k HTTP calls)."""
    from aggregator import FUNDING_FETCHERS, MARKET_FETCHERS
    from exchange_adapters import SPOT_ONLY_EXCHANGES
    from market_fetcher_hub import NATIVE_EXCHANGES, perp_symbols_for_exchange, symbols_for_exchange

    books: dict[str, dict[str, dict[str, Any]]] = {}
    funding: dict[str, dict[str, dict[str, Any]]] = {}
    timeout_sec = max(1.5, float(getattr(config, "LIVE_FETCH_TIMEOUT_SEC", 4)))
    timeout = aiohttp.ClientTimeout(total=timeout_sec)
    deadline = float(getattr(config, "LIVE_FETCH_FAST_DEADLINE_SEC", 2.5)) if fast else timeout_sec + 1

    spot_symbols = [f"{asset}/USDT" for asset in sorted(config.WHITELIST_ASSETS)]
    perp_symbols = [f"{asset}/USDT" for asset in sorted(config.WHITELIST_ASSETS)]
    exchange_ids = _live_exchange_ids(NATIVE_EXCHANGES, fast)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        tasks, meta = _queue_live_fetches(
            session=session,
            exchange_ids=exchange_ids,
            spot_symbols=spot_symbols,
            perp_symbols=perp_symbols,
            market_fetchers=MARKET_FETCHERS,
            funding_fetchers=FUNDING_FETCHERS,
            spot_only_exchanges=SPOT_ONLY_EXCHANGES,
            symbols_for_exchange=symbols_for_exchange,
            perp_symbols_for_exchange=perp_symbols_for_exchange,
        )
        await _wait_for_live_fetches(tasks, deadline)
        timestamp = _utcnow_iso()
        for task, row_meta in zip(tasks, meta):
            _record_live_fetch_result(
                books=books,
                funding=funding,
                task=task,
                meta=row_meta,
                timestamp=timestamp,
            )

    return books, funding


async def get_market_snapshots(
    *,
    prefer_live: bool | None = None,
    force_rest: bool = False,
) -> tuple[dict, dict, str, float]:
    from market_cache import get_market_snapshots_cached, set_cached_snapshots

    low_latency = getattr(config, "LOW_LATENCY_MODE", True)

    # 1) WebSocket in-memory books — always first (sub-ms) unless explicit REST forced.
    if low_latency and not force_rest:
        try:
            from live_book_hub import get_live_books_if_fresh

            fresh = get_live_books_if_fresh()
            if fresh:
                ws_books, age_ms = fresh
                _books, funding, _source, _age = await get_market_snapshots_cached()
                age_sec = age_ms / 1000.0
                set_cached_snapshots(ws_books, funding, source="websocket_live", age_sec=age_sec)
                return ws_books, funding, "websocket_live", age_sec
        except Exception:
            logger.debug("WebSocket live book path unavailable", exc_info=True)

    books, funding, source, age_sec = await get_market_snapshots_cached()

    stale_threshold = float(getattr(config, "LIVE_FETCH_STALE_THRESHOLD_SEC", 8))
    must_refresh = age_sec > stale_threshold or not books

    # 2) REST refresh ONLY when stale/missing OR caller explicitly forces REST.
    #    prefer_live alone must NOT trigger a 2–3s REST round-trip when cache/WS is fresh.
    if force_rest or must_refresh:
        try:
            live_books, live_funding = await fetch_live_market_snapshots(fast=True)
            if live_books:
                books = live_books
                source = "live_api"
                age_sec = 0.0
            if live_funding:
                funding = live_funding
            set_cached_snapshots(books, funding, source=source, age_sec=age_sec)
        except Exception:
            if must_refresh:
                logger.warning(
                    "Stale market data (age=%.1fs) and live refresh failed — results may be unreliable.",
                    age_sec,
                )
            else:
                logger.exception("Live arbitrage snapshot fetch failed; using cache/database fallback.")

    return books, funding, source, age_sec


_institutional_cache: dict[str, Any] | None = None
_institutional_cache_at: float = 0.0


async def get_institutional_context_cached() -> dict[str, Any]:
    """Short TTL cache — avoids ~100–700ms DB hit on every scan pulse."""
    global _institutional_cache, _institutional_cache_at

    ttl = float(getattr(config, "INSTITUTIONAL_CONTEXT_CACHE_SEC", 2.0))
    now = __import__("time").monotonic()
    if _institutional_cache is not None and (now - _institutional_cache_at) < ttl:
        return _institutional_cache

    _institutional_cache = await get_latest_institutional_context()
    _institutional_cache_at = now
    return _institutional_cache


def _format_cross(item: Any, institutional_context: dict | None) -> dict[str, Any]:
    explanation = explain_opportunity(item, "cross_exchange", 0, institutional_context)
    net = float(item.net_profit_usdt)
    return {
        "kind": "cross_exchange",
        "kind_label": "Cross-Exchange",
        "asset": _asset_from_symbol(item.symbol),
        "symbol": item.symbol,
        "buy_exchange": item.buy_exchange,
        "sell_exchange": item.sell_exchange,
        "gross_spread_bps": round(float(item.gross_spread_bps), 2),
        "net_profit_usdt": round(net, 4),
        "net_profit_percent": round(float(item.net_profit_percent), 4),
        "quote_amount": float(item.quote_amount),
        "total_slippage_bps": round(float(item.total_slippage_bps), 2),
        "fees_usdt": round(float(item.trading_fees_usdt + item.withdrawal_fee_usdt), 4),
        "execution_feasibility": _execution_feasibility(net, float(item.total_slippage_bps)),
        "estimated_duration": _DURATION_LABELS["cross_exchange"],
        "why": explanation.summary,
        "reasons": explanation.reasons[:3],
        "risk_factors": explanation.risk_factors[:2],
        "confidence_percent": round(float(explanation.confidence_percent), 1),
    }


def _format_triangular(item: Any, institutional_context: dict | None) -> dict[str, Any]:
    explanation = explain_opportunity(item, "triangular", 0, institutional_context)
    net = float(item.net_profit_usdt)
    return {
        "kind": "triangular",
        "kind_label": "Triangular",
        "asset": item.path.split("->")[0].split("/")[0] if "->" in item.path else "MULTI",
        "symbol": item.path,
        "exchange": item.exchange,
        "path": item.path,
        "gross_spread_bps": round(float(item.gross_spread_bps), 2),
        "net_profit_usdt": round(net, 4),
        "net_profit_percent": round(float(item.net_profit_percent), 4),
        "quote_amount": float(item.quote_amount),
        "total_slippage_bps": round(float(item.total_slippage_bps), 2),
        "fees_usdt": round(float(item.trading_fees_usdt), 4),
        "execution_feasibility": _execution_feasibility(net, float(item.total_slippage_bps)),
        "estimated_duration": _DURATION_LABELS["triangular"],
        "why": explanation.summary,
        "reasons": explanation.reasons[:3],
        "risk_factors": explanation.risk_factors[:2],
        "confidence_percent": round(float(explanation.confidence_percent), 1),
    }


def _format_basis(item: Any, institutional_context: dict | None) -> dict[str, Any]:
    explanation = explain_opportunity(item, "spot_futures", 0, institutional_context)
    net = float(item.net_profit_usdt)
    return {
        "kind": "spot_futures",
        "kind_label": "Spot / Futures Basis",
        "asset": _asset_from_symbol(item.symbol),
        "symbol": item.symbol,
        "exchange": item.exchange,
        "direction": item.direction,
        "basis_bps": round(float(item.basis_bps), 2),
        "net_profit_usdt": round(net, 4),
        "net_profit_percent": round(float(item.net_profit_percent), 4),
        "quote_amount": float(item.quote_amount),
        "total_slippage_bps": round(float(item.total_slippage_bps), 2),
        "fees_usdt": round(float(item.trading_fees_usdt), 4),
        "execution_feasibility": _execution_feasibility(net, float(item.total_slippage_bps)),
        "estimated_duration": _DURATION_LABELS["spot_futures"],
        "why": explanation.summary,
        "reasons": explanation.reasons[:3],
        "risk_factors": explanation.risk_factors[:2],
        "confidence_percent": round(float(explanation.confidence_percent), 1),
    }


def _format_funding(item: Any, institutional_context: dict | None) -> dict[str, Any]:
    explanation = explain_opportunity(item, "funding", 0, institutional_context)
    net = float(item.net_yield_usdt)
    return {
        "kind": "funding",
        "kind_label": "Funding Rate",
        "asset": _asset_from_symbol(item.symbol),
        "symbol": item.symbol,
        "long_exchange": item.long_exchange,
        "short_exchange": item.short_exchange,
        "funding_spread_bps": round(float(item.funding_spread_bps), 2),
        "net_profit_usdt": round(net, 4),
        "net_profit_percent": round(float(item.net_yield_percent), 4),
        "quote_amount": float(item.quote_amount),
        "fees_usdt": round(float(item.trading_fees_usdt), 4),
        "execution_feasibility": _execution_feasibility(net, 10.0),
        "estimated_duration": _DURATION_LABELS["funding"],
        "why": explanation.summary,
        "reasons": explanation.reasons[:3],
        "risk_factors": explanation.risk_factors[:2],
        "confidence_percent": round(float(explanation.confidence_percent), 1),
    }


def _profit_floor(min_profit_usdt: float | None, profitable_only: bool) -> float:
    if profitable_only:
        return 0.0
    if min_profit_usdt is not None:
        return min_profit_usdt
    return -1_000_000.0


def _empty_scan_response(
    *,
    source: str,
    data_age_sec: float,
    scan_ms: float,
    quote_amount: float,
) -> dict[str, Any]:
    return {
        "opportunities": [],
        "counts": {"cross_exchange": 0, "triangular": 0, "spot_futures": 0, "funding": 0},
        "data_source": source,
        "data_age_sec": data_age_sec,
        "scan_ms": scan_ms,
        "quote_amount": quote_amount,
        "timestamp": _utcnow_iso(),
        "message": "No order-book data — start aggregator.py or retry live scan.",
    }


def _strategy_opportunities(
    books: dict[str, dict[str, Any]],
    funding: list[dict[str, Any]],
    notional: float,
    institutional_context: dict[str, Any],
) -> tuple[list[Any], list[Any], list[Any], list[Any]]:
    cross = calculate_cross_exchange_arbitrage(books, notional, institutional_context)
    triangular = calculate_triangular_arbitrage(books, notional, institutional_context)
    basis = calculate_spot_futures_premium(books, notional, institutional_context)
    funding_opps = calculate_funding_arbitrage_with_institutional_context(
        funding,
        notional,
        institutional_context,
        institutional_context,
    )
    return cross, triangular, basis, funding_opps


def _append_profitable(rows: list[dict[str, Any]], row: dict[str, Any], profit_floor: float) -> None:
    if row["net_profit_usdt"] >= profit_floor:
        rows.append(row)


def _append_triangular_row(
    rows: list[dict[str, Any]],
    row: dict[str, Any],
    *,
    data_age_sec: float,
    profit_floor: float,
) -> None:
    if row["net_profit_usdt"] < profit_floor:
        return
    if data_age_sec <= 10:
        row["staleness_ok"] = True
        rows.append(row)
        return
    row["staleness_ok"] = False
    row["risk_factors"] = (row.get("risk_factors") or []) + ["stale_data_for_triangular"]


def _formatted_opportunities(
    *,
    cross: list[Any],
    triangular: list[Any],
    basis: list[Any],
    funding_opps: list[Any],
    institutional_context: dict[str, Any],
    data_age_sec: float,
    profit_floor: float,
) -> list[dict[str, Any]]:
    formatted: list[dict[str, Any]] = []
    for item in cross:
        _append_profitable(formatted, _format_cross(item, institutional_context), profit_floor)
    for item in triangular:
        _append_triangular_row(
            formatted,
            _format_triangular(item, institutional_context),
            data_age_sec=data_age_sec,
            profit_floor=profit_floor,
        )
    for item in basis:
        _append_profitable(formatted, _format_basis(item, institutional_context), profit_floor)
    for item in funding_opps:
        _append_profitable(formatted, _format_funding(item, institutional_context), profit_floor)
    return [row for row in formatted if row.get("staleness_ok", True) is not False]


def _apply_truth_to_row(row: dict[str, Any], quote_age_ms: float) -> None:
    from net_edge_truth import compute_net_edge_truth

    if quote_age_ms and not row.get("quote_age_ms"):
        row["quote_age_ms"] = quote_age_ms
    try:
        truth = compute_net_edge_truth(row)
    except Exception:
        logger.debug("net-edge truth on scan row failed", exc_info=True)
        truth = {"enabled": False, "error": "unavailable"}
    row["net_edge_truth"] = truth
    if not truth.get("reject"):
        return
    row["truth_rejected"] = True
    row["execution_feasibility"] = "not_executable"
    risks = list(row.get("risk_factors") or [])
    if "net_edge_truth_reject" not in risks:
        risks.append("net_edge_truth_reject")
    row["risk_factors"] = risks


def _mark_constitution_gates_unavailable(rows: list[dict[str, Any]]) -> None:
    for row in rows:
        row["gates_missing"] = True
        row["execution_feasibility"] = "not_executable"
        row.setdefault("net_edge_truth", {"enabled": False, "reject": True, "error": "gates_unavailable"})
        row.setdefault("dimension_conflict", {"severity": "unavailable", "veto": False, "abstain": True})
        risks = list(row.get("risk_factors") or [])
        if "constitution_gates_unavailable" not in risks:
            risks.append("constitution_gates_unavailable")
        row["risk_factors"] = risks


def _apply_constitution_scan_gates(
    formatted: list[dict[str, Any]],
    *,
    institutional_context: dict[str, Any],
    data_age_sec: float,
) -> list[dict[str, Any]]:
    try:
        from constitution_gates import apply_constitution_gates_to_scan

        quote_age_ms = max(0.0, float(data_age_sec or 0) * 1000.0)
        for row in formatted:
            _apply_truth_to_row(row, quote_age_ms)
        return apply_constitution_gates_to_scan(
            formatted,
            institutional_context=institutional_context,
            register_limit=12,
        )
    except Exception:
        logger.exception("Constitution scan gates unavailable")
        _mark_constitution_gates_unavailable(formatted)
        return formatted


def _attach_execution_risk_rows(
    formatted: list[dict[str, Any]],
    data_age_sec: float,
) -> list[dict[str, Any]]:
    try:
        from execution_risk_score import attach_execution_risk

        return [
            attach_execution_risk(
                {
                    **row,
                    "data_age_sec": float(data_age_sec or row.get("data_age_sec") or 0),
                }
            )
            for row in formatted
        ]
    except Exception:
        logger.debug("execution risk scoring unavailable", exc_info=True)
        return formatted


def _scan_pricing_errors(
    books: dict[str, dict[str, Any]],
    source: str,
) -> list[dict[str, Any]]:
    pricing_errors: list[dict[str, Any]] = []
    if source == "websocket_live":
        return pricing_errors
    try:
        from pricing_error_sniper import scan_pricing_errors_from_books

        for symbol in config.all_spot_symbols()[:5]:
            scan = scan_pricing_errors_from_books(books, symbol)
            pricing_errors.extend(scan.get("opportunities") or [])
    except Exception:
        logger.exception("Pricing error scan failed")
    return pricing_errors


def _scan_counts(
    cross: list[Any],
    triangular: list[Any],
    basis: list[Any],
    funding_opps: list[Any],
) -> dict[str, int]:
    return {
        "cross_exchange": len(cross),
        "triangular": len(triangular),
        "spot_futures": len(basis),
        "funding": len(funding_opps),
    }


def _is_executable_row(row: dict[str, Any]) -> bool:
    return (
        row.get("execution_feasibility") in {"full", "partial"}
        and not row.get("truth_rejected")
        and not row.get("half_life_killed")
        and not (row.get("dimension_conflict") or {}).get("veto")
        and not (row.get("dimension_conflict") or {}).get("abstain")
    )


def _is_gated_out_row(row: dict[str, Any]) -> bool:
    return (
        row.get("truth_rejected")
        or row.get("half_life_killed")
        or (row.get("dimension_conflict") or {}).get("veto")
        or (row.get("dimension_conflict") or {}).get("abstain")
    )


async def scan_arbitrage_opportunities(
    quote_amount: float | None = None,
    *,
    prefer_live: bool | None = None,
    force_rest: bool = False,
    min_profit_usdt: float | None = None,
    profitable_only: bool = False,
) -> dict[str, Any]:
    """Run all four arbitrage strategies and return ranked opportunities."""
    import time

    scan_started = time.monotonic()
    notional = quote_amount or config.DEFAULT_QUOTE_AMOUNT
    books, funding, source, data_age_sec = await get_market_snapshots(
        prefer_live=prefer_live,
        force_rest=force_rest,
    )
    profit_floor = _profit_floor(min_profit_usdt, profitable_only)

    if not books:
        return _empty_scan_response(
            source=source,
            data_age_sec=data_age_sec,
            scan_ms=round((time.monotonic() - scan_started) * 1000, 1),
            quote_amount=notional,
        )

    institutional_context = await get_institutional_context_cached()

    cross, triangular, basis, funding_opps = _strategy_opportunities(
        books,
        funding,
        notional,
        institutional_context,
    )

    formatted = _formatted_opportunities(
        cross=cross,
        triangular=triangular,
        basis=basis,
        funding_opps=funding_opps,
        institutional_context=institutional_context,
        data_age_sec=data_age_sec,
        profit_floor=profit_floor,
    )
    formatted.sort(key=lambda x: x["net_profit_usdt"], reverse=True)

    from opportunity_tracker import sync_scan_opportunities

    formatted = sync_scan_opportunities(formatted)
    formatted = _apply_constitution_scan_gates(
        formatted,
        institutional_context=institutional_context,
        data_age_sec=data_age_sec,
    )
    formatted = _attach_execution_risk_rows(formatted, data_age_sec)
    pricing_errors = _scan_pricing_errors(books, source)

    latency_tier = _latency_tier(source, data_age_sec)

    return {
        "opportunities": formatted,
        "top_opportunity": formatted[0] if formatted else None,
        "counts": _scan_counts(cross, triangular, basis, funding_opps),
        "executable_count": sum(1 for row in formatted if _is_executable_row(row)),
        "profitable_count": sum(1 for row in formatted if row["net_profit_usdt"] > 0),
        "gated_out_count": sum(1 for row in formatted if _is_gated_out_row(row)),
        "pricing_errors": pricing_errors[:10],
        "data_source": source,
        "data_age_sec": round(data_age_sec, 2),
        "scan_ms": round((time.monotonic() - scan_started) * 1000, 1),
        "latency_tier": latency_tier,
        "quote_amount": notional,
        "constitution_gates": ["D3", "D4", "D2", "D8"],
        "timestamp": _utcnow_iso(),
    }


async def compare_symbol_across_exchanges(
    symbol: str,
    quote_amount: float | None = None,
) -> dict[str, Any]:
    """Comparison engine — best bid/ask per venue with net cross-exchange edge."""
    cleaned = symbol.upper().replace("/", "").replace("-", "")
    asset = cleaned.removesuffix("USDT")
    pair = f"{asset}/USDT"

    notional = quote_amount or config.DEFAULT_QUOTE_AMOUNT
    books, _funding, source, data_age_sec = await get_market_snapshots(prefer_live=False)

    venues: list[dict[str, Any]] = []
    for exchange_id in config.enabled_exchanges():
        book = (books.get(exchange_id) or {}).get(pair)
        if book is None:
            continue
        bid = _top_bid(book)
        ask = _top_ask(book)
        if bid is None or ask is None:
            continue
        spread_bps = ((ask - bid) / ask * 10_000) if ask > 0 else 0.0
        venues.append(
            {
                "exchange": exchange_id,
                "best_bid": round(bid, 6),
                "best_ask": round(ask, 6),
                "spread_bps": round(spread_bps, 2),
                "timestamp": book.get("timestamp"),
            }
        )

    venues.sort(key=lambda x: x["best_ask"])
    best_buy = min(venues, key=lambda x: x["best_ask"]) if venues else None
    best_sell = max(venues, key=lambda x: x["best_bid"]) if venues else None

    gross_spread_bps = 0.0
    net_profit_estimate = 0.0
    if best_buy and best_sell and best_buy["exchange"] != best_sell["exchange"]:
        gross_spread_bps = _gross_spread_bps(best_buy["best_ask"], best_sell["best_bid"])
        fee_drag = notional * config.DEFAULT_TAKER_FEE * 2
        gross_profit = notional * (gross_spread_bps / 10_000)
        net_profit_estimate = gross_profit - fee_drag - 5.0

    from feed_lag_scanner import scan_feed_lag_from_venues

    feed_lag = scan_feed_lag_from_venues(venues, pair)

    from pricing_error_sniper import scan_pricing_errors

    pricing_errors = scan_pricing_errors(venues, pair=pair)

    return {
        "symbol": pair,
        "asset": asset,
        "quote_amount": notional,
        "venues": venues,
        "best_buy_venue": best_buy,
        "best_sell_venue": best_sell,
        "gross_spread_bps": round(gross_spread_bps, 2),
        "net_profit_estimate_usdt": round(net_profit_estimate, 4),
        "net_profit_estimate_percent": round((net_profit_estimate / notional) * 100, 4) if notional else 0,
        "feed_lag": feed_lag,
        "pricing_errors": pricing_errors,
        "data_source": source,
        "data_age_sec": round(data_age_sec, 2),
        "timestamp": _utcnow_iso(),
    }


def _gross_spread_bps(buy_ask: float, sell_bid: float) -> float:
    if buy_ask <= 0:
        return 0.0
    return (sell_bid - buy_ask) / buy_ask * 10_000


async def send_telegram_alert(message: str) -> bool:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}
    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session, session.post(url, json=payload) as resp:
            return resp.status == 200
    except (aiohttp.ClientError, TypeError, ValueError):
        logger.exception("Telegram alert delivery failed")
        return False


def _alert_thresholds_met(opp: dict[str, Any], min_usdt: float, min_pct: float, is_alertable: Any) -> bool:
    if not is_alertable(opp):
        return False
    if float(opp.get("net_profit_usdt") or 0) < min_usdt:
        return False
    return float(opp.get("net_profit_percent") or 0) >= min_pct


def _alert_title(opp: dict[str, Any]) -> str:
    return (
        f"{opp.get('kind_label')} · {opp.get('asset')} · "
        f"+${float(opp.get('net_profit_usdt') or 0):.2f} "
        f"({float(opp.get('net_profit_percent') or 0):.3f}%)"
    )


async def _dispatch_primary_arbitrage_alert(
    title: str,
    opp: dict[str, Any],
    scan_result: dict[str, Any],
) -> None:
    await _dispatch_unified_alert(title, opp)
    await _publish_b2b_arbitrage_alert(opp)
    await _publish_service_bus_arbitrage_alert(opp)
    await _dispatch_free_telegram_if_configured(scan_result)


async def _dispatch_unified_alert(title: str, opp: dict[str, Any]) -> None:
    try:
        from alert_service import dispatch_alert

        body = (
            f"Feasibility: {opp.get('execution_feasibility')}\n"
            f"Duration: {opp.get('estimated_duration')}\n"
            f"{opp.get('why', '')[:200]}"
        )
        await dispatch_alert(title, body, payload=opp)
    except Exception:
        logger.exception("Unified alert dispatch failed")


async def _publish_b2b_arbitrage_alert(opp: dict[str, Any]) -> None:
    try:
        from b2b_websocket_hub import publish_arbitrage_opportunity

        await publish_arbitrage_opportunity(opp)
    except Exception:
        logger.exception("B2B WS arbitrage publish failed")


async def _publish_service_bus_arbitrage_alert(opp: dict[str, Any]) -> None:
    try:
        from service_bus import publish

        await publish(
            "blackdark.arbitrage.hot",
            {
                "asset": opp.get("asset"),
                "kind": opp.get("kind"),
                "net_profit_usdt": opp.get("net_profit_usdt"),
            },
        )
    except Exception:
        logger.debug("Service bus arbitrage publish skipped", exc_info=True)


async def _dispatch_free_telegram_if_configured(scan_result: dict[str, Any]) -> None:
    if not os.getenv("TELEGRAM_BOT_TOKEN"):
        return
    try:
        from telegram_free_alerts import dispatch_free_telegram_alerts

        await dispatch_free_telegram_alerts(scan=scan_result)
    except Exception:
        logger.exception("Free Telegram dispatch from arbitrage alert failed")


async def process_arbitrage_alerts(scan_result: dict[str, Any]) -> list[dict[str, Any]]:
    """Create in-app alerts and dispatch via Telegram/Email/WhatsApp."""
    from database import insert_arbitrage_alert_log

    min_pct = float(os.getenv("ARBITRAGE_ALERT_MIN_PROFIT_PCT", "0.05"))
    min_usdt = float(os.getenv("ARBITRAGE_ALERT_MIN_PROFIT_USDT", "0.10"))
    triggered: list[dict[str, Any]] = []

    from constitution_gates import is_alertable

    for opp in scan_result.get("opportunities", [])[:5]:
        if not _alert_thresholds_met(opp, min_usdt, min_pct, is_alertable):
            continue

        title = _alert_title(opp)
        await insert_arbitrage_alert_log(opp.get("kind", "unknown"), title, json.dumps(opp))
        triggered.append({"title": title, "opportunity": opp})

        if len(triggered) == 1:
            await _dispatch_primary_arbitrage_alert(title, opp, scan_result)

    return triggered
