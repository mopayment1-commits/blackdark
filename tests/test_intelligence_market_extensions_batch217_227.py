"""Tests — Intelligence & Market Extensions (#217–#227)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import intelligence_market_extensions_layer as ime


@pytest.fixture
def seed() -> dict:
    return json.loads(Path("data/legal_retail_commercial_seed.json").read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def reset():
    ime.reset_intelligence_market_extensions_state()
    yield
    ime.reset_intelligence_market_extensions_state()


def test_217_auto_router_rejected(seed):
    status = ime.auto_router_rejected_status_217(seed=seed)
    assert status["auto_router_rejected"] is True
    venue = ime.analyze_best_venue_217(seed=seed)
    assert venue["no_routing"] is True
    assert "analytical_optimal" in venue


def test_218_manual_order_journal(seed):
    entry = ime.add_manual_order_journal_218(
        asset="BTC", target_price=65000, state="Filled", filled_price=65100, seed=seed
    )
    assert entry["entry"]["actual_slippage_pct"] is not None
    journal = ime.list_manual_order_journal_218(seed=seed)
    assert journal["lifecycle_management_rejected"] is True


def test_218_journal_embed(seed):
    from bd_platform.pro_trader_layer import build_journal_tab_76

    tab = build_journal_tab_76(seed=seed)
    assert "manual_orders" in tab
    assert 218 in tab["merged_features"]


def test_219_nlp_sentiment(seed):
    nlp = ime.analyze_nlp_sentiment_219(seed=seed)
    assert nlp["rule_based_only"] is True
    assert "keyword_breakdown" in nlp
    assert -1 <= nlp["sentiment_score"] <= 1


def test_220_pattern_outcome(seed):
    pattern = ime.analyze_pattern_outcome_220(seed=seed)
    assert pattern["roi_probability_rejected"] is True
    assert pattern["no_return_prediction"] is True


def test_220_backtest_embed(seed):
    from bd_platform.pro_trader_layer import run_backtest_74

    backtest = run_backtest_74(seed=seed)
    assert "pattern_outcome" in backtest
    assert 220 in backtest["merged_features"]


def test_221_slippage_rejected(seed):
    assert ime.execution_quality_rejected_status_221(seed=seed)["execution_monitoring_rejected"] is True
    slip = ime.market_slippage_analysis_221(seed=seed)
    assert slip["market_analysis_not_personal_execution"] is True


def test_222_exchange_latency(seed):
    latency = ime.monitor_exchange_latency_222(seed=seed)
    assert latency["data_driven_ranking"] is True
    assert latency["fastest_venue"] == "binance"


def test_223_defi_fundamentals(seed):
    fundamentals = ime.analyze_defi_fundamentals_223(seed=seed)
    assert fundamentals["ps_ratio"] > 0
    assert fundamentals["not_licensed_valuation"] is True


def test_224_token_dcf(seed):
    dcf = ime.analyze_token_dcf_224(seed=seed)
    assert dcf["no_fair_value_guarantee"] is True
    assert dcf["sensitivity_pct"] == 30


def test_225_pwa_deferred(seed):
    pwa = ime.pwa_strategy_status_225(seed=seed)
    assert pwa["native_apps_wave"] == "3+"
    assert pwa["pwa_alternative"] is True


def test_226_launch_rejected(seed):
    assert ime.launch_arbitrage_rejected_status_226(seed=seed)["exploitation_word_rejected"] is True
    launch = ime.analyze_launch_event_226(seed=seed)
    assert launch["analysis_not_exploitation"] is True


def test_227_etf_rejected(seed):
    assert ime.etf_arbitrage_rejected_status_227(seed=seed)["etf_arbitrage_rejected"] is True
    etf = ime.analyze_etf_premium_227(seed=seed)
    assert etf["analysis_not_arbitrage"] is True


def test_intelligence_market_extensions_e2e(seed):
    assert ime.run_intelligence_market_extensions_e2e_217_227(seed=seed)["all_passed"] is True
