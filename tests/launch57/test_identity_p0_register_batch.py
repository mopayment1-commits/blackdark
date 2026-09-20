"""Launch-57 identity P0 — registration, verification, username, audit (batch 2)."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest
from starlette.testclient import TestClient


@pytest.fixture()
def client():
    from dashboard import app

    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


def _register_payload(**overrides):
    base = {
        "email": "register-p0@example.com",
        "password": "valid-password-15chars",
        "accepted_terms": True,
        "accepted_privacy": True,
        "plan": "free",
    }
    base.update(overrides)
    return base


def test_register_requires_separate_terms_and_privacy(client, tmp_path, monkeypatch):
    import database

    monkeypatch.setattr(database.config, "DB_PATH", str(tmp_path / "terms.db"))
    monkeypatch.setenv("IDENTITY_DEBUG_TOKENS", "true")

    async def _init():
        await database.init_db()

    asyncio.run(_init())
    missing_terms = client.post(
        "/api/auth/register",
        json=_register_payload(accepted_terms=False, email="t1@example.com"),
    )
    missing_privacy = client.post(
        "/api/auth/register",
        json=_register_payload(accepted_privacy=False, email="t2@example.com"),
    )
    assert missing_terms.status_code == 400
    assert "Terms" in missing_terms.json()["detail"]
    assert missing_privacy.status_code == 400
    assert "Privacy" in missing_privacy.json()["detail"]


def test_register_html_separate_unchecked_checkboxes():
    html = Path("templates/login.html").read_text(encoding="utf-8")
    assert 'id="regTerms"' in html
    assert 'id="regPrivacy"' in html
    assert 'type="checkbox"' in html
    assert "checked" not in html.split('id="regTerms"')[1].split(">")[0]
    assert "checked" not in html.split('id="regPrivacy"')[1].split(">")[0]


def test_paid_plan_blocked_until_email_verified(client, tmp_path, monkeypatch):
    import database
    from billing.subscription_engine import resolve_entitlements_for_user

    monkeypatch.setattr(database.config, "DB_PATH", str(tmp_path / "paid.db"))
    monkeypatch.setenv("IDENTITY_DEBUG_TOKENS", "true")

    async def _check(uid: int):
        ent = await resolve_entitlements_for_user(uid)
        assert ent["effective_plan"] == "free"
        assert ent["entitlement_allowed"] is False
        assert ent.get("account_exists_not_paid") is True

    asyncio.run(database.init_db())
    res = client.post(
        "/api/auth/register",
        json=_register_payload(email="prouser@example.com", plan="pro"),
    )
    assert res.status_code == 200
    body = res.json()
    assert body["user"]["tier"] == "free"
    assert body["trial"]["pending_until_verification"] is True
    assert body["trial"]["active"] is False
    asyncio.run(_check(int(body["user"]["id"])))


def test_email_verify_activates_pending_paid_plan(client, tmp_path, monkeypatch):
    import database
    from billing.subscription_engine import resolve_entitlements_for_user
    from identity_service import issue_auth_token

    monkeypatch.setattr(database.config, "DB_PATH", str(tmp_path / "verify.db"))
    monkeypatch.setenv("IDENTITY_DEBUG_TOKENS", "true")

    async def _setup():
        await database.init_db()
        from auth_service import register_user

        out = await register_user(
            "verifypro@example.com",
            "valid-password-15chars",
            accepted_terms=True,
            accepted_privacy=True,
            plan="pro",
        )
        uid = int(out["user"]["id"])
        token = await issue_auth_token(uid, "email_verify")
        return uid, token

    uid, raw = asyncio.run(_setup())
    res = client.get(f"/api/auth/verify-email?token={raw}", follow_redirects=False)
    assert res.status_code == 302
    assert "/profile" in (res.headers.get("location") or "")

    async def _ent():
        ent = await resolve_entitlements_for_user(uid)
        assert ent["email_verified"] is True
        assert ent["effective_plan"] == "pro"
        assert ent["entitlement_allowed"] is True

    asyncio.run(_ent())


def test_username_reserved_and_case_folded(tmp_path, monkeypatch):
    import database
    from auth_service import register_user
    from identity_service import validate_username

    monkeypatch.setattr(database.config, "DB_PATH", str(tmp_path / "user.db"))

    assert validate_username("Trader_One") == "trader_one"
    with pytest.raises(ValueError, match="reserved"):
        validate_username("admin")

    async def _run():
        await database.init_db()
        await register_user(
            "u1@example.com",
            "valid-password-15chars",
            username="MyHandle",
            accepted_terms=True,
            accepted_privacy=True,
        )
        with pytest.raises(ValueError, match="taken"):
            await register_user(
                "u2@example.com",
                "valid-password-15chars",
                username="myhandle",
                accepted_terms=True,
                accepted_privacy=True,
            )

    asyncio.run(_run())


def test_change_password_requires_step_up_without_reauth(client, tmp_path, monkeypatch):
    import database
    from auth_service import hash_password, login_user

    monkeypatch.setattr(database.config, "DB_PATH", str(tmp_path / "step.db"))
    monkeypatch.setenv("IDENTITY_DEBUG_TOKENS", "true")

    async def _setup():
        await database.init_db()
        await database.create_user(
            "step@example.com",
            hash_password("initial-password-15"),
            "Step",
        )
        return await login_user("step@example.com", "initial-password-15")

    login = asyncio.run(_setup())
    res = client.post(
        "/api/auth/change-password",
        headers={"Authorization": f"Bearer {login['token']}"},
        json={
            "current_password": "wrong-password-15xx",
            "new_password": "updated-password-15",
        },
    )
    assert res.status_code == 403
    assert "Step-up" in res.json()["detail"]


def test_dsr_erase_requires_step_up_operation_registered():
    from privileged_access.operations import ProtectedOperation, operation_spec

    spec = operation_spec(ProtectedOperation.PRIVACY_DSR_ERASE)
    assert spec.step_up_required is True


def test_identity_audit_events_recorded(client, tmp_path, monkeypatch):
    import database
    from security_events import _log_path

    monkeypatch.setattr(database.config, "DB_PATH", str(tmp_path / "audit.db"))
    monkeypatch.setattr("viral_capacity.viral_middleware_enabled", lambda: False)
    monkeypatch.setenv("IDENTITY_DEBUG_TOKENS", "true")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))

    asyncio.run(database.init_db())
    origin = {"Origin": "https://testserver"}
    reg = client.post(
        "/api/auth/register",
        json=_register_payload(email="audit@example.com"),
        headers=origin,
    )
    assert reg.status_code == 200
    login_fail = client.post(
        "/api/auth/login",
        json={"email": "audit@example.com", "password": "wrong-password-15xx"},
        headers=origin,
    )
    assert login_fail.status_code == 401
    login_ok = client.post(
        "/api/auth/login",
        json={"email": "audit@example.com", "password": "valid-password-15chars"},
        headers=origin,
    )
    assert login_ok.status_code == 200

    kinds = set()
    if _log_path().is_file():
        for line in _log_path().read_text(encoding="utf-8").splitlines():
            if line.strip():
                kinds.add(json.loads(line).get("kind"))
    assert "auth_register" in kinds
    assert "auth_login_failure" in kinds or "login_failure" in kinds
    assert "auth_login_success" in kinds
