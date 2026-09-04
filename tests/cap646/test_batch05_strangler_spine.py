"""Tests for Batch05 Strangler spine — catalog-correct wiring."""

from __future__ import annotations

import inspect

import pytest

from cap646.batch05_dedicated import EXPECTED_SURFACE, execute
from cap646.batch05_strangler_spine import STRANGLER_BUILDERS, STRANGLER_IMPLEMENTED_IDS

WAVE1_IDS = [201, 202, 203, 204]
WAVE2A_IDS = [205]
WAVE2B_IDS = [207, 208, 209, 210, 211, 213, 215, 216]
ALL_STRANGLER_IDS = sorted(STRANGLER_IMPLEMENTED_IDS)


@pytest.mark.parametrize("capability_id", ALL_STRANGLER_IDS)
def test_strangler_builder_registered(capability_id: int):
    assert capability_id in STRANGLER_BUILDERS
    assert STRANGLER_BUILDERS[capability_id].__name__.startswith("build_")


@pytest.mark.parametrize("capability_id", ALL_STRANGLER_IDS)
@pytest.mark.asyncio
async def test_strangler_builder_returns_catalog_payload(capability_id: int):
    builder = STRANGLER_BUILDERS[capability_id]
    sig = inspect.signature(builder)
    kwargs: dict = {"symbol": "BTC", "params": {"tier": "pro"}}
    if "seed" in sig.parameters:
        from cap646.dedicated_common import seed

        kwargs["seed"] = seed()
    payload = await builder(**kwargs)
    root = EXPECTED_SURFACE[capability_id]
    assert payload["ok"] is True
    assert payload["feature_ref"] == capability_id
    assert payload["catalog_goal"] == root
    assert payload.get("miswire_remediation") == "STRANGLER_IMPLEMENTED"
    assert payload["latency_ms"] >= 0
    assert payload["latency_ms"] < 5000


@pytest.mark.parametrize("capability_id", ALL_STRANGLER_IDS)
@pytest.mark.asyncio
async def test_strangler_runtime_dispatch(capability_id: int):
    result = await execute(
        capability_id,
        params={
            "symbol": "BTC",
            "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
            "tier": "pro",
        },
    )
    root = EXPECTED_SURFACE[capability_id]
    assert result["success"] is True
    assert result["surface"] == root
    assert result[root]["feature_ref"] == capability_id
    assert result[root].get("miswire_remediation") == "STRANGLER_IMPLEMENTED"


@pytest.mark.asyncio
async def test_cap205_open_interest_binance_futures():
    result = await execute(205, params={"symbol": "BTC"})
    payload = result["open_interest_intelligence"]
    assert payload["source"] == "free_market_data.binance_futures_snapshot"
    assert "open_interest_usd" in payload


@pytest.mark.asyncio
async def test_cap232_reused_link_to_strangler_205():
    result = await execute(232, params={"symbol": "BTC"})
    assert result["classification"] == "REUSED-LINK"
    assert result["catalog_link"]["canonical_capability_id"] == 205
    assert result["catalog_link"]["binding"] == "cap646/batch05_strangler_spine.py::build_open_interest_205"
    assert result["open_interest_intelligence"]["miswire_remediation"] == "STRANGLER_IMPLEMENTED"


@pytest.mark.parametrize("capability_id,source", [
    (207, "market_context.probe_price_sources+free_market_data.binance_futures_snapshot"),
    (208, "free_market_data.binance_futures_snapshot"),
    (209, "cap646.fallbacks.resolve_ohlcv_closes"),
    (210, "bd_platform.market_rankings.market_rankings"),
    (211, "bd_platform.market_rankings.market_rankings"),
    (213, "footprint_analytics.footprint_snapshot"),
    (215, "onchain_defi_sources_layer.ingest_reddit_sentiment_208"),
    (216, "market_rankings+onchain_defi_sources_layer.ingest_reddit_sentiment_208"),
])
@pytest.mark.asyncio
async def test_wave2b_catalog_sources(capability_id: int, source: str):
    result = await execute(capability_id, params={"symbol": "BTC"})
    root = EXPECTED_SURFACE[capability_id]
    assert result[root]["source"] == source
