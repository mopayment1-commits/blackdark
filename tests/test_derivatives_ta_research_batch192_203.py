"""Tests — Derivatives, TA & Research (#192–#203)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import derivatives_ta_research_layer as dtr


@pytest.fixture
def seed() -> dict:
    return json.loads(Path("data/legal_retail_commercial_seed.json").read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def reset():
    dtr.reset_derivatives_ta_research_state()
    yield
    dtr.reset_derivatives_ta_research_state()


def test_192_funding_rate(seed):
    funding = dtr.analyze_funding_rate_192(seed=seed)
    assert funding["carry_not_guarantee"] is True
    assert "binance" in funding["venues"]


def test_193_auto_arbitrage_rejected(seed):
    assert dtr.auto_arbitrage_rejected_status_193(seed=seed)["auto_arbitrage_rejected"] is True


def test_194_cvd(seed):
    cvd = dtr.compute_cvd_194(seed=seed)
    assert cvd["formula_visible"] is True
    assert "cvd_usd" in cvd


def test_195_strategy_simulator(seed):
    sim = dtr.strategy_simulator_195(strategy="grid", seed=seed)
    assert sim["account_linking_rejected"] is True
    dca = dtr.strategy_simulator_195(strategy="dca", seed=seed)
    assert dca["strategy"] == "dca"


def test_196_yahoo_finance(seed):
    yahoo = dtr.ingest_yahoo_finance_macro_196(seed=seed)
    assert yahoo["attribution"] == "Data: Yahoo Finance"
    assert "SPX" in yahoo["benchmarks"]


def test_197_alpha_vantage(seed):
    av = dtr.ingest_alpha_vantage_macro_197(seed=seed)
    assert av["free_tier_only"] is True


def test_196_macro_embed(seed):
    from bd_platform.onchain_platform_layer import compute_macro_event_nexus_133

    macro = compute_macro_event_nexus_133(seed=seed)
    assert "yahoo_finance" in macro
    assert "alpha_vantage" in macro


def test_198_binance_research(seed):
    research = dtr.ingest_binance_research_198(seed=seed)
    assert research["reports"][0]["attribution"] == "Source: Binance Research"


def test_199_messari_research(seed):
    assert dtr.ingest_messari_research_199(seed=seed)["free_tier_first"] is True


def test_200_coingecko_reports(seed):
    assert dtr.ingest_coingecko_reports_200(seed=seed)["attribution"] == "Source: CoinGecko"


def test_201_quantitative_analysis(seed):
    quant = dtr.quantitative_analysis_framework_201(seed=seed)
    assert quant["quantitative_trading_rejected"] is True
    assert quant["quantitative_analysis_only"] is True


def test_202_hidden_opportunities(seed):
    hidden = dtr.discover_hidden_opportunities_202(seed=seed)
    assert hidden["criteria_visible"] is True
    assert hidden["hidden_opportunity"] is True


def test_203_cryptocompare_oracle(seed):
    cc = dtr.ingest_cryptocompare_price_203(seed=seed)
    assert cc["role"] == "secondary_redundancy"
    consensus = dtr.validate_oracle_consensus_203(seed=seed)
    assert "cryptocompare" in consensus["sources"]


def test_derivatives_ta_research_e2e(seed):
    assert dtr.run_derivatives_ta_research_e2e_192_203(seed=seed)["all_passed"] is True
