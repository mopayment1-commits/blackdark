"""Tests — on-chain live indexer for #577."""

from __future__ import annotations

import pytest

from bd_platform import onchain_live_indexer as oli


@pytest.mark.asyncio
async def test_fetch_btc_live_metrics():
    result = await oli.fetch_live_onchain_metrics("BTC")
    assert result.get("live_fetch_attempted") is True
    metrics = result.get("metrics") or {}
    assert "hash_rate" in metrics
    assert "transaction_count" in metrics
    # At least one live metric should be available from public APIs
    assert result.get("live_metric_count", 0) >= 1


@pytest.mark.asyncio
async def test_fetch_eth_live_metrics():
    result = await oli.fetch_live_onchain_metrics("ETH")
    assert result.get("asset") == "ETH"
    tx = result["metrics"].get("transaction_count", {})
    assert tx.get("available") is True or tx.get("value") is not None


@pytest.mark.asyncio
async def test_missing_not_zero_when_unavailable():
    result = await oli.fetch_live_onchain_metrics("ETH")
    hr = result["metrics"].get("hash_rate", {})
    assert hr.get("available") is False
    assert hr.get("value") != 0


@pytest.mark.asyncio
async def test_unsupported_asset():
    result = await oli.fetch_live_onchain_metrics("SOL")
    assert result.get("ok") is False
