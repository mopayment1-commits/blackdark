"""Tests — Alpha Engine backtest metrics (#13)."""

from __future__ import annotations

from bd_platform.alpha_backtest import MVP_THRESHOLDS, walk_forward_backtest


def test_walk_forward_backtest_metrics():
  # Synthetic 400-day series with mild upward drift
    returns = [0.001] * 200 + [-0.0005] * 100 + [0.002] * 100
    out = walk_forward_backtest(returns, train_window=60, test_window=20)
    assert out["ok"] is True
    assert "sharpe" in out
    assert "max_drawdown_pct" in out
    assert "win_rate" in out
    assert "acceptance" in out
    assert out["mvp_thresholds"]["sharpe_min"] == MVP_THRESHOLDS["sharpe_min"]


def test_walk_forward_insufficient_data():
    out = walk_forward_backtest([0.01] * 10)
    assert out["ok"] is False
    assert out["error"] == "insufficient_history"
