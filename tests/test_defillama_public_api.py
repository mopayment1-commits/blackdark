"""DefiLlama public API helpers (no API key)."""

import pytest

from defillama_public_api import (
    fetch_chains_tvl,
    fetch_defi_context_for_asset,
    fetch_fees_leaders,
    fetch_top_protocols,
    fetch_top_yields,
)


@pytest.fixture(autouse=True)
def _clear_defillama_cache(monkeypatch):
    monkeypatch.setattr("defillama_public_api._CACHE", {})


@pytest.mark.asyncio
async def test_fetch_chains_tvl_parses(monkeypatch):
    async def fake_get(url, *, params=None):
        if "chains" in url:
            return [{"name": "Ethereum", "tvl": 100.5}, {"name": "Solana", "tvl": 50}]
        return None

    monkeypatch.setattr("defillama_public_api._get_json", fake_get)
    rows = await fetch_chains_tvl()
    assert len(rows) == 2
    assert rows[0]["name"] == "Ethereum"
    assert rows[0]["tvl_usd"] == 100.5


@pytest.mark.asyncio
async def test_fetch_fees_leaders(monkeypatch):
    async def fake_get(url, *, params=None):
        if "fees" in url:
            return {
                "protocols": [
                    {"name": "Uniswap", "total24h": 1_000_000},
                    {"name": "Empty", "total24h": 0},
                ]
            }
        return None

    monkeypatch.setattr("defillama_public_api._get_json", fake_get)
    rows = await fetch_fees_leaders(5)
    assert len(rows) == 1
    assert rows[0]["name"] == "Uniswap"
    assert rows[0]["fees_24h_usd"] == 1_000_000.0


@pytest.mark.asyncio
async def test_fetch_top_yields_filters(monkeypatch):
    async def fake_get(url, *, params=None):
        if "yields" in url:
            return {
                "data": [
                    {
                        "project": "aave",
                        "symbol": "USDC",
                        "chain": "Ethereum",
                        "apy": 5.5,
                        "tvlUsd": 2_000_000,
                    },
                    {
                        "project": "tiny",
                        "symbol": "USDC",
                        "chain": "Ethereum",
                        "apy": 1.0,
                        "tvlUsd": 1000,
                    },
                ]
            }
        return None

    monkeypatch.setattr("defillama_public_api._get_json", fake_get)
    rows = await fetch_top_yields(chain="Ethereum", symbol="USDC", limit=5)
    assert len(rows) == 1
    assert rows[0]["project"] == "aave"


@pytest.mark.asyncio
async def test_fetch_defi_context_for_eth(monkeypatch):
    async def fake_get(url, *, params=None):
        if url.endswith("/v2/chains"):
            return [{"name": "Ethereum", "tvl": 200}]
        if "protocols" in url:
            return [{"name": "Lido", "symbol": "ETH", "tvl": 10}]
        if "fees" in url:
            return {"protocols": [{"name": "Uni", "total24h": 100}]}
        if "yields" in url:
            return {"data": []}
        return None

    monkeypatch.setattr("defillama_public_api._get_json", fake_get)
    ctx = await fetch_defi_context_for_asset("ETH")
    assert ctx["source"] == "defillama"
    assert ctx["chain"] == "Ethereum"
    assert ctx["fetched_ok"] is True
    assert ctx["total_defi_tvl_usd"] == 200.0


@pytest.mark.asyncio
async def test_public_defi_context_route(monkeypatch):
    from dashboard import app
    from fastapi.testclient import TestClient

    async def fake_ctx(asset):
        return {
            "source": "defillama",
            "attribution": "Data: DefiLlama",
            "total_defi_tvl_usd": 1.0,
            "fetched_ok": True,
            "top_chains": [],
            "fees_leaders_24h": [],
            "top_yields": [],
        }

    monkeypatch.setattr("defillama_public_api.fetch_defi_context_for_asset", fake_ctx)

    client = TestClient(app)
    res = client.get("/api/public/defi-context?symbol=ETH")
    assert res.status_code == 200
    body = res.json()
    assert body.get("source") == "defillama"
