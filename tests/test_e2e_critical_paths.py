"""E2E critical path smoke — legal, health, auth surface (G6 partial)."""

from __future__ import annotations

import pytest


@pytest.fixture(scope="module")
def client():
    from starlette.testclient import TestClient

    from dashboard import app

    with TestClient(app) as c:
        yield c


def test_health_live(client):
    r = client.get("/health/live")
    assert r.status_code == 200


def test_legal_pages(client):
    for path in ("/terms", "/privacy", "/disclaimer"):
        r = client.get(path)
        assert r.status_code == 200
        assert len(r.text) > 100


def test_auth_login_surface(client):
    r = client.get("/login")
    assert r.status_code == 200


def test_monitoring_status(client):
    r = client.get("/api/monitoring/status")
    assert r.status_code in {200, 401, 403}
