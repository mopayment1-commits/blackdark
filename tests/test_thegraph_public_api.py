"""The Graph gateway client (monthly quota, enrichment)."""

import pytest

from thegraph_public_api import (
    fetch_address_defi_indexed,
    fetch_address_onchain_enrichment,
    fetch_recent_dex_swaps,
    maybe_enrich_explorer_row,
    usage_stats,
)


@pytest.fixture(autouse=True)
def _reset_thegraph(monkeypatch, tmp_path):
    monkeypatch.setattr("thegraph_public_api._CACHE", {})
    monkeypatch.setattr("thegraph_public_api._RPS_TIMES", __import__("collections").deque())
    usage = tmp_path / "thegraph_api_usage.json"
    monkeypatch.setattr("thegraph_public_api._USAGE_PATH", usage)
    monkeypatch.setattr("thegraph_public_api.THE_GRAPH_MONTHLY_LIMIT", 1000)
    monkeypatch.setattr("thegraph_public_api.THE_GRAPH_API_KEY", "test-key")


def test_usage_stats_configured():
    stats = usage_stats()
    assert stats["configured"] is True
    assert stats["monthly_limit"] == 1000
    assert stats["remaining_this_month"] == 1000


@pytest.mark.asyncio
async def test_fetch_recent_dex_swaps(monkeypatch):
    async def fake_post(subgraph_id, query, variables=None):
        return {
            "data": {
                "swaps": [
                    {
                        "id": "1",
                        "timestamp": "1700000000",
                        "amountUSD": "12.5",
                        "token0": {"symbol": "WETH"},
                        "token1": {"symbol": "USDC"},
                        "transaction": {"id": "0x" + "a" * 64},
                    }
                ],
                "pools": [],
            }
        }

    monkeypatch.setattr("thegraph_public_api._post_graphql", fake_post)
    rows = await fetch_recent_dex_swaps("0x" + "d" * 40, chain="ethereum")
    assert len(rows) == 1
    assert rows[0]["token0_symbol"] == "WETH"


@pytest.mark.asyncio
async def test_fetch_address_defi_indexed_pools(monkeypatch):
    async def fake_post(subgraph_id, query, variables=None):
        return {
            "data": {
                "swaps": [],
                "pools": [
                    {
                        "id": "0xpool",
                        "totalValueLockedUSD": "1000000",
                        "volumeUSD": "50000",
                        "token0": {"symbol": "WETH"},
                        "token1": {"symbol": "USDC"},
                    }
                ],
            }
        }

    monkeypatch.setattr("thegraph_public_api._post_graphql", fake_post)
    row = await fetch_address_defi_indexed("0x" + "2" * 40, chain="ethereum", pool_limit=3)
    assert row["liquidity_pools"][0]["pair"] == "WETH/USDC"


@pytest.mark.asyncio
async def test_fetch_address_onchain_enrichment(monkeypatch):
    async def fake_indexed(address, *, chain="ethereum", swap_limit=5, pool_limit=3):
        return {"swaps": [{"id": "1"}], "liquidity_pools": [{"id": "p1"}]}

    monkeypatch.setattr("thegraph_public_api.fetch_address_defi_indexed", fake_indexed)
    out = await fetch_address_onchain_enrichment("0x" + "e" * 40, chain="ethereum")
    assert out["ok"] is True
    assert out["source"] == "the_graph"
    assert out["swap_count"] == 1
    assert out["pool_count"] == 1


@pytest.mark.asyncio
async def test_maybe_enrich_thin_explorer(monkeypatch):
    async def fake_enrich(address, *, chain="ethereum", swap_limit=5):
        return {"ok": True, "source": "the_graph", "recent_dex_swaps": [{"id": "x"}]}

    monkeypatch.setattr("thegraph_public_api.fetch_address_onchain_enrichment", fake_enrich)
    base = {"ok": True, "source": "blockscout", "recent_transactions": []}
    out = await maybe_enrich_explorer_row(base, "0x" + "f" * 40, chain="ethereum")
    assert out.get("thegraph_enrichment", {}).get("ok") is True


@pytest.mark.asyncio
async def test_not_configured_without_key(monkeypatch):
    monkeypatch.setattr("thegraph_public_api.THE_GRAPH_API_KEY", "")
    out = await fetch_address_onchain_enrichment("0x" + "1" * 40)
    assert out["ok"] is False
    assert out["error"] == "not_configured"


def test_public_thegraph_usage_route():
    from dashboard import app
    from fastapi.testclient import TestClient

    client = TestClient(app)
    res = client.get("/api/public/onchain/thegraph/usage")
    assert res.status_code == 200
    assert "monthly_limit" in res.json()
