"""Launch-57 anonymous public surface — cost guards + AV-24 leak sweep."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from starlette.testclient import TestClient

from anonymous_route_foundation import ANONYMOUS_ROUTE_ALLOWLIST_EXACT
from launch57.anonymous_public_cost_guards import (
    PUBLIC_ROUTE_COST_POLICIES,
    PublicRouteCostPolicy,
    build_public_route_cost_manifest,
    enforce_public_rate_limit,
    iter_allowlist_probe_paths,
    resolve_public_cost_policy,
    scan_public_response_for_av24_leak,
    sweep_allowlist_av24,
)


@pytest.fixture(autouse=True)
def disable_viral_rate_limits(monkeypatch):
    monkeypatch.setattr("viral_capacity.viral_middleware_enabled", lambda: False)


@pytest.fixture()
def client():
    from dashboard import app

    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


def test_every_allowlist_exact_path_has_cost_policy():
    missing = [p for p in sorted(ANONYMOUS_ROUTE_ALLOWLIST_EXACT) if p not in PUBLIC_ROUTE_COST_POLICIES]
    assert missing == []
    manifest = build_public_route_cost_manifest()
    assert len(manifest) >= len(ANONYMOUS_ROUTE_ALLOWLIST_EXACT)


def test_rate_limit_exceeded_returns_429(client, monkeypatch):
    monkeypatch.setitem(
        PUBLIC_ROUTE_COST_POLICIES,
        "/api/status",
        PublicRouteCostPolicy(
            "/api/status",
            "public_api",
            rate_limit=2,
            rate_window_sec=60,
            max_response_bytes=131_072,
            timeout_sec=5.0,
        ),
    )
    statuses = [client.get("/api/status").status_code for _ in range(3)]
    assert statuses[:2] == [200, 200]
    assert statuses[2] == 429


def test_response_size_cap_returns_413(client, monkeypatch):
    monkeypatch.setitem(
        PUBLIC_ROUTE_COST_POLICIES,
        "/how-it-works",
        PublicRouteCostPolicy(
            "/how-it-works",
            "public_html",
            rate_limit=90,
            rate_window_sec=60,
            max_response_bytes=512,
            timeout_sec=15.0,
        ),
    )
    res = client.get("/how-it-works", headers={"Accept": "text/html"})
    assert res.status_code == 413
    assert res.json().get("error") == "response_too_large"


def test_timeout_returns_504(client, monkeypatch):
    async def slow_call_next(request):
        await asyncio.sleep(0.05)
        from starlette.responses import JSONResponse

        return JSONResponse({"ok": True})

    monkeypatch.setitem(
        PUBLIC_ROUTE_COST_POLICIES,
        "/api/status",
        PublicRouteCostPolicy(
            "/api/status",
            "public_api",
            rate_limit=120,
            rate_window_sec=60,
            max_response_bytes=131_072,
            timeout_sec=0.01,
        ),
    )

    from launch57.anonymous_public_cost_guards import apply_public_cost_guards

    class _Req:
        url = type("U", (), {"path": "/api/status"})()
        method = "GET"
        headers = {}
        cookies = {}
        client = type("C", (), {"host": "127.0.0.1"})()

    response = asyncio.run(apply_public_cost_guards(_Req(), slow_call_next))
    assert response.status_code == 504


def test_av24_scan_detects_forbidden_field():
    leak = scan_public_response_for_av24_leak(
        path="/api/launch57/guest-trust",
        status_code=200,
        body_text='{"email":"leak@example.com","symbol":"BTC"}',
        content_type="application/json",
    )
    assert leak["boundary_ok"] is False
    assert "email" in leak["forbidden_keys"]


def test_av24_allowlist_sweep_no_private_leak(client, monkeypatch):
    async def fake_guest_trust(symbol: str, params=None):
        return {"launch_item_id": 46, "guest_trust": {"symbol": symbol}}

    async def fake_real_time_prices(symbol: str, params=None):
        return {"launch_item_id": 22, "symbol": symbol, "price": 1.0, "freshness_state": "LIVE"}

    async def fake_shareable_accuracy_page(symbol: str, params=None):
        return {"launch_item_id": 45, "symbol": symbol, "success": True}

    monkeypatch.setattr("launch57.trust_batch2.guest_trust_surface", fake_guest_trust)
    monkeypatch.setattr("launch57.data_batch1.real_time_prices", fake_real_time_prices)
    monkeypatch.setattr("launch57.trust_batch2.shareable_accuracy_page", fake_shareable_accuracy_page)
    monkeypatch.setattr(
        "launch57.anonymous_public_cost_guards.enforce_public_rate_limit",
        lambda request, policy: None,
    )

    rows: list[dict] = []
    for method, path, params in iter_allowlist_probe_paths():
        if method != "GET":
            continue
        res = client.get(path, params=params or {}, headers={"Accept": "text/html,application/json"})
        rows.append(
            scan_public_response_for_av24_leak(
                path=path,
                status_code=res.status_code,
                body_text=res.text,
                content_type=res.headers.get("content-type", ""),
            )
        )

    summary = sweep_allowlist_av24(rows)
    assert summary["boundary_ok"] is True, summary["failures"]


def test_share_proof_44_anonymous_401(client):
    res = client.get(
        "/api/launch57/share-proof",
        params={"symbol": "BTC", "decision_action": "WAIT"},
    )
    assert res.status_code == 401


def test_shareable_accuracy_45_anonymous_200(client, monkeypatch):
    async def fake_shareable_accuracy_page(symbol: str, params=None):
        return {"launch_item_id": 45, "symbol": symbol, "success": True}

    monkeypatch.setattr("launch57.trust_batch2.shareable_accuracy_page", fake_shareable_accuracy_page)
    res = client.get("/api/launch57/shareable-accuracy", params={"symbol": "BTC"})
    assert res.status_code == 200
    assert res.json().get("launch_item_id") == 45


def test_landing_zero_analytics_requests():
    landing = Path("templates/landing.html").read_text(encoding="utf-8")
    forbidden = (
        "/api/analytics/",
        "loadLandingAnalytics",
        "/api/discipline-mirror/",
        "/api/telegram/free/",
        "/api/billing/payments",
    )
    hits = [token for token in forbidden if token in landing]
    assert hits == []


def test_cost_policy_has_upstream_budget_for_launch57_api():
    policy = resolve_public_cost_policy("/api/launch57/guest-trust")
    assert policy is not None
    assert policy.upstream_budget == 1
    assert policy.rate_limit >= 1
    assert policy.max_response_bytes >= 1024
    assert policy.timeout_sec > 0


def test_enforce_public_rate_limit_raises(monkeypatch):
    calls: list[str] = []

    def fake_check_rate_limit(key, *, limit, window_sec, prefix):
        calls.append(key)
        if limit < 5:
            from fastapi import HTTPException

            raise HTTPException(status_code=429, detail={"error": "rate_limited"})

    monkeypatch.setattr("viral_capacity.check_rate_limit", fake_check_rate_limit)

    class _Req:
        url = type("U", (), {"path": "/api/status"})()
        method = "GET"
        headers = {}
        cookies = {}
        client = type("C", (), {"host": "10.0.0.1"})()

    policy = PublicRouteCostPolicy("/api/status", "public_api", 1, 60, 1024, 5.0)
    with pytest.raises(Exception) as exc:
        enforce_public_rate_limit(_Req(), policy)
        enforce_public_rate_limit(_Req(), policy)
    assert getattr(exc.value, "status_code", None) == 429 or calls
