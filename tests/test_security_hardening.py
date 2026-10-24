"""Security hardening closure tests."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient


def test_security_headers_helper():
    from starlette.requests import Request

    from security_middleware import security_headers_for

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "https",
        "path": "/",
        "raw_path": b"/",
        "query_string": b"",
        "headers": [],
        "client": ("127.0.0.1", 123),
        "server": ("test", 443),
    }
    req = Request(scope)
    headers = security_headers_for(req)
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["X-Frame-Options"] == "DENY"
    assert "Content-Security-Policy" in headers
    csp = headers["Content-Security-Policy"]
    assert "nonce-" in csp
    assert "strict-dynamic" in csp
    assert "default-src 'none'" in csp
    script_src = csp.split("script-src")[1].split(";")[0]
    assert "'unsafe-inline'" not in script_src
    assert "Strict-Transport-Security" in headers
    assert "max-age=31536000" in headers["Strict-Transport-Security"]
    assert "includeSubDomains" in headers["Strict-Transport-Security"]
    assert "preload" in headers["Strict-Transport-Security"]
    assert headers.get("Cross-Origin-Embedder-Policy") == "credentialless"
    assert headers.get("X-XSS-Protection") == "0"


def test_security_posture_honesty():
    from security_posture import security_posture_report

    report = security_posture_report()
    assert report["honesty"]["soc2_claimed"] is False
    assert report["honesty"]["pentest_report_in_repo"] is False
    assert "Fernet" in report["controls"]["user_api_keys"]
    assert "not Fernet+HMAC certification" in report["controls"]["model_weights"]


def test_mark_read_idor_denied():
    from in_app_alerts import _INBOX, _LOCK, mark_read

    with _LOCK:
        _INBOX.clear()
        _INBOX.append(
            {
                "id": "alert-owner-a",
                "user_email": "a@example.com",
                "read": False,
                "title": "x",
            }
        )
    assert mark_read("alert-owner-a", user_email="b@example.com") is None
    hit = mark_read("alert-owner-a", user_email="a@example.com")
    assert hit is not None
    assert hit["read"] is True


def test_production_guard_blocks_soft_launch_live_money(monkeypatch):
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("SOFT_LAUNCH", "true")
    monkeypatch.setenv("LIVE_EXECUTION_ALLOW_API", "true")
    monkeypatch.setenv("SERVICE_MODE", "web")
    monkeypatch.setenv("SECRETS_MASTER_KEY", "x" * 32)
    monkeypatch.setenv("SESSION_TOKEN_PEPPER", "y" * 16)
    monkeypatch.setenv("ADMIN_API_KEY", "z" * 24)
    from production_guard import evaluate_production_guard

    report = evaluate_production_guard()
    assert "soft_launch_no_live_money" in report["required_failures"]


def test_secrets_vault_prod_ignores_local_dev(monkeypatch):
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("LOCAL_DEV", "true")
    monkeypatch.delenv("SECRETS_MASTER_KEY", raising=False)
    monkeypatch.delenv("SECRETS_VAULT_KEY", raising=False)
    from secrets_vault import _is_production, get_vault_key

    assert _is_production() is True
    with pytest.raises(RuntimeError):
        get_vault_key()


@pytest.mark.asyncio
async def test_b2b_ws_info_hides_demo_key(monkeypatch):
    monkeypatch.delenv("EXPOSE_B2B_DEMO_KEY", raising=False)
    import config

    monkeypatch.setattr(config, "B2B_DEMO_API_KEY", "secret-demo-key-should-hide")
    from dashboard import b2b_ws_info

    payload = await b2b_ws_info()
    assert "demo_key" not in payload["auth"]
    assert payload["auth"].get("key_on_public_page") is False


@pytest.mark.asyncio
async def test_security_status_route_and_headers():
    from dashboard import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/api/security/status")
        assert r.status_code == 200
        body = r.json()
        assert body["honesty"]["soc2_claimed"] is False
        assert "X-Content-Type-Options" in r.headers or "x-content-type-options" in {
            k.lower() for k in r.headers
        }
        # Middleware should attach hardening marker
        assert r.headers.get("X-Security-Hardening") == "1" or r.headers.get(
            "x-security-hardening"
        ) == "1"


@pytest.mark.asyncio
async def test_telegram_test_requires_auth():
    from dashboard import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post("/api/alerts/telegram/test", json={"chat_id": "123"})
        assert r.status_code == 401


@pytest.mark.asyncio
async def test_logout_clears_without_user_token_field():
    """Logout must not depend on user['token'] (never echoed)."""
    import inspect

    from api.routers import auth as auth_router

    src = inspect.getsource(auth_router.auth_logout)
    assert "raw_bearer_or_cookie" in src or "token" in src
    assert 'user.get("token")' not in src


def test_auth_login_post_requires_csrf_without_session(monkeypatch):
    from fastapi.testclient import TestClient

    from dashboard import app
    import tests.conftest as conftest_mod

    orig = getattr(conftest_mod, "_testclient_request_original", TestClient.request)
    monkeypatch.setattr(TestClient, "request", orig)

    def _noop_rate_limit(_key: str) -> None:
        return None

    monkeypatch.setattr("security_auth.check_login_rate_limit", _noop_rate_limit)
    monkeypatch.setattr("security_auth.check_api_rate_limit", _noop_rate_limit)

    client = TestClient(app)
    res = client.post(
        "/api/auth/login",
        json={"email": "csrf-probe@example.com", "password": "x" * 12},
        headers={"Origin": "https://testserver"},
    )
    assert res.status_code == 403
    body = res.json()
    assert body.get("error") == "csrf_rejected"


def test_csrf_cookie_is_httponly():
    from starlette.requests import Request
    from starlette.responses import Response

    from security_csrf import attach_csrf_cookie, csrf_token_for_request

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "https",
        "path": "/",
        "raw_path": b"/",
        "query_string": b"",
        "headers": [],
        "client": ("127.0.0.1", 123),
        "server": ("test", 443),
    }
    req = Request(scope)
    token = csrf_token_for_request(req)
    resp = Response()
    attach_csrf_cookie(resp, req)
    raw = resp.headers.get("set-cookie") or ""
    assert "bd_csrf=" in raw
    assert "httponly" in raw.lower()
    assert token in raw


def test_html_rewrite_injects_csrf_meta():
    from security_middleware import _inject_html_csp_nonce

    html = "<html><head><title>x</title></head><body></body></html>"
    out = _inject_html_csp_nonce(html, "abc123", "tok.test.sig")
    assert 'name="bd-csrf-token"' in out
    assert "tok.test.sig" in out


def test_csp_nonce_mode_emits_nonce_without_unsafe_inline(monkeypatch):
    from types import SimpleNamespace
    from security_middleware import security_headers_for

    monkeypatch.delenv("CSP_NONCE_MODE", raising=False)  # default-on
    monkeypatch.delenv("CONTENT_SECURITY_POLICY", raising=False)
    req = SimpleNamespace(state=SimpleNamespace(), url=SimpleNamespace(scheme="http"))
    headers = security_headers_for(req)
    csp = headers["Content-Security-Policy"]
    assert "strict-dynamic" in csp
    assert "nonce-" in csp
    assert "require-trusted-types-for" in csp
    assert "trusted-types default" in csp
    assert "'unsafe-inline'" not in csp.split("script-src")[1].split(";")[0]
    assert getattr(req.state, "csp_nonce", None)


def test_csp_nonce_mode_can_rollback_to_unsafe_inline(monkeypatch):
    from types import SimpleNamespace
    from security_middleware import security_headers_for

    monkeypatch.setenv("CSP_NONCE_MODE", "false")
    monkeypatch.delenv("CONTENT_SECURITY_POLICY", raising=False)
    req = SimpleNamespace(state=SimpleNamespace(), url=SimpleNamespace(scheme="http"))
    headers = security_headers_for(req)
    script_src = headers["Content-Security-Policy"].split("script-src")[1].split(";")[0]
    assert "'unsafe-inline'" in script_src
