"""Tests — Batch 36: #990 Query Governance, #992 Real Volume, #993-995 Reference Price."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import data_engine_query_performance_governance as qgov
from bd_platform import oracle_vwap_layer as oracle


@pytest.fixture
def qgov_seed() -> dict:
    return json.loads(Path("data/data_engine_query_performance_governance_seed.json").read_text(encoding="utf-8"))


@pytest.fixture
def oracle_seed() -> dict:
    return json.loads(Path("data/oracle_vwap_seed.json").read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def reset_state():
    qgov.reset_query_governance_state()
    yield
    qgov.reset_query_governance_state()


# --- #990 Query Performance Governance ---


def test_990_status(qgov_seed):
    status = qgov.query_performance_governance_status_990(seed=qgov_seed)
    assert status["standalone_rejected"] is True
    assert status["no_public_dashboard"] is True
    assert status["query_timeout_sec"] == 30
    assert status["audit_retention_days"] == 90
    assert status["sql_workspace_ref"] == 978


def test_990_timeout_enforced(qgov_seed):
    ok = qgov.enforce_query_timeout_990(15.0, seed=qgov_seed)
    bad = qgov.enforce_query_timeout_990(35.0, seed=qgov_seed)
    assert ok["ok"] is True
    assert bad["ok"] is False
    assert bad["kill_automatic"] is True


def test_990_quota_backend(qgov_seed):
    quota = qgov.enforce_tier_quota_990("user_pro", "pro", 1.0, seed=qgov_seed)
    assert quota["backend_enforced"] is True
    assert quota["no_client_side_quota"] is True


def test_990_cache_and_audit(qgov_seed):
    cache = qgov.cache_query_result_990("hash1", {"rows": 5}, freshness="fresh", seed=qgov_seed)
    hit = qgov.get_cached_query_990("hash1")
    audit = qgov.log_query_audit_990(user_id="u1", sql="SELECT 1", cost_usd=0.01, rows=5, seed=qgov_seed)
    assert cache["cached"] is True
    assert hit["cache_hit"] is True
    assert audit["audit_logged"] is True
    assert audit["retention_days"] == 90


def test_990_slow_query_ops_only(qgov_seed):
    analysis = qgov.run_slow_query_analysis_990(seed=qgov_seed)
    assert analysis["ops_internal_only"] is True
    assert analysis["no_public_dashboard"] is True
    assert analysis["flagged_count"] >= 1


def test_990_e2e(qgov_seed):
    e2e = qgov.run_query_governance_e2e_990(seed=qgov_seed)
    assert e2e["all_passed"] is True


# --- #992 Real Volume ---


def test_992_real_volume(oracle_seed):
    vol = oracle.build_real_volume_992("BTC", seed=oracle_seed)
    assert vol["ok"] is True
    assert vol["real_lte_reported"] is True
    assert vol["venue_inclusion_auditable"] is True
    assert vol["methodology_version"] is not None
    assert len(vol["excluded_venues"]) >= 1


def test_992_market_radar_widget(oracle_seed):
    widget = oracle.build_market_radar_real_volume_widget_992("BTC", seed=oracle_seed)
    assert widget["integration"] == "market_radar_asset_card"
    assert widget["widget"] == "real_volume"


def test_992_daily_reconciliation(oracle_seed):
    recon = oracle.run_daily_volume_reconciliation_992(seed=oracle_seed)
    assert recon["ok"] is True
    assert recon["daily_reconciliation"] is True


def test_992_backtest_90d(oracle_seed):
    bt = oracle.run_real_volume_backtest_992(seed=oracle_seed)
    assert bt["backtest_days"] == 90
    assert bt["ok"] is True


# --- #993 + #994 + #995 Unified Reference Price ---


def test_993_unified_reference_price(oracle_seed):
    ref = oracle.build_oracle_reference_price("BTC", seed=oracle_seed)
    assert ref["ok"] is True
    assert ref["unified_endpoint"] is True
    assert 993 in ref["feature_refs"]
    assert 994 in ref["feature_refs"]
    assert 995 in ref["feature_refs"]
    assert ref["reference_price"] == ref["reference_rate"]


def test_993_constituent_audit(oracle_seed):
    ref = oracle.build_oracle_reference_price("BTC", seed=oracle_seed)
    assert ref["constituents_auditable"] is True
    assert ref["constituent_source_audit"] is True


def test_994_audit_trail(oracle_seed):
    ref = oracle.build_oracle_reference_price("BTC", seed=oracle_seed)
    assert ref["audit_trail"]["each_price_has_constituents"] is True
    assert ref["audit_trail"]["recalculations_logged"] is True


def test_995_methodology_governance(oracle_seed):
    ref = oracle.build_oracle_reference_price("BTC", seed=oracle_seed)
    assert ref["governance"]["methodology_governed"] is True
    assert ref["governance"]["approval_required"] is True


def test_oracle_reconciliation_includes_new_features(oracle_seed):
    recon = oracle.run_reconciliation_tests(seed=oracle_seed)
    assert recon["ok"] is True
    check_ids = {c["id"] for c in recon["checks"]}
    assert "unified_reference_993_995" in check_ids
    assert "real_volume_992" in check_ids
    assert "daily_volume_recon" in check_ids


# --- Regression batch 35 ---


def test_batch35_kpi_e2e_regression():
    from bd_platform.protocol_kpi_intelligence import run_protocol_kpi_e2e

    e2e = run_protocol_kpi_e2e()
    assert e2e["all_passed"] is True
