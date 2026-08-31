"""Tests — Advanced TA & Risk (#117–#128)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import advanced_ta_risk_layer as ta


@pytest.fixture
def seed() -> dict:
    return json.loads(Path("data/legal_retail_commercial_seed.json").read_text(encoding="utf-8"))


def test_117_liquidity_vacuum(seed):
    vac = ta.compute_liquidity_vacuum_117(seed=seed)
    assert vac["vacuum_pct"] > 0
    assert vac["technical_insight_not_recommendation"] is True


def test_118_risk_distribution(seed):
    from bd_platform.institutional_b2b_layer import build_exchange_health_with_counterparty_92

    ex = build_exchange_health_with_counterparty_92(seed=seed)
    assert "risk_distribution" in ex
    assert 118 in ex["merged_features"]


def test_119_gas_rejected(seed):
    gas = ta.gas_spike_alert_119(seed=seed)
    assert gas["execution_rejected"] is True
    assert gas["no_hold_no_execution"] is True


def test_120_leverage_risk(seed):
    from bd_platform.whales_institutional_layer import build_advanced_risk_report_77

    risk = build_advanced_risk_report_77(
        [{"symbol": "BTC", "value_usd": 100000, "btc_beta": 1.0}], seed=seed
    )
    assert "leverage_risk_analysis" in risk
    assert risk["leverage_risk_analysis"]["optimization_rejected"] is True


def test_121_pnl_attribution(seed):
    from bd_platform.pro_trader_layer import build_journal_tab_76

    journal = build_journal_tab_76(seed=seed)
    assert "pnl_attribution" in journal
    assert "drift_residual_usd" in journal["pnl_attribution"]["attribution"]


def test_122_structural_break(seed):
    brk = ta.compute_structural_break_122(seed=seed)
    assert brk["statistical_not_ai"] is True
    assert brk["ai_rejected_rule_based_only"] is True


def test_123_volume_profile(seed):
    poc = ta.compute_volume_profile_poc_123(seed=seed)
    assert poc["poc_price"] > 0
    assert len(poc["value_area_prices"]) >= 1


def test_124_fvg_detector(seed):
    fvg = ta.detect_fair_value_gaps_124(seed=seed)
    assert isinstance(fvg["gaps"], list)


def test_125_custody_deferred(seed):
    assert ta.custody_tracking_status_125(seed=seed)["status"] == "deferred"


def test_126_dex_rejected(seed):
    dex = ta.dex_front_running_risk_126(seed=seed)
    assert dex["no_shield_no_execution"] is True


def test_127_inefficiency_rejected(seed):
    ob = ta.orderbook_inefficiency_insight_127(seed=seed)
    assert ob["exploiter_naming_rejected"] is True


def test_128_jargon(seed):
    from bd_platform.retail_intelligence_layer import glossary_manifest_64

    j = ta.jargon_explanation_128("Impermanent Loss", locale="en")
    assert j["merged_into"] == "simple_language_64"
    gloss = glossary_manifest_64()
    terms = {t["term"] for t in gloss["terms"]}
    assert "Impermanent Loss" in terms


def test_advanced_ta_risk_e2e(seed):
    assert ta.run_advanced_ta_risk_e2e_117_128(seed=seed)["all_passed"] is True
