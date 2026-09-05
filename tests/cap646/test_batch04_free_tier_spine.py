"""Tests for Batch04 free-tier Strangler spine (#168, #171, #186)."""

from __future__ import annotations

import pytest

from cap646.dedicated_common import seed as _seed


@pytest.mark.asyncio
async def test_cap171_coingecko_trending():
    from cap646.batch04_free_tier_spine import build_trending_coins_171

    payload = await build_trending_coins_171(symbol="BTC")
    assert payload["ok"] is True
    assert payload["feature_ref"] == 171
    assert payload["source"] == "coingecko_search_trending"
    assert isinstance(payload["trending_coins"], list)


@pytest.mark.asyncio
async def test_cap168_santiment_free_tier():
    from cap646.batch04_free_tier_spine import build_social_dominance_168

    payload = await build_social_dominance_168(symbol="BTC", seed=_seed())
    assert payload["ok"] is True
    assert payload["feature_ref"] == 168
    assert payload["free_tier_only"] is True
    assert "accuracy_disclaimer" in payload
    assert payload["dominance_pct"] >= 0


@pytest.mark.asyncio
async def test_cap186_wallet_history_requires_address():
    from cap646.batch04_free_tier_spine import build_wallet_balance_history_186

    payload = await build_wallet_balance_history_186(symbol="ETH", address="", params={})
    assert payload["ok"] is False
    assert payload["error"] == "wallet_address_required"


@pytest.mark.asyncio
async def test_cap168_171_186_runtime_dispatch():
    from cap646.runtime import execute_capability

    r171 = await execute_capability(171, skip_entitlement=True, params={"symbol": "BTC", "tier": "pro"})
    assert r171["success"] is True
    assert r171["trending_coins"]["source"] == "coingecko_search_trending"

    r168 = await execute_capability(168, skip_entitlement=True, params={"symbol": "BTC", "tier": "pro"})
    assert r168["success"] is True
    assert r168["social_dominance_intelligence"]["free_tier_only"] is True

    r186 = await execute_capability(
        186,
        skip_entitlement=True,
        params={
            "symbol": "ETH",
            "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
            "tier": "pro",
        },
    )
    assert r186["success"] is True
    assert "balance_history" in r186["historical_wallet_balance_tool"]


@pytest.mark.asyncio
async def test_cap181_182_catalog_names():
    from cap646.catalog import catalog_by_id

    assert catalog_by_id()[181]["capability"] == "IC Committee Packets Status"
    assert catalog_by_id()[182]["capability"] == "White-Label Infrastructure Status"
