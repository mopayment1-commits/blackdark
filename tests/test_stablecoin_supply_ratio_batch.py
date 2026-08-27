"""Tests — #698 Stablecoin Supply Ratio Intelligence (merged into #577)."""

from __future__ import annotations

from pathlib import Path

import pytest

from bd_platform import capital_protection_controls as cpc
from bd_platform import daily_market_brief as dmb
from bd_platform import on_chain_financials as ocf
from bd_platform import onchain_metrics_library as oml
from bd_platform import unified_arbitrage_engine as uae


@pytest.fixture
def oml_seed(tmp_path, monkeypatch):
    p = tmp_path / "onchain_metrics_library_seed.json"
    p.write_text(Path("data/onchain_metrics_library_seed.json").read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(oml, "_SEED_PATH", p)
    return p


@pytest.fixture
def fin_seed(tmp_path, monkeypatch):
    p = tmp_path / "on_chain_financials_seed.json"
    p.write_text(Path("data/on_chain_financials_seed.json").read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(ocf, "_SEED_PATH", p)
    return p


def test_698_ssr_formula_and_value(oml_seed):
    suite = oml.build_stablecoin_supply_ratio_698()
    assert suite["ok"] is True
    assert suite["ssr"] == 4.2
    assert suite["supported_stablecoins_display"] == "USDC + USDT + DAI + BUSD"
    assert (suite.get("formula") or {}).get("documented") is True
    assert suite.get("unsupported_excluded") is True


def test_698_oscillator_and_bands(oml_seed):
    suite = oml.build_stablecoin_supply_ratio_698()
    assert suite["ssr_oscillator"] is not None
    assert (suite.get("historical_bands") or {}).get("band") == "Undersupplied"
    assert suite["historical_percentile"] < 25
    assert "descriptive_not_predictive" in (suite.get("explanation") or {})


def test_698_historical_regression(oml_seed):
    regression = oml.run_ssr_regression_tests_698()
    assert regression["deterministic"] is True
    assert regression["historical_reproducibility"] is True


def test_698_metrics_library_panel(oml_seed):
    panel = oml.build_metrics_library_panel("BTC")
    assert panel["sub_modules"]["698_stablecoin_supply_ratio"]["ok"] is True


def test_698_market_radar_widget(oml_seed):
    widget = oml.build_market_radar_ssr_widget_698()
    assert widget["widget_label_ar"] == "نسبة السيولة"
    assert widget["ok"] is True


def test_698_daily_brief_hook(oml_seed):
    brief = oml.build_ssr_daily_brief_hook_474()
    assert brief is not None
    assert brief.get("integration_698") is True
    assert "percentile" in brief.get("mention_en", "").lower()


def test_698_capital_protection_alert(oml_seed):
    alerts = oml.build_ssr_liquidity_stress_alert_410()
    assert alerts["ok"] is True
    assert alerts["alert_count"] >= 1
    assert alerts["alerts"][0]["alert_type"] == "ssr_liquidity_stress"


def test_698_arbitrage_adjustment(oml_seed):
    adj = oml.apply_ssr_arbitrage_adjustment_429({"net_edge_bps": 50})
    assert adj["ssr_context_698"]["integration_429"] is True
    assert adj["ssr_adjusted_edge_bps"] is not None


def test_698_financials_market_context(fin_seed, oml_seed):
    panel = ocf.build_on_chain_financials("uniswap")
    ctx = panel.get("ssr_market_context_698")
    assert ctx is not None
    assert ctx.get("ssr") == 4.2


def test_698_qa_reconciliation(oml_seed):
    qa = oml.run_historical_qa_tests()
    assert qa["all_passed"] is True


def test_698_daily_brief_integration(oml_seed):
    brief = dmb.generate_daily_brief()
    assert brief.get("ssr_brief_698") is not None


def test_698_capital_protection_panel(oml_seed):
    panel = cpc.build_capital_awareness_panel()
    ssr_block = panel.get("ssr_liquidity_stress_698")
    assert ssr_block is not None
    assert ssr_block.get("alert_count", 0) >= 1


def test_698_api_route(oml_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    client = TestClient(app)
    resp = client.get("/api/platform/intelligence-ledger/onchain-layer/metrics-library/stablecoin-supply-ratio")
    assert resp.status_code == 200
    assert resp.json().get("ssr") == 4.2
