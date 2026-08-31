"""Tests — #433 Fill Risk + #434 Alerts + #438 DeFi + #449 Portfolio Intelligence."""

from __future__ import annotations

from pathlib import Path

import pytest

from bd_platform import fill_risk_assessment as fra
from bd_platform import portfolio_intelligence_engine as pie
from bd_platform import unified_arbitrage_engine as uae


@pytest.fixture
def fra_seed(tmp_path, monkeypatch):
    main = Path("data/fill_risk_assessment_seed.json")
    p = tmp_path / "fill_risk_assessment_seed.json"
    p.write_text(main.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(fra, "_SEED_PATH", p)
    return p


@pytest.fixture
def uae_seed(tmp_path, monkeypatch):
    main = Path("data/unified_arbitrage_engine_seed.json")
    p = tmp_path / "unified_arbitrage_engine_seed.json"
    p.write_text(main.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(uae, "_SEED_PATH", p)
    monkeypatch.setattr(fra, "_SEED_PATH", tmp_path / "fill_risk_assessment_seed.json")
    (tmp_path / "fill_risk_assessment_seed.json").write_text(
        Path("data/fill_risk_assessment_seed.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    return p


@pytest.fixture
def pie_seed(tmp_path, monkeypatch):
    main = Path("data/portfolio_intelligence_engine_seed.json")
    p = tmp_path / "portfolio_intelligence_engine_seed.json"
    p.write_text(main.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(pie, "_SEED_PATH", p)
    return p


# --- #433 ---


def test_433_status(fra_seed):
    status = fra.fill_risk_assessment_status()
    assert status["feature_id"] == 433
    assert status["legal_name"] == "Fill Risk Assessment"
    assert status["no_opaque_score"] is True
    assert status["infrastructure_sla_cancelled"] is True


def test_433_fill_risk_breakdown(fra_seed):
    opp = {
        "asset": "BTC",
        "slippage_bps": 10,
        "quote_usd": 1000,
        "buy_venue": "binance",
        "sell_venue": "coinbase",
        "volume_feasibility": {"liquidity_score": 85, "verdict": "full_fill"},
    }
    risk = fra.assess_fill_risk(opp)
    assert 0 <= risk["fill_risk_pct"] <= 100
    assert len(risk["component_breakdown"]) == 5
    assert risk["weights_documented"] is True


def test_433_net_edge_gate(fra_seed):
    opp = {
        "asset": "UNI",
        "slippage_bps": 90,
        "quote_usd": 1000,
        "volume_feasibility": {"liquidity_score": 5, "verdict": "not_fillable"},
        "net_edge_usdt": 0.5,
        "trading_fees_usdt": 0.1,
        "withdrawal_fee_usdt": 0.2,
        "quote_age_ms": 500,
    }
    gate = fra.apply_net_edge_risk_gate(opp)
    assert gate["feature_ref"] == 417


def test_433_reconciliation(fra_seed):
    result = fra.run_reconciliation_tests()
    assert result["ok"] is True


# --- #434 #438 via unified engine ---


def test_438_defi_scanner(uae_seed):
    opps = uae.scan_defi_opportunities()
    assert len(opps) >= 1
    assert opps[0]["feature_ref"] == 438
    assert opps[0]["cancelled_v1_scope"]["flash_loan_simulation"] is True


def test_434_opportunity_alerts(uae_seed):
    panel = uae.build_opportunity_alert_panel()
    assert panel["feature_id"] == 434
    assert panel["worth_studying_not_execution"] is True
    assert panel["no_auto_execution"] is True


def test_433_in_unified_feed(uae_seed):
    feed = uae.build_unified_feed()
    cross = [o for o in feed["opportunities"] if o.get("buy_venue")]
    if cross:
        assert "fill_risk_assessment" in cross[0]


def test_429_extended_reconciliation(uae_seed):
    result = uae.run_reconciliation_tests()
    assert result["ok"] is True


# --- #449 ---


def test_449_existing_module(pie_seed):
    status = pie.portfolio_intelligence_engine_status()
    assert status["feature_id"] == 449
    assert status["existing_module"] is True
    assert status["no_new_module_built"] is True
    assert status["legal_name"] == "Portfolio Intelligence Engine"


def test_449_integrations(pie_seed):
    panel = pie.build_integrated_panel()
    assert panel["capital_protection_410"]["ok"] is True
    assert panel["live_breakeven_404"]["ok"] is True
    assert panel["performance_sla_cancelled"] is True


def test_449_reconciliation(pie_seed):
    result = pie.run_reconciliation_tests()
    assert result["ok"] is True
