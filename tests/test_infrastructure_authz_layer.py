"""Tests — AuthZ Layer RBAC Core + SSO (Sprint 1/2 Infrastructure)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import infrastructure_authz_layer as authz


@pytest.fixture
def authz_seed() -> dict:
    return json.loads(Path("data/infrastructure_authz_layer_seed.json").read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def reset_state():
    authz.reset_authz_state()
    yield
    authz.reset_authz_state()


def test_authz_status_no_standalone(authz_seed):
    status = authz.authz_layer_status(seed=authz_seed)
    assert status["standalone_rejected"] is True
    assert status["sprint_rbac"] == 1
    assert status["sprint_sso"] == 2
    assert len(status["policy"]["canonical_roles"]) == 4


def test_four_canonical_roles_matrix(authz_seed):
    matrix = authz.canonical_role_matrix()
    assert "viewer" in matrix
    assert "analyst" in matrix
    assert "admin" in matrix
    assert "super_admin" in matrix
    assert "data.export" not in matrix["viewer"]
    assert "data.export" in matrix["analyst"]
    assert "users.manage" in matrix["admin"]
    assert "platform.ops" in matrix["super_admin"]


def test_legacy_role_normalization():
    assert authz.normalize_canonical_role("pm") == "analyst"
    assert authz.normalize_canonical_role("compliance") == "analyst"
    assert authz.normalize_canonical_role("admin") == "admin"


def test_tenant_isolation(authz_seed):
    from org_tenant import create_org, add_member

    org = create_org(name="Iso Org", owner_email="owner@iso.test", require_mfa=False)
    org_id = org["org_id"]
    add_member(org_id, "member@iso.test", "viewer")

    ok = authz.enforce_tenant_isolation(user_id=1, email="member@iso.test", tenant_id=org_id, seed=authz_seed)
    assert ok["isolated"] is True

    denied = authz.enforce_tenant_isolation(user_id=2, email="outsider@iso.test", tenant_id=org_id, seed=authz_seed)
    assert denied["cross_tenant_blocked"] is True


def test_viewer_cannot_export(authz_seed):
    from org_tenant import create_org, add_member

    org = create_org(name="Viewer Org", owner_email="admin@viewer.test", require_mfa=False)
    org_id = org["org_id"]
    add_member(org_id, "viewer@viewer.test", "viewer")

    result = authz.authorize_request(
        user_id=1,
        email="viewer@viewer.test",
        tenant_id=org_id,
        permission="data.export",
        seed=authz_seed,
    )
    assert result["allowed"] is False
    assert result["integration"]["ref"] == 924


def test_analyst_can_export_and_sql(authz_seed):
    from org_tenant import create_org, add_member

    org = create_org(name="Analyst Org", owner_email="admin@analyst.test", require_mfa=False)
    org_id = org["org_id"]
    add_member(org_id, "analyst@analyst.test", "analyst")

    export = authz.authorize_request(
        user_id=2,
        email="analyst@analyst.test",
        tenant_id=org_id,
        permission="data.export",
        seed=authz_seed,
    )
    sql = authz.authorize_request(
        user_id=2,
        email="analyst@analyst.test",
        tenant_id=org_id,
        permission="sql.workspace",
        seed=authz_seed,
    )
    assert export["allowed"] is True
    assert sql["allowed"] is True


def test_admin_manage_users_and_certificate(authz_seed):
    from org_tenant import create_org, add_member

    org = create_org(name="Admin Org", owner_email="owner@admin.test", require_mfa=False)
    org_id = org["org_id"]
    add_member(org_id, "admin@admin.test", "admin")

    users = authz.authorize_request(
        user_id=3,
        email="admin@admin.test",
        tenant_id=org_id,
        permission="users.manage",
        seed=authz_seed,
    )
    cert = authz.authorize_request(
        user_id=3,
        email="admin@admin.test",
        tenant_id=org_id,
        permission="decision.certificate",
        seed=authz_seed,
    )
    assert users["allowed"] is True
    assert cert["allowed"] is True


def test_authz_audit_and_fee_db(authz_seed):
    from org_tenant import create_org, add_member

    org = create_org(name="Audit Org", owner_email="owner@audit.test", require_mfa=False)
    org_id = org["org_id"]
    add_member(org_id, "analyst@audit.test", "analyst")

    authz.authorize_request(
        user_id=1,
        email="analyst@audit.test",
        tenant_id=org_id,
        permission="data.export",
        seed=authz_seed,
    )
    trail = authz.get_authz_audit_trail()
    assert trail["count"] >= 1
    assert trail["audit_trail"][-1]["append_only"] is True


def test_sso_jit_default_viewer(authz_seed):
    sso = authz.sso_authz_status(seed=authz_seed)
    assert sso["jit_default_role"] == "viewer"
    assert "okta" in sso["idp_integrations"]
    assert "oidc" in sso["protocols"]


def test_enterprise_sso_jit_role():
    from enterprise_sso import _jit_default_role

    assert _jit_default_role() == "viewer"


def test_require_authorization_raises(authz_seed):
    from org_tenant import create_org, add_member

    org = create_org(name="Deny Org", owner_email="owner@deny.test", require_mfa=False)
    org_id = org["org_id"]
    add_member(org_id, "viewer@deny.test", "viewer")

    with pytest.raises(PermissionError):
        authz.require_authorization(
            user_id=1,
            email="viewer@deny.test",
            tenant_id=org_id,
            permission="users.manage",
            seed=authz_seed,
        )


def test_e2e_all_checks(authz_seed):
    e2e = authz.run_authz_layer_e2e(seed=authz_seed)
    assert e2e["all_passed"] is True
    failed = [c for c in e2e["checks"] if not c["passed"]]
    assert failed == [], f"Failed: {failed}"
