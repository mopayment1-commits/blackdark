"""Tests — User Activity Audit Trail (cross-cutting)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import user_activity_audit_trail as uat


@pytest.fixture
def uat_seed() -> dict:
    return json.loads(Path("data/user_activity_audit_seed.json").read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def _reset():
    uat.reset_user_activity_state()
    audit = Path("data/user_activity_audit.jsonl")
    if audit.is_file():
        audit.unlink()
    imm = Path("data/immutable_recommendation_audit")
    if imm.is_dir():
        for f in imm.glob("*.json"):
            f.unlink()
    yield
    uat.reset_user_activity_state()


def test_status_no_standalone(uat_seed):
    status = uat.user_activity_status(seed=uat_seed)
    assert status["standalone_rejected"] is True
    assert status["policy"]["worm_storage"] is True
    assert status["policy"]["operational_retention_days"] == 730
    assert status["policy"]["institutional_retention_days"] == 1825


def test_five_dimension_logging(uat_seed):
    evt = uat.log_user_activity(
        "data.export",
        user_id=42,
        email="analyst@corp.example",
        role="analyst",
        tenant_id="org_abc",
        resource_id="report_xyz",
        data_snapshot_hash="abc123",
        ip="203.0.113.1",
        device_fingerprint="fp_deadbeef",
        result="success",
        seed=uat_seed,
    )
    assert evt["who"]["user_id"] == 42
    assert evt["what"]["action"] == "data.export"
    assert evt["where"]["ip"] == "203.0.113.1"
    assert evt["result"]["status"] == "success"
    assert evt["signature"]
    assert Path("data/user_activity_audit.jsonl").is_file()


def test_immutable_mirror_for_insight_actions(uat_seed):
    uat.log_user_activity("report.generate", user_id=1, resource_id="r1", seed=uat_seed)
    imm_dir = Path("data/immutable_recommendation_audit")
    assert imm_dir.is_dir()
    assert any(imm_dir.glob("*.json"))


def test_bridge_auth_event(uat_seed):
    uat.bridge_auth_event("login", user_id=1, email="u@example.com", ip="1.2.3.4")
    trail = uat.get_user_activity_trail(limit=5)
    actions = [e["what"]["action"] for e in trail["events"]]
    assert "auth.login" in actions


def test_bridge_authz_event(uat_seed):
    uat.bridge_authz_event(
        email="admin@example.com",
        tenant_id="org_x",
        role="admin",
        action="permission_check",
        resource="data.export",
        result="allowed",
        user_id=2,
    )
    trail = uat.get_user_activity_trail(limit=5)
    assert trail["events_count"] >= 1


def test_query_own_scope(uat_seed):
    uat.log_user_activity("settings.change", user_id=7, email="me@example.com", seed=uat_seed)
    uat.log_user_activity("settings.change", user_id=8, email="other@example.com", seed=uat_seed)
    result = uat.query_user_activity(
        viewer_email="me@example.com",
        viewer_user_id=7,
        limit=10,
        seed=uat_seed,
    )
    assert result["scope"] == "own"
    assert all(e["who"]["user_id"] == 7 for e in result["events"])


def test_gdpr_anonymize(uat_seed):
    uat.log_user_activity("data.export", user_id=99, email="gone@example.com", seed=uat_seed)
    result = uat.anonymize_user_activity(99, seed=uat_seed)
    assert result["anonymized"] is True
    anon_evt = uat.log_user_activity("data.export", user_id=99, email="gone@example.com", seed=uat_seed)
    assert anon_evt["who"]["user_id"] is None
    assert anon_evt["who"]["email_hash"] is None


def test_production_gate(uat_seed):
    gate = uat.check_user_activity_gate(seed=uat_seed)
    assert gate["ok"] is True
    assert gate["blocks_production"] is True


def test_e2e(uat_seed):
    result = uat.run_user_activity_e2e(seed=uat_seed)
    assert result["all_passed"] is True
