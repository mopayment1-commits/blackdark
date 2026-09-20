"""Production auth transport behind Railway proxy + GIS COOP headers."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client():
    from dashboard import app

    return TestClient(app)


def test_production_auth_post_with_forwarded_proto_not_blocked(client, monkeypatch):
    monkeypatch.setenv("ENV", "production")
    for path in ("/api/auth/register", "/api/auth/login"):
        res = client.post(
            path,
            json={"email": "probe@example.com", "password": "short"},
            headers={"X-Forwarded-Proto": "https", "Host": "blackdark-production.up.railway.app"},
        )
        body = res.json() if res.headers.get("content-type", "").startswith("application/json") else {}
        assert body.get("error") != "insecure_transport_forbidden"
        assert res.status_code != 403 or body.get("error") != "insecure_transport_forbidden"


def test_production_auth_post_with_rfc7239_forwarded_not_blocked(client, monkeypatch):
    monkeypatch.setenv("ENV", "production")
    res = client.post(
        "/api/auth/login",
        json={"email": "probe@example.com", "password": "short"},
        headers={
            "Forwarded": 'for=1.2.3.4;proto=https;host="blackdark-production.up.railway.app"',
            "Host": "blackdark-production.up.railway.app",
        },
    )
    body = res.json()
    assert body.get("error") != "insecure_transport_forbidden"


def test_production_direct_http_auth_post_still_blocked(client, monkeypatch):
    monkeypatch.setenv("ENV", "production")
    res = client.post(
        "/api/auth/login",
        json={"email": "probe@example.com", "password": "short"},
    )
    assert res.status_code == 403
    assert res.json()["error"] == "insecure_transport_forbidden"


def test_login_page_coop_allows_popups(client, monkeypatch):
    monkeypatch.setenv("ENV", "production")
    res = client.get("/login", headers={"Accept": "text/html"})
    assert res.status_code == 200
    assert res.headers.get("cross-origin-opener-policy") == "same-origin-allow-popups"


def test_homepage_coop_remains_same_origin(client, monkeypatch):
    monkeypatch.setenv("ENV", "production")
    res = client.get("/", headers={"Accept": "text/html"})
    assert res.status_code == 200
    assert res.headers.get("cross-origin-opener-policy") == "same-origin"
