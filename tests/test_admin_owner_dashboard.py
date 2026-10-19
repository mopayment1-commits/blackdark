"""Owner admin dashboard at /admin — DB-backed metrics API."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("ENV", "development")
os.environ.setdefault("SESSION_TOKEN_PEPPER", "test-pepper-admin-owner")

from anonymous_route_foundation import classify_route, path_is_public
from dashboard import app


@pytest.fixture()
def client():
    from starlette.testclient import TestClient

    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


def test_admin_root_classified_as_admin():
    assert classify_route("/admin").value == "admin"
    assert not path_is_public("/admin")
    assert not path_is_public("/api/admin/owner-metrics")


def test_admin_routes_registered_on_app():
    paths = set(app.openapi().get("paths") or {})
    assert "/admin" in paths
    assert "/api/admin/owner-metrics" in paths


def test_owner_metrics_requires_admin(client):
    assert client.get("/admin").status_code in {401, 403}
    assert client.get("/api/admin/owner-metrics").status_code in {401, 403}


def test_owner_metrics_shape_with_admin_key(client, monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "test-admin-key-please-rotate")
    monkeypatch.setenv("ADMIN_MFA_REQUIRED", "false")
    headers = {"X-Admin-Key": "test-admin-key-please-rotate"}
    res = client.get("/api/admin/owner-metrics", headers=headers)
    assert res.status_code == 200
    body = res.json()
    for key in ("users", "subscribers", "revenue", "visitors", "emails", "subscriptions"):
        assert key in body
    assert "total" in body["users"]
    assert "mrr_cents" in body["revenue"]
    assert body["emails"]["opened"] is None
    assert body["revenue"]["nrr_pct"] is None


def test_admin_dashboard_html_with_admin_key(client, monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "test-admin-key-please-rotate")
    monkeypatch.setenv("ADMIN_MFA_REQUIRED", "false")
    headers = {"X-Admin-Key": "test-admin-key-please-rotate"}
    res = client.get("/admin", headers=headers)
    assert res.status_code == 200
    assert "لوحة المالك" in res.text
    assert "/api/admin/owner-metrics" in res.text
