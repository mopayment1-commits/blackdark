"""P0 financial executability — false-profit prevention and fail-closed execution."""

from __future__ import annotations

import pytest

import executable_edge_truth as eet
import profit_fee_algorithms as pfa
from fast_scan_engine import _cross_exchange_spread


def _book(bid: float, ask: float, qty: float = 100.0) -> dict:
    return {"bids": [[bid, qty]], "asks": [[ask, qty]]}


def test_mark_indicative_clears_actionable_labels():
    out = eet.mark_indicative_only(
        {"profitable": True, "executable": True, "net_profit_usdt": 12.0, "net_spread_bps": 40},
        reason="top_of_book_only_no_depth",
    )
    assert out["profitable"] is False
    assert out["executable"] is False
    assert out["actionable"] is False
    assert out["indicative"] is True
    assert out["indicative_net_profit_usdt"] == 12.0
    assert out["net_executable_profit_usdt"] is None


def test_apply_net_rejects_non_positive():
    out = eet.apply_net_executable_profit({"executable": True}, net_profit_usdt=-0.01)
    assert out["profitable"] is False
    assert out["executable"] is False


def test_apply_net_accepts_positive_executable():
    out = eet.apply_net_executable_profit({"executable": True}, net_profit_usdt=1.25)
    assert out["profitable"] is True
    assert out["executable"] is True
    assert out["net_executable_profit_usdt"] == 1.25


def test_fees_erase_apparent_topline_profit():
    # Tiny spread that looks positive on mid/topline but dies after fees+withdraw.
    buy = _book(100.0, 100.0, qty=200.0)
    sell = _book(100.15, 100.2, qty=200.0)
    row = pfa.net_cross_exchange_profit(
        buy,
        sell,
        buy_exchange="binance",
        sell_exchange="okx",
        symbol="BTC/USDT",
        notional=1000.0,
    )
    assert row is not None
    assert row["net_profit_usdt"] < 0


def test_unknown_withdrawal_blocks_net_profit():
    buy = _book(100.0, 100.0, qty=200.0)
    sell = _book(120.0, 121.0, qty=200.0)
    row = pfa.net_cross_exchange_profit(
        buy,
        sell,
        buy_exchange="binance",
        sell_exchange="okx",
        symbol="UNKNOWNCOIN/USDT",
        notional=100.0,
    )
    assert row is None


def test_insufficient_depth_returns_none():
    thin = {"bids": [[110.0, 0.001]], "asks": [[100.0, 0.001]]}
    assert (
        pfa.net_cross_exchange_profit(
            thin,
            thin,
            buy_exchange="binance",
            sell_exchange="okx",
            symbol="BTC/USDT",
            notional=10_000.0,
        )
        is None
    )


def test_fast_scan_never_claims_executable(monkeypatch):
    def _fake_best(exchange: str, symbol: str):
        prices = {
            "binance": {"bid": 100.0, "ask": 100.1, "mid": 100.05},
            "okx": {"bid": 101.0, "ask": 101.1, "mid": 101.05},
        }
        row = prices.get(exchange)
        return row

    monkeypatch.setattr("fast_scan_engine.get_best_price", _fake_best)
    opp = _cross_exchange_spread("BTC")
    assert opp is not None
    assert opp.get("topline_positive") is True
    assert opp.get("profitable") is False
    assert opp.get("executable") is False
    assert opp.get("indicative") is True


@pytest.mark.asyncio
async def test_rewalk_rejects_when_fees_erase_profit(monkeypatch):
    import slippage_guard
    from live_book_hub import _books, _last_update_ms, update_top_of_book

    _books.clear()
    _last_update_ms.clear()
    # Spread too thin vs withdrawal + trading fees.
    update_top_of_book("binance", "BTC/USDT", bid=99.9, bid_qty=50.0, ask=100.0, ask_qty=50.0)
    update_top_of_book("okx", "BTC/USDT", bid=100.2, bid_qty=50.0, ask=100.3, ask_qty=50.0)

    out = await slippage_guard.rewalk_opportunity_slippage(
        {
            "kind": "cross_exchange",
            "asset": "BTC",
            "buy_exchange": "binance",
            "sell_exchange": "okx",
            "quote_amount": 1000.0,
        }
    )
    assert out.get("executable") is False
    assert out.get("profitable") is False


@pytest.mark.asyncio
async def test_try_execute_skips_non_executable(monkeypatch):
    import execution_engine as ee

    async def _truth(opp):
        return eet.mark_indicative_only(opp, reason="stale_or_invalid_quotes")

    async def _state():
        return {"panic_active": False, "auto_execution_enabled": True}

    monkeypatch.setattr(ee, "_live_enabled", lambda: False)
    monkeypatch.setattr(ee, "_dry_run_default", lambda: True)
    monkeypatch.setattr(ee, "_state_skip_reason", lambda *a, **k: None)
    monkeypatch.setattr(ee, "_opportunity_risk_skip_reason", lambda *a, **k: None)
    monkeypatch.setattr(ee, "_ensure_execution_gates_safe", lambda o: o)
    monkeypatch.setattr(ee, "_gate_skip_reason", lambda *a, **k: None)
    monkeypatch.setattr(ee, "_half_life_skip_reason", lambda *a, **k: None)
    monkeypatch.setattr("executable_edge_truth.enforce_execution_quote_truth", _truth)
    monkeypatch.setattr("database.fetch_execution_state", _state)
    monkeypatch.setattr("risk_manager.is_trading_frozen", lambda: False)

    result = await ee.try_execute_from_opportunity(
        {"kind": "cross_exchange", "asset": "BTC", "executable": True, "net_profit_usdt": 50}
    )
    assert result.get("skipped") is True
    assert result.get("reason") in {"stale_or_invalid_quotes", "not_executable"}


@pytest.mark.asyncio
async def test_enforce_execution_truth_stale(monkeypatch):
    monkeypatch.setattr(
        "stale_price_guard.validate_opportunity_quotes",
        lambda *_a, **_k: (False, {"reason": "stale"}),
    )

    out = await eet.enforce_execution_quote_truth(
        {"kind": "cross_exchange", "asset": "BTC", "executable": True, "profitable": True}
    )
    assert out["executable"] is False
    assert out["profitable"] is False
    assert out.get("cancel_reason") == "stale_prices"
