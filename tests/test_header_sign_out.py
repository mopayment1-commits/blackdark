"""Header Sign out — server session revoke + anonymous chrome."""

from __future__ import annotations

import os
import uuid

os.environ.setdefault("SOFT_LAUNCH", "1")

from fastapi.testclient import TestClient

from dashboard import app

client = TestClient(app)


def _register() -> None:
    email = f"signout-{uuid.uuid4().hex[:10]}@example.com"
    res = client.post(
        "/api/auth/register",
        json={"email": email, "password": "SecurePass1234!", "accepted_terms": True},
        headers={"Origin": "https://testserver"},
    )
    assert res.status_code == 200, res.text


def test_sign_out_clears_session_and_header_shows_login():
    _register()
    authed = client.get("/")
    assert 'id="bdAccountTrigger"' in authed.text
    assert 'id="bdUtilLogin"' not in authed.text

    out = client.post("/api/auth/logout", headers={"Origin": "https://testserver"})
    assert out.status_code == 200
    assert out.json().get("success") is True

    anon = client.get("/")
    assert 'id="bdUtilLogin"' in anon.text
    assert 'id="bdUtilSignup"' in anon.text
    assert 'id="bdAccountTrigger"' not in anon.text


def test_logout_returns_200_when_revoke_is_slow(monkeypatch):
    import asyncio

    async def slow_logout(_token: str) -> None:
        await asyncio.sleep(30)

    monkeypatch.setattr("auth_service.logout_user", slow_logout)
    _register()
    import time

    t0 = time.monotonic()
    out = client.post("/api/auth/logout", headers={"Origin": "https://testserver"})
    elapsed = time.monotonic() - t0
    assert out.status_code == 200, out.text
    assert out.json().get("success") is True
    assert elapsed < 8.0
    assert "bd_token=" in out.headers.get("set-cookie", "").lower()


def test_logout_revoked_token_cannot_restore_session():
    _register()
    authed = client.get("/")
    assert 'id="bdAccountTrigger"' in authed.text
    token_cookie = client.cookies.get("bd_token")
    assert token_cookie

    out = client.post("/api/auth/logout", headers={"Origin": "https://testserver"})
    assert out.status_code == 200

    client.cookies.set("bd_token", token_cookie)
    again = client.get("/")
    assert 'id="bdUtilLogin"' in again.text
    assert 'id="bdAccountTrigger"' not in again.text


def test_logout_without_session_cookie_still_200():
    from anonymous_route_foundation import is_anonymous_route_allowed

    assert is_anonymous_route_allowed("POST", "/api/auth/logout") is True
    res = client.post("/api/auth/logout", headers={"Origin": "https://testserver"})
    assert res.status_code == 200
    assert res.json().get("success") is True


def test_clear_session_cookie_matches_secure_flags():
    from starlette.responses import Response

    from security_middleware import clear_session_cookie, cookie_session_kwargs

    resp = Response()
    clear_session_cookie(resp)
    raw = resp.headers.get("set-cookie", "").lower()
    assert "bd_token=" in raw
    kw = cookie_session_kwargs()
    if kw.get("secure"):
        assert "secure" in raw
    assert "max-age=0" in raw or "1970" in raw
