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
from datetime import datetime, timezone
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
from database import fetch_latest_funding_rates, fetch_latest_order_books
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
    return datetime.now(timezone.utc).isoformat()


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


def _top_bid(book: dict[str, Any]) -> float | None:
    bids = book.get("bids") or []
    return float(bids[0][0]) if bids else None


def _top_ask(book: dict[str, Any]) -> float | None:
    asks = book.get("asks") or []
    return float(asks[0][0]) if asks else None


async def fetch_live_market_snapshots() -> tuple[dict[str, dict[str, dict[str, Any]]], dict[str, dict[str, dict[str, Any]]]]:
    """Pull fresh order books and funding rates from all enabled exchanges."""
    from aggregator import FUNDING_FETCHERS, MARKET_FETCHERS
    from exchange_adapters import SPOT_ONLY_EXCHANGES

    books: dict[str, dict[str, dict[str, Any]]] = {}
    funding: dict[str, dict[str, dict[str, Any]]] = {}
    timestamp = _utcnow_iso()
    timeout = aiohttp.ClientTimeout(total=25)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        tasks: list[Any] = []
        meta: list[tuple[str, str, str]] = []

        for exchange_id in config.enabled_exchanges():
            market_fetcher = MARKET_FETCHERS.get(exchange_id)
            funding_fetcher = FUNDING_FETCHERS.get(exchange_id)
            if market_fetcher is None:
                continue

            for symbol in config.all_spot_symbols():
                tasks.append(market_fetcher(session, symbol, "spot"))
                meta.append((exchange_id, symbol, "spot"))

            for symbol in config.perpetual_symbols():
                if exchange_id in SPOT_ONLY_EXCHANGES:
                    continue
                tasks.append(market_fetcher(session, symbol, "perpetual"))
                meta.append((exchange_id, f"{symbol}@perpetual", "perpetual"))
                if funding_fetcher is not None:
                    tasks.append(funding_fetcher(session, symbol))
                    meta.append((exchange_id, symbol, "funding"))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        idx = 0
        for exchange_id, key, kind in meta:
            result = results[idx]
            idx += 1
            if isinstance(result, Exception):
                logger.debug("Live fetch failed | %s %s %s | %s", exchange_id, key, kind, result)
                continue

            if kind == "funding":
                snap = result
                funding.setdefault(exchange_id, {})[key.replace("@perpetual", "")] = {
                    "funding_rate": float(snap.funding_rate),
                    "next_funding_time": snap.next_funding_time,
                    "timestamp": timestamp,
                }
                continue

            _ticker, order_book = result
            symbol_key = key if kind == "perpetual" else key
            books.setdefault(exchange_id, {})[symbol_key] = {
                "bids": order_book.bids,
                "asks": order_book.asks,
                "timestamp": timestamp,
                "market_type": kind if kind != "spot" else ("cross" if "/" in key and not key.endswith("/USDT") else "spot"),
                "symbol": key.replace("@perpetual", ""),
            }

    return books, funding


async def get_market_snapshots(*, prefer_live: bool = True) -> tuple[dict, dict, str]:
    books = await fetch_latest_order_books()
    funding = await fetch_latest_funding_rates()
    source = "database"

    if prefer_live or not books:
        try:
            live_books, live_funding = await fetch_live_market_snapshots()
            if live_books:
                books = live_books
                source = "live_api"
            if live_funding:
                funding = live_funding
        except Exception:
            logger.exception("Live arbitrage snapshot fetch failed; using database fallback.")

    return books, funding, source


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


