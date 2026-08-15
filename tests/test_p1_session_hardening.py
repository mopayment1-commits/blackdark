"""P1 session / CSRF / cookie hardening regression tests."""

from __future__ import annotations

import pytest
from fastapi import Request
from starlette.datastructures import Headers

import security_middleware as sm


def _request(headers: dict[str, str], method: str = "POST") -> Request:
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": method,
        "scheme": "https",
        "path": "/api/auth/logout",
        "raw_path": b"/api/auth/logout",
        "query_string": b"",
        "headers": Headers(headers).raw,
        "client": ("203.0.113.10", 443),
        "server": ("example.com", 443),
    }
    return Request(scope)


def test_allowed_hosts_include_railway_healthcheck(monkeypatch):
    monkeypatch.setenv("APP_BASE_URL", "https://blackdark-production.up.railway.app")
    monkeypatch.setenv("RAILWAY_PUBLIC_DOMAIN", "blackdark-production.up.railway.app")
    hosts = sm._allowed_hosts()
    assert "blackdark-production.up.railway.app" in hosts
    assert "healthcheck.railway.app" in hosts


def test_health_live_not_blocked_by_trusted_host(monkeypatch):
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("APP_BASE_URL", "https://blackdark-production.up.railway.app")
    monkeypatch.setenv("TRUSTED_HOST_ENFORCE", "true")
    from fastapi.testclient import TestClient

    from dashboard import app

    client = TestClient(app)
    resp = client.get("/health/live", headers={"Host": "healthcheck.railway.app"})
    assert resp.status_code == 200
    assert resp.json().get("status") == "ok"


def test_csrf_rejects_cookie_mutation_without_origin(monkeypatch):
    monkeypatch.setenv("APP_BASE_URL", "https://example.com")
    req = _request({"cookie": "bd_token=abc", "host": "example.com"})
    assert sm._request_origin_ok(req) is False


def test_csrf_allows_matching_origin(monkeypatch):
    monkeypatch.setenv("APP_BASE_URL", "https://example.com")
    req = _request(
        {
            "cookie": "bd_token=abc",
            "host": "example.com",
            "origin": "https://example.com",
        }
    )
    assert sm._request_origin_ok(req) is True


def test_csrf_allows_loopback_http_any_port(monkeypatch):
    monkeypatch.delenv("APP_BASE_URL", raising=False)
    req = _request(
        {
            "cookie": "bd_token=abc",
            "host": "127.0.0.1:8081",
            "origin": "http://127.0.0.1:8081",
        }
    )
    assert sm._request_origin_ok(req) is True


def _force_production_markers(monkeypatch) -> None:
    """APP_ENV=production must win even when ENV is polluted to development."""
    monkeypatch.setenv("ENV", "development")
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    monkeypatch.delenv("RAILWAY_ENVIRONMENT", raising=False)


def test_production_rejects_legacy_clear_cookie(monkeypatch):
    _force_production_markers(monkeypatch)
    monkeypatch.delenv("ALLOW_LEGACY_SESSION_COOKIE", raising=False)
    assert sm.cookie_to_session_bearer("plainBearerTokenValue1234567890") == ""


def test_sealed_cookie_roundtrip(monkeypatch):
    _force_production_markers(monkeypatch)
    # Production vault requires explicit key material (fail-closed).
    monkeypatch.setenv("SECRETS_MASTER_KEY", "p1-session-hardening-test-master-key")
    from secrets_vault import encrypt_secret

    plain = "sessionBearerTokenValueABCDEFG123"
    sealed = encrypt_secret(plain)
    assert sealed.startswith("gAAAA")
    assert sm.cookie_to_session_bearer(sealed) == plain


def test_auth_body_omits_token_in_production(monkeypatch):
    _force_production_markers(monkeypatch)
    monkeypatch.delenv("AUTH_TOKEN_IN_BODY", raising=False)
    from api.routers.auth import _session_response_body

    body = _session_response_body({"token": "abc", "user": {"id": 1}})
    assert "token" not in body
    assert body.get("session") == "cookie"


def test_cookie_secure_in_production(monkeypatch):
    _force_production_markers(monkeypatch)
    monkeypatch.delenv("COOKIE_SECURE", raising=False)
    monkeypatch.delenv("APP_BASE_URL", raising=False)
    kwargs = sm.cookie_session_kwargs()
    assert kwargs["httponly"] is True
    assert kwargs["secure"] is True
    assert kwargs["samesite"] == "lax"


def test_cookie_secure_false_overrides_production_http(monkeypatch):
    _force_production_markers(monkeypatch)
    monkeypatch.setenv("COOKIE_SECURE", "false")
    monkeypatch.delenv("APP_BASE_URL", raising=False)
    kwargs = sm.cookie_session_kwargs()
    assert kwargs["secure"] is False
    assert kwargs["httponly"] is True


@pytest.mark.asyncio
async def test_csp_rewrite_reads_streaming_html_body():
    from starlette.responses import StreamingResponse

    async def _chunks():
        yield b"<html><body><script>window.x=1</script></body></html>"

    streamed = StreamingResponse(_chunks(), media_type="text/html")
    rewritten = await sm._maybe_rewrite_html_with_nonce(streamed, "streamNonce")
    text = rewritten.body.decode("utf-8")
    assert 'nonce="streamNonce"' in text
    assert "/static/js/csp_events.js" in text


@pytest.mark.asyncio
async def test_csp_rewrite_unzips_gzip_html_stream():
    import gzip

    from starlette.responses import StreamingResponse

    html = b"<html><body><script>window.x=1</script></body></html>"

    async def _chunks():
        yield gzip.compress(html)

    streamed = StreamingResponse(_chunks(), media_type="text/html", headers={"content-encoding": "gzip"})
    rewritten = await sm._maybe_rewrite_html_with_nonce(streamed, "gzNonce")
    raw = rewritten.body
    if (rewritten.headers.get("content-encoding") or "") == "gzip":
        raw = gzip.decompress(raw)
    text = raw.decode("utf-8")
    assert 'nonce="gzNonce"' in text
    assert "/static/js/csp_events.js" in text


def test_login_html_scripts_receive_csp_nonce():
    from fastapi.testclient import TestClient

    from dashboard import app

    client = TestClient(app)
    resp = client.get("/login")
    assert resp.status_code == 200
    csp = resp.headers.get("content-security-policy") or ""
    assert "nonce-" in csp
    body = resp.text
    assert "csp_events.js" in body
    assert body.count("nonce=") >= 2
    assert 'id="registerForm"' in body
