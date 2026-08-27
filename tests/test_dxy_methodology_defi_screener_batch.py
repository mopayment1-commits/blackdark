"""Tests — #655 DXY Elasticity, #656 Methodology Registry, #658 DeFi Screener."""

from __future__ import annotations

from pathlib import Path

import pytest

from bd_platform import daily_market_brief as dmb
from bd_platform import defi_opportunity_scanner as dos
from bd_platform import dxy_dollar_elasticity as dxy
from bd_platform import investment_thesis_scoring as its
from bd_platform import market_radar_indicators as mri
from bd_platform import onchain_metrics_library as oml


@pytest.fixture
def dxy_seed(tmp_path, monkeypatch):
    p = tmp_path / "dxy_dollar_elasticity_seed.json"
    p.write_text(Path("data/dxy_dollar_elasticity_seed.json").read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(dxy, "_SEED_PATH", p)
    return p


@pytest.fixture
def oml_seed(tmp_path, monkeypatch):
    p = tmp_path / "onchain_metrics_library_seed.json"
    p.write_text(Path("data/onchain_metrics_library_seed.json").read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(oml, "_SEED_PATH", p)
    return p


@pytest.fixture
def defi_seed(tmp_path, monkeypatch):
    p = tmp_path / "defi_opportunity_scanner_seed.json"
    p.write_text(Path("data/defi_opportunity_scanner_seed.json").read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(dos, "_SEED_PATH", p)
    return p


@pytest.fixture
def brief_seed(tmp_path, monkeypatch):
    p = tmp_path / "daily_market_brief_seed.json"
    p.write_text(Path("data/daily_market_brief_seed.json").read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(dmb, "_SEED_PATH", p)
    return p


def test_655_macro_panel_ok(dxy_seed):
    panel = dxy.build_macro_context_panel("BTC")
    assert panel["ok"] is True
    assert panel["standalone"] is False
    assert panel["no_prediction_guarantee"] is True


def test_655_correlation_30d(dxy_seed):
    corr = dxy.compute_dxy_correlation("BTC")
    assert corr["correlation_coefficient_30d"] == pytest.approx(-0.62, abs=0.01)
    assert corr["window_days"] == 30


def test_655_elasticity_with_ci(dxy_seed):
    est = dxy.estimate_elasticity("BTC")
    assert est["elasticity_pct_per_dxy_pct"] == pytest.approx(-0.8, abs=0.01)
    assert est["confidence_interval"]["low"] < est["elasticity_pct_per_dxy_pct"]
    assert est["context_not_forecast"] is True


def test_655_fred_source(dxy_seed):
    panel = dxy.build_macro_context_panel()
    assert panel["dxy"]["source"] == "FRED"


def test_655_sla(dxy_seed):
    panel = dxy.build_macro_context_panel()
    assert panel["sla"]["response_within_target"] is True
    assert panel["sla"]["accuracy_pct"] >= 95


def test_655_usd_pair_adjustment(dxy_seed):
    opps = dxy.apply_dxy_trend_to_usd_pairs([{"pair": "BTC/USD", "net_edge_usdt": 100}])
    assert opps[0]["dxy_macro_adjustment_655"] is not None


def test_655_daily_brief_integration(dxy_seed, brief_seed):
    brief = dmb.generate_daily_brief()
    assert brief.get("dxy_macro_context_655") is not None
    assert any(i.get("feature_ref_655") == 655 for i in brief.get("why") or [])


def test_655_market_radar_integration(dxy_seed):
    panel = mri.build_market_radar_panel()
    assert panel.get("dxy_macro_context_655", {}).get("ok") is True


def test_656_methodology_registry(oml_seed):
    registry = oml.build_methodology_registry()
    assert registry["ok"] is True
    assert registry["code_docs_parity_required"] is True
    assert registry["metric_count"] >= 3


def test_656_methodology_page(oml_seed):
    page = oml.build_methodology_page("active_addresses")
    assert page["ok"] is True
    assert page["methodology_button"] == "المنهجية"
    assert len(page["contracts"]) >= 1
    assert page["code_docs_parity"]["parity_verified"] is True


def test_656_metric_definitions_button(oml_seed):
    defs = oml.build_metric_definitions()
    assert all(m.get("methodology_button") == "المنهجية" for m in defs["metrics"])


def test_656_thesis_links(oml_seed):
    links = oml.get_thesis_methodology_links("BTC")
    assert len(links) >= 2
    assert links[0]["methodology_button"] == "المنهجية"


def test_656_thesis_integration(oml_seed):
    thesis = its.score_investment_thesis("BTC")
    assert len(thesis.get("methodology_links_656") or []) >= 2


def test_658_screener_ok(defi_seed):
    screener = dos.build_defi_opportunity_screener()
    assert screener["ok"] is True
    assert screener["risk_return_separated"] is True
    assert screener["no_apy_only_ranking"] is True


def test_658_display_columns(defi_seed):
    screener = dos.build_defi_opportunity_screener()
    cols = screener["opportunities"][0]["display_columns"]
    assert "base_apy_pct" in cols
    assert "incentive_apy_pct" in cols
    assert "risk_grade" in cols
    assert "net_score" in cols


def test_658_backend_filters(defi_seed):
    filtered = dos.build_defi_opportunity_screener(chain="ethereum", risk_grade="A", min_liquidity_usd=400_000_000)
    assert filtered["filters_applied"]["backend_filters"] is True
    assert filtered["count"] >= 1


def test_658_defi_panel_integration(defi_seed):
    panel = dos.build_defi_panel()
    assert panel.get("defi_opportunity_screener_658", {}).get("ok") is True


def test_655_reconciliation(dxy_seed):
    result = dxy.run_reconciliation_tests()
    assert result["ok"] is True


def test_658_reconciliation(defi_seed):
    result = dos.run_reconciliation_tests()
    assert result["ok"] is True
    ids = {c["id"] for c in result["checks"] if c["passed"]}
    assert "defi_screener_658" in ids
