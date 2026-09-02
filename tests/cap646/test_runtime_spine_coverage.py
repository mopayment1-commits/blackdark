"""Runtime spine coverage — exercise routing branches (CLOSURE-MANDATE-LAST item 2)."""

from __future__ import annotations

import pytest

from cap646.catalog import catalog_by_id
from cap646.runtime import _route_handler, execute_capability

BATCH02_SAMPLE = [51, 57, 69, 85, 88]
BATCH01_SAMPLE = [1, 6, 17, 47, 50]
FREE_TIER_SAMPLE = [5, 7]
HANDLER_ROUTE_SAMPLES = [
    (329, "T02"),  # institutional
    (86, "T05"),  # derivatives / funding
    (88, "T05"),  # liquidation
    (17, "T13"),  # alerts
    (63, "T03"),  # data quality
    (200, "T04"),  # market (non-batch)
    (400, "T12"),  # ai
    (338, "T04"),  # option A data
    (500, "T04"),  # option A data
    (49, "T12"),  # verified
    (632, "T12"),  # verified family
    (642, "T17"),  # wave/ai
]
ROUTE_HANDLER_ONLY = [
    (150, "T06", "Arbitrage Scanner"),
    (250, "T09", "On-Chain Wallet Intelligence"),
    (300, "T13", "Smart Alerts Engine"),
    (350, "T02", "Institutional API Gateway"),
]


@pytest.mark.parametrize("capability_id", BATCH01_SAMPLE + BATCH02_SAMPLE)
@pytest.mark.asyncio
async def test_execute_capability_official_spine(capability_id: int):
    result = await execute_capability(capability_id, params={"symbol": "BTC"}, skip_entitlement=True)
    assert "surface" in result
    assert result.get("classification") in {"PRODUCTION-ALIGNED", "NOT_COMPLETE", "DUPLICATE/ALREADY_COVERED"}


@pytest.mark.parametrize("capability_id", FREE_TIER_SAMPLE)
@pytest.mark.asyncio
async def test_free_tier_path(capability_id: int):
    result = await execute_capability(capability_id, params={"symbol": "BTC"}, skip_entitlement=True)
    assert result.get("capability_id") == capability_id


@pytest.mark.asyncio
async def test_unknown_capability_rejected():
    result = await execute_capability(99999, params={"symbol": "BTC"}, skip_entitlement=True)
    assert result.get("success") is False


@pytest.mark.asyncio
async def test_batch_spine_enrichment_fields():
    result = await execute_capability(69, params={"symbol": "BTC"}, skip_entitlement=True)
    assert result.get("surface") == "cross_domain_decision_intelligence_layer"
    assert result.get("production_spine") == "batch02"


@pytest.mark.parametrize("capability_id,track", HANDLER_ROUTE_SAMPLES)
def test_route_handler_resolution(capability_id: int, track: str):
    row = catalog_by_id()[capability_id]
    handler = _route_handler(track, row["capability"], capability_id)
    assert handler is not None
    assert callable(handler)


@pytest.mark.parametrize("capability_id,track,capability_name", ROUTE_HANDLER_ONLY)
def test_route_handler_specialized_branches(capability_id: int, track: str, capability_name: str):
    handler = _route_handler(track, capability_name, capability_id)
    assert callable(handler)


@pytest.mark.asyncio
async def test_batch03_prep_path_blocked_but_routed():
    result = await execute_capability(101, params={"symbol": "BTC"}, skip_entitlement=True)
    assert result.get("capability_id") == 101
    assert "classification" in result


@pytest.mark.asyncio
async def test_verified_capability_paths():
    for cap_id in (49, 50):
        result = await execute_capability(cap_id, params={"symbol": "BTC"}, skip_entitlement=True)
        assert result.get("capability_id") == cap_id


@pytest.mark.asyncio
async def test_handler_exception_path(monkeypatch):
    import cap646.runtime as runtime_mod

    async def _boom(*_args, **_kwargs):
        raise RuntimeError("test handler failure")

    monkeypatch.setattr(runtime_mod, "handle_market_capability", _boom)
    result = await execute_capability(200, params={"symbol": "BTC"}, skip_entitlement=True)
    assert result.get("success") is False
    assert "test handler failure" in str(result.get("error", ""))


@pytest.mark.asyncio
async def test_non_batch_market_handler_path():
    result = await execute_capability(200, params={"symbol": "BTC"}, skip_entitlement=True)
    assert result.get("capability_id") == 200
    assert "classification" in result


@pytest.mark.asyncio
async def test_institutional_handler_path():
    result = await execute_capability(329, params={"symbol": "BTC"}, skip_entitlement=True)
    assert result.get("capability_id") == 329


@pytest.mark.asyncio
async def test_duplicate_capability_delegates():
    dup_id = 212
    row = catalog_by_id().get(dup_id)
    if row and row.get("capability") == "Smart Alerts":
        result = await execute_capability(dup_id, params={"symbol": "BTC"}, skip_entitlement=True)
        assert result.get("classification") == "DUPLICATE/ALREADY_COVERED"
        assert result.get("duplicate_of") == 17


@pytest.mark.asyncio
async def test_free_tier_non_batch_capabilities():
    for cap_id in (196, 331, 337):
        result = await execute_capability(cap_id, params={"symbol": "BTC"}, skip_entitlement=True)
        assert result.get("capability_id") == cap_id


def test_route_handler_option_a_branches():
    assert _route_handler("T04", "Market", 507).__name__ == "handle_market_capability"
    assert _route_handler("T04", "Data Platform", 338).__name__ == "handle_data_capability"
    assert _route_handler("T04", "Data Platform", 500).__name__ == "handle_data_capability"
    assert _route_handler("T12", "AI Research", 400).__name__ == "handle_ai_capability"


@pytest.mark.asyncio
async def test_entitlement_denied_without_skip(monkeypatch):
    from cap646 import entitlements

    async def _deny(*_args, **_kwargs):
        return {"allowed": False, "reason": "test_denied"}

    monkeypatch.setattr(entitlements.entitlement_engine, "check", _deny)
    result = await execute_capability(200, params={"symbol": "BTC"}, skip_entitlement=False, user=None)
    assert result.get("success") is False
    assert "entitlement" in result
