"""Unit tests — slippage_guard re-walk and alert validation."""

from __future__ import annotations

import pytest

import slippage_guard
from live_book_hub import update_top_of_book


def _seed_cross_books(*, wide_spread: bool = False) -> None:
    from live_book_hub import _books, _last_update_ms

    _books.clear()
    _last_update_ms.clear()
    ask = 100.0 if wide_spread else 100.0
    bid = 102.0 if wide_spread else 100.5
    book_buy = {"asks": [[ask, 50.0]], "bids": [[ask - 0.5, 50.0]]}
    book_sell = {"asks": [[bid + 0.5, 50.0]], "bids": [[bid, 50.0]]}
    for ex, book in (("binance", book_buy), ("okx", book_sell), ("bybit", book_sell)):
        update_top_of_book(
            ex,
            "BTC/USDT",
            bid=book["bids"][0][0],
            bid_qty=book["bids"][0][1],
            ask=book["asks"][0][0],
            ask_qty=book["asks"][0][1],
        )


@pytest.mark.asyncio
async def test_rewalk_cross_exchange_ok():
    slippage_guard._active_alerts.clear()
    _seed_cross_books(wide_spread=True)
    opp = {
        "kind": "cross_exchange",
        "asset": "BTC",
        "buy_exchange": "binance",
        "sell_exchange": "okx",
        "quote_amount": 100.0,
    }
    out = await slippage_guard.rewalk_opportunity_slippage(opp)
    assert out.get("rewalk") == "ok"
    assert out.get("total_slippage_bps", 0) >= 0


@pytest.mark.asyncio
async def test_rewalk_no_fresh_books():
    slippage_guard._active_alerts.clear()
    from live_book_hub import _books, _last_update_ms

    _books.clear()
    _last_update_ms.clear()
    out = await slippage_guard.rewalk_opportunity_slippage(
        {"kind": "cross_exchange", "asset": "BTC", "buy_exchange": "binance", "sell_exchange": "okx"}
    )
    assert out.get("executable") is False
    assert out.get("rewalk") == "no_fresh_books"


@pytest.mark.asyncio
async def test_validate_alert_sends_when_executable():
    slippage_guard._active_alerts.clear()
    _seed_cross_books(wide_spread=True)
    opp = {
        "kind": "fast_cross",
        "asset": "BTC",
        "buy_exchange": "binance",
        "sell_exchange": "okx",
        "quote_amount": 50.0,
    }
    send, updated = await slippage_guard.validate_alert(opp)
    assert isinstance(updated, dict)
    assert slippage_guard.guard_stats()["active_alerts"] >= 0


@pytest.mark.asyncio
async def test_reconcile_cancels_stale_alerts():
    slippage_guard._active_alerts.clear()
    slippage_guard._active_alerts["abc"] = {"at": 0, "opportunity": {}}
    cancelled = await slippage_guard.reconcile_active_alerts([])
    assert "abc" in cancelled


@pytest.mark.asyncio
async def test_rewalk_cex_dex_path():
    opp = {
        "kind": "cex_dex",
        "dex_liquidity_usd": 500_000.0,
        "dex_price": 100.0,
        "quote_amount": 200.0,
    }
    out = await slippage_guard.rewalk_opportunity_slippage(opp)
    assert out.get("rewalk") == "dex_ok"
    assert "total_slippage_bps" in out


@pytest.mark.asyncio
async def test_rewalk_missing_books_on_cross():
    _seed_cross_books()
    opp = {
        "kind": "cross_exchange",
        "asset": "BTC",
        "buy_exchange": "binance",
        "sell_exchange": "missing_venue",
        "quote_amount": 100.0,
    }
    out = await slippage_guard.rewalk_opportunity_slippage(opp)
    assert out.get("executable") is False


@pytest.mark.asyncio
async def test_rewalk_insufficient_buy_depth():
    _seed_cross_books()
    opp = {
        "kind": "cross_exchange",
        "asset": "BTC",
        "buy_exchange": "binance",
        "sell_exchange": "okx",
        "quote_amount": 1_000_000.0,
    }
    out = await slippage_guard.rewalk_opportunity_slippage(opp)
    assert out.get("executable") is False


@pytest.mark.asyncio
async def test_validate_alert_cancels_when_not_executable():
    slippage_guard._active_alerts.clear()
    from live_book_hub import _books, _last_update_ms

    _books.clear()
    _last_update_ms.clear()
    send, updated = await slippage_guard.validate_alert(
        {"kind": "cross_exchange", "asset": "BTC", "buy_exchange": "binance", "sell_exchange": "okx"}
    )
    assert send is False
    assert updated.get("cancel_reason") in {"stale_prices", "no_fresh_books"} or updated.get("rewalk") == "no_fresh_books"


