"""Tests — #92 Strategy Lab Replay + #94 AI Trade Simulator."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from bd_platform.strategy_lab_replay import (
    PurgedBarSeries,
    point_in_time_decision_signal,
    ReplaySession,
    _outcome_after_bars,
)
from bd_platform.ai_trade_simulator import (
    execution_price,
    exchange_fee_usd,
    performance_report,
    historical_backtest,
    reset_portfolio,
    _max_drawdown,
)


def _bars(n: int = 100, *, start: float = 100.0, drift: float = 0.001) -> list[dict]:
    rows = []
    price = start
    for i in range(n):
        price *= 1 + drift
        rows.append({"ts": i * 3_600_000, "open": price, "high": price, "low": price, "close": price, "volume": 1.0})
    return rows


def test_purged_series_no_future_leakage():
    series = PurgedBarSeries(asset="BTC", interval="1h", bars=_bars(50), source="test")
    view = series.view_as_of(10)
    assert len(view) == 11
    assert view[-1]["close"] == series.bar(10)["close"]
    with pytest.raises(IndexError):
        series.view_as_of(100)


def test_point_in_time_signal_uses_past_only():
    closes = [100 + i * 0.5 for i in range(30)]
    sig = point_in_time_decision_signal(closes, asset="BTC")
    assert sig["action"] in {"buy", "sell", "hold"}
    assert sig["future_data_used"] is False
    assert sig["confidence_pct"] > 0


def test_outcome_computed_from_future_bars_only():
    out = _outcome_after_bars(100.0, [101.0, 102.0, 103.0], horizon=3)
    assert out["available"] is True
    assert out["pnl_pct"] == pytest.approx(3.0, abs=0.1)


def test_replay_session_step_no_leakage():
    series = PurgedBarSeries(asset="BTC", interval="1h", bars=_bars(80), source="test")
    session = ReplaySession(session_id="t1", series=series, horizon_bars=5)
    result = session.step()
    assert result["ok"] is True
    assert result["step"]["no_future_leakage"] is True
    assert "ai_signal" in result["step"]
    assert "actual_outcome" in result["step"]


def test_execution_price_includes_slippage():
    ex = execution_price(100.0, side="buy", order_usd=10_000)
    assert ex["executed_price"] > 100.0
    ex_sell = execution_price(100.0, side="sell", order_usd=10_000)
    assert ex_sell["executed_price"] < 100.0


def test_exchange_fee_positive():
    assert exchange_fee_usd(1000.0) > 0


def test_performance_report_metrics():
    trades = [
        {"status": "closed", "pnl_usd": 100},
        {"status": "closed", "pnl_usd": -50},
        {"status": "closed", "pnl_usd": 80},
    ]
    equity = [10_000, 10_100, 10_050, 10_130]
    perf = performance_report(trades, equity, initial_capital=10_000)
    assert perf["win_rate"] == pytest.approx(2 / 3, abs=0.01)
    assert perf["total_pnl_usd"] == 130
    assert _max_drawdown([10_000, 10_500, 9_000, 9_500]) == 14.29


@pytest.mark.asyncio
async def test_historical_backtest_mocked():
    bars = _bars(120, drift=0.002)
    series = PurgedBarSeries(asset="BTC", interval="1h", bars=bars, source="test")
    with patch(
        "bd_platform.strategy_lab_replay.fetch_ohlcv_series",
        new=AsyncMock(return_value=series),
    ):
        out = await historical_backtest("BTC", max_bars=50, initial_capital=10_000)
    assert out["ok"] is True
    assert out["feature"] == "#94"
    assert out["no_future_leakage"] is True
    assert "performance" in out
    assert "comparison" in out


@pytest.mark.asyncio
async def test_replay_batch_mocked():
    bars = _bars(100)
    series = PurgedBarSeries(asset="ETH", interval="1h", bars=bars, source="test")
    with patch(
        "bd_platform.strategy_lab_replay.fetch_ohlcv_series",
        new=AsyncMock(return_value=series),
    ):
        from bd_platform.strategy_lab_replay import run_replay_batch

        out = await run_replay_batch("ETH", max_steps=10)
    assert out["ok"] is True
    assert out["no_future_leakage"] is True
    assert out["summary"]["steps_played"] >= 1


def test_reset_portfolio(tmp_path, monkeypatch):
    monkeypatch.setattr("bd_platform.ai_trade_simulator._PORTFOLIOS_PATH", tmp_path / "portfolios.json")
    out = reset_portfolio("user-test-1", capital=50_000)
    assert out["ok"] is True
    assert out["portfolio"]["cash_usd"] == 50_000
