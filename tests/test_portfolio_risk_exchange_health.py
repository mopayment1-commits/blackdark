"""Tests — Portfolio Risk Management (#109) + Exchange Health Monitor (#110)."""

from __future__ import annotations

import pytest

from bd_platform.portfolio_risk_management import (
    analyze_concentration,
    analyze_portfolio_risk,
    score_protocol_risk,
    suggest_stop_loss,
)
from bd_platform.exchange_health_monitor import (
    _build_alert,
    exchange_health_status,
    LEGAL_DISCLAIMER,
)


def test_stop_loss_suggestion_actionable():
    sl = suggest_stop_loss("SOL", value_usd=10_000, volatility_24h_pct=6.0)
    assert "drops" in sl["action"].lower()
    assert "sell" in sl["action"].lower()
    assert sl["trigger_drop_pct"] >= 2.0
    assert 10 <= sl["suggested_trim_pct"] <= 50


def test_protocol_risk_high_tvl_low_audit():
    low = score_protocol_risk("new_farm")
    assert low["risk_level"] == "high"
    assert low["exit_recommended"] is True
    assert "TVL" in " ".join(low["factors"])


def test_protocol_risk_aave_safe():
    safe = score_protocol_risk("aave")
    assert safe["risk_level"] == "low"
    assert safe["exit_recommended"] is False


def test_concentration_solana_ecosystem():
    holdings = [
        {"symbol": "SOL", "value_usd": 6000},
        {"symbol": "RAY", "value_usd": 2000},
        {"symbol": "BTC", "value_usd": 2000},
    ]
    out = analyze_concentration(holdings, 10_000)
    assert out["concentration_risk"] is True
    assert out["dominant_ecosystem"] == "Solana"
    assert out["dominant_pct"] == 80.0
    assert "concentration risk" in out["action"].lower()


def test_analyze_portfolio_risk_actionable_alerts():
    holdings = [
        {"symbol": "SOL", "value_usd": 7000, "volatility_24h_pct": 9.0},
        {"symbol": "ETH", "value_usd": 2000, "protocol": "new_farm"},
        {"symbol": "BTC", "value_usd": 1000},
    ]
    out = analyze_portfolio_risk(holdings)
    assert out["ok"] is True
    assert out["feature_id"] == 109
    assert out["surface"] == "portfolio_risk_management"
    assert len(out["stop_loss_suggestions"]) == 3
    assert any(a["type"] == "protocol_exit" for a in out["actionable_alerts"])
    assert out["sla_met"] is True
    assert "security" in out


def test_exchange_health_ftx_red_flag():
    snap = {
        "exchange_id": "ftx",
        "health_score": 15,
        "badge": "Blacklisted",
        "dimensions": {"withdrawal": 40.0, "operational": 35.0},
        "explanation": "FTX collapsed",
        "timestamp": "2026-08-24T13:18:45+00:00",
    }
    alert = _build_alert("ftx", snap)
    assert alert["alert_level"] == "critical"
    assert alert["risk_signal"] == "collapse_risk"
    assert "RED FLAG" in alert["headline"]


def test_exchange_health_status_has_disclaimer():
    out = exchange_health_status()
    assert out["ok"] is True
    assert out["feature_id"] == 110
    assert out["product_name"] == "Exchange Health Monitor"
    assert out["mode"] == "risk_signal_only"
    assert LEGAL_DISCLAIMER in out["legal_disclaimer"]
    assert out["sla_met"] is True
    assert "platform_status_134" in out


def test_exchange_health_single_exchange():
    out = exchange_health_status(exchange_id="binance")
    assert out["ok"] is True
    assert out["alert"]["exchange_id"] == "binance"
    assert "withdrawal_status" in out["alert"]


@pytest.mark.asyncio
async def test_portfolio_risk_overview_async(monkeypatch):
    async def fake_ctx(asset):
        return {"volatility_24h_pct": 5.0, "price_usd": 100}

    monkeypatch.setattr("bd_platform.slippage_tolerance_optimizer._market_context", fake_ctx)

    from bd_platform.portfolio_risk_management import portfolio_risk_overview

    out = await portfolio_risk_overview([{"symbol": "ETH", "value_usd": 5000}])
    assert out["ok"] is True
    assert out["stop_loss_suggestions"][0]["volatility_24h_pct"] == 5.0
