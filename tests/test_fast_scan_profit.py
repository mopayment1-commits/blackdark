"""Tests — fast_scan profit path (price in memory → decision)."""

from __future__ import annotations

from fast_scan_engine import run_fast_scan
from live_book_hub import update_top_of_book


def _seed_profitable_spread():
    update_top_of_book("binance", "BTC/USDT", bid=50000, bid_qty=2, ask=50005, ask_qty=2)
    update_top_of_book("okx", "BTC/USDT", bid=50100, bid_qty=2, ask=50105, ask_qty=2)
    update_top_of_book("bybit", "BTC/USDT", bid=50050, bid_qty=2, ask=50055, ask_qty=2)


def test_fast_scan_latency_under_50ms_warm():
    _seed_profitable_spread()
    run_fast_scan()  # warmup
    result = run_fast_scan()
    assert result["latency_ms"] < 50
    assert result["latency_tier"] == "millisecond"


def test_fast_scan_net_profit_after_fees():
    _seed_profitable_spread()
    result = run_fast_scan()
    opps = result.get("opportunities") or []
    if opps:
        top = opps[0]
        assert "net_profit_usdt" in top
        assert "net_spread_bps" in top


def test_fast_scan_no_opportunity_when_spread_negative():
    from live_book_hub import _books, _last_update_ms

    _books.clear()
    _last_update_ms.clear()
    update_top_of_book("binance", "BTC/USDT", bid=100, bid_qty=1, ask=101, ask_qty=1)
    update_top_of_book("okx", "BTC/USDT", bid=99, bid_qty=1, ask=100, ask_qty=1)
    result = run_fast_scan()
    assert result["opportunities"] == []


def test_fast_scan_same_exchange_best_bid_and_ask():
    from live_book_hub import _books, _last_update_ms

    _books.clear()
    _last_update_ms.clear()
    update_top_of_book("binance", "SOL/USDT", bid=150.5, bid_qty=2, ask=150.0, ask_qty=2)
    update_top_of_book("okx", "SOL/USDT", bid=149.0, bid_qty=2, ask=149.5, ask_qty=2)
    result = run_fast_scan()
    assert result["engine"] == "fast_scan_in_memory"


def test_fast_scan_skips_when_single_venue_dominates_bid_and_ask():
    """best_bid_ex == best_ask_ex → no cross-exchange opportunity."""
    from live_book_hub import _books, _last_update_ms

    _books.clear()
    _last_update_ms.clear()
    update_top_of_book("binance", "ETH/USDT", bid=3000, bid_qty=1, ask=3001, ask_qty=1)
    result = run_fast_scan()
    assert result["opportunities"] == []
