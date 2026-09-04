"""Batch05 upstream reliability modes — HTTP 429/5xx, retry exhaustion, recovery (local fault injection)."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest


def _mock_aiohttp_status(monkeypatch, module, status: int) -> None:
    class MockResponse:
        def __init__(self, code: int) -> None:
            self.status = code

        async def json(self) -> dict:
            return {}

        async def __aenter__(self) -> MockResponse:
            return self

        async def __aexit__(self, *_args: object) -> None:
            return None

    class MockSession:
        def __init__(self, *_a: object, **_k: object) -> None:
            pass

        def get(self, *_a: object, **_k: object) -> MockResponse:
            return MockResponse(status)

        async def __aenter__(self) -> MockSession:
            return self

        async def __aexit__(self, *_args: object) -> None:
            return None

    monkeypatch.setattr(module.aiohttp, "ClientSession", MockSession)


@pytest.mark.asyncio
async def test_reliability_http_429_stale_fallback_local(monkeypatch):
    """CoinGecko 429 → stale cache fallback (batch05 #202 dependency chain)."""
    import time

    from blackdark.ingestion import coingecko_connector as cg

    cg._CACHE.clear()
    cg._RATE_LIMIT_UNTIL = 0.0
    cg._CACHE["path?{}"] = (time.time() - 999_999, {"ok": True, "data": {"bitcoin": {"usd": 1}}})

    _mock_aiohttp_status(monkeypatch, cg, 429)
    result = await cg._request("/simple/price", cache_key="path?{}")
    assert result.get("ok") is True
    assert result.get("stale_fallback") is True
    assert result.get("rate_limited") is True


@pytest.mark.asyncio
async def test_reliability_http_429_fail_closed_local(monkeypatch):
    """CoinGecko 429 without cache → fail-closed degraded payload."""
    from blackdark.ingestion import coingecko_connector as cg

    cg._CACHE.clear()
    cg._RATE_LIMIT_UNTIL = 0.0

    _mock_aiohttp_status(monkeypatch, cg, 429)
    result = await cg._request("/simple/price", cache_key="missing_key")
    assert result.get("ok") is False
    assert result.get("error") == "rate_limited"


@pytest.mark.asyncio
async def test_reliability_http_5xx_stale_fallback_local(monkeypatch):
    """HTTP 503 → stale cache fallback."""
    import time

    from blackdark.ingestion import coingecko_connector as cg

    cg._CACHE.clear()
    cg._RATE_LIMIT_UNTIL = 0.0
    cg._CACHE["stale_503"] = (time.time() - 999_999, {"ok": True, "data": {"x": 1}})

    _mock_aiohttp_status(monkeypatch, cg, 503)
    result = await cg._request("/markets", cache_key="stale_503")
    assert result.get("ok") is True
    assert result.get("stale_fallback") is True
    assert result.get("http_status") == 503


@pytest.mark.asyncio
async def test_reliability_http_5xx_fail_closed_local(monkeypatch):
    """HTTP 500 without cache → fail-closed."""
    from blackdark.ingestion import coingecko_connector as cg

    cg._CACHE.clear()
    cg._RATE_LIMIT_UNTIL = 0.0

    _mock_aiohttp_status(monkeypatch, cg, 500)
    result = await cg._request("/markets", cache_key="no_cache_500")
    assert result.get("ok") is False
    assert "http_500" in str(result.get("error"))


@pytest.mark.asyncio
async def test_reliability_retry_exhaustion_local(monkeypatch):
    """Redis connect retries exhaust → fail-closed (non-strict mode)."""
    import redis_price_cache as rpc

    rpc._client = None
    rpc._connected = False

    async def _never_connect(**_kwargs: object) -> None:
        return None

    monkeypatch.setattr(rpc, "_redis", _never_connect)
    monkeypatch.setattr(rpc, "strict_mode", lambda: False)

    ok = await rpc.ensure_redis_ready(retries=3, delay_sec=0)
    assert ok is False


@pytest.mark.asyncio
async def test_reliability_recovery_after_dependency_restored_local(monkeypatch):
    """Batch05 #201: upstream failure then recovery on subsequent execute."""
    from cap646.runtime import execute_capability

    calls = {"n": 0}

    async def _footprint(asset: str = "BTC") -> dict:
        calls["n"] += 1
        if calls["n"] == 1:
            raise ConnectionError("simulated upstream unavailable")
        return {
            "asset": asset.upper(),
            "timestamp": "2026-09-04T00:00:00+00:00",
            "top_of_book": [{"exchange": "binance", "bid": 1.0, "ask": 1.1, "mid": 1.05, "spread_bps": 1.0}],
            "depth_levels": [],
            "aggregate_bid_depth_5": 1.0,
            "aggregate_ask_depth_5": 1.0,
            "order_flow_delta": 0.0,
            "type": "multi_venue_footprint",
            "success": True,
        }

    monkeypatch.setattr("bd_platform.footprint_analytics.footprint_snapshot", _footprint)

    failed = await execute_capability(201, params={"symbol": "BTC"}, skip_entitlement=True)
    assert failed.get("success") is False

    recovered = await execute_capability(201, params={"symbol": "BTC"}, skip_entitlement=True)
    assert recovered.get("success") is True
    assert recovered.get("surface") == "network_growth_intelligence"


@pytest.mark.asyncio
async def test_reliability_batch05_holder_path_429_degraded_local(monkeypatch):
    """Batch05 #202 path tolerates upstream JSON failure without crash."""
    from unittest.mock import patch

    from cap646.runtime import execute_capability

    with patch(
        "bd_platform.free_integrations._get_json",
        new=AsyncMock(return_value=None),
    ), patch(
        "bd_platform.free_market_data.binance_futures_snapshot",
        new=AsyncMock(return_value={"long_short_ratio": None, "funding_rate_pct": None}),
    ):
        result = await execute_capability(202, params={"symbol": "BTC"}, skip_entitlement=True)
    assert result.get("success") is True
    assert result.get("surface") == "supply_distribution_intelligence"
