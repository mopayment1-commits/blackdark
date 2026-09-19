"""Calm signup surface — /login?tab=register + Google GIS gate."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client():
    from dashboard import app

    return TestClient(app)


def test_register_tab_calm_html(client):
    res = client.get("/login?tab=register", headers={"Accept": "text/html"})
    assert res.status_code == 200
    html = res.text
    assert "text/html" in (res.headers.get("content-type") or "")
    assert "Create your free account" in html
    assert "or continue with email" in html
    assert 'id="regEmail"' in html
    assert 'id="regPassword"' in html
    assert 'minlength="12"' in html
    assert "Already have an account?" in html
    assert "Anonymous access denied" not in html
    assert "Choose your plan" not in html
    assert 'name="regPlan"' in html
    assert "plan-grid" not in html
    assert "regUsername" not in html
    assert "regName" not in html


def test_register_empty_submit_shows_html_error(client):
    res = client.get("/login?tab=register", headers={"Accept": "text/html"})
    assert res.status_code == 200
    assert 'role="alert"' in res.text
    assert "validateRegisterForm" in res.text
    assert "Please enter your email address" in res.text


def test_google_signin_blocked_when_client_id_missing(client, monkeypatch):
    monkeypatch.delenv("OAUTH_GOOGLE_CLIENT_ID", raising=False)
    res = client.get("/login?tab=register", headers={"Accept": "text/html"})
    assert res.status_code == 200
    assert "Google sign-in not configured" in res.text
    assert "accounts.google.com/gsi/client" not in res.text

    status = client.get("/api/auth/oauth/status").json()
    assert status["google_signin"]["state"] == "BLOCKED_EXTERNAL"
    assert status["google_signin"]["blocked_key"] == "missing_oauth_google_client_id"


def test_google_signin_configured_when_client_id_set(client, monkeypatch):
    monkeypatch.setenv("OAUTH_GOOGLE_CLIENT_ID", "test-client-id.apps.googleusercontent.com")
    res = client.get("/login?tab=register", headers={"Accept": "text/html"})
    assert res.status_code == 200
    assert "googleBtnHost" in res.text
    assert "accounts.google.com/gsi/client" in res.text
    assert "Google sign-in not configured" not in res.text

    status = client.get("/api/auth/oauth/status").json()
    assert status["google_signin"]["state"] == "CONFIGURED"
    assert status["google_signin"]["client_id"].endswith(".apps.googleusercontent.com")


def test_register_redirect_alias(client):
    res = client.get("/register", follow_redirects=False)
    assert res.status_code == 307
    assert res.headers.get("location") == "/login?tab=register"


def test_login_and_profile_no_anonymous_json(client):
    for path in ("/login", "/profile"):
        res = client.get(path, headers={"Accept": "text/html"})
        assert "Anonymous access denied" not in res.text


def test_google_credential_endpoint_blocked_without_client_id(client, monkeypatch):
    monkeypatch.delenv("OAUTH_GOOGLE_CLIENT_ID", raising=False)
    res = client.post(
        "/api/auth/oauth/google/credential",
        json={"credential": "x" * 24, "plan": "free"},
    )
    assert res.status_code == 503
    assert "not configured" in res.json()["detail"].lower()


def test_login_forms_bind_submit_without_csp_events():
    html = Path("templates/login.html").read_text(encoding="utf-8")
    assert "getElementById('loginForm')?.addEventListener('submit', doLogin)" in html
    assert "getElementById('registerForm')?.addEventListener('submit', doRegister)" in html


def test_password_toggle_controls_present():
    html = Path("templates/login.html").read_text(encoding="utf-8")
    assert "togglePassword" in html
    assert 'id="loginPasswordToggle"' in html
    assert 'id="regPasswordToggle"' in html
    assert "Show password" in html
    assert "Hide password" in html
    assert "input.type = show ? 'text' : 'password'" in html


def test_non_json_api_errors_handled_gracefully():
    html = Path("templates/login.html").read_text(encoding="utf-8")
    assert "readApiError" in html
    assert "readApiJson" in html
    assert "unreadable response" in html
    assert "loginErrorMessage" in html
    assert "already registered" in html.lower()
    assert 'href="/login">Sign in</a>' in html


def test_google_signin_uses_redirect_mode_not_popup_only():
    """Fails if GIS reverts to popup-only (callback fetch) without redirect login_uri."""
    html = Path("templates/login.html").read_text(encoding="utf-8")
    dashboard = Path("dashboard.py").read_text(encoding="utf-8")
    assert "ux_mode: 'redirect'" in html
    assert "login_uri" in html
    assert "googleLoginUri" in html
    assert '@app.post("/login")' in dashboard
    assert "/api/auth/oauth/google/credential" not in html


def test_google_gis_redirect_post_login_route(client, monkeypatch):
    monkeypatch.setenv("OAUTH_GOOGLE_CLIENT_ID", "test-client-id.apps.googleusercontent.com")

    async def fake_verify(_credential: str):
        return {
            "provider": "google",
            "subject": "sub-1",
            "email": "google-user@example.com",
            "name": "Google User",
        }

    async def fake_login(_profile):
        return {"token": "session-token-abc", "user": {"email": "google-user@example.com"}}

    monkeypatch.setattr("oauth_service.verify_google_credential", fake_verify)
    monkeypatch.setattr("oauth_service.login_or_link_oauth_user", fake_login)

    res = client.post(
        "/login?tab=register&plan=free",
        data={"credential": "x" * 24},
        follow_redirects=False,
    )
    assert res.status_code == 303
    assert res.headers.get("location") == "/dashboard"


def test_register_not_500_when_session_pepper_missing_but_master_key_set(
    client, tmp_path, monkeypatch
):
    """Reproduces production 500: create_session before SESSION_TOKEN_PEPPER fallback."""
    import asyncio

    import database

    monkeypatch.setattr(database.config, "DB_PATH", str(tmp_path / "sess.db"))
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("SECRETS_MASTER_KEY", "production-master-key-32chars!!")
    monkeypatch.delenv("SESSION_TOKEN_PEPPER", raising=False)
    monkeypatch.setenv("IDENTITY_DEBUG_TOKENS", "true")

    async def _init():
        await database.init_db()

    asyncio.run(_init())
    res = client.post(
        "/api/auth/register",
        json={
            "email": "sessfallback@example.com",
            "password": "strong-pass-1234",
            "accepted_terms": True,
            "plan": "free",
        },
        headers={"X-Forwarded-Proto": "https"},
    )
    assert res.status_code != 500
    assert res.status_code == 200


def test_google_login_post_valid_credential_shape_not_500(client, monkeypatch, tmp_path):
    import asyncio

    import database

    monkeypatch.setattr(database.config, "DB_PATH", str(tmp_path / "google_sess.db"))
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("SECRETS_MASTER_KEY", "production-master-key-32chars!!")
    monkeypatch.delenv("SESSION_TOKEN_PEPPER", raising=False)
    monkeypatch.setenv("OAUTH_GOOGLE_CLIENT_ID", "test-client-id.apps.googleusercontent.com")

    async def _init():
        await database.init_db()

    asyncio.run(_init())

    async def fake_verify(_credential: str):
        return {
            "provider": "google",
            "subject": "google-sub-prod",
            "email": "google-sess@example.com",
            "name": "Google Sess",
        }

    monkeypatch.setattr("oauth_service.verify_google_credential", fake_verify)

    res = client.post(
        "/login?plan=free",
        data={"credential": "eyJhbGciOiJIUzI1NiJ9." + ("x" * 24)},
        headers={"X-Forwarded-Proto": "https"},
        follow_redirects=False,
    )
    assert res.status_code != 500
    assert res.status_code == 303
    assert res.headers.get("location") == "/dashboard"


def test_register_api_rejects_short_password(client, tmp_path, monkeypatch):
    import database

    monkeypatch.setattr(database.config, "DB_PATH", str(tmp_path / "pw.db"))

    async def _init():
        await database.init_db()

    import asyncio

    asyncio.run(_init())
    res = client.post(
        "/api/auth/register",
        json={
            "email": "shortpw@example.com",
            "password": "short-pass",
            "accepted_terms": True,
            "plan": "free",
        },
    )
    assert res.status_code == 422 or res.status_code == 400
