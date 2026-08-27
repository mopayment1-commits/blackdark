"""Tests — #673 Liquid Staking, #675 Long/Short Ratio, #676 MVRV Z-Score Suite."""

from __future__ import annotations

from pathlib import Path

import pytest

from bd_platform import capital_protection_controls as cpc
from bd_platform import defi_opportunity_scanner as dos
from bd_platform import investment_thesis_scoring as its
from bd_platform import on_chain_financials as ocf
from bd_platform import onchain_metrics_library as oml
from bd_platform import onchain_metrics_suite as oms
from bd_platform import stablecoin_health_monitor as shm


@pytest.fixture
def dos_seed(tmp_path, monkeypatch):
    p = tmp_path / "defi_opportunity_scanner_seed.json"
    p.write_text(Path("data/defi_opportunity_scanner_seed.json").read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(dos, "_SEED_PATH", p)
    return p


@pytest.fixture
def shm_seed(tmp_path, monkeypatch):
    p = tmp_path / "stablecoin_health_monitor_seed.json"
    p.write_text(Path("data/stablecoin_health_monitor_seed.json").read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(shm, "_SEED_PATH", p)
    return p


@pytest.fixture
def oml_seed(tmp_path, monkeypatch):
    p = tmp_path / "onchain_metrics_library_seed.json"
    p.write_text(Path("data/onchain_metrics_library_seed.json").read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(oml, "_SEED_PATH", p)
    return p


@pytest.fixture
def oms_seed(tmp_path, monkeypatch):
    p = tmp_path / "onchain_metrics_suite_seed.json"
    p.write_text(Path("data/onchain_metrics_suite_seed.json").read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(oms, "_SEED_PATH", p)
    return p


@pytest.fixture
def fin_seed(tmp_path, monkeypatch):
    p = tmp_path / "on_chain_financials_seed.json"
    p.write_text(Path("data/on_chain_financials_seed.json").read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(ocf, "_SEED_PATH", p)
    return p


# --- #673 Liquid Staking ---


def test_673_five_providers(dos_seed):
    lst = dos.build_liquid_staking_dashboard()
    assert lst["ok"] is True
    assert lst["provider_count"] == 5
    assert lst["backing_depeg_source_required"] is True
    names = {p["provider_name"] for p in lst["providers"]}
    assert names == {"Lido", "Rocket Pool", "Coinbase", "Frax", "StakeWise"}


def test_673_mandatory_metrics(dos_seed):
    lst = dos.build_liquid_staking_dashboard()
    for p in lst["providers"]:
        m = p["mandatory_metrics"]
        assert "tvl_usd" in m
        assert "staking_yield_pct" in m
        assert "peg_deviation_pct" in m
        assert "withdrawal_queue_days" in m
        assert p.get("display_backing")
        assert p.get("depeg_source")


def test_673_screener_filter(dos_seed):
    screener = dos.build_defi_opportunity_screener(category="liquid_staking")
    assert screener["screener_filter"] == "liquid_staking"
    assert screener["count"] == 5


def test_673_defi_panel(dos_seed):
    panel = dos.build_defi_panel()
    lst = panel["liquid_staking_intelligence_673"]
    assert lst["ok"] is True
    assert lst["filter"] == "liquid_staking"


def test_673_lst_depeg_monitor(shm_seed):
    monitor = shm.build_lst_depeg_monitor_673()
    assert monitor["ok"] is True
    assert monitor["backing_depeg_source_required"] is True
    assert monitor["alert_count"] >= 1
    assert monitor["alerts"][0].get("depeg_source")


def test_673_portfolio_lst_alerts_410(shm_seed):
    alerts = shm.build_portfolio_lst_alerts_410()
    assert alerts["ok"] is True
    assert alerts["threatened_exposure"] is True
    assert len(alerts["alerts"]) >= 1


def test_673_lst_revenue_641(fin_seed):
    lido = ocf.build_on_chain_financials("lido")
    lst_rev = lido["lst_staking_fee_revenue_673"]
    assert lst_rev["ok"] is True
    assert lst_rev["revenue_type"] == "lst_staking_fees"
    assert lst_rev["staking_fee_revenue_30d_usd"] == 28000000


def test_673_reconciliation(dos_seed):
    result = dos.run_reconciliation_tests()
    ids = {c["id"] for c in result["checks"]}
    assert "liquid_staking_673" in ids
    assert result["ok"] is True


# --- #675 Long/Short Ratio ---


def test_675_per_venue_normalization(oml_seed):
    metric = oml.build_long_short_ratio_metric_577()
    assert metric["ok"] is True
    assert metric["different_exchange_definitions_not_merged_blindly"] is True
    assert len(metric["venues"]) == 4
    for v in metric["venues"]:
        assert v.get("definition_tooltip")
        assert v.get("not_merged_blindly") is True


def test_675_global_weighted_average(oml_seed):
    metric = oml.build_long_short_ratio_metric_577()
    assert metric["global_long_short_ratio"] is not None
    assert metric["weights_documented"] is True


def test_675_extreme_alert_410(oml_seed):
    alert = oml.build_extreme_long_short_alert_410()
    assert alert["ok"] is True
    assert alert["source_ref"] == 675


def test_675_market_radar_widget(oml_seed):
    widget = oml.build_market_radar_long_short_widget_675()
    assert widget["ok"] is True
    assert widget["widget"] == "long_short_ratio"


def test_675_daily_brief_hook(oml_seed):
    brief = oml.build_long_short_daily_brief_hook_474()
    assert brief is not None
    assert brief.get("integration_675") is True
    assert "Binance" in brief.get("mention_en", "")


def test_675_capital_awareness_integration(oml_seed):
    panel = cpc.build_capital_awareness_panel()
    ls = panel.get("long_short_alerts_675") or {}
    assert ls.get("ok") is True or ls.get("feature_ref") == 675


# --- #676 MVRV Z-Score Suite ---


def test_676_cohort_variants(oml_seed, oms_seed):
    suite = oml.build_mvrv_zscore_metric_577("BTC")
    assert suite["ok"] is True
    variants = suite["variants"]
    assert set(variants.keys()) == {"total", "sth", "lth"}
    for v in variants.values():
        assert v.get("no_sell_signal") is True
        assert v.get("no_arbitrary_thresholds") is True


def test_676_formula_and_bands(oml_seed, oms_seed):
    suite = oml.build_mvrv_zscore_metric_577("BTC")
    assert suite["formula_matches_academic_definition"] is True
    assert suite.get("historical_bands")
    assert suite.get("explanation_descriptive_not_predictive") is True


def test_676_regression_deterministic(oms_seed):
    result = oms.run_mvrv_regression_tests_676("BTC")
    assert result["ok"] is True
    assert result["deterministic"] is True


def test_676_market_radar_widget(oml_seed, oms_seed):
    widget = oml.build_market_radar_mvrv_widget_676("BTC")
    assert widget["ok"] is True
    assert widget["section"] == "protocol_valuation"


def test_676_thesis_valuation_dimension(oml_seed, oms_seed):
    dim = oml.score_mvrv_valuation_dimension_676("BTC")
    assert dim["ok"] is True
    assert dim["no_arbitrary_thresholds"] is True
    assert dim["historical_percentile"] is not None


def test_676_thesis_integration(oml_seed, oms_seed):
    thesis = its.score_investment_thesis("BTC")
    assert "mvrv_valuation_676" in (thesis.get("dimensions") or {})


def test_676_metrics_library_panel(oml_seed, oms_seed):
    panel = oml.build_metrics_library_panel("BTC")
    assert panel["sub_modules"]["675_long_short_ratio"]["ok"] is True
    assert panel["sub_modules"]["676_mvrv_zscore_suite"]["ok"] is True


def test_676_historical_qa(oml_seed, oms_seed):
    qa = oml.run_historical_qa_tests()
    test_names = {t["test"] for t in qa["reconciliation_tests"]}
    assert "mvrv_zscore_suite_676" in test_names
    assert "long_short_ratio_675" in test_names


# --- API routes ---


def test_api_routes(oml_seed, oms_seed, dos_seed, shm_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/intelligence-ledger/unified-arbitrage/defi/liquid-staking").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/unified-arbitrage/defi/screener?category=liquid_staking").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/portfolio-ai/capital-awareness/stablecoin-health/lst-monitor").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/onchain-layer/metrics-library/long-short-ratio").status_code == 200
    mvrv = c.get("/api/platform/intelligence-ledger/onchain-layer/metrics-library/mvrv-zscore?asset=BTC")
    assert mvrv.status_code == 200
    assert mvrv.json().get("ok") is True
    regression = c.get("/api/platform/intelligence-ledger/onchain-layer/metrics-library/mvrv-zscore/regression-tests?asset=BTC")
    assert regression.status_code == 200
    assert regression.json().get("deterministic") is True
