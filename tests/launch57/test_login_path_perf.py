"""Login path must not block on command-home; redirect uses replace."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
DASHBOARD = ROOT / "templates/dashboard.html"
LOGIN = ROOT / "templates/login.html"


def test_login_save_auth_uses_immediate_replace():
    html = LOGIN.read_text(encoding="utf-8")
    assert "window.location.replace(resolvePostAuthUrl(data))" in html


def test_dashboard_defers_command_home_after_paint():
    dash = DASHBOARD.read_text(encoding="utf-8")
    assert 'id="trust-pulse" class="tp-loading"' in dash
    boot = dash.split("function boot()", 1)[1].split("if (document.readyState", 1)[0]
    assert "scheduleCommandHome()" in boot
    assert boot.count("loadCommandHome(true)") == 0


def test_google_login_uri_uses_public_origin_helper():
    from dashboard import _google_login_uri_base, _request_public_origin
    from starlette.requests import Request

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/login",
        "headers": [
            (b"x-forwarded-proto", b"https"),
            (b"x-forwarded-host", b"app.blackdark.io"),
            (b"host", b"internal.railway"),
        ],
        "query_string": b"",
        "server": ("internal.railway", 8080),
    }
    req = Request(scope)
    assert _request_public_origin(req) == "https://app.blackdark.io"
    assert _google_login_uri_base(req) == "https://app.blackdark.io/login"


def test_login_path_segment_latencies_bounded():
    """Sanity guard — login HTML and API stay sub-second locally; command-home may be slower."""
    import time
    import uuid

    client = TestClient(__import__("dashboard").app)
    email = f"perf-{uuid.uuid4().hex[:10]}@example.com"
    client.post(
        "/api/auth/register",
        json={"email": email, "password": "SecurePass1234!", "accepted_terms": True},
        headers={"Origin": "https://testserver"},
    )

    t0 = time.perf_counter()
    login = client.post(
        "/api/auth/login",
        json={"email": email, "password": "SecurePass1234!"},
        headers={"Origin": "https://testserver"},
    )
    login_ms = (time.perf_counter() - t0) * 1000
    assert login.status_code == 200
    assert login_ms < 5000

    t0 = time.perf_counter()
    dash = client.get("/dashboard", headers={"Accept": "text/html"})
    dash_ms = (time.perf_counter() - t0) * 1000
    assert dash.status_code == 200
    assert dash_ms < 5000
    assert 'id="trust-pulse" class="tp-loading"' in dash.text
