"""Launch-57 identity closure — sessions, DSR, profile, email, OAuth, audit, homoglyph."""

from __future__ import annotations

import asyncio
import json

import pytest
from starlette.testclient import TestClient


@pytest.fixture()
def client():
    from dashboard import app

    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


ORIGIN = {"Origin": "https://testserver"}


def test_revoked_session_token_returns_401(client, tmp_path, monkeypatch):
    import database
    from auth_service import create_session, hash_password, login_user

    monkeypatch.setattr(database.config, "DB_PATH", str(tmp_path / "sess.db"))
    monkeypatch.setenv("IDENTITY_DEBUG_TOKENS", "true")

    async def _setup():
        await database.init_db()
        uid = await database.create_user(
            "sess@example.com",
            hash_password("valid-password-15chars"),
            "Sess",
        )
        from security_auth import hash_session_token

        login = await login_user("sess@example.com", "valid-password-15chars")
        second = await create_session(uid, revoke_others=False, auth_method="password")
        sessions = await database.fetch_user_sessions(uid)
        login_hash = hash_session_token(login["token"])
        other = next(s for s in sessions if s["token"] != login_hash)
        return login["token"], second["token"], other["id"]

    keeper_token, revoked_token, session_id = asyncio.run(_setup())
    del_res = client.delete(
        f"/api/auth/sessions/{session_id}",
        headers={**ORIGIN, "Authorization": f"Bearer {keeper_token}"},
    )
    assert del_res.status_code == 200
    protected = client.get(
        "/api/auth/sessions",
        headers={**ORIGIN, "Authorization": f"Bearer {revoked_token}"},
    )
    assert protected.status_code == 401
    keeper = client.get(
        "/api/auth/sessions",
        headers={**ORIGIN, "Authorization": f"Bearer {keeper_token}"},
    )
    assert keeper.status_code == 200


def test_dsr_erase_sets_deletion_pending(client, tmp_path, monkeypatch):
    import database
    from auth_service import hash_password, login_user
    from privileged_access.step_up import issue_step_up_grant

    monkeypatch.setattr(database.config, "DB_PATH", str(tmp_path / "dsr.db"))
    monkeypatch.setenv("IDENTITY_DEBUG_TOKENS", "true")

    async def _setup():
        await database.init_db()
        await database.create_user(
            "erase@example.com",
            hash_password("valid-password-15chars"),
            "Erase",
        )
        return await login_user("erase@example.com", "valid-password-15chars")

    login = asyncio.run(_setup())
    step = issue_step_up_grant(
        subject_id=str(login["user"]["id"]),
        operation="privacy.dsr.erase",
    )
    res = client.post(
        "/api/privacy/dsr/erase",
        headers={
            **ORIGIN,
            "Authorization": f"Bearer {login['token']}",
            "X-Step-Up-Token": step["step_up_token"],
        },
        json={"confirm": False},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "DELETION_PENDING"
    status = client.get(
        "/api/privacy/dsr/status",
        headers={**ORIGIN, "Authorization": f"Bearer {login['token']}"},
    )
    assert status.json()["account_state"] == "DELETION_PENDING"


def test_public_profile_hides_email(client, tmp_path, monkeypatch):
    import database
    from auth_service import hash_password, register_user

    monkeypatch.setattr(database.config, "DB_PATH", str(tmp_path / "pub.db"))

    async def _setup():
        await database.init_db()
        await register_user(
            "public@example.com",
            "valid-password-15chars",
            "Public User",
            username="public_user",
            accepted_terms=True,
            accepted_privacy=True,
        )

    asyncio.run(_setup())
    res = client.get("/api/auth/public/profile/public_user")
    assert res.status_code == 200
    body = res.json()
    assert "email" not in body
    assert body.get("username") == "public_user"


def test_change_email_requires_step_up(client, tmp_path, monkeypatch):
    import database
    from auth_service import hash_password, login_user

    monkeypatch.setattr(database.config, "DB_PATH", str(tmp_path / "email.db"))
    monkeypatch.setenv("IDENTITY_DEBUG_TOKENS", "true")

    async def _setup():
        await database.init_db()
        await database.create_user(
            "mail@example.com",
            hash_password("valid-password-15chars"),
            "Mail",
        )
        return await login_user("mail@example.com", "valid-password-15chars")

    login = asyncio.run(_setup())
    res = client.post(
        "/api/auth/change-email",
        headers={**ORIGIN, "Authorization": f"Bearer {login['token']}"},
        json={"new_email": "newmail@example.com", "current_password": "wrong-password-15xx"},
    )
    assert res.status_code == 403


def test_google_oauth_blocked_external_without_keys(client, monkeypatch):
    monkeypatch.delenv("OAUTH_GOOGLE_CLIENT_ID", raising=False)
    res = client.get("/api/auth/oauth/google/start")
    assert res.status_code == 503
    assert res.json()["detail"]["state"] == "BLOCKED_EXTERNAL"


def test_security_notification_logged_blocked_external(client, tmp_path, monkeypatch):
    from identity_closure import notify_security_event
    from security_events import _log_path

    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    out = notify_security_event(user_id=1, email="a@b.co", kind="password_change")
    assert out["delivery_status"] == "BLOCKED_EXTERNAL"
    kinds = {
        json.loads(line).get("kind")
        for line in _log_path().read_text(encoding="utf-8").splitlines()
        if line.strip()
    }
    assert "security_notification_password_change" in kinds


def test_login_history_user_visible(client, tmp_path, monkeypatch):
    import database
    from auth_service import hash_password, login_user

    monkeypatch.setattr(database.config, "DB_PATH", str(tmp_path / "hist.db"))

    async def _setup():
        await database.init_db()
        await database.create_user(
            "hist@example.com",
            hash_password("valid-password-15chars"),
            "Hist",
        )
        return await login_user("hist@example.com", "valid-password-15chars", ip="1.2.3.4")

    login = asyncio.run(_setup())
    client.post(
        "/api/auth/login",
        json={"email": "hist@example.com", "password": "wrong-password-15xx"},
        headers=ORIGIN,
    )
    res = client.get(
        "/api/auth/login-history",
        headers={**ORIGIN, "Authorization": f"Bearer {login['token']}"},
    )
    assert res.status_code == 200
    rows = res.json()["history"]
    assert rows
    assert rows[0]["status"] in {"success", "failure"}
    assert "fraud" not in json.dumps(rows).lower()


def test_homoglyph_minimum_rejects_mixed_script():
    from identity_service import validate_username

    with pytest.raises(ValueError):
        validate_username("аdmin")  # Cyrillic а + Latin dmin
    assert validate_username("valid_user") == "valid_user"


def test_google_no_email_only_linking(tmp_path, monkeypatch):
    import database
    from oauth_service import login_or_link_oauth_user

    monkeypatch.setattr(database.config, "DB_PATH", str(tmp_path / "oauth.db"))

    async def _run():
        await database.init_db()
        await database.create_user(
            "existing@example.com",
            __import__("auth_service").hash_password("valid-password-15chars"),
            "Existing",
        )
        with pytest.raises(ValueError, match="email alone"):
            await login_or_link_oauth_user(
                {
                    "provider": "google",
                    "subject": "google-sub-unique",
                    "email": "existing@example.com",
                    "name": "Google",
                }
            )

    asyncio.run(_run())
