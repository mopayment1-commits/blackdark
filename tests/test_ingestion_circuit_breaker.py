"""Ingestion-layer circuit breaker integration (#32) — fail-closed on external API calls."""

from __future__ import annotations

import pytest

from blackdark.data import circuit_breaker as cb
from blackdark.ingestion.connector_cache import IngestionCache


@pytest.fixture(autouse=True)
def _clear_circuits():
    cb._circuits.clear()
    yield
    cb._circuits.clear()


def test_circuit_open_blocks_live_call_fail_closed():
    cache = IngestionCache()
    key = "test:cb:block"
    for i in range(3):
        cb.record_failure("test_upstream", f"fail-{i}")
    assert cb.is_open("test_upstream") is True

    blocked = cache._circuit_blocked("test_upstream", key)
    assert blocked is not None
    assert blocked.get("ok") is False
    assert blocked.get("circuit_open") is True
    assert blocked.get("fail_closed") is True


def test_circuit_open_allows_stale_cache_only():
    cache = IngestionCache()
    key = "test:cb:stale"
    cache.set(key, {"ok": True, "data": "cached", "cache_hit": False})
    for i in range(3):
        cb.record_failure("stale_src", f"fail-{i}")

    blocked = cache._circuit_blocked("stale_src", key)
    assert blocked is not None
    assert blocked.get("ok") is True
    assert blocked.get("stale_fallback") is True
    assert blocked.get("circuit_open") is True
    assert blocked.get("fail_closed") is True


@pytest.mark.asyncio
async def test_http_get_records_failure_and_opens_circuit(monkeypatch):
    cache = IngestionCache()

    class _FakeResp:
        status = 500

        async def text(self):
            return ""

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_a):
            return None

    class _FakeSession:
        def __init__(self, *_a, **_k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_a):
            return None

        def get(self, *_a, **_k):
            return _FakeResp()

    import aiohttp

    monkeypatch.setattr(aiohttp, "ClientSession", _FakeSession)

    for _ in range(3):
        resp = await cache.http_get(
            "https://example.invalid/test",
            cache_key="cb:http",
            ttl=60,
            source_slug="cb_test_src",
        )
        assert resp.get("ok") is False
        assert resp.get("fail_closed") is True

    assert cb.is_open("cb_test_src") is True

    resp = await cache.http_get(
        "https://example.invalid/test",
        cache_key="cb:http",
        ttl=60,
        source_slug="cb_test_src",
    )
    assert resp.get("circuit_open") is True


@pytest.mark.asyncio
async def test_fetch_single_source_skips_when_circuit_open(monkeypatch):
    import aiohttp

    from data_sources_registry import DataSourceSpec
    from ingestion_fetchers import fetch_single_source

    cb._circuits.clear()
    for i in range(3):
        cb.record_failure("test_source_cb", f"f{i}")

    async def _noop(*_a, **_k):
        return None

    monkeypatch.setattr("ingestion_fetchers.upsert_ingestion_health", _noop)

    spec = DataSourceSpec(
        source_id="test_source_cb",
        category="prices",
        name="Test CB",
        fetch_kind="rest",
        url="https://example.invalid",
        interval_seconds=0,
        env_key=None,
    )

    timeout = aiohttp.ClientTimeout(total=1)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        ok = await fetch_single_source(session, spec)
    assert ok is False


def test_chaos_gas_oracle_fail_closed(monkeypatch):
    """Regression: gas oracle must not invent prices on failure."""
    import gas_oracle

    gas_oracle._CACHE.clear()
    gas_oracle._CACHE_TS.clear()

    async def _boom(*_a, **_k):
        return None

    monkeypatch.setattr(gas_oracle, "_fetch_eth_gas_gwei", _boom)

    async def _check():
        await gas_oracle.refresh_gas_cache(chains=("ethereum",))
        return await gas_oracle.get_swap_gas_usd("ethereum")

    import asyncio

    result = asyncio.run(_check())
    assert result is None
