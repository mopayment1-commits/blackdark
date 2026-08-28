"""Tests — Batch 30: #945 Master Provenance, #946/#947/#948 merged, #949 Retention/Privacy."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import data_engine_provenance_layer as prov
from bd_platform import infrastructure_retention_privacy_governance as retention


@pytest.fixture
def prov_seed() -> dict:
    return json.loads(Path("data/data_engine_provenance_layer_seed.json").read_text(encoding="utf-8"))


@pytest.fixture
def retention_seed() -> dict:
    return json.loads(Path("data/infrastructure_retention_privacy_seed.json").read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def reset_state():
    retention.reset_retention_privacy_state()
    yield
    retention.reset_retention_privacy_state()


# --- #945 Master ---


def test_945_status_cross_cutting(prov_seed):
    status = prov.provenance_layer_status_945(seed=prov_seed)
    assert status["standalone_rejected"] is True
    assert status["cross_cutting"] is True
    assert status["fail_closed_policy"] == "hidden_or_degraded"
    assert 946 in status["merged_refs"].values()


def test_945_full_lineage_graph(prov_seed):
    lineage = prov.get_lineage_audit_1003("aave_tvl", seed=prov_seed)
    assert lineage["lineage_graph_complete"] is True
    assert lineage["raw_to_user_traceable"] is True


def test_945_full_badge(prov_seed):
    badge = prov.build_full_metric_badge_945("btc_price", seed=prov_seed)
    assert badge["badge"]["freshness"] == "fresh"
    assert badge["badge"]["confidence"] == "high"
    assert badge["badge"]["methodology_version"] is not None


# --- #946 Freshness/Confidence ---


def test_946_freshness_fresh(prov_seed):
    fresh = prov.compute_freshness_badge_946("2026-08-28T01:55:00+00:00", seed=prov_seed)
    assert fresh["freshness"] == "fresh"


def test_946_freshness_frozen(prov_seed):
    frozen = prov.compute_freshness_badge_946("2026-08-25T00:00:00+00:00", seed=prov_seed)
    assert frozen["freshness"] == "frozen"


def test_946_confidence_high(prov_seed):
    conf = prov.compute_confidence_score_946(source_count=3, qa_passed=True, seed=prov_seed)
    assert conf["confidence"] == "high"


def test_946_confidence_low(prov_seed):
    conf = prov.compute_confidence_score_946(source_count=1, qa_passed=False, seed=prov_seed)
    assert conf["confidence"] == "low"


# --- #947 Fail-Closed ---


def test_947_delivery_ok(prov_seed):
    delivery = prov.evaluate_metric_delivery_947("btc_price", seed=prov_seed)
    assert delivery["delivery_status"] == "ok"
    assert delivery["visible"] is True


def test_947_fail_closed(prov_seed):
    delivery = prov.evaluate_metric_delivery_947("sol_funding_rate", seed=prov_seed)
    assert delivery["delivery_status"] in ("degraded", "hidden")
    assert delivery["no_silent_serving"] is True


def test_947_critical_insight_traceable(prov_seed):
    audit = prov.build_audit_view_943("aave_tvl", seed=prov_seed)
    assert audit["end_to_end_traceable"] is True
    assert audit["audit_view_ops_only"] is True


# --- #948 Methodologies ---


def test_948_methodology_version(prov_seed):
    meth = prov.get_methodology_version_948("aave_tvl", seed=prov_seed)
    assert meth["versioned"] is True
    assert meth["version"] == "2.1.0"


def test_948_reconciliation(prov_seed):
    recon = prov.run_qa_reconciliation_948(seed=prov_seed)
    assert recon["total"] >= 2
    assert any(not t["passed"] for t in recon["reconciliation_tests"])


# --- #945 E2E ---


def test_945_e2e(prov_seed):
    e2e = prov.run_provenance_layer_e2e(seed=prov_seed)
    assert e2e["all_passed"] is True
    assert 946 in e2e["feature_refs"]
    assert 947 in e2e["feature_refs"]
    assert 948 in e2e["feature_refs"]


# --- #949 Retention/Privacy ---


def test_949_status(retention_seed):
    status = retention.retention_privacy_status_949(seed=retention_seed)
    assert status["standalone_rejected"] is True
    assert status["no_performance_sla"] is True
    assert status["encryption_at_rest"] is True


def test_949_retention_policies(retention_seed):
    raw = retention.get_retention_policy_949("raw_data", seed=retention_seed)
    assert raw["policy"]["retention_days"] == 90
    agg = retention.get_retention_policy_949("aggregated_data", seed=retention_seed)
    assert agg["policy"]["retention_years"] == 2
    archive = retention.get_retention_policy_949("archive_data", seed=retention_seed)
    assert archive["policy"]["retention_years"] == 5


def test_949_right_to_erasure(retention_seed):
    deletion = retention.request_data_deletion_949("user_test", seed=retention_seed)
    assert deletion["deletion_logged"] is True


def test_949_access_audit(retention_seed):
    retention.log_data_access_949("ops", "user_data", seed=retention_seed)
    trail = retention.get_access_audit_trail_949(seed=retention_seed)
    assert trail["access_count"] >= 1


def test_949_e2e(retention_seed):
    e2e = retention.run_retention_privacy_e2e_949(seed=retention_seed)
    assert e2e["all_passed"] is True


# --- Regression batch 29 provenance ---


def test_943_944_still_work(prov_seed):
    norm = prov.normalize_dataset_944("defi_protocol_metrics", seed=prov_seed)
    assert norm["normalization_applied"] is True
    audit = prov.build_audit_view_943("btc_price", seed=prov_seed)
    assert audit["ok"] is True
