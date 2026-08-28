"""Tests — Institutional RBAC Hardening (#1022)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import institutional_rbac_hardening as irb
from decision_certificate import build_decision_certificate
from org_rbac import has_permission, rbac_status, require_permission
from org_tenant import add_member, create_org, list_members, remove_member


@pytest.fixture
def rbac_seed() -> dict:
    return json.loads(Path("data/rbac_institutional_seed.json").read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def _reset():
    irb.reset_rbac_state()
    audit = Path("data/authz_audit.jsonl")
    if audit.is_file():
        audit.unlink()
    yield
    irb.reset_rbac_state()


def test_rbac_status_no_standalone(rbac_seed):
    status = irb.institutional_rbac_status(seed=rbac_seed)
    assert status["standalone_rejected"] is True
    assert len(status["institutional_roles"]) == 4
    assert "viewer" in status["matrix"]
    assert "data.export" not in status["matrix"]["viewer"]
    assert "data.export" in status["matrix"]["analyst"]


def test_viewer_cannot_export(rbac_seed):
    org = create_org(name="Export Org", owner_email="owner@export.test")
    add_member(org["org_id"], "viewer@export.test", "viewer")
    with pytest.raises(PermissionError):
        irb.assert_data_export_allowed(org["org_id"], "viewer@export.test", seed=rbac_seed)


def test_analyst_can_export(rbac_seed):
    org = create_org(name="Analyst Org", owner_email="owner@analyst.test")
    add_member(org["org_id"], "analyst@analyst.test", "analyst")
    irb.assert_data_export_allowed(org["org_id"], "analyst@analyst.test", seed=rbac_seed)


def test_viewer_cannot_sql_workspace(rbac_seed):
    org = create_org(name="SQL Org", owner_email="owner@sql.test")
    add_member(org["org_id"], "viewer@sql.test", "viewer")
    with pytest.raises(PermissionError):
        irb.assert_sql_workspace_allowed(org["org_id"], "viewer@sql.test", seed=rbac_seed)


def test_admin_team_management(rbac_seed):
    org = create_org(name="Team Org", owner_email="admin@team.test")
    result = irb.manage_team_member(
        org["org_id"],
        actor_email="admin@team.test",
        action="create",
        target_email="newhire@team.test",
        role="analyst",
        seed=rbac_seed,
    )
    assert result["ok"] is True
    emails = {m["email"] for m in list_members(org["org_id"])}
    assert "newhire@team.test" in emails


def test_viewer_cannot_manage_team(rbac_seed):
    org = create_org(name="Block Org", owner_email="admin@block.test")
    add_member(org["org_id"], "viewer@block.test", "viewer")
    with pytest.raises(PermissionError):
        irb.manage_team_member(
            org["org_id"],
            actor_email="viewer@block.test",
            action="create",
            target_email="x@block.test",
            role="analyst",
            seed=rbac_seed,
        )


def test_remove_member(rbac_seed):
    org = create_org(name="Remove Org", owner_email="admin@remove.test")
    add_member(org["org_id"], "gone@remove.test", "analyst")
    remove_member(org["org_id"], "gone@remove.test", actor_email="admin@remove.test")
    emails = {m["email"] for m in list_members(org["org_id"])}
    assert "gone@remove.test" not in emails


def test_authz_audit_logged(rbac_seed):
    org = create_org(name="Audit Org", owner_email="owner@audit.test")
    add_member(org["org_id"], "analyst@audit.test", "analyst")
    irb.assert_data_export_allowed(org["org_id"], "analyst@audit.test", seed=rbac_seed)
    trail = irb.get_authz_audit_trail(limit=10)
    assert trail["events_count"] >= 1
    assert Path("data/authz_audit.jsonl").is_file()


def test_org_rbac_has_permission(rbac_seed):
    org = create_org(name="Matrix Org", owner_email="owner@matrix.test")
    assert has_permission(org["org_id"], "owner@matrix.test", "org.members.manage")
    assert not has_permission(org["org_id"], "nobody@matrix.test", "org.members.manage")


def test_institutional_certificate_requires_admin(rbac_seed):
    org = create_org(name="Cert Org", owner_email="admin@cert.test")
    add_member(org["org_id"], "viewer@cert.test", "viewer")
    with pytest.raises(PermissionError):
        build_decision_certificate(
            {"tier": "institutional", "symbol": "BTC"},
            org_id=org["org_id"],
            actor_email="viewer@cert.test",
        )
    cert = build_decision_certificate(
        {"tier": "institutional", "symbol": "BTC", "decision_action": "WAIT"},
        org_id=org["org_id"],
        actor_email="admin@cert.test",
    )
    assert cert["asset"] == "BTC"


def test_production_gate(rbac_seed):
    gate = irb.check_rbac_production_gate(seed=rbac_seed)
    assert gate["ok"] is True
    assert gate["blocks_production"] is True


def test_e2e(rbac_seed):
    result = irb.run_institutional_rbac_e2e(seed=rbac_seed)
    assert result["all_passed"] is True


def test_rbac_status_surface():
    status = rbac_status()
    assert status["feature_ref"] == 1022
    assert "institutional_roles" in status
