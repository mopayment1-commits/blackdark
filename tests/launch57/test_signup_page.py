"""Calm signup surface — /login?tab=register + Google GIS gate."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client():
    from dashboard import app

    return TestClient(app)


def test_login_header_is_direct_child_before_main_column(client):
    for path in ("/login", "/login?tab=register"):
        res = client.get(path, headers={"Accept": "text/html"})
        assert res.status_code == 200, path
        html = res.text
        header_pos = html.find('class="bd-global-header"')
        main_pos = html.find('class="login-main"')
        card_pos = html.find('class="card"')
        assert header_pos > 0, path
        assert main_pos > header_pos, path
        assert card_pos > main_pos, path
        assert html.find('class="bd-global-header"', card_pos) < 0, path
        assert "login-page" in html
        assert "align-items:center; justify-content:center; padding:1.5rem" not in html


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
    assert 'class="auth-tabs"' in html
    assert 'id="tabRegister"' in html
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


def test_login_submit_shows_loading_before_fetch():
    html = Path("templates/login.html").read_text(encoding="utf-8")
    assert 'id="loginSubmitBtn"' in html
    assert "function setLoginSubmitLoading" in html
    assert "Signing in…" in html
    assert "aria-busy" in html
    assert "btn-spinner" in html
    login_fn = html.split("async function doLogin(e)", 1)[1].split("async function doMfa", 1)[0]
    assert "if (loginBtn?.disabled) return" in login_fn
    assert "setLoginSubmitLoading(true)" in login_fn
    assert login_fn.index("setLoginSubmitLoading(true)") < login_fn.index("await fetch('/api/auth/login'")
    assert "setLoginSubmitLoading(false)" in login_fn
    assert "saveAuth(d)" in login_fn
    assert login_fn.rindex("setLoginSubmitLoading(true)") < login_fn.index("saveAuth(d)")


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


def test_register_not_500_when_kms_provider_local_dev_but_master_key_set(
    client, tmp_path, monkeypatch
):
    """Railway may still have KMS_PROVIDER=local_dev while SECRETS_MASTER_KEY is set."""
    import asyncio

    import database

    monkeypatch.setattr(database.config, "DB_PATH", str(tmp_path / "kms.db"))
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("SECRETS_MASTER_KEY", "production-master-key-32chars!!")
    monkeypatch.setenv("KMS_PROVIDER", "local_dev")
    monkeypatch.delenv("SESSION_TOKEN_PEPPER", raising=False)

    async def _init():
        await database.init_db()

    asyncio.run(_init())
    res = client.post(
        "/api/auth/register",
        json={
            "email": "kmsoverride@example.com",
            "password": "strong-pass-1234",
            "accepted_terms": True,
            "plan": "free",
        },
        headers={"X-Forwarded-Proto": "https"},
    )
    assert res.status_code != 500
    assert res.status_code == 200


def test_register_not_500_when_email_outbox_read_only(client, tmp_path, monkeypatch):
    """Production disks may deny writes to data/email_outbox.jsonl."""
    import asyncio
    import os
    import stat
    from pathlib import Path

    import database

    monkeypatch.setattr(database.config, "DB_PATH", str(tmp_path / "outbox.db"))
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("SECRETS_MASTER_KEY", "production-master-key-32chars!!")
    monkeypatch.delenv("SESSION_TOKEN_PEPPER", raising=False)

    async def _init():
        await database.init_db()

    asyncio.run(_init())

    outbox = Path("data/email_outbox.jsonl")
    outbox.parent.mkdir(parents=True, exist_ok=True)
    outbox.touch(exist_ok=True)
    os.chmod(outbox, stat.S_IRUSR)
    try:
        res = client.post(
            "/api/auth/register",
            json={
                "email": "outboxro@example.com",
                "password": "strong-pass-1234",
                "accepted_terms": True,
                "plan": "free",
            },
            headers={"X-Forwarded-Proto": "https"},
        )
    finally:
        os.chmod(outbox, stat.S_IRWXU)

    assert res.status_code != 500
    assert res.status_code == 200


def test_register_missing_session_secrets_not_500(client, tmp_path, monkeypatch):
    """Misconfigured production secrets must not surface as silent 500."""
    import asyncio

    import database

    monkeypatch.setattr(database.config, "DB_PATH", str(tmp_path / "nosecrets.db"))
    monkeypatch.setenv("ENV", "production")
    monkeypatch.delenv("SESSION_TOKEN_PEPPER", raising=False)
    monkeypatch.delenv("SECRETS_MASTER_KEY", raising=False)
    monkeypatch.delenv("SECRETS_VAULT_KEY", raising=False)
    monkeypatch.delenv("MFA_ENCRYPTION_KEY", raising=False)

    async def _init():
        await database.init_db()

    asyncio.run(_init())
    res = client.post(
        "/api/auth/register",
        json={
            "email": "nosecrets@example.com",
            "password": "strong-pass-1234",
            "accepted_terms": True,
            "plan": "free",
        },
        headers={"X-Forwarded-Proto": "https"},
    )
    assert res.status_code != 500
    assert res.status_code == 503
    assert "SESSION_TOKEN_PEPPER" in res.json()["detail"]


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
