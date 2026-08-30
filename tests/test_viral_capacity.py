from __future__ import annotations

"""Viral launch capacity protections."""

from pathlib import Path

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

    # Drain any leftover local slots
    for _ in range(50):
        if inflight_count() <= 0:
            break
        end_inflight("memory")
    ok, token = begin_inflight()
    assert ok is True
    assert token in {"memory", "redis"}
    assert inflight_count() >= 1
    end_inflight(token)


def test_quick_cache_roundtrip():
    from viral_capacity import quick_cache_get, quick_cache_set

    quick_cache_set("BTC", "en", "beginner", {"symbol": "BTC", "ok": True})
    hit = quick_cache_get("BTC", "en", "beginner")
    assert hit is not None
    assert hit["viral_cache"] == "hit"
    assert hit["ok"] is True


def test_quick_cache_graceful_without_redis_url(monkeypatch):
    import config
    import viral_capacity as vc

    monkeypatch.delenv("REDIS_URL", raising=False)
    monkeypatch.setattr(config, "REDIS_URL", "", raising=False)
    vc._redis = None
    vc._redis_fail_until = 0.0
    vc._quick_cache.clear()

    vc.quick_cache_set("ETH", "en", "beginner", {"symbol": "ETH", "ok": True})
    hit = vc.quick_cache_get("ETH", "en", "beginner")
    assert hit is not None
    assert hit["viral_cache"] == "hit"
    assert vc.cache_backend() == "memory"


def test_quick_cache_survives_transient_redis_outage(monkeypatch):
    import config
    import viral_capacity as vc

    redis_url = (getattr(config, "REDIS_URL", "") or "redis://127.0.0.1:6379/0").strip()
    if not redis_url:
        pytest.skip("REDIS_URL not configured")
    monkeypatch.setenv("REDIS_URL", redis_url)
    monkeypatch.setattr(config, "REDIS_URL", redis_url, raising=False)
    vc._redis = None
    vc._redis_fail_until = 0.0
    vc._quick_cache.clear()

    vc.quick_cache_set("SOL", "en", "beginner", {"symbol": "SOL", "ok": True})
    assert vc.cache_backend() == "redis"

    client = vc._redis_client()
    assert client is not None
    original_get = client.get

    def _broken_get(*args, **kwargs):
        raise ConnectionError("simulated redis outage")

    monkeypatch.setattr(client, "get", _broken_get)
    hit = vc.quick_cache_get("SOL", "en", "beginner")
    assert hit is not None
    assert hit["viral_cache"] == "hit"
    assert hit["ok"] is True

    monkeypatch.setattr(client, "get", original_get)
    vc._drop_redis_client()
    remote = vc._redis_client()
    assert remote is not None
    raw = remote.get("bd:viral:qcache:SOL:en:beginner")
    assert raw is not None


def test_viral_readiness_honesty(monkeypatch):
    monkeypatch.setenv("SOFT_LAUNCH", "true")
    monkeypatch.setenv("VIRAL_MODE", "true")
    monkeypatch.setenv("WEB_CONCURRENCY", "1")
    monkeypatch.setenv("WEB_REPLICAS", "1")
    # Isolate from any deposited signed-capacity artifact on disk.
    monkeypatch.setattr(
        "institutional_assurance.get_signed_capacity",
        lambda: None,
        raising=False,
    )
    from viral_capacity import viral_readiness_report

    report = viral_readiness_report()
    assert report["honesty"]["proven_signed_load_test"] is False
    assert report["viral_codepath_ready"] is False  # soft launch + 1 worker
    assert "VIRAL_LAUNCH_CAPACITY" in report["playbook"]


def test_effective_parallelism_replicas(monkeypatch):
    monkeypatch.setenv("WEB_CONCURRENCY", "1")
    monkeypatch.setenv("WEB_REPLICAS", "2")
    from viral_capacity import effective_parallelism

    p = effective_parallelism()
    assert p["parallelism"] == 2
    assert p["replicas"] == 2


def test_scale_report_links_viral():
    from scale_readiness import scale_readiness_report

    report = scale_readiness_report()
    assert report["viral"]["readiness_api"] == "/api/viral/readiness"
    assert "parallelism" in report


def test_production_guard_viral_ha_requires_redis(monkeypatch):
    monkeypatch.setenv("ENV", "production")
    monkeypatch.delenv("SOFT_LAUNCH", raising=False)
    monkeypatch.setenv("VIRAL_MODE", "true")
    monkeypatch.setenv("SERVICE_MODE", "web")
    monkeypatch.setenv("SECRETS_MASTER_KEY", "x" * 32)
    monkeypatch.setenv("SESSION_TOKEN_PEPPER", "y" * 16)
    monkeypatch.setenv("ADMIN_API_KEY", "z" * 24)
    monkeypatch.setenv("LEMON_SQUEEZY_CHECKOUT_PRO", "https://example.com/c")
    monkeypatch.setenv("LEMON_SQUEEZY_WEBHOOK_SECRET", "whsec")
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@h/db")
    monkeypatch.setenv("WEB_CONCURRENCY", "1")
    monkeypatch.setenv("WEB_REPLICAS", "1")
    monkeypatch.delenv("REDIS_URL", raising=False)
    import config

    monkeypatch.setattr(config, "DATABASE_URL", "postgresql://u:p@h/db")
    monkeypatch.setattr(config, "REDIS_URL", "")
    monkeypatch.setattr(config, "SERVICE_BUS_LOCAL", True)
    monkeypatch.setattr(config, "SERVICE_MODE", "web")

    from production_guard import evaluate_production_guard

    report = evaluate_production_guard()
    assert report["viral_ha_enforced"] is True
    assert "redis_shared_bus" in report["required_failures"]
    assert "viral_multi_instance" in report["required_failures"]


def test_run_service_honors_web_concurrency():
    src = Path("run_service.py").read_text(encoding="utf-8")
    assert "WEB_CONCURRENCY" in src
    assert "--workers" in src


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
async def test_health_viral_route():
    from httpx import ASGITransport, AsyncClient

    from dashboard import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/health/viral")
        assert r.status_code in {200, 503}
        body = r.json()
        assert body["probe"] == "viral"
        assert "parallelism" in body


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


def test_redis_negative_cache_avoids_repeat_connect_penalty(monkeypatch):
    """Dead REDIS_URL must not re-pay connect timeout on every request."""
    import time

    import config
    import viral_capacity as vc

    dead = "redis://127.0.0.1:1/0"
    monkeypatch.setenv("REDIS_URL", dead)
    monkeypatch.setattr(config, "REDIS_URL", dead, raising=False)
    monkeypatch.setattr(vc, "_REDIS_CONNECT_TIMEOUT", 0.05)
    monkeypatch.setattr(vc, "_REDIS_SOCKET_TIMEOUT", 0.05)
    monkeypatch.setattr(vc, "_REDIS_NEG_TTL_SEC", 30.0)
    vc._redis = None
    vc._redis_fail_until = 0.0

    t0 = time.perf_counter()
    assert vc._redis_client() is None
    first_ms = (time.perf_counter() - t0) * 1000
    assert vc._redis_fail_until > time.time()

    t0 = time.perf_counter()
    assert vc._redis_client() is None
    second_ms = (time.perf_counter() - t0) * 1000
    # Second call must be near-instant (negative cache), not another socket wait.
    assert second_ms < 5.0, f"second={second_ms:.2f}ms first={first_ms:.2f}ms"
