"""Public open B2B demo endpoint (anonymous, capped)."""

from __future__ import annotations

import asyncio
import os

import pytest

os.environ.setdefault("ENV", "development")
os.environ.setdefault("SESSION_TOKEN_PEPPER", "test-pepper-b2b-demo")

from anonymous_route_foundation import is_anonymous_route_allowed
from dashboard import app


@pytest.fixture()
def client():
    from starlette.testclient import TestClient

    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


def test_b2b_demo_allowed_anonymous_get():
    assert is_anonymous_route_allowed("GET", "/api/b2b/demo") is True
    assert is_anonymous_route_allowed("GET", "/api/b2b/feed") is False


def test_b2b_demo_anonymous_returns_200_not_401(client, monkeypatch):
    async def fake_rows(*, limit=250, flow_types=None):
        return [{"flow_type": "manipulation_alert", "asset": "BTC", "id": 1}]

    monkeypatch.setattr("database.fetch_institutional_feed_rows", fake_rows)

    res = client.get("/api/b2b/demo")
    assert res.status_code == 200
    body = res.json()
    assert body.get("demo") is True
    assert body.get("record_count") == 1
    assert "Anonymous access denied" not in res.text


def test_b2b_demo_feed_cached(monkeypatch):
    import dashboard as dash

    calls = 0

    class FakeExporter:
        async def export_open_demo_feed(self, *, limit=None):
            nonlocal calls
            calls += 1
            return {"record_count": 0, "records": [], "feed_version": "test"}

    monkeypatch.setattr(dash, "_B2B_DEMO_FEED_CACHE", None)
    monkeypatch.setattr(dash, "_B2B_DEMO_FEED_CACHE_TTL_SEC", 60.0)
    monkeypatch.setattr(
        "whale_tracker.InstitutionalDataExporter",
        lambda *a, **k: FakeExporter(),
    )

    from starlette.testclient import TestClient

    with TestClient(dash.app, raise_server_exceptions=False) as client:
        client.get("/api/b2b/demo")
        client.get("/api/b2b/demo")
    assert calls == 1
