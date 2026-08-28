"""Portfolio Concentration Risk tests."""

from __future__ import annotations

from portfolio_concentration_risk import (
    compute_concentration,
    concentration_risk_status,
    escalate_with_correlation,
    run_concentration_risk_e2e,
    save_user_thresholds,
)


def test_concentration_status():
    status = concentration_risk_status()
    assert status["insight_only"] is True
    assert status["user_configurable_thresholds"] is True


def test_high_concentration_alert():
    holdings = [{"symbol": "BTC", "value_usd": 85000}, {"symbol": "ETH", "value_usd": 15000}]
    result = compute_concentration(holdings, per_asset_thresholds={"default_pct": 30})
    assert result["ok"] is True
    assert len(result["alerts"]) >= 1
    assert result["alerts"][0]["symbol"] == "BTC"
    assert "does not protect" in result["disclaimer"].lower()


def test_correlation_escalation():
    holdings = [{"symbol": "BTC", "value_usd": 90000}, {"symbol": "ETH", "value_usd": 10000}]
    conc = compute_concentration(holdings, per_asset_thresholds={"default_pct": 30})
    out = escalate_with_correlation(
        conc,
        high_correlation_pairs=[{"asset_a": "BTC", "asset_b": "ETH", "correlation": "0.9000"}],
    )
    assert out["risk_score_adjustment"] >= 3


def test_user_thresholds(tmp_path, monkeypatch):
    monkeypatch.setattr("portfolio_concentration_risk._THRESHOLDS_PATH", tmp_path / "thresh.json")
    save_user_thresholds(42, {"default_pct": 25, "BTC": 20})
    result = compute_concentration(
        [{"symbol": "BTC", "value_usd": 80000}, {"symbol": "ETH", "value_usd": 20000}],
        user_id=42,
    )
    assert result["alerts"]


def test_e2e():
    assert run_concentration_risk_e2e()["all_passed"] is True
