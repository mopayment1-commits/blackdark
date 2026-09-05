"""Dedicated-backend tests for Batch 01 formerly-generic capabilities."""

from __future__ import annotations

import pytest

from cap646.batch01_dedicated import BATCH01_DEDICATED_IDS, EXPECTED_SURFACE, GENERIC_SURFACES
from cap646.batch05_dedicated import BATCH05_REUSED_LINK_BATCH01_IDS

# #214/#245 route via batch05 facade at runtime (MECE overlap) — test batch01 spine via direct execute.
RUNTIME_BATCH01_IDS = BATCH01_DEDICATED_IDS - BATCH05_REUSED_LINK_BATCH01_IDS


@pytest.mark.parametrize("capability_id", sorted(RUNTIME_BATCH01_IDS))
@pytest.mark.asyncio
async def test_batch01_dedicated_surface_and_success(capability_id: int):
    from cap646.runtime import execute_capability

    params = {
        "symbol": "BTC",
        "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
        "email": "batch01-dedicated@blackdark.local",
        "tier": "pro",
    }
    result = await execute_capability(capability_id, skip_entitlement=True, params=params)
    assert result["success"] is True, result
    assert result["surface"] == EXPECTED_SURFACE[capability_id], result
    generic_misroute = result["surface"] in GENERIC_SURFACES and result["surface"] != EXPECTED_SURFACE[capability_id]
    assert not generic_misroute
    assert result["production_spine"] == "batch01"
    assert result["backend_module"] == "cap646.batch01_production"


@pytest.mark.parametrize("capability_id", sorted(BATCH01_DEDICATED_IDS))
@pytest.mark.asyncio
async def test_batch01_dedicated_direct_execute(capability_id: int):
    from cap646.batch01_dedicated import execute

    result = await execute(
        capability_id,
        params={
            "symbol": "BTC",
            "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
        },
    )
    assert result["success"] is True
    assert result["surface"] == EXPECTED_SURFACE[capability_id]


@pytest.mark.asyncio
async def test_cap006_screener_has_ranked_tokens():
    from cap646.batch01_dedicated import execute

    result = await execute(6, params={"symbol": "BTC"})
    assert result["surface"] == "smart_money_token_screener"
    assert "screener" in result


@pytest.mark.asyncio
async def test_cap214_watchlists_not_market_probe():
    from cap646.batch01_dedicated import execute

    result = await execute(
        214,
        params={
            "symbol": "BTC",
            "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
        },
    )
    assert result["surface"] == "watchlists"
    assert "watchlists" in result
    assert "probe" not in result
    items = result["watchlists"]["items"]
    assert isinstance(items, list)
    assert len(items) > 0
    assert all(isinstance(item, dict) for item in items)
    assert isinstance(result["watchlists"]["market_watchlists"], list)
    assert result["count"] == len(items)


@pytest.mark.asyncio
async def test_cap055_nvt_not_generic_onchain():
    from cap646.batch01_dedicated import execute

    result = await execute(55, params={"symbol": "BTC"})
    assert result["surface"] == "nvt_fair_value_model"
    assert "nvt" in result
    ratio = float(result["nvt_ratio"])
    signal = result["fair_value_signal"]
    assert ratio > 0
    if ratio > 120:
        assert signal == "Overheated (high NVT)"
    elif ratio > 40:
        assert signal == "Fair range"
    else:
        assert signal == "Undervalued zone"


@pytest.mark.asyncio
async def test_cap629_wallet_alerts_not_engine_stats():
    from cap646.batch01_dedicated import execute

    result = await execute(629, params={"symbol": "BTC"})
    assert result["surface"] == "real_time_wallet_alerts"
    assert "wallet_alerts" in result
    assert result["surface"] != "smart_alerts"


@pytest.mark.asyncio
async def test_cap029_cross_market_not_market_data():
    from cap646.batch01_dedicated import execute

    result = await execute(29, params={"symbol": "BTC"})
    assert result["surface"] == "cross_market_decision_intelligence_engine"
    assert "decision_engine" in result
