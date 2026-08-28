"""Tests — Batch: #828 Backup & Disaster Recovery (REL-003 Sprint-0 Infrastructure)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import infrastructure_backup_disaster_recovery as backup_dr


@pytest.fixture
def backup_seed() -> dict:
    return json.loads(
        Path("data/infrastructure_backup_disaster_recovery_seed.json").read_text(encoding="utf-8")
    )


@pytest.fixture(autouse=True)
def reset_state():
    backup_dr.reset_backup_dr_state()
    yield
    backup_dr.reset_backup_dr_state()


def test_828_status_policy(backup_seed):
    status = backup_dr.backup_dr_status_828(seed=backup_seed)
    assert status["standalone_rejected"] is True
    assert status["control_ref"] == "REL-003"
    assert status["sprint"] == 0
    policy = status["policy"]
    assert policy["full_backup_frequency"] == "daily"
    assert policy["incremental_frequency_hours"] == 6
    assert policy["rpo_hours"] <= 6
    assert policy["rto_hours"] <= 2
    assert policy["encryption_at_rest"] == "AES-256"
    assert policy["encryption_in_transit"] == "TLS 1.3"
    assert policy["off_site_storage"]["cross_region"] is True
    assert policy["off_site_storage"]["same_datacenter"] is False


def test_828_retention_policy(backup_seed):
    retention = backup_dr.backup_dr_status_828(seed=backup_seed)["policy"]["retention"]
    assert retention["daily_days"] == 30
    assert retention["weekly_weeks"] == 12
    assert retention["monthly_months"] == 12


def test_828_scope_and_tenant_isolation(backup_seed):
    policy = backup_dr.backup_dr_status_828(seed=backup_seed)["policy"]
    scope = set(policy["scope"])
    assert "database" in scope
    assert "historical_archive" in scope
    assert "configuration" in scope
    assert "secrets_backup" in scope
    tenant = policy["tenant_isolation"]
    assert tenant["per_tenant_key"] is True
    assert tenant["no_cross_tenant_recovery"] is True


def test_828_ops_panel(backup_seed):
    panel = backup_dr.build_backup_dr_panel_828(seed=backup_seed)
    assert panel["ok"] is True
    assert panel["last_full_backup"]["backup_type"] == "full"
    assert panel["last_incremental_backup"]["backup_type"] == "incremental"
    assert panel["last_dr_restore_test"]["result"] == "success"


def test_828_record_backup_operation(backup_seed):
    op = backup_dr.record_backup_operation_828(
        backup_type="full",
        size_bytes=1024,
        checksum="abc",
        location="s3://bucket/full/",
        off_site_location="s3://bucket-replica/full/",
        test_result="passed",
        seed=backup_seed,
    )
    assert op["operation"]["audit_logged"] is True
    assert op["operation"]["encrypted_at_rest"] is True


def test_828_backup_failure_alerts(backup_seed):
    failed = backup_dr.record_backup_operation_828(test_result="failed", seed=backup_seed)
    assert failed["alert_triggered"] is True
    assert failed["no_silent_failure"] is True


def test_828_integrity_validation():
    ok = backup_dr.validate_backup_integrity_828(
        checksum="deadbeef", expected_checksum="deadbeef", size_bytes=1024
    )
    assert ok["integrity_passed"] is True
    bad = backup_dr.validate_backup_integrity_828(
        checksum="bad", expected_checksum="good", size_bytes=0
    )
    assert bad["integrity_passed"] is False


def test_828_dr_restore_test(backup_seed):
    dr = backup_dr.record_dr_restore_test_828(result="success", seed=backup_seed)
    assert dr["ok"] is True
    test = dr["dr_test"]
    assert test["real_restore"] is True
    assert test["simulation_only"] is False
    assert test["rpo_met"] is True
    assert test["rto_met"] is True
    assert test["lineage_integrity_passed"] is True


def test_828_post_restore_lineage(backup_seed):
    lineage = backup_dr.run_post_restore_lineage_check_828(seed=backup_seed)
    assert lineage["lineage_integrity_passed"] is True
    assert lineage["provenance_ref"] == 945


def test_828_audit_trail(backup_seed):
    backup_dr.record_backup_operation_828(test_result="passed", seed=backup_seed)
    trail = backup_dr.get_backup_audit_trail_828(seed=backup_seed)
    assert trail["entry_count"] >= 2
    assert trail["audit_retention_years"] == 2


def test_828_institutional_bridge(backup_seed):
    status = backup_dr.institutional_backup_status_828(seed=backup_seed)
    assert status["control_ref"] == "REL-003"
    assert status["targets"]["rpo_minutes"] == 360
    assert status["targets"]["rto_minutes"] == 120


def test_828_e2e(backup_seed):
    e2e = backup_dr.run_backup_disaster_recovery_e2e_828(seed=backup_seed)
    assert e2e["all_passed"] is True
    assert len(e2e["checks"]) >= 20


def test_institutional_assurance_delegates():
    from institutional_assurance import backup_status, record_backup_drill

    drill = record_backup_drill(rpo_minutes=300, rto_minutes=90, result="success")
    assert drill.get("result") == "success" or drill.get("real_restore") is True
    status = backup_status()
    assert status["control_ref"] == "REL-003"
