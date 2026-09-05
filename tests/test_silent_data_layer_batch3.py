"""Tests — Binance, block search, lending markets (#21, #23, #25, #26)."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from blackdark.ingestion.binance_connector import fetch_binance_spot_ticker
from blackdark.ingestion.lending_markets_connector import (
    _normalize_borrow_apr,
    _reconcile_market,
    fetch_lending_markets,
)
from bd_platform.address_intelligence import search_block


@pytest.mark.asyncio
async def test_binance_spot_mock():
    fake = {
        "ok": True,
        "data": {
            "lastPrice": "65000",
            "priceChangePercent": "2.5",
            "volume": "1000",
            "quoteVolume": "65000000",
        },
        "latency_ms": 30,
    }
    with patch(
        "blackdark.ingestion.binance_connector._binance_get",
        new=AsyncMock(return_value=fake),
    ):
        out = await fetch_binance_spot_ticker("BTC")
    assert out["ok"] is True
    assert out["price_usd"] == 65000
    assert out["feature"] == "#21"
    assert out["sla_met"] is True


@pytest.mark.asyncio
async def test_binance_fallback():
    with patch(
        "blackdark.ingestion.binance_connector._binance_get",
        new=AsyncMock(return_value={"ok": False, "error": "rate_limited"}),
    ), patch(
        "blackdark.ingestion.binance_connector._spot_fallback",
        new=AsyncMock(return_value={"ok": True, "price_usd": 64000, "fallback": True}),
    ):
        out = await fetch_binance_spot_ticker("BTC")
    assert out["ok"] is True
    assert out.get("fallback") is True


@pytest.mark.asyncio
async def test_search_block_mock():
    fake_block = {
        "ok": True,
        "block_number": 18_000_000,
        "hash": "0xabc",
        "transaction_count": 150,
        "reorg_handling": {"finalized": True, "reorg_risk": "low"},
        "semantics": "point_in_time",
    }
    with patch(
        "bd_platform.onchain_client.get_block_by_number",
        new=AsyncMock(return_value=fake_block),
    ):
        out = await search_block(18_000_000, chain="ethereum")
    assert out["ok"] is True
    assert out["feature"] == "#23"
    assert out["capability"] == "block_search"
    assert out["reorg_handling"]["reorg_risk"] == "low"


def test_lending_borrow_apr_normalize():
    apr = _normalize_borrow_apr({"apyBaseBorrow": 5.25})
    assert apr == 5.25


def test_lending_market_reconciliation():
    recon = _reconcile_market(
        {"project": "aave", "chain": "Ethereum", "symbol": "USDC", "pool": "0x1"},
        borrow_usd=1_000_000,
        borrow_apr=4.5,
    )
    assert recon["ok"] is True
    assert recon["mapped"] is True


@pytest.mark.asyncio
async def test_lending_markets_mock():
    from blackdark.ingestion import lending_markets_connector as lm

    pools = {
        "data": [
            {
                "project": "aave-v3",
                "chain": "Ethereum",
                "symbol": "USDC",
                "pool": "0xpool",
                "category": "lending",
                "tvlUsd": 500000000,
                "apy": 3.5,
                "apyBaseBorrow": 5.1,
                "totalBorrowUsd": 200000000,
            }
        ]
    }

    async def _fake_json(*_a, **_k):
        return {"ok": True, "data": pools, "cache_hit": False}

    lm._CACHE._store.clear()
    with patch.object(lm._CACHE, "http_get_json", _fake_json):
        out = await fetch_lending_markets(limit=5)
    assert out["ok"] is True
    assert out["market_count"] >= 1
    assert out["total_borrow_outstanding_usd"] > 0
    assert out["borrowing_screener"]
