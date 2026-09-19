"""Calm signup surface — /login?tab=register + Google GIS gate."""

from __future__ import annotations

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
