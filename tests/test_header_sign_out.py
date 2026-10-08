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
