"""P0 — Anonymous security and route foundation closure tests."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("ENV", "development")
os.environ.setdefault("SESSION_TOKEN_PEPPER", "test-pepper-p0-anonymous")

from anonymous_route_foundation import (
    PRIVATE_BY_DEFAULT,
    ProductAuthState,
    build_route_inventory,
    is_anonymous_route_allowed,
    path_is_public,
    request_has_authentication_signal,
    resolve_product_auth_state,
    response_contains_private_data,
    summarize_inventory,
)
from dashboard import app


@pytest.fixture()
def client():
    from starlette.testclient import TestClient

    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


@pytest.fixture()
def inventory():
    return build_route_inventory(app)


def test_private_by_default_enabled():
    assert PRIVATE_BY_DEFAULT is True


def test_explicit_anonymous_product_state():
    assert resolve_product_auth_state(None) == ProductAuthState.ANONYMOUS
    assert resolve_product_auth_state({"tier": "free"}) == ProductAuthState.FREE_ACCOUNT
    assert resolve_product_auth_state({"tier": "pro"}) == ProductAuthState.PAID_INDIVIDUAL
    assert resolve_product_auth_state({"tier": "whale", "org_id": "org-1"}) == ProductAuthState.INSTITUTIONAL


def test_route_inventory_complete(inventory):
    assert len(inventory) >= 600
    summary = summarize_inventory(inventory)
    assert summary["ROUTES_INVENTORIED"] == len(inventory)
    assert summary["PUBLIC_EXPLICIT"] > 0
    assert summary["PRIVATE_PROTECTED"] > 0
    for row in inventory:
        assert row["METHOD"]
        assert row["PATH"]
        assert row["OWNER"]
        assert row["DATA_CLASS"]
        assert "TEST_EVIDENCE" in row


def test_allowlist_is_explicit_not_implicit():
    assert is_anonymous_route_allowed("GET", "/api/status") is True
    assert is_anonymous_route_allowed("GET", "/") is True
    assert is_anonymous_route_allowed("GET", "/api/platform/keys/status") is False
    assert path_is_public("/health/live") is True


def test_no_cookie_private_route_denied(client):
    private_paths = (
        "/api/user/profile",
        "/api/privacy/export",
        "/api/platform/keys/status",
        "/dashboard",
        "/profile",
        "/admin/launch",
        "/api/cap646/47",
    )
    for path in private_paths:
        response = client.get(path)
        assert response.status_code in {401, 403, 404, 405, 422}, path


def test_no_cookie_public_allowlist_ok(client):
    public_paths = (
        "/",
        "/health/live",
        "/api/status",
        "/api/security/status",
        "/login",
        "/register",
        "/oracle-accuracy",
        "/api/docs/public-manifest",
    )
    for path in public_paths:
        response = client.get(path)
        assert response.status_code in {200, 302, 307}, f"{path} -> {response.status_code}"


def test_no_cookie_auth_flow_post_allowed(client):
    response = client.post(
        "/api/auth/login",
        json={"email": "nobody@example.com", "password": "wrong-password-123"},
    )
    assert response.status_code in {400, 401, 403, 422, 429}


def test_admin_route_not_public_without_admin(client):
    response = client.get("/admin/launch")
    assert response.status_code in {401, 403, 404}


def test_accidental_public_routes_zero(client):
    """Spot-check private API/HTML routes — middleware must deny before handler."""
    private_probe_paths = (
        "/api/platform/keys/status",
        "/api/user/profile",
        "/api/privacy/export",
        "/api/billing/subscription",
        "/api/cap646/47",
        "/api/v1/data/status",
        "/api/journal",
        "/dashboard",
        "/profile",
        "/admin/launch",
        "/openapi.json",
        "/graphql",
    )
    accidental = []
    for path in private_probe_paths:
        response = client.get(path)
        if response.status_code in {200, 201, 204}:
            accidental.append(path)
    assert accidental == []


def test_enforce_anonymous_route_boundary_unit():
    from anonymous_route_foundation import enforce_anonymous_route_boundary

    class _Req:
        method = "GET"
        url = type("U", (), {"path": "/api/user/profile"})()
        headers = {}
        cookies = {}
        query_params = {}

    denial = enforce_anonymous_route_boundary(_Req())
    assert denial is not None
    assert denial.status_code == 401


def test_private_data_not_leaked_on_public_routes(client):
    exposure_paths = []
    for path in ("/api/status", "/api/security/status", "/health/live", "/api/site-services"):
        response = client.get(path)
        if response.status_code == 200 and response_contains_private_data(response.text):
            exposure_paths.append(path)
    assert exposure_paths == []


def test_client_only_auth_boundaries_zero(client):
    """Private endpoints must not return 200 with user payloads without server auth."""
    client_only = []
    probes = (
        "/api/auth/me",
        "/api/user/profile",
        "/api/billing/subscription",
    )
    for path in probes:
        response = client.get(path)
        if response.status_code == 200:
            client_only.append(path)
    assert client_only == []


def test_api_stream_boundary_no_cookie(client):
    assert is_anonymous_route_allowed("GET", "/api/dashboard/stream") is True
    assert is_anonymous_route_allowed("GET", "/api/trust-pulse/stream") is False
    denied = client.get("/api/trust-pulse/stream", timeout=3.0)
    assert denied.status_code in {401, 403, 404, 422, 429}


def test_request_has_authentication_signal():
    class _Req:
        headers = {"authorization": "Bearer abc"}
        cookies = {}
        query_params = {}

    assert request_has_authentication_signal(_Req()) is True
