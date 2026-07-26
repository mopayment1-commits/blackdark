"""Tests for arbitrage engine slippage/spread."""

from arbitrage_engine import _gross_spread_bps, walk_asks


def test_gross_spread_bps_positive():
    bps = _gross_spread_bps(100.0, 101.0)
    assert bps > 0


def test_walk_asks_returns_execution():
    book = {
        "asks": [[100.0, 10.0], [101.0, 10.0]],
        "bids": [[99.0, 10.0]],
    }
    result = walk_asks(book, 500.0)
    assert result is not None
    assert result.average_price > 0
    assert result.base_amount > 0
