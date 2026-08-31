"""Tests — On-Chain, DeFi & Arbitrage Sources (#204–#216)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import onchain_defi_sources_layer as ods


@pytest.fixture
def seed() -> dict:
    return json.loads(Path("data/legal_retail_commercial_seed.json").read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def reset():
    ods.reset_onchain_defi_sources_state()
    yield
    ods.reset_onchain_defi_sources_state()


def test_204_bscscan(seed):
    bsc = ods.ingest_bscscan_204(seed=seed)
    assert bsc["token_standard"] == "BEP-20"
    assert bsc["attribution"] == "Data: BscScan"
    assert bsc["cross_validation_primary_rpc"] is True


def test_205_glassnode(seed):
    glass = ods.ingest_glassnode_metrics_205(seed=seed)
    assert glass["free_tier_only"] is True
    assert "mvrv" in glass["metrics"]
    assert glass["attribution"] == "Data: Glassnode"


def test_206_uniswap(seed):
    uni = ods.ingest_uniswap_subgraph_206(seed=seed)
    assert uni["attribution"] == "Data: Uniswap Subgraph (The Graph)"
    assert uni["liquidity_usd"] > 0


def test_207_aave(seed):
    aave = ods.ingest_aave_data_207(seed=seed)
    assert aave["protocol_version"] == "v3"
    assert aave["attribution"] == "Data: Aave"


def test_208_reddit_dedup(seed):
    reddit = ods.ingest_reddit_sentiment_208(seed=seed)
    assert reddit["deduplicated"] is True
    assert reddit["post_count"] == 2
    assert reddit["attribution"] == "Source: Reddit r/CryptoCurrency"


def test_209_blockchain_wallets_merged(seed):
    status = ods.blockchain_wallets_status_209(seed=seed)
    assert status["duplicate_of"] == 148
    assert status["activation_not_build"] is True


def test_210_predictive_arbitrage(seed):
    pred = ods.analyze_predictive_arbitrage_210(seed=seed)
    assert pred["no_auto_execution"] is True
    assert pred["probability_not_prediction"] is True


def test_210_arbitrage_embed(seed):
    from bd_platform.intelligence_analysis_layer import analyze_arbitrage_opportunity_153

    arb = analyze_arbitrage_opportunity_153(seed=seed)
    assert "predictive_layer" in arb
    assert "triangular_analysis" in arb
    assert 210 in arb["merged_features"]
    assert 214 in arb["merged_features"]


def test_211_cross_margin_alert(seed):
    alert = ods.cross_margin_risk_alert_211(seed=seed)
    assert alert["safeguard_rejected"] is True
    assert alert["no_block_no_execution"] is True


def test_212_hedge_rejected(seed):
    hedge = ods.hedge_effectiveness_analysis_212(seed=seed)
    assert hedge["rehedging_rejected"] is True
    assert hedge["simulation_not_execution"] is True


def test_213_capital_allocation_rejected(seed):
    cap = ods.capital_allocation_insight_213(seed=seed)
    assert cap["auto_balancing_rejected"] is True
    assert cap["educational_not_automated"] is True


def test_214_triangular_analysis(seed):
    tri = ods.analyze_triangular_arbitrage_214(seed=seed)
    assert tri["in_flight_modification_rejected"] is True
    assert tri["optimal_path_analytical"] == "A→B→C→A"


def test_215_flash_loan_rejected(seed):
    flash = ods.flash_loan_gas_rejected_status_215(seed=seed)
    assert flash["flash_loans_rejected"] is True
    assert flash["alternative"] == "gas_volatility_profile_159"


def test_216_whale_contrarian(seed):
    whale = ods.whale_contrarian_insight_216(seed=seed)
    assert whale["counter_trading_rejected"] is True
    assert whale["no_position_no_execution"] is True


def test_216_whale_narrative_embed(seed):
    from bd_platform.pro_trader_layer import build_whale_narrative_71

    narrative = build_whale_narrative_71(seed=seed)
    assert "contrarian_insight" in narrative
    assert 216 in narrative["merged_features"]


def test_onchain_defi_sources_e2e(seed):
    assert ods.run_onchain_defi_sources_e2e_204_216(seed=seed)["all_passed"] is True
