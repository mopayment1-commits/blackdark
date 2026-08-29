"""Tests — Risk & Infrastructure (#164–#176)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import risk_infrastructure_layer as ri


@pytest.fixture
def seed() -> dict:
    return json.loads(Path("data/legal_retail_commercial_seed.json").read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def reset():
    ri.reset_risk_infrastructure_state()
    yield
    ri.reset_risk_infrastructure_state()


def test_164_liquidity_impact_rejected(seed):
    liq = ri.liquidity_impact_warning_164(seed=seed)
    assert liq["panic_button_rejected"] is True
    assert liq["estimated_slippage_pct"] > 0


def test_165_hashrate_capitulation(seed):
    mining = ri.hashrate_capitulation_forecast_165(seed=seed)
    assert mining["formula_visible"] is True
    assert mining["historical_not_prediction"] is True


def test_166_brokerage_rejected(seed):
    assert ri.brokerage_rejected_status_166(seed=seed)["brokerage_rejected"] is True


def test_167_time_sync(seed):
    from bd_platform.infra_intelligence_layer import validate_oracle_freshness_101

    sync = ri.validate_time_sync_167(seed=seed)
    assert "sync_status" in sync
    fresh = validate_oracle_freshness_101(primary_timestamp_ms=1_000_000, secondary_timestamp_ms=1_000_200, seed=seed)
    assert "time_sync" in fresh


def test_168_cluster_index(seed):
    from bd_platform.onchain_platform_layer import cluster_sybil_identities_129

    cluster = cluster_sybil_identities_129(seed=seed)
    assert cluster.get("cluster_index_ref") == 168
    assert "potential_price_impact_pct" in cluster["clusters"][0]


def test_169_correlation_decay(seed):
    decay = ri.compute_correlation_decay_matrix_169(seed=seed)
    assert decay["formula_visible"] is True
    assert len(decay["matrix"]) >= 4


def test_169_risk_embed(seed):
    from bd_platform.whales_institutional_layer import build_advanced_risk_report_77

    risk = build_advanced_risk_report_77([{"symbol": "BTC", "value_usd": 100000, "btc_beta": 1.0}], seed=seed)
    assert "correlation_decay" in risk
    assert 169 in risk["merged_features"]


def test_170_oi_momentum(seed):
    oi = ri.compute_oi_momentum_delta_170(seed=seed)
    assert oi["flow_signal"] in {"inflow", "outflow", "neutral"}


def test_171_m2_macro(seed):
    from bd_platform.onchain_platform_layer import compute_macro_event_nexus_133

    macro = compute_macro_event_nexus_133(seed=seed)
    assert "m2_flow" in macro
    assert macro["m2_flow"]["source"] == "FRED"


def test_172_institutional_memory(seed):
    assert ri.institutional_memory_status_172(seed=seed)["activation_not_build"] is True


def test_173_institutional_rbac(seed):
    rbac = ri.institutional_rbac_status_173(seed=seed)
    assert rbac["duplicate_of"] == 88


def test_174_full_white_label(seed):
    wl = ri.full_white_label_status_174(seed=seed)
    assert wl["wave"] == 3


def test_175_risk_intelligence(seed):
    assert ri.risk_intelligence_status_175(seed=seed)["risk_insight_not_protection"] is True


def test_176_operational_resilience(seed):
    res = ri.operational_resilience_status_176(seed=seed)
    assert res["internal_only"] is True
    assert res["sprint"] == 0


def test_risk_infrastructure_e2e(seed):
    assert ri.run_risk_infrastructure_e2e_164_176(seed=seed)["all_passed"] is True
