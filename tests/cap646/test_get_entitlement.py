"""GET /api/cap646/{id} must enforce entitlement_engine.check (OWASP ASVS V4)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from dashboard import app

    return TestClient(app)


def test_get_pro_capability_denied_for_anonymous(client: TestClient):
    response = client.get("/api/cap646/47", params={"symbol": "BTC"})
    assert response.status_code == 200
    body = response.json()
    assert body.get("success") is False
    ent = body.get("entitlement") or {}
    assert ent.get("allowed") is False
    assert ent.get("reason") in {"tier_insufficient", "teaser"}


def test_get_free_capability_allowed_for_anonymous(client: TestClient):
    response = client.get("/api/cap646/1", params={"symbol": "BTC"})
    assert response.status_code == 200
    body = response.json()
    assert body.get("success") is True
    assert body.get("production_spine") == "batch01"


def test_get_pro_capability_allowed_with_pro_user(client: TestClient):
    from dashboard import app
    from security_auth import optional_user_from_request

    async def _pro_user() -> dict:
        return {"email": "pro@proof.blackdark.local", "tier": "pro"}

    app.dependency_overrides[optional_user_from_request] = _pro_user
    try:
        response = client.get("/api/cap646/47", params={"symbol": "BTC"})
        assert response.status_code == 200
        body = response.json()
        assert body.get("success") is True
    finally:
        app.dependency_overrides.pop(optional_user_from_request, None)
