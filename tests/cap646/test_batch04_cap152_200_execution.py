"""Capability-specific execution tests for Batch04 #152–#200."""

from __future__ import annotations

import time

import pytest

from cap646.batch04_dedicated import BATCH04_DEDICATED_IDS, EXPECTED_SURFACE

BLOCKER_IDS = frozenset({159, 183})
HERO_DOMAIN_SAMPLE = frozenset({152, 154, 164, 176, 192, 200})


@pytest.mark.parametrize("capability_id", sorted(BATCH04_DEDICATED_IDS - BLOCKER_IDS))
@pytest.mark.asyncio
async def test_batch04_domain_payload_not_stub(capability_id: int):
    from cap646.runtime import execute_capability

    result = await execute_capability(
        capability_id,
        skip_entitlement=True,
        params={"symbol": "BTC", "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb", "tier": "pro"},
    )
    root = EXPECTED_SURFACE[capability_id]
    assert result["success"] is True, result
    payload = result[root]
    assert payload["feature_ref"] == capability_id
    assert payload["ok"] is True
    keys = set(payload.keys()) - {"ok", "feature_ref", "symbol", "catalog_goal"}
    assert len(keys) >= 1, f"#{capability_id} must have domain fields beyond stub template"


@pytest.mark.asyncio
async def test_cap159_blocker_not_complete():
    from cap646.runtime import execute_capability

    result = await execute_capability(159, skip_entitlement=True, params={"symbol": "BTC", "tier": "pro"})
    assert result["success"] is True
    assert result.get("blocker") == "BLOCKER-159-103"
    assert result["api_data_platform"]["canonical_status"] == "OVERLAP-PARTIAL"


@pytest.mark.asyncio
async def test_cap183_distinct_whale_not_reused():
    from cap646.runtime import execute_capability

    result = await execute_capability(
        183,
        skip_entitlement=True,
        params={"symbol": "BTC", "amount_usd": 2_000_000, "flow_direction": "exchange_inflow", "tier": "pro"},
    )
    assert result["success"] is True
    assert result["whale_transaction"]["risk_score"] >= 0
    assert result["whale_transaction"]["distinct_from_130"]["reused_link"] is False
    assert result.get("catalog_link") is None


@pytest.mark.parametrize("capability_id", sorted(HERO_DOMAIN_SAMPLE))
@pytest.mark.asyncio
async def test_batch04_hero_domain_fields(capability_id: int):
    from cap646.runtime import execute_capability

    result = await execute_capability(capability_id, skip_entitlement=True, params={"symbol": "ETH", "tier": "pro"})
    root = EXPECTED_SURFACE[capability_id]
    payload = result[root]
    assert payload["symbol"] == "ETH"


@pytest.mark.parametrize("capability_id", [151, 194, 200])
@pytest.mark.asyncio
async def test_batch04_performance_under_threshold(capability_id: int):
    from cap646.runtime import execute_capability

    start = time.perf_counter()
    result = await execute_capability(capability_id, skip_entitlement=True, params={"symbol": "BTC", "tier": "pro"})
    elapsed_ms = (time.perf_counter() - start) * 1000
    assert result["success"] is True
    assert elapsed_ms < 2000, f"#{capability_id} took {elapsed_ms:.1f}ms"
