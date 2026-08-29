"""Tests — Intelligence & UX Extensions (#228–#241)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import intelligence_ux_extensions_layer as iux


@pytest.fixture
def seed() -> dict:
    return json.loads(Path("data/legal_retail_commercial_seed.json").read_text(encoding="utf-8"))


def test_228_portfolio_insurance_rejected(seed):
    assert iux.portfolio_insurance_rejected_status_228(seed=seed)["portfolio_insurance_rejected"] is True
    hedge = iux.simulate_drawdown_hedge_228(seed=seed)
    assert hedge["simulation_not_insurance"] is True


def test_229_reasoning_explanation(seed):
    reasoning = iux.generate_reasoning_explanation_229(seed=seed)
    assert reasoning["template_engine"] is True
    assert reasoning["ai_naming_rejected"] is True


def test_229_explain_embed(seed):
    from bd_platform.data_sources_layer import explain_opportunity_151

    explain = explain_opportunity_151(seed=seed)
    assert "reasoning" in explain
    assert 229 in explain["merged_features"]


def test_230_cross_exchange_merged(seed):
    status = iux.cross_exchange_arbitrage_status_230(seed=seed)
    assert status["duplicate_of"] == 153
    divergence = iux.analyze_cross_exchange_divergence_230(seed=seed)
    assert divergence["no_execution"] is True


def test_231_triangular_merged(seed):
    assert iux.triangular_arbitrage_status_231(seed=seed)["activation_not_build"] is True


def test_232_price_comparison(seed):
    comparison = iux.analyze_price_comparison_232(seed=seed)
    assert comparison["analyzable_not_exploitable"] is True


def test_232_arbitrage_embed(seed):
    from bd_platform.intelligence_analysis_layer import analyze_arbitrage_opportunity_153

    arb = analyze_arbitrage_opportunity_153(seed=seed)
    assert "price_comparison" in arb
    assert 232 in arb["merged_features"]


def test_233_heatmap(seed):
    heatmap = iux.build_heatmap_component_233(seed=seed)
    assert heatmap["rule_based_coloring"] is True
    assert len(heatmap["cells"]) >= 1


def test_234_live_dashboard_merged(seed):
    assert iux.live_dashboard_status_234(seed=seed)["duplicate_of"] == 179


def test_235_whale_merged(seed):
    assert iux.whale_intelligence_status_235(seed=seed)["duplicate_of"] == 71


def test_236_subscription_merged(seed):
    assert iux.subscription_tiers_status_236(seed=seed)["duplicate_of"] == 60


def test_237_market_summary(seed):
    summary = iux.generate_market_summary_237(seed=seed)
    assert summary["summary_not_prediction"] is True
    assert "fields" in summary


def test_238_market_scan(seed):
    scan = iux.scan_market_opportunities_238(seed=seed)
    assert scan["buy_signal_rejected"] is True
    assert scan["opportunity_detection_only"] is True


def test_239_live_ta_merged(seed):
    assert iux.live_ta_status_239(seed=seed)["activation_not_build"] is True


def test_240_s2f(seed):
    s2f = iux.compute_s2f_240(seed=seed)
    assert s2f["s2f_ratio"] > 50
    assert s2f["historical_not_price_prediction"] is True


def test_241_fred(seed):
    fred = iux.ingest_fred_macro_241(seed=seed)
    assert "FRED" in fred["attribution"]
    assert "M2SL" in fred["series"]


def test_241_macro_embed(seed):
    from bd_platform.onchain_platform_layer import compute_macro_event_nexus_133

    macro = compute_macro_event_nexus_133(seed=seed)
    assert "fred" in macro
    assert 241 in macro["merged_features"]


def test_intelligence_ux_extensions_e2e(seed):
    assert iux.run_intelligence_ux_extensions_e2e_228_241(seed=seed)["all_passed"] is True
