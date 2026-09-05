"""Portfolio Risk Tab — CVaR, Correlation, Stress tests."""

from __future__ import annotations

from decimal import Decimal

from portfolio_correlation_analysis import (
    compute_portfolio_correlation_from_holdings,
    pearson_correlation,
    run_portfolio_correlation_e2e,
)
from portfolio_cvar_metric import compute_historical_cvar, compute_portfolio_cvar_from_holdings, run_portfolio_cvar_e2e
from portfolio_risk_tab import compute_portfolio_risk_tab, run_portfolio_risk_tab_e2e
from portfolio_stress_testing import compute_portfolio_stress_from_holdings, run_portfolio_stress_e2e


def test_cvar_exceeds_var():
    returns = [-0.05, -0.04, -0.03, -0.02, -0.01, 0.0, 0.01, 0.02, -0.025, -0.035]
    cvar = compute_historical_cvar(daily_returns=returns, portfolio_value_usd=100_000, confidence=0.95)
    assert cvar["ok"] is True
    assert float(cvar["cvar_usd"]) >= float(cvar["var_usd"])
    assert "not a catastrophe guarantee" in cvar["disclaimer"].lower()


def test_portfolio_cvar_from_holdings():
    holdings = [{"symbol": "BTC", "value_usd": 100000, "btc_beta": 1.0}]
    result = compute_portfolio_cvar_from_holdings(holdings)
    assert result["ok"] is True
    assert "tail_hit_rate" in result


def test_pearson_perfect_correlation():
    assert pearson_correlation([0.01, 0.02, 0.03], [0.02, 0.04, 0.06]) == Decimal("1.0000")


def test_correlation_matrix_two_assets():
    holdings = [
        {"symbol": "BTC", "value_usd": 50000, "btc_beta": 1.0},
        {"symbol": "ETH", "value_usd": 50000, "btc_beta": 1.1},
    ]
    result = compute_portfolio_correlation_from_holdings(holdings)
    assert result["ok"] is True
    assert "matrix" in result
    assert "BTC" in result["matrix"]


def test_stress_three_scenarios():
    holdings = [{"symbol": "BTC", "value_usd": 100000, "btc_beta": 1.0}]
    result = compute_portfolio_stress_from_holdings(holdings, var_usd="500", cvar_usd="800")
    assert result["ok"] is True
    ids = {s["id"] for s in result["scenarios"]}
    assert "flash_crash" in ids
    assert "liquidity_freeze" in ids
    assert "correlation_breakdown" in ids


def test_unified_risk_tab():
    holdings = [
        {"symbol": "BTC", "value_usd": 60000, "btc_beta": 1.0},
        {"symbol": "ETH", "value_usd": 40000, "btc_beta": 1.1},
    ]
    tab = compute_portfolio_risk_tab(holdings)
    assert tab["ok"] is True
    assert tab["var_metric"]["ok"] is True
    assert tab["cvar_metric"]["ok"] is True
    assert tab["correlation_analysis"]["ok"] is True
    assert tab["stress_testing"]["ok"] is True


def test_component_e2e():
    assert run_portfolio_cvar_e2e()["all_passed"] is True
    assert run_portfolio_correlation_e2e()["all_passed"] is True
    assert run_portfolio_stress_e2e()["all_passed"] is True
    assert run_portfolio_risk_tab_e2e()["all_passed"] is True
