"""Tests — #456 Exchange Health Monitor (Sprint-2 Risk Layer)."""

from __future__ import annotations

from pathlib import Path

import pytest

from bd_platform import capital_protection_controls as cac
from bd_platform import exchange_health_monitor as ehm
from bd_platform import fill_feasibility_simulator as ffs


@pytest.fixture
def ehm_seed(tmp_path, monkeypatch):
    main = Path("data/exchange_health_monitor_seed.json")
    p = tmp_path / "exchange_health_monitor_seed.json"
    p.write_text(main.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(ehm, "_SEED_PATH", p)
    return p


@pytest.fixture
def cac_seed(tmp_path, monkeypatch):
    main = Path("data/capital_protection_controls_seed.json")
    p = tmp_path / "capital_protection_controls_seed.json"
    p.write_text(main.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(cac, "_SEED_PATH", p)
    return p


@pytest.fixture
def ffs_seed(tmp_path, monkeypatch):
    main = Path("data/fill_feasibility_seed.json")
    p = tmp_path / "fill_feasibility_seed.json"
    p.write_text(main.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(ffs, "_SEED_PATH", p)
    monkeypatch.setattr(ehm, "_SEED_PATH", tmp_path / "exchange_health_monitor_seed.json")
    (tmp_path / "exchange_health_monitor_seed.json").write_text(
        Path("data/exchange_health_monitor_seed.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    return p


def test_456_status_risk_layer(ehm_seed):
    status = ehm.exchange_health_monitor_status()
    assert status["feature_id"] == 456
    assert status["standalone"] is False
    assert status["legal_name"] == "Exchange Health Monitor"
    assert status["renamed_from"] == "Exchange Insolvency Risk Scraper"
    assert status["infrastructure_sla_cancelled"] is True


def test_456_exchange_grade_scale(ehm_seed):
    coinbase = ehm.evaluate_exchange("coinbase")
    assert coinbase["exchange_grade"] == "A+"
    assert coinbase["health_score"] >= 95
    assert coinbase["constituent_source_metadata"] is True


def test_456_low_health_exchange(ehm_seed):
    htx = ehm.evaluate_exchange("htx")
    assert htx["low_health"] is True
    assert htx["exchange_grade"] in {"F", "D-", "D", "D+"}


def test_456_all_indicators_scored(ehm_seed):
    ev = ehm.evaluate_exchange("binance")
    assert set(ev["component_scores"].keys()) == {
        "proof_of_reserves",
        "hot_wallet_flow_anomaly",
        "withdrawal_suspension_history",
        "regulatory_actions",
        "social_panic_signals",
    }


def test_456_capital_protection_exposure_alert(ehm_seed):
    alerts = ehm.build_portfolio_exchange_exposure_alerts()
    assert alerts["alert_count"] >= 1
    assert alerts["feature_ref"] == 410
    htx_alerts = [a for a in alerts["alerts"] if a["exchange_id"] == "htx"]
    assert len(htx_alerts) == 1
    assert htx_alerts[0]["exposure_pct"] == 22.0


def test_456_capital_awareness_panel_integration(ehm_seed, cac_seed):
    panel = cac.build_capital_awareness_panel()
    eh = panel["exchange_health_alerts"]
    assert eh["integration"] == "capital_protection_controls"
    assert eh["alert_count"] >= 1


def test_456_arbitrage_auto_suppress(ehm_seed):
    panel = ehm.build_arbitrage_health_panel()
    assert panel["suppressed_count"] >= 1
    suppressed = panel["suppressed_opportunities"][0]
    assert suppressed["signal_suppressed"] is True
    assert suppressed["exchange_health"]["suppressed"] is True


def test_456_fill_feasibility_arbitrage_integration(ffs_seed):
    opp = {
        "opportunity_id": "test",
        "asset": "BTC",
        "symbol": "BTC/USDT",
        "buy_venue": "htx",
        "sell_venue": "binance",
    }
    enriched = ffs.enrich_arbitrage_opportunity(opp, size=1.0)
    vf = enriched["volume_feasibility"]
    assert vf["exchange_health_suppressed"] is True
    assert vf["signal_suppressed"] is True


def test_456_methodology_documented(ehm_seed):
    panel = ehm.build_exchange_health_panel()
    assert "proof-of-reserves" in panel["methodology"].lower()
    assert len(panel["grade_scale"]) >= 10


def test_456_reconciliation(ehm_seed):
    result = ehm.run_reconciliation_tests()
    assert result["ok"] is True
    assert result["passed"] == result["total"]
