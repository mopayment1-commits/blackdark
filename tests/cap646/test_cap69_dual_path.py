"""#69 SSOT contract — official batch02 spine vs inventory parallel path (ISO/IEC 29119-4)."""

from __future__ import annotations

import pytest

SYMBOLS = ["BTC", "ETH", "SOL", "AVAX", "DOGE"]


@pytest.mark.parametrize("symbol", SYMBOLS)
@pytest.mark.asyncio
async def test_cap69_official_vs_parallel_match(symbol: str):
    from cap646.parallel_invoke import invoke_inventory_backend
    from cap646.runtime import execute_capability

    params = {"symbol": symbol, "kind": "spot_futures"}
    official = await execute_capability(69, params=params, skip_entitlement=True)
    parallel = await invoke_inventory_backend("cap646.batch02_production.cap_069", params=params)
    assert official.get("surface") == parallel.get("surface") == "cross_domain_decision_intelligence_layer"
    assert bool(official.get("success")) == bool(parallel.get("success"))


@pytest.mark.asyncio
async def test_cap69_onchain_facade_delegates_to_batch02():
    from cap646.handlers.onchain import handle_onchain_capability
    from cap646.runtime import execute_capability

    params = {"symbol": "BTC"}
    official = await execute_capability(69, params=params, skip_entitlement=True)
    facade = await handle_onchain_capability(69, params=params)
    assert facade.get("surface") == official.get("surface")
    assert facade.get("production_spine") == "batch02"
