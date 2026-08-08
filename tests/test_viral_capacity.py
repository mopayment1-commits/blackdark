"""Viral launch capacity protections."""

from __future__ import annotations

import os

import pytest
from fastapi import HTTPException


def test_rate_limit_trips_in_memory(monkeypatch):
    monkeypatch.delenv("REDIS_URL", raising=False)
    from viral_capacity import check_rate_limit

    key = "unit-test-burst"
    for _ in range(5):
        check_rate_limit(key, limit=5, window_sec=60, prefix="test")
    with pytest.raises(HTTPException) as exc:
        check_rate_limit(key, limit=5, window_sec=60, prefix="test")
    assert exc.value.status_code == 429


def test_inflight_shed():
    from viral_capacity import begin_inflight, end_inflight, inflight_count

    # Drain any leftover
    while inflight_count() > 0:
        end_inflight()
    assert begin_inflight() is True
    assert inflight_count() >= 1
    end_inflight()


def test_quick_cache_roundtrip():
    from viral_capacity import quick_cache_get, quick_cache_set

    quick_cache_set("BTC", "en", "beginner", {"symbol": "BTC", "ok": True})
    hit = quick_cache_get("BTC", "en", "beginner")
    assert hit is not None
    assert hit["viral_cache"] == "hit"
    assert hit["ok"] is True


def test_viral_readiness_honesty(monkeypatch):
    monkeypatch.setenv("SOFT_LAUNCH", "true")
    monkeypatch.setenv("VIRAL_MODE", "true")
    monkeypatch.setenv("WEB_CONCURRENCY", "1")
    from viral_capacity import viral_readiness_report

    report = viral_readiness_report()
    assert report["honesty"]["proven_signed_load_test"] is False
    assert report["viral_codepath_ready"] is False  # soft launch + 1 worker
    assert "VIRAL_LAUNCH_CAPACITY" in report["playbook"]


def test_scale_report_links_viral():
    from scale_readiness import scale_readiness_report

    report = scale_readiness_report()
    assert report["viral"]["readiness_api"] == "/api/viral/readiness"


@pytest.mark.asyncio
async def test_viral_readiness_route():
    from httpx import ASGITransport, AsyncClient

    from dashboard import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/api/viral/readiness")
        assert r.status_code == 200
        body = r.json()
        assert "limits" in body
        assert body["honesty"]["code_protects_under_spike"] is True


@pytest.mark.asyncio
async def test_health_not_rate_limited_under_burst():
    from httpx import ASGITransport, AsyncClient

    from dashboard import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        codes = []
        for _ in range(30):
            r = await client.get("/health/live")
            codes.append(r.status_code)
        assert all(c == 200 for c in codes)
