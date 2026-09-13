"""Security workflow register — live verification (WF-005, WF-015, WF-016, WF-017)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi import HTTPException

REGISTER = Path(__file__).resolve().parents[1] / "docs/security/SECURITY_WORKFLOW_REGISTER.json"


def test_security_workflow_register_exists():
    data = json.loads(REGISTER.read_text(encoding="utf-8"))
    ids = {w["id"] for w in data["workflows"]}
    assert "WF-015" in ids
    assert "WF-016" in ids


@pytest.mark.asyncio
async def test_wf015_identity_impersonation(monkeypatch):
    """WF-015 — body actor/owner cannot override authenticated principal."""
    from api.routers.institutional import OrgCreate, create_org, org_mfa_policy, org_role_change
    from api.routers.institutional import MfaPolicy, RoleChange

    captured: dict = {}

    def _create_org(**kwargs):
        captured["create"] = kwargs
        return {"org_id": "o1"}

    def _set_role(org_id, email, role, *, actor_email):
        captured["role"] = actor_email
        return {}

    def _set_mfa(org_id, required, *, actor_email):
        captured["mfa"] = actor_email
        return {}

    monkeypatch.setattr("org_tenant.create_org", _create_org)
    monkeypatch.setattr("org_tenant.set_member_role", _set_role)
    monkeypatch.setattr("org_tenant.set_org_mfa_required", _set_mfa)

    auth = {"email": "Owner@Example.com"}
    await create_org(OrgCreate(name="X", owner_email="spoof@evil.com"), user=auth)
    assert captured["create"]["owner_email"] == "owner@example.com"

    await org_role_change("org1", RoleChange(email="m@example.com", role="admin", actor_email="spoof@evil.com"), user=auth)
    assert captured["role"] == "owner@example.com"

    await org_mfa_policy("org1", MfaPolicy(require_mfa=True, actor_email="spoof@evil.com"), user=auth)
    assert captured["mfa"] == "owner@example.com"


@pytest.mark.asyncio
async def test_wf016_org_members_requires_membership(monkeypatch):
    from api.routers.institutional import org_members
    monkeypatch.setattr("org_tenant.list_members", lambda org_id: [{"email": "a@b.com"}])
    def _deny(*_a, **_k):
        raise PermissionError("cross_tenant_denied")

    monkeypatch.setattr("org_tenant.assert_org_access", _deny)
    with pytest.raises(HTTPException) as exc:
        await org_members("org_other", user={"email": "intruder@evil.com"})
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_wf017_org_add_member_requires_admin(monkeypatch):
    from api.routers.institutional import MemberAdd, org_add_member
    monkeypatch.setattr("org_tenant.add_member", lambda *a, **k: {"ok": True})
    def _deny_admin(*_a, **_k):
        raise PermissionError("admin_required")

    monkeypatch.setattr("org_tenant.assert_org_access", _deny_admin)
    with pytest.raises(HTTPException) as exc:
        await org_add_member("org1", MemberAdd(email="x@y.com", role="analyst"), user={"email": "viewer@co.com"})
    assert exc.value.status_code == 403


def test_wf005_cross_tenant_org_access():
    from org_tenant import assert_org_access, create_org

    org = create_org(name="Acme", owner_email="owner@acme.com")
    assert_org_access(org["org_id"], "owner@acme.com", min_role="admin")
    with pytest.raises(PermissionError):
        assert_org_access(org["org_id"], "stranger@evil.com")
