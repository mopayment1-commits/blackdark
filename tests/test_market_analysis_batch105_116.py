"""Tests — Market Analysis (#105–#116)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import market_analysis_layer as ma


@pytest.fixture
def seed() -> dict:
    return json.loads(Path("data/legal_retail_commercial_seed.json").read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def reset(seed):
    ma.reset_market_analysis_state()
    yield
    ma.reset_market_analysis_state()


def test_105_tail_risk(seed):
    tail = ma.compute_tail_risk_alpha_105(seed=seed)
    assert "tail_alpha" in tail
    assert tail["historical_analysis_only"] is True


def test_105_backtest_embed(seed):
    from bd_platform.pro_trader_layer import run_backtest_74

    bt = run_backtest_74(seed=seed)
    assert "tail_risk_alpha" in bt


def test_106_contagion(seed):
    c = ma.compute_contagion_vector_106(seed=seed)
    assert c["vector_score"] > 0
    assert c["no_auto_action"] is True


def test_107_whale_retail(seed):
    from bd_platform.pro_trader_layer import build_whale_narrative_71

    whale = build_whale_narrative_71(seed=seed)
    assert "whale_retail_ratio" in whale


def test_108_orderbook_skew(seed):
    skew = ma.compute_orderbook_skew_108(seed=seed)
    assert -1 <= skew["skew"] <= 1


def test_109_liquidation_anchors(seed):
    from bd_platform.whales_institutional_layer import evaluate_liquidation_alert_82

    liq = evaluate_liquidation_alert_82(price=62100, seed=seed)
    assert "spike_anchors" in liq
    assert 109 in liq["merged_features"]


def test_110_wallet_acceleration(seed):
    accel = ma.compute_wallet_age_acceleration_110(
        wallet_age_days=800, current_tx_per_month=12, historical_tx_per_month=2, seed=seed
    )
    assert accel["awakening_signal"] is True


def test_111_spx_correlation(seed):
    from bd_platform.pro_trader_layer import build_multi_dim_analysis_73

    multi = build_multi_dim_analysis_73(seed=seed)
    assert "spx_correlation" in multi["dimensions"]["macro"]


def test_112_gcli(seed):
    gcli = ma.compute_gcli_112(seed=seed)
    assert 0 <= gcli["gcli_score"] <= 100


def test_113_imbalance_delta(seed):
    imb = ma.compute_imbalance_delta_113(seed=seed)
    assert "delta" in imb


def test_114_whale_ls_ratio(seed):
    ls = ma.compute_whale_ls_ratio_114(seed=seed)
    assert ls["whale_filtered_ratio"] > 0


def test_115_volume_velocity(seed):
    vel = ma.compute_volume_velocity_115(seed=seed)
    assert vel["velocity_pct"] > 0


def test_116_delta_hedging(seed):
    delta = ma.compute_delta_hedging_flow_116(seed=seed)
    assert delta["hedge_detected"] is True


def test_103_105_advanced_risk(seed):
    from bd_platform.whales_institutional_layer import build_advanced_risk_report_77

    risk = build_advanced_risk_report_77(
        [{"symbol": "BTC", "value_usd": 100000, "btc_beta": 1.0}], seed=seed
    )
    assert "tail_risk_alpha" in risk
    assert "drawdown_lifecycle" in risk


def test_market_analysis_e2e(seed):
    assert ma.run_market_analysis_e2e_105_116(seed=seed)["all_passed"] is True