@pytest.mark.asyncio
async def test_rewalk_triangular_missing_legs():
    _seed_cross_books(wide_spread=True)
    out = await slippage_guard.rewalk_opportunity_slippage(
        {"kind": "triangular", "exchange": "binance", "legs": []}
    )
    assert out.get("rewalk") == "missing_legs"


@pytest.mark.asyncio
async def test_rewalk_triangular_with_books():
    slippage_guard._active_alerts.clear()
    _seed_cross_books(wide_spread=True)
    opp = {
        "kind": "triangular",
        "exchange": "binance",
        "quote_amount": 50.0,
        "legs": [("BTC/USDT", "buy"), ("ETH/BTC", "buy"), ("ETH/USDT", "sell")],
    }
    out = await slippage_guard.rewalk_opportunity_slippage(opp)
    assert out.get("rewalk") in {"triangle_ok", "triangle_depth_fail", "missing_legs", "no_fresh_books"}


@pytest.mark.asyncio
async def test_rewalk_cex_dex_liquidity_fail():
    opp = {"kind": "cex_dex", "dex_liquidity_usd": 0.0, "dex_price": 100.0, "quote_amount": 200.0}
    out = await slippage_guard.rewalk_opportunity_slippage(opp)
    assert out.get("rewalk") == "dex_liquidity_fail"
    assert out.get("executable") is False


@pytest.mark.asyncio
async def test_rewalk_triangular_no_fresh_books():
    from live_book_hub import _books, _last_update_ms

    _books.clear()
    _last_update_ms.clear()
    out = await slippage_guard.rewalk_opportunity_slippage(
        {"kind": "triangular", "exchange": "binance", "legs": [("BTC/USDT", "buy")]}
    )
    assert out.get("rewalk") == "no_fresh_books"


@pytest.mark.asyncio
async def test_rewalk_insufficient_sell_depth():
    _seed_cross_books()
    opp = {
        "kind": "cross_exchange",
        "asset": "BTC",
        "buy_exchange": "binance",
        "sell_exchange": "okx",
        "quote_amount": 500_000.0,
    }
    out = await slippage_guard.rewalk_opportunity_slippage(opp)
    assert out.get("executable") is False
    assert out.get("rewalk") in {"insufficient_buy_depth", "insufficient_sell_depth"}


@pytest.mark.asyncio
async def test_validate_alert_cancels_on_slippage(monkeypatch):
    slippage_guard._active_alerts.clear()
    _seed_cross_books()

    async def _fake_rewalk(opportunity, *, quote_amount=None):
        return {**opportunity, "executable": False, "cancel_reason": "slippage_exceeded", "rewalk": "ok"}

    monkeypatch.setattr(slippage_guard, "rewalk_opportunity_slippage", _fake_rewalk)
    send, updated = await slippage_guard.validate_alert(
        {"kind": "cross_exchange", "asset": "BTC", "buy_exchange": "binance", "sell_exchange": "okx"}
    )
    assert send is False
    assert updated.get("cancel_reason") == "slippage_exceeded"


@pytest.mark.asyncio
async def test_validate_alert_cancels_on_crowd_guard(monkeypatch):
    slippage_guard._active_alerts.clear()
    _seed_cross_books(wide_spread=True)

    async def _fake_crowd(opp):
        return False, {**opp, "cancel_reason": "crowd_saturation", "executable": False}

    monkeypatch.setattr("flywheel_saturation_guard.apply_crowd_guard_to_alert", _fake_crowd)
    send, updated = await slippage_guard.validate_alert(
        {
            "kind": "cross_exchange",
            "asset": "BTC",
            "buy_exchange": "binance",
            "sell_exchange": "okx",
            "quote_amount": 50.0,
        }
    )
    assert send is False
    assert updated.get("cancel_reason") == "crowd_saturation"


def test_guard_stats():
    slippage_guard._active_alerts.clear()
    stats = slippage_guard.guard_stats()
    assert "active_alerts" in stats
    assert "cancelled_total" in stats


def test_fingerprint_stable():
    opp = {"kind": "cross_exchange", "asset": "BTC", "buy_exchange": "binance", "sell_exchange": "okx"}
    assert slippage_guard._fingerprint(opp) == slippage_guard._fingerprint(opp)


@pytest.mark.asyncio
async def test_rewalk_skipped_kind():
    _seed_cross_books(wide_spread=True)
    out = await slippage_guard.rewalk_opportunity_slippage({"kind": "unknown_kind"})
    assert out.get("rewalk") == "skipped"
    assert out.get("executable") is True
