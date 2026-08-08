"""Core module tests for 80% buyer-critical coverage."""

import pytest

from fast_scan_engine import _cross_exchange_spread, run_fast_scan
from live_book_hub import get_best_price, hub_stats, update_top_of_book
from service_bus import bus_enabled, bus_stats, publish, subscribe


def test_live_book_hub_update_and_read():
    update_top_of_book("binance", "BTC/USDT", bid=50000, bid_qty=1, ask=50001, ask_qty=1)
    update_top_of_book("okx", "BTC/USDT", bid=50010, bid_qty=1, ask=50011, ask_qty=1)
    px = get_best_price("binance", "BTC/USDT")
    assert px is not None
    assert px["bid"] == 50000
    stats = hub_stats()
    assert stats["symbol_count"] >= 1


def test_cross_exchange_spread():
    update_top_of_book("binance", "ETH/USDT", bid=3000, bid_qty=1, ask=3001, ask_qty=1)
    update_top_of_book("okx", "ETH/USDT", bid=3010, bid_qty=1, ask=3005, ask_qty=1)
    opp = _cross_exchange_spread("ETH")
    assert opp is not None
    assert opp["asset"] == "ETH"


def test_fast_scan_returns_latency():
    update_top_of_book("binance", "SOL/USDT", bid=100, bid_qty=1, ask=100.1, ask_qty=1)
    update_top_of_book("bybit", "SOL/USDT", bid=100.5, bid_qty=1, ask=100.2, ask_qty=1)
    result = run_fast_scan()
    assert "latency_ms" in result
    assert result["latency_ms"] < 500
    assert result["engine"] == "fast_scan_in_memory"


@pytest.mark.asyncio
async def test_service_bus_local_publish():
    received = []

    async def handler(payload):
        received.append(payload)

    subscribe("test.channel", handler)
    ok = await publish("test.channel", {"asset": "BTC", "profit": 1.0})
    assert ok is True
    assert len(received) == 1
    stats = bus_stats()
    assert stats["enabled"] is True


def test_bus_enabled():
    assert bus_enabled() is True
