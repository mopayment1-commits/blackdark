"""Login recovery: forgot password, forgot email, remember-me cookie."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


def test_login_template_recovery_controls():
    html = Path("templates/login.html").read_text(encoding="utf-8")
    assert 'id="rememberMe"' in html
    assert "Forgot password?" in html
    assert "Forgot email?" in html
    assert "forgotEmailForm" in html
    assert "/api/auth/forgot-email" in html
    assert "remember_me" in html
    reset = Path("templates/reset_password.html").read_text(encoding="utf-8")
    assert "resetForm" in reset
    assert "addEventListener('submit'" in reset


def test_session_cookie_session_only_flag():
    from starlette.responses import Response

    from security_middleware import attach_session_cookie, cookie_session_kwargs

    persistent = cookie_session_kwargs()
    session = cookie_session_kwargs(session_only=True)
    assert "max_age" in persistent
    assert "max_age" not in session
    resp = Response()
    attach_session_cookie(resp, "x" * 48, session_only=True)
    assert resp.headers.get("set-cookie")


@pytest.mark.asyncio
async def test_forgot_email_recovery_by_name_and_wallet(tmp_path, monkeypatch):
    import database
    from auth_service import hash_password
    from identity_service import normalize_recovery_wallet, recover_account_email

    monkeypatch.setattr(database.config, "DB_PATH", str(tmp_path / "fe.db"))
    await database.init_db()
    uid = await database.create_user(
        "hidden@example.com",
        hash_password("old-password-99"),
        "Wallet User",
    )
    await database.update_user_profile_fields(
        uid,
        {"recovery_wallet": "0xAbCd" + "0" * 36},
    )
    miss = await recover_account_email(name="Nobody", wallet_address="")
    assert miss["found"] is False
    hit = await recover_account_email(
        name="Wallet User",
        wallet_address="0xabcd" + "0" * 36,
    )
    assert hit["found"] is True
    assert hit["email"] == "hidden@example.com"
    assert normalize_recovery_wallet("0xAbCd") == "abcd"


def test_password_reset_roundtrip(tmp_path, monkeypatch):
    import database
    from auth_service import hash_password, verify_password
    from dashboard import app
    from identity_service import consume_auth_token, issue_auth_token

    monkeypatch.setattr(database.config, "DB_PATH", str(tmp_path / "pr.db"))
    monkeypatch.setenv("IDENTITY_DEBUG_TOKENS", "true")

    async def _setup():
        await database.init_db()
        return await database.create_user(
            "round@example.com",
            hash_password("old-password-99"),
            "Round Trip",
        )

    uid = asyncio.run(_setup())
    raw = asyncio.run(issue_auth_token(uid, "password_reset"))
    client = TestClient(app, base_url="https://testserver")
    res = client.post(
        "/api/auth/reset-password",
        json={"token": raw, "password": "new-secure-pass-42"},
    )
    assert res.status_code == 200
    assert res.json().get("ok") is True
    login = client.post(
        "/api/auth/login",
        headers={"Origin": "https://testserver"},
        json={
            "email": "round@example.com",
            "password": "new-secure-pass-42",
            "remember_me": True,
        },
    )
    assert login.status_code == 200
    row = asyncio.run(database.fetch_user_by_id(uid))
    assert verify_password("new-secure-pass-42", row["password_hash"])
    with pytest.raises(ValueError):
        asyncio.run(consume_auth_token(raw, "password_reset"))
