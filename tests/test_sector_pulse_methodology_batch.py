"""Tests — #678 Sector Market Brief + #679 Methodology Governance Layer."""

from __future__ import annotations

from pathlib import Path

import pytest

from bd_platform import daily_market_brief as dmb
from bd_platform import market_radar_indicators as mri
from bd_platform import onchain_metrics_library as oml
from bd_platform import sector_market_brief as smb
from bd_platform import unified_arbitrage_engine as uae


@pytest.fixture
def sector_seed(tmp_path, monkeypatch):
    p = tmp_path / "sector_market_brief_seed.json"
    p.write_text(Path("data/sector_market_brief_seed.json").read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(smb, "_SEED_PATH", p)
    return p


@pytest.fixture
def oml_seed(tmp_path, monkeypatch):
    p = tmp_path / "onchain_metrics_library_seed.json"
    p.write_text(Path("data/onchain_metrics_library_seed.json").read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(oml, "_SEED_PATH", p)
    return p


# --- #678 Sector Market Brief ---


def test_678_four_sector_cards(sector_seed):
    pulse = smb.build_sector_pulse_dashboard_678()
    assert pulse["ok"] is True
    assert pulse["card_count"] == 4
    assert pulse["ml_template_rejected"] is True
    assert pulse["no_buy_sell_signals"] is True


def test_678_sector_narratives(sector_seed):
    pulse = smb.build_sector_pulse_dashboard_678()
    assert len(pulse["active_narratives"]) >= 1
    assert "Gaming" in pulse["daily_narrative_en"] or "Solana" in pulse["daily_narrative_en"]
    for card in pulse["sector_cards"]:
        assert card.get("purely_descriptive") is True
        assert card.get("no_buy_sell_signal") is True


def test_678_sector_metrics_577(sector_seed):
    metrics = smb.build_sector_metrics_577()
    assert metrics["ok"] is True
    assert "gaming_liquidity" in metrics["metrics"]
    assert "ai_token_index" in metrics["metrics"]
    assert "rwa_inflows" in metrics["metrics"]
    assert "solana_ecosystem_activity" in metrics["metrics"]


def test_678_daily_brief_hook(sector_seed):
    brief = smb.build_sector_pulse_daily_brief_hook_474()
    assert brief is not None
    assert brief.get("integration_678") is True
    assert brief.get("integration_474") is True


def test_678_sector_ranking_429(sector_seed):
    opps = [
        {"opportunity_id": "defi_gaming_yield_001", "net_edge_usdt": 100},
        {"opportunity_id": "other_opp", "net_edge_usdt": 120},
    ]
    boosted = smb.apply_sector_ranking_boost_429(opps)
    gaming = next(o for o in boosted if o["opportunity_id"] == "defi_gaming_yield_001")
    assert gaming.get("sector_pulse_boost_678") == 5


def test_678_market_radar_widget(sector_seed):
    widget = smb.build_market_radar_sector_pulse_widget_678()
    assert widget["ok"] is True
    assert widget["widget"] == "sector_pulse"


def test_678_status(sector_seed):
    status = smb.sector_market_brief_status()
    assert status["standalone"] is False
    assert status["ml_template_rejected"] is True
    assert "Sharpe" in str(status["rejected_claims"])


def test_678_reconciliation(sector_seed):
    result = smb.run_reconciliation_tests()
    assert result["ok"] is True


def test_678_market_radar_panel(sector_seed):
    panel = mri.build_market_radar_panel()
    assert panel["sector_pulse_678"]["ok"] is True


def test_678_daily_brief_integration(sector_seed, tmp_path, monkeypatch):
    p = tmp_path / "daily_market_brief_seed.json"
    p.write_text(Path("data/daily_market_brief_seed.json").read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(dmb, "_SEED_PATH", p)
    monkeypatch.setattr(smb, "_SEED_PATH", sector_seed)
    brief = dmb.generate_daily_brief()
    assert brief.get("sector_pulse_brief_678") is not None


# --- #679 Methodology Governance ---


def test_679_methodology_page_fields(oml_seed):
    page = oml.build_methodology_page("active_addresses")
    assert page["ok"] is True
    assert page.get("definition")
    assert page.get("formula")
    assert page.get("version")
    assert page.get("migration_history")
    assert page.get("code_link")
    assert page.get("no_undocumented_formula") is True


def test_679_parity_tests(oml_seed):
    parity = oml.run_methodology_parity_tests_679()
    assert parity["ok"] is True
    assert parity["all_passed"] is True
    assert parity["ci_gate"] is True


def test_679_no_undocumented_formula(oml_seed):
    check = oml.validate_undocumented_metrics_679()
    assert check["all_documented"] is True
    assert check["display_blocked_without_methodology"] is True


def test_679_governance_registry(oml_seed):
    registry = oml.build_methodology_registry()
    assert registry["governance_layer"] is True
    assert registry["governance_ref"] == 679
    assert registry["no_undocumented_formula"] is True


def test_679_strategy_vetting_integration(oml_seed):
    verified = oml.verify_strategy_metrics_documented_492(["active_addresses", "mvrv_zscore"])
    assert verified["ok"] is True
    assert verified["all_metrics_documented"] is True


def test_679_metrics_library_panel(oml_seed, sector_seed):
    panel = oml.build_metrics_library_panel("BTC")
    assert panel["sub_modules"]["679_methodology_governance"]["ok"] is True
    assert panel["sub_modules"]["678_sector_metrics"]["ok"] is True


def test_679_historical_qa(oml_seed, sector_seed):
    qa = oml.run_historical_qa_tests()
    test_names = {t["test"] for t in qa["reconciliation_tests"]}
    assert "methodology_parity_679" in test_names
    assert "no_undocumented_formula_679" in test_names


# --- API routes ---


def test_api_routes(oml_seed, sector_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/intelligence-ledger/market-radar/sector-pulse").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/market-radar/sector-pulse/status").status_code == 200
    parity = c.get("/api/platform/intelligence-ledger/onchain-metrics/methodology/parity-tests")
    assert parity.status_code == 200
    assert parity.json().get("all_passed") is True
    page = c.get("/api/platform/intelligence-ledger/onchain-metrics/methodology/active_addresses")
    assert page.status_code == 200
    assert page.json().get("governance_ref") == 679
