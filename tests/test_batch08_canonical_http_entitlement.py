"""Batch08 canonical HTTP entitlement path — real TestClient, no entitlement mocks."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "scripts" / "partial_batches" / "batch_08_351_400.json"
CANONICAL_ROUTE = "/api/cap646/{capability_id}"


def _batch_ids() -> list[int]:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return [int(x) for x in data["capability_ids"]]


@pytest.fixture
def client() -> TestClient:
    from dashboard import app

    return TestClient(app)


@pytest.mark.parametrize("capability_id", _batch_ids())
def test_http_get_real_path_anonymous_allowed(client: TestClient, capability_id: int):
    """Free-tier Batch08 surfaces: real GET must succeed without auth bypass."""
    response = client.get(f"/api/cap646/{capability_id}", params={"symbol": "BTC"})
    assert response.status_code == 200
    body = response.json()
    assert body.get("success") is True, body
    assert body.get("capability_id") == capability_id or body.get("requested_capability_id") == capability_id


@pytest.mark.parametrize("capability_id", _batch_ids())
def test_http_get_real_path_pro_user_allowed(client: TestClient, capability_id: int):
    from dashboard import app
    from security_auth import optional_user_from_request

    async def _pro_user() -> dict:
        return {"id": 1, "email": "batch08-http@blackdark.local", "tier": "pro", "role": "user"}

    app.dependency_overrides[optional_user_from_request] = _pro_user
    try:
        response = client.get(f"/api/cap646/{capability_id}", params={"symbol": "BTC"})
        assert response.status_code == 200
        body = response.json()
        assert body.get("success") is True, body
    finally:
        app.dependency_overrides.pop(optional_user_from_request, None)


def test_batch08_entitlement_requirement_matrix():
    """Machine record: Batch08 IDs use default free min_tier — tier-denial tests NOT_APPLICABLE."""
    from cap646.catalog import catalog_by_id, is_external
    from cap646.entitlements import _ORG_PERMISSIONS, _TIER_REQUIREMENTS

    cat = catalog_by_id()
    restricted: list[int] = []
    for cid in _batch_ids():
        row = cat.get(cid, {})
        if is_external(cid):
            restricted.append(cid)
            continue
        if _TIER_REQUIREMENTS.get(cid, "free") != "free":
            restricted.append(cid)
            continue
        if _ORG_PERMISSIONS.get(cid) or row.get("feature_key") or row.get("usage_meter_key"):
            restricted.append(cid)
    assert restricted == [], f"unexpected restricted Batch08 IDs: {restricted}"


def test_manifest_count():
    assert len(_batch_ids()) == 50
