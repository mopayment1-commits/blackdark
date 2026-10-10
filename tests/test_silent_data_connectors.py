"""Tests — silent data ingestion connectors (#46 DeBank, #49 DexScreener, #50 Etherscan)."""

from __future__ import annotations

import time
from unittest.mock import AsyncMock, patch

import pytest

from blackdark.ingestion.connector_cache import IngestionCache, cache_key
from blackdark.ingestion.debank_connector import (
    debank_connector_status,
    fetch_debank_total_balance,
)
from blackdark.ingestion.dexscreener_connector import (
    _liquidity_drain_signal,
    _normalize_pair,
    dexscreener_connector_status,
    fetch_dex_pairs,
)
from blackdark.ingestion.etherscan_connector import (
    _exchange_deposit_score,
    etherscan_connector_status,
    fetch_eth_balance,
    fetch_whale_flow_signal,
)


def test_cache_key_stable():
    assert cache_key("a", 1) == cache_key("a", 1)
    assert cache_key("a", 1) != cache_key("b", 1)


def test_ingestion_cache_ttl_bounds(monkeypatch):
    monkeypatch.setenv("DEBANK_CACHE_TTL_SEC", "30")
    cache = IngestionCache(default_ttl_sec=3600, max_ttl_sec=86400)
    assert cache.ttl("DEBANK_CACHE_TTL_SEC", 3600) == 60
    monkeypatch.setenv("DEBANK_CACHE_TTL_SEC", "999999")
    assert cache.ttl("DEBANK_CACHE_TTL_SEC", 3600) == 86400


def test_debank_status():
    st = debank_connector_status()
    assert st["feature"] == "#46"
    assert "debank_api" in st["fallback_chain"][0]


def test_dexscreener_status():
    st = dexscreener_connector_status()
    assert st["feature"] == "#49"
    assert st["role"] == "dex_liquidity_ingestion"


def test_etherscan_status():
    st = etherscan_connector_status()
    assert st["feature"] == "#50"


def test_normalize_pair():
    row = {
        "pairAddress": "0xabc",
        "chainId": "ethereum",
        "dexId": "uniswap",
        "baseToken": {"symbol": "ETH"},
        "quoteToken": {"symbol": "USDT"},
        "priceUsd": "2500",
        "liquidity": {"usd": 1000000},
        "volume": {"h24": 500000},
        "priceChange": {"h24": -10},
    }
    norm = _normalize_pair(row)
    assert norm["base_symbol"] == "ETH"
    assert norm["liquidity_usd"] == 1000000


def test_liquidity_drain_signal_detected():
    pairs = [
        {
            "base_symbol": "TOKEN",
            "quote_symbol": "USDT",
            "liquidity_usd": 20000,
            "volume_24h_usd": 80000,
            "price_change_24h_pct": -12,
        }
    ]
    sig = _liquidity_drain_signal(pairs)
    assert sig is not None
    assert sig["signal"] == "liquidity_drain_risk"


def test_exchange_deposit_score_high_outflow():
    txs = [{"value_eth": 50, "to": "0xexchange"} for _ in range(3)]
    flow = _exchange_deposit_score(txs)
    assert flow["sell_probability_pct"] >= 55
    assert flow["signal"] == "elevated_outflow"


@pytest.mark.asyncio
async def test_fetch_debank_mock(monkeypatch):
    monkeypatch.setenv("DEBANK_API_KEY", "test-key")
    fake = {
        "ok": True,
        "data": {"total_usd": 12345.67, "chain_list": [{"id": "eth"}]},
        "latency_ms": 40,
        "cache_hit": False,
    }
    with patch(
        "blackdark.ingestion.debank_connector._CACHE.http_get",
        new=AsyncMock(return_value=fake),
    ):
        row = await fetch_debank_total_balance("0x1234567890abcdef1234567890abcdef12345678")
    assert row["ok"] is True
    assert row["total_usd"] == 12345.67
    assert row["sla_met"] is True


@pytest.mark.asyncio
async def test_fetch_dex_pairs_mock():
    fake = {
        "ok": True,
        "data": {
            "pairs": [
                {
                    "pairAddress": "0x1",
                    "chainId": "eth",
                    "dexId": "uni",
                    "baseToken": {"symbol": "BTC"},
                    "quoteToken": {"symbol": "USDT"},
                    "priceUsd": "60000",
                    "liquidity": {"usd": 500000},
                    "volume": {"h24": 100000},
                    "priceChange": {"h24": 1},
                }
            ]
        },
        "latency_ms": 30,
    }
    with patch(
        "blackdark.ingestion.dexscreener_connector._CACHE.http_get",
        new=AsyncMock(return_value=fake),
    ):
        row = await fetch_dex_pairs("BTC")
    assert row["ok"] is True
    assert row["count"] == 1
    assert row["pairs"][0]["base_symbol"] == "BTC"


@pytest.mark.asyncio
async def test_fetch_eth_balance_mock(monkeypatch):
    monkeypatch.setenv("ETHERSCAN_API_KEY", "test-key")
    fake = {
        "ok": True,
        "data": {"result": "1000000000000000000"},
        "latency_ms": 25,
    }
    with patch(
        "blackdark.ingestion.etherscan_connector._etherscan_get",
        new=AsyncMock(return_value=fake),
    ):
        row = await fetch_eth_balance("0x1234567890abcdef1234567890abcdef12345678")
    assert row["ok"] is True
    assert row["balance_eth"] == 1.0


@pytest.mark.asyncio
async def test_whale_flow_signal_mock(monkeypatch):
    monkeypatch.setenv("ETHERSCAN_API_KEY", "test-key")
    with patch(
        "blackdark.ingestion.etherscan_connector.fetch_eth_balance",
        new=AsyncMock(return_value={"ok": True, "balance_eth": 100}),
    ), patch(
        "blackdark.ingestion.etherscan_connector.fetch_eth_transactions",
        new=AsyncMock(
            return_value={
                "ok": True,
                "transactions": [{"value_eth": 25, "to": "0xabc"} for _ in range(4)],
            }
        ),
    ):
        row = await fetch_whale_flow_signal("0x1234567890abcdef1234567890abcdef12345678")
    assert row["ok"] is True
    assert row["sell_probability_pct"] is not None


@pytest.mark.asyncio
async def test_cache_hit_served_from_memory():
    cache = IngestionCache(default_ttl_sec=3600)
    cache.set("k", {"ok": True, "data": {"x": 1}})
    got = cache.get("k", ttl=3600)
    assert got["data"]["x"] == 1


def test_connectors_status_api(tmp_path, monkeypatch):
    import asyncio

    import config
    import database

    db_path = tmp_path / "conn_api.db"
    monkeypatch.setattr(config, "DB_PATH", db_path)
    monkeypatch.setattr(database.config, "DB_PATH", db_path)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("ENV", "test")
    asyncio.run(database.init_db())

    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    r = c.get("/api/platform/ingestion/connectors/status")
    assert r.status_code == 200
    body = r.json()
    assert "debank" in body
    assert "dexscreener" in body
    assert "etherscan" in body
