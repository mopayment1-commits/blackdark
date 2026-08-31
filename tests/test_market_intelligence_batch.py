"""Tests — #719 #721 #723 #724 #726 #728 market intelligence batch."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import (
    dashboard_builder,
    interactive_charting_engine,
    market_breadth,
    market_intelligence_engine,
    portfolio_risk_analytics,
    smart_anomaly_alert_engine,
)


@pytest.fixture
def anomaly_seed(tmp_path, monkeypatch):
    p = tmp_path / "smart_anomaly_alert_engine_seed.json"
    p.write_text(json.dumps({
        "backtest": {"total_alerts": 100, "correct_alerts": 85, "false_positives": 15},
        "baselines": {"BTC": {"volume_24h": {"rolling_mean": 100, "rolling_std": 10, "sample_days": 30}}},
        "metrics": {"BTC": [{"metric": "volume_24h", "asset": "BTC", "current_value": 150}]},
        "alerts": [{"alert_id": "a1", "type": "unusual_liquidity", "absorbed_from": 131, "asset": "BTC", "metric": "v", "z_score": 3.5, "deviation_pct": 50, "severity": "high"}],
    }), encoding="utf-8")
    monkeypatch.setattr(smart_anomaly_alert_engine, "_SEED_PATH", p)
    return p


@pytest.fixture
def bot_seed(tmp_path, monkeypatch):
    p = tmp_path / "market_intelligence_engine_seed.json"
    p.write_text(json.dumps({
        "false_positive_tests": [{"passed": True, "false_positive_rate_pct": 10}],
        "assets": {"BTC": {"patterns": {"cadence_regularity": 0.8, "size_uniformity": 0.7, "cancel_ratio": 0.5, "round_lot_pct": 0.9}}},
    }), encoding="utf-8")
    monkeypatch.setattr(market_intelligence_engine, "_SEED_PATH", p)
    return p


@pytest.fixture
def corr_seed(tmp_path, monkeypatch):
    p = tmp_path / "portfolio_risk_analytics_seed.json"
    p.write_text(json.dumps({
        "universes": {"default": {"assets": ["BTC", "ETH"]}},
        "correlations": {"default": {"matrix": {"BTC": {"BTC": 1.0, "ETH": 0.8}, "ETH": {"BTC": 0.8, "ETH": 1.0}}}},
    }), encoding="utf-8")
    monkeypatch.setattr(portfolio_risk_analytics, "_SEED_PATH", p)
    return p


@pytest.fixture
def breadth_seed(tmp_path, monkeypatch):
    p = tmp_path / "market_breadth_seed.json"
    p.write_text(json.dumps({
        "universe": {"version": "2.3", "last_rebalance": "2026-08-01", "benchmark": "Top 100"},
        "breadth": {"advancing": 60, "declining": 30, "unchanged": 10, "missing": 0, "constituents": []},
    }), encoding="utf-8")
    monkeypatch.setattr(market_breadth, "_SEED_PATH", p)
    return p


@pytest.fixture
def chart_seed(tmp_path, monkeypatch):
    p = tmp_path / "interactive_charting_engine_seed.json"
    p.write_text(json.dumps({
        "performance": {"measured_latency_ms": 45},
        "indicators": [f"IND{i}" for i in range(55)],
    }), encoding="utf-8")
    monkeypatch.setattr(interactive_charting_engine, "_SEED_PATH", p)
    return p


@pytest.fixture
def dash_seed(tmp_path, monkeypatch):
    p = tmp_path / "dashboard_builder_seed.json"
    p.write_text(json.dumps({
        "dashboards": {"default": {"dashboard_id": "default", "name": "Test", "owner": "u1", "version": 1, "widgets": [{"type": "chart"}]}},
    }), encoding="utf-8")
    monkeypatch.setattr(dashboard_builder, "_SEED_PATH", p)

    def _mock_deps():
        return {
            "dependencies": {726: {"ready": True}, 742: {"ready": True}},
            "all_dependencies_met": True,
            "display": "mock",
        }

    monkeypatch.setattr(dashboard_builder, "check_dependencies", _mock_deps)
    return p


def test_719_baseline_and_low_sample(anomaly_seed):
    guard = smart_anomaly_alert_engine.build_low_sample_guard(5)
    assert guard["alert_suppressed"] is True
    bt = smart_anomaly_alert_engine.build_backtest_false_positives()
    assert bt["false_positives"] == 15
    assert "15.0%" in bt["display"]


def test_719_anomaly_detection(anomaly_seed):
    panel = smart_anomaly_alert_engine.build_smart_anomaly_panel("BTC")
    assert panel["ok"] is True
    assert len(panel["detected_anomalies"]) >= 1


def test_721_bot_activity_layer(bot_seed):
    panel = market_intelligence_engine.build_market_intelligence_panel("BTC")
    assert panel["bot_activity"]["rule_based_first"] is True
    assert "oracle_api_export" in panel


def test_723_correlation_not_standalone(corr_seed):
    panel = portfolio_risk_analytics.build_correlation_panel()
    assert panel["correlation"]["not_standalone"] is True
    assert panel["correlation"]["missing_data_policy"]["no_interpolation"] is True


def test_724_breadth_universe(breadth_seed):
    panel = market_breadth.build_market_breadth_panel()
    assert "2.3" in panel["universe"]["display"]
    assert panel["disclaimer_hideable"] is False


def test_726_renamed_charting(chart_seed):
    status = interactive_charting_engine.interactive_charting_status()
    assert status["renamed_from"] == "CryptoQuant (Free Data/Charts)"
    assert status["indicators"]["requirement_met"] is True
    assert status["drawing_tools"]["sub_task"] == "#732"


def test_728_dashboard_builder(dash_seed):
    panel = dashboard_builder.build_dashboard_panel("default")
    assert panel["ok"] is True
    assert panel["permissions_enforced"] is True


def test_api_routes(anomaly_seed, bot_seed, corr_seed, breadth_seed, chart_seed, dash_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/intelligence-ledger/smart-anomaly-alerts/status").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/market-intelligence/bot-activity?asset=BTC").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/portfolio-risk/correlation").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/market-breadth").status_code == 200
    assert c.get("/api/platform/charting/status").status_code == 200
    assert c.get("/api/platform/dashboard-builder/status").status_code == 200


def test_full_seeds_exist():
    assert json.loads(Path("data/smart_anomaly_alert_engine_seed.json").read_text())["feature_id"] == 719
    assert json.loads(Path("data/market_intelligence_engine_seed.json").read_text())["feature_id"] == 721
