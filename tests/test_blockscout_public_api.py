"""Blockscout API (multi-chain gateway + public fallback)."""

import pytest

from blockscout_public_api import (
    _api_v2_root,
    fetch_address_summary,
    fetch_explorer_fallback,
    supported_chains,
)


@pytest.fixture(autouse=True)
def _reset_blockscout(monkeypatch, tmp_path):
    monkeypatch.setattr("blockscout_public_api._CACHE", {})
    monkeypatch.setattr("blockscout_public_api._RPS_TIMES", __import__("collections").deque())
    usage = tmp_path / "blockscout_api_usage.json"
    monkeypatch.setattr("blockscout_public_api._USAGE_PATH", usage)
    monkeypatch.setattr("blockscout_public_api.BLOCKSCOUT_DAILY_LIMIT", 1000)


def test_supported_chains():
    assert "ethereum" in supported_chains()
    assert "polygon" in supported_chains()


def test_gateway_root_with_api_key(monkeypatch):
    monkeypatch.setattr("blockscout_public_api.BLOCKSCOUT_API_KEY", "proapi_test")
    assert _api_v2_root("ethereum") == "https://api.blockscout.com/1/api/v2"
    monkeypatch.setattr("blockscout_public_api.BLOCKSCOUT_API_KEY", "")
    assert _api_v2_root("ethereum") == "https://eth.blockscout.com/api/v2"


@pytest.mark.asyncio
async def test_fetch_address_summary(monkeypatch):
    async def fake_get(chain, path):
        if "/addresses/" in path:
            return {
                "coin_balance": "1000000000000000000",
                "exchange_rate": "2000",
                "ens_domain_name": "test.eth",
            }
        return None

    monkeypatch.setattr("blockscout_public_api._get_json", fake_get)
    row = await fetch_address_summary("0x" + "a" * 40, chain="ethereum")
    assert row["balance_native"] == 1.0
    assert row["native_usd_estimate"] == 2000.0


@pytest.mark.asyncio
async def test_fetch_explorer_fallback(monkeypatch):
    async def fake_summary(address, *, chain="ethereum"):
        return {"balance_native": 1.0, "chain": chain}

    async def fake_txs(address, *, chain="ethereum", limit=5):
        return [{"hash": "0xabc"}]

    monkeypatch.setattr("blockscout_public_api.fetch_address_summary", fake_summary)
    monkeypatch.setattr("blockscout_public_api.fetch_address_transactions", fake_txs)
    out = await fetch_explorer_fallback("0x" + "b" * 40, chain="polygon")
    assert out["ok"] is True
    assert out["chain"] == "polygon"


@pytest.mark.asyncio
async def test_etherscan_falls_back_to_blockscout(monkeypatch):
    from etherscan_public_api import fetch_address_onchain_fallback

    monkeypatch.setattr("etherscan_public_api.ETHERSCAN_API_KEY", "")

    async def fake_bs(address, *, chain="ethereum", include_transactions=True, tx_limit=5):
        return {"ok": True, "source": "blockscout", "chain": chain}

    monkeypatch.setattr("blockscout_public_api.fetch_explorer_fallback", fake_bs)
    row = await fetch_address_onchain_fallback("0x" + "c" * 40)
    assert row.get("source") == "blockscout"


@pytest.mark.asyncio
async def test_public_blockscout_usage_route():
    from dashboard import app
    from fastapi.testclient import TestClient

    client = TestClient(app)
    res = client.get("/api/public/onchain/blockscout/usage")
    assert res.status_code == 200
    assert res.json().get("no_api_key") is True