async def scan_arbitrage_opportunities(
    quote_amount: float | None = None,
    *,
    prefer_live: bool = True,
    min_profit_usdt: float | None = None,
    profitable_only: bool = False,
) -> dict[str, Any]:
    """Run all four arbitrage strategies and return ranked opportunities."""
    notional = quote_amount or config.DEFAULT_QUOTE_AMOUNT
    books, funding, source = await get_market_snapshots(prefer_live=prefer_live)
    profit_floor = 0.0 if profitable_only else (min_profit_usdt if min_profit_usdt is not None else -1_000_000.0)

    if not books:
        return {
            "opportunities": [],
            "counts": {"cross_exchange": 0, "triangular": 0, "spot_futures": 0, "funding": 0},
            "data_source": source,
            "quote_amount": notional,
            "timestamp": _utcnow_iso(),
            "message": "No order-book data — start aggregator.py or retry live scan.",
        }

    institutional_context = await get_latest_institutional_context()

    cross = calculate_cross_exchange_arbitrage(books, notional, institutional_context)
    triangular = calculate_triangular_arbitrage(books, notional, institutional_context)
    basis = calculate_spot_futures_premium(books, notional, institutional_context)
    funding_opps = calculate_funding_arbitrage_with_institutional_context(
        funding, notional, institutional_context, institutional_context
    )

    formatted: list[dict[str, Any]] = []
    for item in cross:
        row = _format_cross(item, institutional_context)
        if row["net_profit_usdt"] >= profit_floor:
            formatted.append(row)
    for item in triangular:
        row = _format_triangular(item, institutional_context)
        if row["net_profit_usdt"] >= profit_floor:
            formatted.append(row)
    for item in basis:
        row = _format_basis(item, institutional_context)
        if row["net_profit_usdt"] >= profit_floor:
            formatted.append(row)
    for item in funding_opps:
        row = _format_funding(item, institutional_context)
        if row["net_profit_usdt"] >= profit_floor:
            formatted.append(row)

    formatted.sort(key=lambda x: x["net_profit_usdt"], reverse=True)

    from opportunity_tracker import sync_scan_opportunities

    formatted = sync_scan_opportunities(formatted)

    pricing_errors: list[dict[str, Any]] = []
    try:
        from pricing_error_sniper import scan_pricing_errors_from_books

        for symbol in config.all_spot_symbols()[:5]:
            scan = scan_pricing_errors_from_books(books, symbol)
            pricing_errors.extend(scan.get("opportunities") or [])
    except Exception:
        logger.exception("Pricing error scan failed")

    return {
        "opportunities": formatted,
        "top_opportunity": formatted[0] if formatted else None,
        "counts": {
            "cross_exchange": len(cross),
            "triangular": len(triangular),
            "spot_futures": len(basis),
            "funding": len(funding_opps),
        },
        "executable_count": sum(
            1 for row in formatted if row["execution_feasibility"] in {"full", "partial"}
        ),
        "profitable_count": sum(1 for row in formatted if row["net_profit_usdt"] > 0),
        "pricing_errors": pricing_errors[:10],
        "data_source": source,
        "quote_amount": notional,
        "timestamp": _utcnow_iso(),
    }


async def compare_symbol_across_exchanges(
    symbol: str,
    quote_amount: float | None = None,
) -> dict[str, Any]:
    """Comparison engine — best bid/ask per venue with net cross-exchange edge."""
    cleaned = symbol.upper().replace("/", "").replace("-", "")
    if cleaned.endswith("USDT"):
        asset = cleaned[:-4]
    else:
        asset = cleaned
    pair = f"{asset}/USDT"

    notional = quote_amount or config.DEFAULT_QUOTE_AMOUNT
    books, _funding, source = await get_market_snapshots(prefer_live=True)

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
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, json=payload) as resp:
                return resp.status == 200
    except (aiohttp.ClientError, TypeError, ValueError):
        logger.exception("Telegram alert delivery failed")
        return False


async def process_arbitrage_alerts(scan_result: dict[str, Any]) -> list[dict[str, Any]]:
    """Create in-app alerts and dispatch via Telegram/Email/WhatsApp."""
    from database import insert_arbitrage_alert_log

    min_pct = float(os.getenv("ARBITRAGE_ALERT_MIN_PROFIT_PCT", "0.05"))
    min_usdt = float(os.getenv("ARBITRAGE_ALERT_MIN_PROFIT_USDT", "0.10"))
    triggered: list[dict[str, Any]] = []

    for opp in scan_result.get("opportunities", [])[:5]:
        if opp.get("execution_feasibility") == "not_executable":
            continue
        if float(opp.get("net_profit_usdt") or 0) < min_usdt:
            continue
        if float(opp.get("net_profit_percent") or 0) < min_pct:
            continue

        title = (
            f"{opp.get('kind_label')} · {opp.get('asset')} · "
            f"+${float(opp.get('net_profit_usdt') or 0):.2f} "
            f"({float(opp.get('net_profit_percent') or 0):.3f}%)"
        )
        await insert_arbitrage_alert_log(opp.get("kind", "unknown"), title, json.dumps(opp))
        triggered.append({"title": title, "opportunity": opp})

        if len(triggered) == 1:
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

    return triggered
