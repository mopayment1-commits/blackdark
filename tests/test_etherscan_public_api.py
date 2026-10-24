"""Etherscan free API fallback (rate-limited)."""

import json

import pytest

from etherscan_public_api import (
    _try_consume_quota,
    fetch_address_onchain_fallback,
    fetch_eth_balance_wei,
    usage_stats,
)


@pytest.fixture(autouse=True)
def _reset_etherscan_state(monkeypatch, tmp_path):
    monkeypatch.setattr("etherscan_public_api._CACHE", {})
    monkeypatch.setattr("etherscan_public_api._RPS_TIMES", __import__("collections").deque())
    usage_file = tmp_path / "etherscan_api_usage.json"
    monkeypatch.setattr("etherscan_public_api._USAGE_PATH", usage_file)
    monkeypatch.setattr("etherscan_public_api.ETHERSCAN_API_KEY", "test-key")
    monkeypatch.setattr("etherscan_public_api.ETHERSCAN_DAILY_LIMIT", 100)
    monkeypatch.setattr("etherscan_public_api.ETHERSCAN_RPS_LIMIT", 5)


@pytest.mark.asyncio
async def test_fetch_eth_balance(monkeypatch):
    async def fake_api(params):
        assert params["action"] == "balance"
        return {"status": "1", "message": "OK", "result": "1000000000000000000"}

    monkeypatch.setattr("etherscan_public_api._api_get", fake_api)
    row = await fetch_eth_balance_wei("0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045")
    assert row["balance_eth"] == 1.0


@pytest.mark.asyncio
async def test_daily_quota_blocks(monkeypatch):
    usage_file = __import__("etherscan_public_api")._USAGE_PATH
    usage_file.write_text(json.dumps({"day": usage_stats()["day_utc"], "count": 100}), encoding="utf-8")
    assert _try_consume_quota() is False


@pytest.mark.asyncio
async def test_address_fallback_bundle(monkeypatch):
    async def fake_bal(address):
        return {"balance_eth": 2.0, "balance_wei": 2 * 10**18}

    async def fake_txs(address, *, limit=5):
        return [{"hash": "0xabc"}]

    monkeypatch.setattr("etherscan_public_api.fetch_eth_balance_wei", fake_bal)
    monkeypatch.setattr("etherscan_public_api.fetch_normal_transactions", fake_txs)
    out = await fetch_address_onchain_fallback("0x" + "a" * 40)
    assert out["ok"] is True
    assert out["balance"]["balance_eth"] == 2.0
    assert len(out["recent_transactions"]) == 1


@pytest.mark.asyncio
async def test_public_etherscan_usage_route():
    from dashboard import app
    from fastapi.testclient import TestClient

    client = TestClient(app)
    res = client.get("/api/public/onchain/etherscan/usage")
    assert res.status_code == 200
    body = res.json()
    assert "daily_limit" in body


@pytest.mark.asyncio
async def test_wallet_balance_etherscan_fallback(monkeypatch):
    async def fail_tracely(*args, **kwargs):
        return None

    async def fake_eth(address):
        return {"balance_eth": 0.5, "balance_wei": int(0.5 * 1e18)}

    monkeypatch.setattr("bd_platform.free_integrations.tracely_portfolio", fail_tracely)
    async def no_zerion(a):
        return None

    monkeypatch.setattr("bd_platform.free_integrations.zerion_wallet", no_zerion)
    monkeypatch.setenv("DEBANK_API_KEY", "")
    monkeypatch.setenv("ZERION_API_KEY", "")
    monkeypatch.setattr("etherscan_public_api.fetch_eth_balance_wei", fake_eth)

    from bd_platform.free_integrations import wallet_balance

    row = await wallet_balance("0x" + "b" * 40)
    assert row["available"] is True
    assert row["source"] == "etherscan_free"
