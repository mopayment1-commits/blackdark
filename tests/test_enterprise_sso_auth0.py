"""Enterprise SSO — Auth0 OIDC live path (mocked token exchange)."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def auth0_env(monkeypatch):
    monkeypatch.setenv("APP_BASE_URL", "https://blackdark-production.up.railway.app")
    monkeypatch.setenv("ENTERPRISE_OIDC_ISSUER", "https://blackdark.us.auth0.com")
    monkeypatch.setenv("ENTERPRISE_OIDC_CLIENT_ID", "auth0-client-id")
    monkeypatch.setenv("ENTERPRISE_OIDC_CLIENT_SECRET", "auth0-client-secret")
    monkeypatch.setenv("ENTERPRISE_SSO_DEMO", "false")
    monkeypatch.setenv("ENTERPRISE_SSO_DEFAULT_ORG_ID", "org-auth0-test")


def test_sso_status_oidc_ready_when_auth0_env(auth0_env):
    from enterprise_sso import sso_status

    st = sso_status()
    assert st["configured"] is True
    assert st["oidc_ready"] is True
    assert st["demo_mode"] is False
    assert st["idp"] == "auth0"
    assert st["callback_url"] == "https://blackdark-production.up.railway.app/api/institutional/sso/callback"


def test_sec_006_passes_when_auth0_env(auth0_env):
    from cap646.institutional_controls import _sec_006

    row = _sec_006()
    assert row["status"] == "VERIFIED_COMPLETE"
    assert row["id"] == "SEC-006"


@pytest.mark.asyncio
async def test_auth0_authorize_url_uses_auth0_authorize_endpoint(auth0_env):
    from org_tenant import create_org
    from enterprise_sso import build_sso_authorize_url_async

    org = create_org(name="Auth0 Org", owner_email="owner@auth0.example")
    monkeypatch_id = org["org_id"]
    import os

    os.environ["ENTERPRISE_SSO_DEFAULT_ORG_ID"] = monkeypatch_id

    result = await build_sso_authorize_url_async(
        monkeypatch_id,
        redirect_uri="https://blackdark-production.up.railway.app/api/institutional/sso/callback",
        email_hint="user@auth0.example",
    )
    assert result["ready"] is True
    assert "blackdark.us.auth0.com/authorize" in result["authorize_url"]
    assert "client_id=auth0-client-id" in result["authorize_url"]
    assert "state=" in result["authorize_url"]


@pytest.mark.asyncio
async def test_auth0_callback_exchanges_code_and_issues_session(auth0_env, tmp_path, monkeypatch):
    from org_tenant import create_org
    from enterprise_sso import build_sso_authorize_url_async, complete_sso_login_async

    import config
    import database

    monkeypatch.setattr(config, "DB_PATH", str(tmp_path / "test.db"), raising=False)
    await database.init_db()

    org = create_org(name="Auth0 Org", owner_email="owner@auth0.example")
    monkeypatch.setenv("ENTERPRISE_SSO_DEFAULT_ORG_ID", org["org_id"])

    auth = await build_sso_authorize_url_async(
        org["org_id"],
        redirect_uri="https://blackdark-production.up.railway.app/api/institutional/sso/callback",
    )
    state = auth["state"]

    mock_token_resp = MagicMock()
    mock_token_resp.raise_for_status = MagicMock()
    mock_token_resp.json.return_value = {"access_token": "at-123", "token_type": "Bearer"}

    mock_user_resp = MagicMock()
    mock_user_resp.raise_for_status = MagicMock()
    mock_user_resp.json.return_value = {
        "sub": "auth0|abc123",
        "email": "user@auth0.example",
        "name": "Auth0 User",
    }

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_token_resp)
    mock_client.get = AsyncMock(return_value=mock_user_resp)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("httpx.AsyncClient", return_value=mock_client):
        result = await complete_sso_login_async(state=state, code="live-auth-code")

    assert result["demo_or_live"] == "live"
    assert result["email"] == "user@auth0.example"
    assert result["token"]
    mock_client.post.assert_called_once()
    posted = mock_client.post.call_args
    assert posted[0][0] == "https://blackdark.us.auth0.com/oauth/token"


def test_public_sso_routes_without_auth(monkeypatch):
    monkeypatch.setenv("SOFT_LAUNCH", "true")
    monkeypatch.setenv("APP_BASE_URL", "https://blackdark-production.up.railway.app")
    from fastapi.testclient import TestClient

    from dashboard import app

    client = TestClient(app)
    status = client.get("/api/institutional/sso/status")
    assert status.status_code == 200
    body = status.json()
    assert body["surface"] == "enterprise_sso"
