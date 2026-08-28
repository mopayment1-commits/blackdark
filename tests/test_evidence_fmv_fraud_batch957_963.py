"""Tests — Batch 32: #957 Evidence Provenance, #959 FMV, #960 Fraud Screening, #962 Futures Volume, #963 Governance."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import data_engine_provenance_layer as prov
from bd_platform import market_radar_futures_volume as futures
from bd_platform import market_radar_governance as gov
from bd_platform import onchain_intelligence_extension as onchain
from bd_platform import oracle_vwap_layer as oracle


@pytest.fixture
def prov_seed() -> dict:
    return json.loads(Path("data/data_engine_provenance_layer_seed.json").read_text(encoding="utf-8"))


@pytest.fixture
def oracle_seed() -> dict:
    return json.loads(Path("data/oracle_vwap_seed.json").read_text(encoding="utf-8"))


@pytest.fixture
def onchain_seed() -> dict:
    return json.loads(Path("data/onchain_intelligence_extension_seed.json").read_text(encoding="utf-8"))


@pytest.fixture
def futures_seed() -> dict:
    return json.loads(Path("data/market_radar_futures_volume_seed.json").read_text(encoding="utf-8"))


@pytest.fixture
def gov_seed() -> dict:
    return json.loads(Path("data/market_radar_governance_seed.json").read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def reset_state():
    gov.reset_governance_state()
    yield
    gov.reset_governance_state()


# --- #957 Evidence & Provenance ---


def test_957_merged_into_945(prov_seed):
    status = prov.provenance_layer_status_945(seed=prov_seed)
    assert 957 in status["merged_refs"].values()
    assert status["evidence_linking"] is True
    assert status["every_critical_insight_traceable"] is True


def test_957_evidence_linking(prov_seed):
    linked = prov.link_insight_evidence_957("aave_tvl_growth_signal", seed=prov_seed)
    assert linked["ok"] is True
    assert linked["evidence_count"] >= 2
    assert linked["assumptions_documented"] is True
    assert linked["every_source_linked"] is True


def test_957_insight_badge(prov_seed):
    badge = prov.build_insight_evidence_badge_957("aave_tvl_growth_signal", seed=prov_seed)
    assert badge["badge"]["assumptions_visible"] is True
    assert badge["badge"]["freshness"] is not None
    assert len(badge["badge"]["source_urls"]) >= 2


def test_957_missing_source_fail_closed(prov_seed):
    delivery = prov.evaluate_critical_insight_delivery_957("unverified_rumor_signal", seed=prov_seed)
    assert delivery["missing_source_fails_closed"] is True
    assert delivery["delivery_status"] in ("hidden", "degraded")
    assert delivery["no_silent_serving"] is True


def test_957_audit_view(prov_seed):
    audit = prov.build_insight_audit_view_957("aave_tvl_growth_signal", seed=prov_seed)
    assert audit["end_to_end_traceable"] is True
    assert audit["audit_view_ops_only"] is True


# --- #959 FMV Pricing ---


def test_959_fmv_price(oracle_seed):
    fmv = oracle.build_fmv_reference_price_959("BTC", seed=oracle_seed)
    assert fmv["ok"] is True
    assert fmv["fmv_price"] > 0
    assert fmv["constituents_auditable"] is True
    assert fmv["methodology_version"] == "1.0.0"
    assert fmv["no_silent_recalculation"] is True


def test_959_reference_same_calc(oracle_seed):
    fmv = oracle.build_fmv_reference_price_959("BTC", label="fmv", seed=oracle_seed)
    ref = oracle.build_fmv_reference_price_959("BTC", label="reference", seed=oracle_seed)
    assert fmv["fmv_price"] == ref["reference_price"]
    assert ref["price_label"] == "reference_benchmark"


def test_959_outlier_rejection(oracle_seed):
    constituents = (oracle_seed["assets"]["BTC"]["constituents"]).copy()
    constituents.append({
        "venue": "outlier_exchange",
        "price": 90000.0,
        "volume_24h_usd": 1000000,
        "vwap_1h": 90000.0,
        "source": "test_api",
        "timestamp": "2026-08-26T19:00:00Z",
    })
    result = oracle.compute_outlier_resistant_median_959(constituents)
    assert result["ok"] is True
    assert result["outlier_count"] >= 1


def test_959_oracle_status():
    status = oracle.oracle_vwap_status()
    assert status["fmv_pricing_ref"] == 959


# --- #960 Fraud Screening ---


def test_960_suspicious_not_fraud(onchain_seed):
    result = onchain.screen_fraud_activity_960("0x742d35cc6634c0532925a3b844bc9e7595f0bbe0", seed=onchain_seed)
    assert result["ok"] is True
    assert result["not_fraud_detected"] is True
    assert result["fraud_detected"] is False
    assert result["no_legal_conclusion"] is True


def test_960_risk_score_scale(onchain_seed):
    result = onchain.screen_fraud_activity_960("0x742d35cc6634c0532925a3b844bc9e7595f0bbe0", seed=onchain_seed)
    assert 1 <= result["risk_score"] <= 10
    assert result["indicator_count"] >= 3


def test_960_explainable_indicators(onchain_seed):
    result = onchain.screen_fraud_activity_960("0x742d35cc6634c0532925a3b844bc9e7595f0bbe0", seed=onchain_seed)
    assert all(i.get("explainable") for i in result["indicators"])
    assert result["audit"]["audit_logged"] is True


# --- #962 Futures Volume ---


def test_962_dashboard(futures_seed):
    dash = futures.build_futures_volume_dashboard_962("BTC", seed=futures_seed)
    assert dash["ok"] is True
    assert dash["metrics"]["volume_usd"] > 0
    assert dash["metrics"]["open_interest_usd"] > 0
    assert dash["usd_conversion_audited"] is True
    assert dash["exchange_timestamp_used"] is True


def test_962_per_exchange(futures_seed):
    dash = futures.build_futures_volume_dashboard_962("BTC", seed=futures_seed)
    assert dash["exchange_count"] >= 2
    for ex in dash["per_exchange"]:
        assert ex["exchange_timestamp"] is not None
        assert ex["usd_conversion_method"] == "notional_x_reference_price_959"


def test_962_e2e(futures_seed):
    e2e = futures.run_futures_volume_e2e_962(seed=futures_seed)
    assert e2e["all_passed"] is True


# --- #963 Governance ---


def test_963_feed(gov_seed):
    feed = gov.build_governance_feed_963(seed=gov_seed)
    assert feed["feed_count"] >= 2
    assert feed["no_inferred_outcome"] is True
    assert all(p["official_source_preferred"] for p in feed["proposals"])


def test_963_proposal_details(gov_seed):
    details = gov.get_proposal_details_963("aave_fee_update_001", seed=gov_seed)
    assert details["ok"] is True
    assert details["status_transitions_audited"] is True
    assert details["parameter_impact"] is not None
    assert details["facts_vs_hypotheses"]["hypothesis_separated"] is True


def test_963_status_transition_audit(gov_seed):
    trans = gov.log_status_transition_963("aave_fee_update_001", from_status="active", to_status="passed", seed=gov_seed)
    assert trans["status_transitions_audited"] is True
    assert trans["ok"] is True


def test_963_e2e(gov_seed):
    e2e = gov.run_governance_e2e_963(seed=gov_seed)
    assert e2e["all_passed"] is True


# --- Regression ---


def test_945_e2e_includes_957(prov_seed):
    e2e = prov.run_provenance_layer_e2e(seed=prov_seed)
    assert e2e["all_passed"] is True
    assert 957 in e2e["feature_refs"]


def test_onchain_e2e_includes_960(onchain_seed):
    e2e = onchain.run_onchain_extension_e2e(seed=onchain_seed)
    assert e2e["all_passed"] is True
    assert 960 in e2e["feature_refs"]
