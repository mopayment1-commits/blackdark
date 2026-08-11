"""
BLACKDARK — Pre-execution slippage re-walk + alert validation/cancellation.
"""

from __future__ import annotations

import asyncio

import hashlib
import logging
import time
from typing import Any

import config

try:
    from arbitrage_engine import _walk_triangle_legs, walk_asks, walk_bids
except ImportError:  # pragma: no cover
    walk_asks = walk_bids = _walk_triangle_legs = None  # type: ignore

logger = logging.getLogger("BLACKDARK.SlippageGuard")

_active_alerts: dict[str, dict[str, Any]] = {}
_cancelled_total = 0


def _fingerprint(opp: dict[str, Any]) -> str:
    raw = "|".join(
        [
            str(opp.get("kind") or ""),
            str(opp.get("asset") or opp.get("symbol") or ""),
            str(opp.get("buy_exchange") or opp.get("buy_venue") or ""),
            str(opp.get("sell_exchange") or opp.get("sell_venue") or ""),
        ]
    )
    return hashlib.sha1(raw.encode()).hexdigest()[:16]


def _rewalk_triangular(opportunity: dict[str, Any], notional: float) -> dict[str, Any]:
    from live_book_hub import get_live_books_if_fresh

    fresh = get_live_books_if_fresh()
    if not fresh:
        return {**opportunity, "rewalk": "no_fresh_books", "executable": False}
    books_map, age_ms = fresh
    exchange = str(opportunity.get("exchange") or "binance").lower()
    books = books_map.get(exchange) or {}
    legs = opportunity.get("legs") or []
    if not legs:
        return {**opportunity, "rewalk": "missing_legs", "executable": False}

    from fee_matrix import taker_fee

    ex_fee = taker_fee(exchange)
    net_final, slip = _walk_triangle_legs(legs, books, notional, ex_fee, True)
    if net_final is None:
        return {**opportunity, "rewalk": "triangle_depth_fail", "executable": False, "cancel_reason": "liquidity"}

    from risk_manager import check_slippage

    verdict = check_slippage(slip)
    updated = {
        **opportunity,
        "total_slippage_bps": round(slip, 2),
        "rewalk_age_ms": round(age_ms, 1),
        "executable": verdict.allowed and net_final > notional,
        "rewalk": "triangle_ok",
        "net_after_walk_usdt": round(net_final - notional, 4),
    }
    if not updated["executable"]:
        updated["cancel_reason"] = verdict.reason or "unprofitable_after_walk"
    return updated


async def rewalk_opportunity_slippage(
    opportunity: dict[str, Any],
    *,
    quote_amount: float | None = None,
) -> dict[str, Any]:
    """Re-simulate order book depth before execution; update slippage fields."""
    await asyncio.sleep(0)
    from live_book_hub import get_live_books_if_fresh

    notional = quote_amount or float(opportunity.get("quote_amount") or config.DEFAULT_QUOTE_AMOUNT)
    kind = str(opportunity.get("kind") or "")

    if kind == "triangular":
        return _rewalk_triangular(opportunity, notional)

    if kind == "cex_dex":
        from dex_slippage import simulate_amm_swap

        liq = float(opportunity.get("dex_liquidity_usd") or 0)
        price = float(opportunity.get("dex_price") or opportunity.get("buy_price") or 0)
        sim = simulate_amm_swap(amount_in_usd=notional, price=price, liquidity_usd=liq)
        if sim is None:
            return {**opportunity, "rewalk": "dex_liquidity_fail", "executable": False, "cancel_reason": "liquidity"}
        return {
            **opportunity,
            "total_slippage_bps": sim["slippage_bps"],
            "executable": sim["executable"],
            "rewalk": "dex_ok",
        }

    fresh = get_live_books_if_fresh()
    if not fresh:
        return {**opportunity, "rewalk": "no_fresh_books", "executable": False}

    books, age_ms = fresh
    buy_ex = str(opportunity.get("buy_exchange") or opportunity.get("buy_venue") or "").lower()
    sell_ex = str(opportunity.get("sell_exchange") or opportunity.get("sell_venue") or "").lower()
    asset = str(opportunity.get("asset") or "BTC")
    symbol = f"{asset}/USDT"

    if kind in {"cross_exchange", "fast_cross", "stream_cross_exchange"}:
        buy_book = (books.get(buy_ex) or {}).get(symbol)
        sell_book = (books.get(sell_ex) or {}).get(symbol)
        if not buy_book or not sell_book:
            return {**opportunity, "rewalk": "missing_books", "executable": False}

        buy_exec = walk_asks(buy_book, notional)
        if buy_exec is None:
            return {**opportunity, "rewalk": "insufficient_buy_depth", "executable": False, "cancel_reason": "liquidity"}

        sell_exec = walk_bids(sell_book, buy_exec.base_amount)
        if sell_exec is None:
            return {**opportunity, "rewalk": "insufficient_sell_depth", "executable": False, "cancel_reason": "liquidity"}

        total_slip = buy_exec.slippage_bps + sell_exec.slippage_bps
        from risk_manager import check_slippage

        verdict = check_slippage(total_slip)
        updated = {
            **opportunity,
            "total_slippage_bps": round(total_slip, 2),
            "buy_slippage_bps": round(buy_exec.slippage_bps, 2),
            "sell_slippage_bps": round(sell_exec.slippage_bps, 2),
            "rewalk_age_ms": round(age_ms, 1),
            "executable": verdict.allowed,
            "rewalk": "ok",
        }
        if not verdict.allowed:
            updated["cancel_reason"] = verdict.reason
        return updated

    return {**opportunity, "rewalk": "skipped", "executable": True}


async def validate_alert(opportunity: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    """Returns (should_send, updated_opp). Cancels if re-walk fails."""
    global _cancelled_total
    fp = _fingerprint(opportunity)

    from stale_price_guard import validate_opportunity_quotes

    send_ok, stale_detail = validate_opportunity_quotes(opportunity, for_execution=False)
    if not send_ok:
        _cancelled_total += 1
        _active_alerts.pop(fp, None)
        logger.info("Alert cancelled (stale) | fp=%s detail=%s", fp, stale_detail)
        return False, {**opportunity, "cancel_reason": "stale_prices", "stale_guard": stale_detail, "executable": False}

    updated = await rewalk_opportunity_slippage(opportunity)

    if not updated.get("executable", True):
        _cancelled_total += 1
        _active_alerts.pop(fp, None)
        logger.info("Alert cancelled | fp=%s reason=%s", fp, updated.get("cancel_reason"))
        return False, updated

    from flywheel_saturation_guard import apply_crowd_guard_to_alert

    send_ok, updated = await apply_crowd_guard_to_alert(updated)
    if not send_ok:
        _cancelled_total += 1
        _active_alerts.pop(fp, None)
        return False, updated

    _active_alerts[fp] = {"at": time.monotonic(), "opportunity": updated}
    return True, updated


def reconcile_active_alerts(current_opportunities: list[dict[str, Any]]) -> list[str]:
    """Cancel stale alerts not in current profitable set."""
    global _cancelled_total
    current_fps = {_fingerprint(o) for o in current_opportunities}
    cancelled: list[str] = []
    stale = [fp for fp in _active_alerts if fp not in current_fps]
    for fp in stale:
        _active_alerts.pop(fp, None)
        _cancelled_total += 1
        cancelled.append(fp)
    return cancelled


def guard_stats() -> dict[str, Any]:
    return {
        "active_alerts": len(_active_alerts),
        "cancelled_total": _cancelled_total,
    }
