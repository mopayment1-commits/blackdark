"""Tests — PnL Attribution & Drift Analysis Engine (#199)."""

from __future__ import annotations

import pytest

from bd_platform import pnl_attribution_engine as pnl


@pytest.fixture
def isolated_pnl_paths(tmp_path, monkeypatch):
    reports = tmp_path / "reports.jsonl"
    monkeypatch.setattr(pnl, "_REPORTS_PATH", reports)
    return reports


def _sample_trade(**overrides):
    base = {
        "trade_id": "t-001",
        "side": "long",
        "entry_price": 100.0,
        "exit_price": 105.0,
        "quantity": 100.0,
        "notional_usd": 10_000.0,
        "trading_fees_usd": 15.0,
        "slippage_usd": 8.0,
        "gas_usd": 5.0,
        "bridge_fees_usd": 0.0,
        "funding_costs_usd": 0.0,
        "expected_net_pnl_usd": 490.0,
        "expected_slippage_usd": 3.0,
        "market_move_pct": 2.0,
        "entry_delay_sec": 30,
        "exit_delay_sec": 10,
        "venue": "uniswap",
        "expected_venue": "binance",
    }
    base.update(overrides)
    return base


def test_waterfall_gross_to_net(isolated_pnl_paths):
    report = pnl.attribute_trade_pnl(_sample_trade())
    assert report["ok"] is True
    assert report["gross_pnl_usd"] == 500.0
    assert report["net_pnl_usd"] == 472.0
    waterfall = report["waterfall"]
    assert waterfall[0]["label"] == "Gross PnL"
    assert waterfall[-1]["label"] == "Net PnL"


def test_drift_analysis_labeled(isolated_pnl_paths):
    report = pnl.attribute_trade_pnl(_sample_trade())
    drift = report["drift_analysis"]
    assert drift is not None
    assert drift["all_labeled"] is True
    assert drift["unexplained_drift_pct"] <= 0.5
    assert "slippage_drift" in drift["attribution"]
    assert report["drift_alert"] is not None


def test_trade_sla_met(isolated_pnl_paths):
    report = pnl.attribute_trade_pnl(_sample_trade())
    assert report["sla_met"] is True
    assert report["duration_ms"] <= 3000


def test_portfolio_sharpe_on_net(isolated_pnl_paths):
    trades = [_sample_trade(trade_id=f"t-{i}") for i in range(5)]
    portfolio = pnl.attribute_portfolio_pnl(trades, period_label="monthly")
    assert portfolio["ok"] is True
    assert portfolio["trade_count"] == 5
    assert portfolio["risk_metrics"]["computed_on"] == "net_pnl"
    assert "sharpe" in portfolio["risk_metrics"]
    assert portfolio["sla_met"] is True


def test_csv_export(isolated_pnl_paths):
    report = pnl.attribute_trade_pnl(_sample_trade())
    csv = pnl.export_trade_csv(report)
    assert "Gross PnL" in csv
    assert "slippage_drift" in csv


def test_methodology_versioned():
    doc = pnl.methodology_documentation()
    assert doc["version"] == "1.0.0"
    assert len(doc["attribution_factors"]) >= 5


def test_pnl_attribution_status():
    status = pnl.pnl_attribution_status()
    assert status["feature_id"] == 199
    assert status["true_cost_engine"] is True
    assert "#113" in status["integrated_features"]
    assert "#130" in status["integrated_features"]
