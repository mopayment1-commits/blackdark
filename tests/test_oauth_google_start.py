"""OAuth authorization start must redirect (RFC 6749), not 500."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("SOFT_LAUNCH", "1")
os.environ.setdefault("SESSION_TOKEN_PEPPER", "test-pepper-oauth-start")


@pytest.fixture()
def client(tmp_path, monkeypatch):
    import database

    monkeypatch.setattr(database.config, "DB_PATH", str(tmp_path / "oauth_start.db"))
    from starlette.testclient import TestClient

    from dashboard import app

    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


def test_google_oauth_start_redirects_302(client, monkeypatch):
    monkeypatch.setenv("OAUTH_GOOGLE_CLIENT_ID", "gid-test")
    monkeypatch.setenv("OAUTH_GOOGLE_CLIENT_SECRET", "gsecret-test")
    monkeypatch.setenv("APP_BASE_URL", "https://blackdark.io")

    res = client.get("/api/auth/oauth/google/start", follow_redirects=False)
    assert res.status_code == 302
    loc = res.headers.get("location") or ""
    assert loc.startswith("https://accounts.google.com/o/oauth2/v2/auth?")
    assert "client_id=gid-test" in loc
    assert "redirect_uri=" in loc


def test_google_oauth_start_302_when_oauth_state_db_unavailable(client, monkeypatch):
    """Redirect must not depend on oauth_states table (production Postgres edge cases)."""
    monkeypatch.setenv("OAUTH_GOOGLE_CLIENT_ID", "gid-test")
    monkeypatch.setenv("OAUTH_GOOGLE_CLIENT_SECRET", "gsecret-test")
    monkeypatch.setenv("APP_BASE_URL", "https://blackdark.io")

    async def _boom(**_kwargs):
        raise RuntimeError("simulated db down")

    import database

    monkeypatch.setattr(database, "insert_oauth_state", _boom)

    res = client.get("/api/auth/oauth/google/start", follow_redirects=False)
    assert res.status_code == 302
    assert "accounts.google.com" in (res.headers.get("location") or "")


def test_google_oauth_start_400_when_not_configured(client, monkeypatch):
    monkeypatch.delenv("OAUTH_GOOGLE_CLIENT_ID", raising=False)
    monkeypatch.delenv("OAUTH_GOOGLE_CLIENT_SECRET", raising=False)
    monkeypatch.setenv("APP_BASE_URL", "https://blackdark.io")

    res = client.get("/api/auth/oauth/google/start")
    assert res.status_code == 400
    assert res.status_code != 500
    detail = res.json().get("detail", "")
    assert detail
