"""Tests — On-Chain Platform (#129–#139)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import onchain_platform_layer as oc


@pytest.fixture
def seed() -> dict:
    return json.loads(Path("data/legal_retail_commercial_seed.json").read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def reset(seed):
    oc.reset_onchain_platform_state()
    yield
    oc.reset_onchain_platform_state()


def test_129_sybil_clustering(seed):
    from bd_platform.infra_intelligence_layer import filter_sybil_clusters_99

    result = filter_sybil_clusters_99([
        {"wallet_id": "w1", "timestamp": "2026-01-01T12:00:00", "amount": 100, "funding_source": "x"},
        {"wallet_id": "w2", "timestamp": "2026-01-01T12:00:00", "amount": 100, "funding_source": "x"},
        {"wallet_id": "w3", "timestamp": "2026-01-01T12:00:00", "amount": 100, "funding_source": "x"},
    ], seed=seed)
    assert "identity_linker" in result
    assert result["identity_linker"]["cluster_count"] >= 1


def test_130_tx_risk_rejected(seed):
    tx = oc.transaction_risk_insight_130(seed=seed)
    assert tx["execution_rejected"] is True


def test_131_dust_rejected(seed):
    dust = oc.analyze_dust_assets_131(seed=seed)
    assert dust["no_sweeper_no_automation"] is True


def test_132_flash_loan_scan(seed):
    scan = oc.scan_flash_loan_vulnerabilities_132(protocol="custom_defi", seed=seed)
    assert scan["self_patching_rejected"] is True
    assert scan["alert_triggered"] is True


def test_133_macro_nexus(seed):
    from bd_platform.pro_trader_layer import build_multi_dim_analysis_73

    multi = build_multi_dim_analysis_73(seed=seed)
    assert "event_nexus" in multi["dimensions"]["macro"]


def test_134_delta_convergence(seed):
    delta = oc.compute_delta_convergence_134(seed=seed)
    assert delta["convergence_pct"] > 0
    assert delta["no_auto_action"] is True


def test_135_liquidity_vortex(seed):
    vortex = oc.locate_liquidity_vortex_135(seed=seed)
    assert vortex["vortex_score"] > 0


def test_136_support_chat(seed):
    chat = oc.support_chat_response_136(message="should I buy BTC?", seed=seed)
    assert chat["broker_advisor_rejected"] is True
    assert chat["escalate_to_human"] is True


def test_137_b2b_not_technical(seed):
    assert oc.b2b_relationships_status_137(seed=seed)["not_a_technical_feature"] is True


def test_138_institution_activation(seed):
    assert oc.institution_features_status_138(seed=seed)["activation_not_build"] is True


def test_139_stress_alert_rejected(seed):
    stress = oc.portfolio_stress_alert_139(seed=seed)
    assert stress["panic_button_rejected"] is True
    assert stress["alert_triggered"] is True


def test_onchain_platform_e2e(seed):
    assert oc.run_onchain_platform_e2e_129_139(seed=seed)["all_passed"] is True
