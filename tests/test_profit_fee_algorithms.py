"""Due diligence — profit_fee_algorithms (depth walk + net profit after fees)."""

from __future__ import annotations

import profit_fee_algorithms as pfa


def _book(bid: float, ask: float, qty: float = 100.0) -> dict:
    return {"bids": [[bid, qty]], "asks": [[ask, qty]]}


def test_gross_spread_and_tops():
    book = _book(99.0, 100.0)
    assert pfa.gross_spread_bps(100.0, 101.0) > 0
    assert pfa.top_ask(book) == 100.0
    assert pfa.top_bid(book) == 99.0


def test_walk_asks_and_bids_roundtrip():
    buy = _book(99.0, 100.0, qty=50.0)
    sell = _book(101.0, 102.0, qty=50.0)
    bought = pfa.walk_asks(buy, 500.0)
    assert bought is not None
    sold = pfa.walk_bids(sell, bought.base_amount)
    assert sold is not None
    assert sold.quote_value > bought.quote_cost


def test_net_cross_exchange_profit_positive():
    buy = _book(100.0, 100.0, qty=200.0)
    sell = _book(102.0, 103.0, qty=200.0)
    row = pfa.net_cross_exchange_profit(
        buy,
        sell,
        buy_exchange="binance",
        sell_exchange="okx",
        symbol="BTC/USDT",
        notional=100.0,
    )
    assert row is not None
    assert row["trading_fees_usdt"] >= 0
    assert row["withdrawal_fee_usdt"] >= 0
    assert "net_profit_usdt" in row


def test_fee_helpers():
    assert pfa.open_leg_fees_usdt(1000.0) > 0
    assert pfa.funding_open_leg_fees_usdt(1000.0) > 0
    assert pfa.slippage_buffer_usdt(100.0, 5.0) >= 0


def test_net_cross_returns_none_without_depth():
    thin = {"bids": [[100.0, 0.001]], "asks": [[100.1, 0.001]]}
    assert pfa.net_cross_exchange_profit(thin, thin, buy_exchange="a", sell_exchange="b", symbol="BTC/USDT") is None


def test_walk_asks_partial_level():
    book = {"asks": [[100.0, 1.0], [101.0, 100.0]], "bids": [[99.0, 10.0]]}
    ex = pfa.walk_asks(book, 150.0)
    assert ex is not None
    assert ex.levels_consumed >= 2


def test_walk_bids_partial_level():
    book = {"bids": [[100.0, 1.0], [99.0, 50.0]], "asks": [[101.0, 10.0]]}
    ex = pfa.walk_bids(book, 1.5)
    assert ex is not None
    assert ex.levels_consumed >= 2
