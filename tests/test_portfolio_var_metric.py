"""Portfolio VaR Metric tests."""

from __future__ import annotations

from decimal import Decimal

from portfolio_var_metric import (
    compute_historical_var,
    compute_portfolio_var_from_holdings,
    compute_var_hit_rate,
    portfolio_var_status,
    run_portfolio_var_e2e,
)


def test_portfolio_var_status():
    status = portfolio_var_status()
    assert status["feature"] == "portfolio_var_metric"
    assert status["insight_only"] is True
    assert status["methodology"] == "historical_percentile"


def test_historical_var():
    returns = [-0.03, -0.02, -0.01, 0.0, 0.01, 0.02, -0.015, -0.005, 0.005, -0.025]
    result = compute_historical_var(daily_returns=returns, portfolio_value_usd=100_000, confidence=0.95)
    assert result["ok"] is True
    assert Decimal(result["var_usd"]) > 0
    assert "not a loss guarantee" in result["disclaimer"].lower()


def test_insufficient_data():
    result = compute_historical_var(daily_returns=[0.01], portfolio_value_usd=1000)
    assert result["ok"] is False


def test_portfolio_var_from_holdings():
    holdings = [
        {"symbol": "BTC", "value_usd": 60000, "btc_beta": 1.0},
        {"symbol": "ETH", "value_usd": 40000, "btc_beta": 1.1},
    ]
    result = compute_portfolio_var_from_holdings(holdings, confidence=0.95)
    assert result["ok"] is True
    assert result["holdings_count"] == 2
    assert "hit_rate" in result
    assert result["provenance"]["methodology_version"]


def test_hit_rate():
    returns = [-0.03, -0.02, -0.01, 0.0, 0.01, 0.02, -0.015, -0.005, 0.005, -0.025]
    hr = compute_var_hit_rate(daily_returns=returns, confidence=0.95)
    assert hr["total_days"] == 10
    assert hr["published_to_accuracy_ledger"] is True


def test_e2e():
    e2e = run_portfolio_var_e2e()
    assert e2e["all_passed"] is True
