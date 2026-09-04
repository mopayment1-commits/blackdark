"""Tests for Batch04 Strangler spine — catalog-correct wiring."""

from __future__ import annotations

import pytest

from cap646.batch04_strangler_spine import STRANGLER_BUILDERS

STRANGLER_IDS = sorted(STRANGLER_BUILDERS)


@pytest.mark.parametrize("capability_id", STRANGLER_IDS)
@pytest.mark.asyncio
async def test_strangler_builder_returns_ok(capability_id: int):
    builder = STRANGLER_BUILDERS[capability_id]
    import inspect

    kwargs: dict = {"symbol": "BTC"}
    sig = inspect.signature(builder)
    if "seed" in sig.parameters:
        from cap646.dedicated_common import seed

        kwargs["seed"] = seed()
    if "params" in sig.parameters:
        kwargs["params"] = {"tier": "pro", "exchange": "binance"}
    payload = await builder(**kwargs)
    assert payload["ok"] is True
    assert payload["feature_ref"] == capability_id
    assert "latency_ms" in payload
    assert payload["latency_ms"] >= 0


@pytest.mark.parametrize("capability_id", STRANGLER_IDS)
@pytest.mark.asyncio
async def test_strangler_runtime_dispatch(capability_id: int):
    from cap646.batch04_dedicated import EXPECTED_SURFACE, execute

    result = await execute(
        capability_id,
        params={"symbol": "BTC", "tier": "pro", "exchange": "binance"},
    )
    root = EXPECTED_SURFACE[capability_id]
    assert result["success"] is True
    assert result["surface"] == root
    assert result[root]["feature_ref"] == capability_id


@pytest.mark.asyncio
async def test_cap198_dormancy_proxy_disclaimer():
    from cap646.batch04_strangler_spine import build_dormancy_proxy_198

    payload = await build_dormancy_proxy_198(symbol="BTC", params={})
    assert payload["metric_type"] == "PARTIAL_MISNAMED"
    assert "Glassnode" in payload["accuracy_disclaimer"]
    assert payload["catalog_display_name"] == "On-Chain Dormancy Proxy"


@pytest.mark.asyncio
async def test_cap199_invested_age_proxy_disclaimer():
    from cap646.batch04_strangler_spine import build_invested_age_proxy_199

    payload = await build_invested_age_proxy_199(symbol="BTC", params={})
    assert payload["metric_type"] == "PARTIAL_MISNAMED"
    assert "MDIA" in payload["accuracy_disclaimer"]
    assert payload["catalog_display_name"] == "Invested-Age Proxy"


@pytest.mark.asyncio
async def test_cap165_defillama_free_tier():
    from cap646.batch04_strangler_spine import build_fundraising_momentum_165

    payload = await build_fundraising_momentum_165(symbol="BTC", params={})
    assert payload["source"] == "defillama_raises_free_tier"
    assert "free_tier" in payload.get("accuracy_disclaimer", "").lower() or payload.get("free_tier_only")


@pytest.mark.asyncio
async def test_cap165_defillama_raises_mock_documents_api_wiring(monkeypatch):
    """Documented mock for DeFiLlama /raises — live endpoint returns HTTP 402 (paid plan) in this env."""

    sample_raises = [
        {"name": "Bitcoin Infrastructure Co", "symbol": "BTC", "amount": 12_000_000},
        {"name": "Ethereum L2 Labs", "symbol": "ETH", "amount": 8_000_000},
        {"name": "Unrelated Protocol", "symbol": "UNI", "amount": 3_000_000},
    ]

    async def _mock_raises_funding_rounds(*, limit: int = 50):
        rows = sample_raises[:limit]
        return {
            "source": "defillama",
            "raises": rows,
            "count": len(rows),
            "free_tier": True,
        }

    monkeypatch.setattr(
        "bd_platform.free_tier_capabilities.raises_funding_rounds",
        _mock_raises_funding_rounds,
    )

    from cap646.batch04_strangler_spine import build_fundraising_momentum_165

    payload = await build_fundraising_momentum_165(symbol="BTC", params={"limit": 5})
    # Fixture: 1 BTC-related row of 3 → min(100, 1*20 + 3*0.5) = 21.5
    expected_momentum = 21.5
    assert payload["ok"] is True
    assert payload["source"] == "defillama_raises_free_tier"
    assert payload["total_raises_tracked"] == 3
    assert len(payload["fundraising_rounds"]) == 1
    assert payload["fundraising_rounds"][0]["symbol"] == "BTC"
    assert payload["momentum_score"] == expected_momentum
