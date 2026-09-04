"""Tests for Batch05 Strangler spine — catalog-correct wiring (wave 1: 201–204)."""

from __future__ import annotations

import inspect

import pytest

from cap646.batch05_dedicated import EXPECTED_SURFACE, execute
from cap646.batch05_strangler_spine import STRANGLER_BUILDERS, STRANGLER_IMPLEMENTED_IDS

WAVE1_IDS = sorted(STRANGLER_IMPLEMENTED_IDS)


@pytest.mark.parametrize("capability_id", WAVE1_IDS)
def test_strangler_builder_registered(capability_id: int):
    assert capability_id in STRANGLER_BUILDERS
    assert STRANGLER_BUILDERS[capability_id].__name__.startswith("build_")


@pytest.mark.parametrize("capability_id", WAVE1_IDS)
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


@pytest.mark.parametrize("capability_id", WAVE1_IDS)
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
async def test_cap201_footprint_network_growth_fields():
    result = await execute(201, params={"symbol": "BTC"})
    payload = result["network_growth_intelligence"]
    assert payload["source"] == "footprint_analytics.footprint_snapshot"
    assert "order_flow_delta" in payload or "footprint" in payload


@pytest.mark.asyncio
async def test_cap202_supply_distribution_holder_metrics():
    result = await execute(202, params={"symbol": "BTC"})
    payload = result["supply_distribution_intelligence"]
    assert "holder_metrics" in payload
    assert payload["source"]


@pytest.mark.asyncio
async def test_cap203_dex_trading_pairs():
    result = await execute(203, params={"symbol": "BTC"})
    payload = result["dex_trading_intelligence"]
    assert payload["source"] == "onchain_hub.dexscreener_pairs"
    assert "dex_pairs" in payload


@pytest.mark.asyncio
async def test_cap204_defi_protocol_bsc_activity():
    result = await execute(
        204,
        params={"symbol": "BTC", "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"},
    )
    payload = result["defi_protocol_activity_intelligence"]
    assert payload["chain"] == "BSC"
    assert payload["source"] == "onchain_defi_sources_layer.ingest_bscscan_204"
