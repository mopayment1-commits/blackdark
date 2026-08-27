"""Tests — #824 Data Integrity Monitor + #826 API Token Rotation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import api_gateway_token_rotation as tr
from bd_platform import data_engine_quality_monitor as qm
from bd_platform import infrastructure_observability_stack as ios


@pytest.fixture
def qm_seed() -> dict:
    return json.loads(Path("data/data_engine_quality_monitor_seed.json").read_text(encoding="utf-8"))


@pytest.fixture
def gw_seed() -> dict:
    return json.loads(Path("data/api_gateway_seed.json").read_text(encoding="utf-8"))


@pytest.fixture
def ios_seed() -> dict:
    return json.loads(Path("data/infrastructure_observability_stack_seed.json").read_text(encoding="utf-8"))


# --- #824 ---


def test_824_status(qm_seed):
    status = qm.quality_monitor_status_824(seed=qm_seed)
    assert status["standalone_rejected"] is True
    assert status["component"] == "quality_monitor"
    assert status["daily_checks"] == ["gap_detection", "outlier_detection", "reconciliation"]
    assert status["accuracy_internal_only"] is True
    assert status["no_user_surface"] is True


def test_824_three_daily_checks(qm_seed):
    checks = qm.run_all_daily_quality_checks_824(seed=qm_seed)
    assert checks["checks_run"] == 3
    assert checks["ok"] is True
    assert checks["within_accuracy_target"] is True


def test_824_gap_detection(qm_seed):
    result = qm.run_daily_quality_check_824("gap_detection", seed=qm_seed)
    assert result["ok"] is True
    assert result["within_query_target"] is True


def test_824_retention_policy(qm_seed):
    panel = qm.build_quality_monitor_panel_824(seed=qm_seed)
    retention = panel["retention_policy"]
    assert retention["configured_years"] >= 2
    assert retention["infrastructure_concern"] is True


def test_824_internal_targets_not_user_promise(qm_seed):
    panel = qm.build_quality_monitor_panel_824(seed=qm_seed)
    targets = panel["internal_targets"]
    assert targets["accuracy_internal_only"] is True
    assert targets["query_latency_internal_only"] is True
    assert targets["within_query_target"] is True


def test_824_feeds_infra_observability(qm_seed):
    feed = qm.build_infra_observability_quality_feed_824(seed=qm_seed)
    assert feed["feeds"] == "#789 Infrastructure Observability"
    assert feed["quality_metrics"]["accuracy_pct"] >= 99.99


def test_824_infra_stack_integration(ios_seed):
    stack = ios.build_sre_observability_with_quality_monitor_789(seed=ios_seed)
    assert "quality_monitor_feed_824" in stack
    assert stack.get("quality_monitor_feed_824", {}).get("feeds") == "#789 Infrastructure Observability"


def test_824_e2e(qm_seed):
    e2e = qm.run_quality_monitor_e2e_824(seed=qm_seed)
    assert e2e["all_passed"] is True


# --- #826 ---


def test_826_status(gw_seed):
    status = tr.token_rotation_status_826(seed=gw_seed)
    assert status["standalone_rejected"] is True
    assert status["no_user_dashboard"] is True
    assert status["rotation_interval_days"] == 90
    assert status["fallback_grace_hours"] == 24
    assert status["automated_rotation"] is True


def test_826_no_permanent_keys(gw_seed):
    panel = tr.build_token_rotation_panel_826(seed=gw_seed)
    assert panel["no_permanent_api_keys"] is True
    assert panel["no_user_dashboard"] is True


def test_826_rotation_due(gw_seed):
    due = tr.list_rotation_due_keys_826(seed=gw_seed)
    assert due["ok"] is True
    assert due["due_count"] >= 1
    assert "overdue_demo_key" in [k["key_id"] for k in due["due_keys"]]


def test_826_automated_rotation_dry_run(gw_seed):
    result = tr.rotate_api_key_826("gateway_service_key", dry_run=True, seed=gw_seed)
    assert result["ok"] is True
    assert result["rotation_event"]["automated"] is True
    assert result["rotation_event"]["manual_rotation_rejected"] is True
    assert result["no_downtime"] is True


def test_826_fallback_grace(gw_seed):
    state = tr.evaluate_key_rotation_state_826("gateway_service_key", seed=gw_seed)
    assert state["ok"] is True
    assert state["no_permanent_keys"] is True


def test_826_api_gateway_ref(gw_seed):
    status = tr.token_rotation_status_826(seed=gw_seed)
    assert status["api_gateway_ref"] == 876
    assert status["api_throttling_ref"] == 833


def test_826_e2e(gw_seed):
    e2e = tr.run_token_rotation_e2e_826(seed=gw_seed)
    assert e2e["all_passed"] is True


def test_824_826_module_functions():
    """Direct module tests — admin routes require auth."""
    assert qm.quality_monitor_status_824()["ok"] is True
    assert tr.token_rotation_status_826()["ok"] is True
