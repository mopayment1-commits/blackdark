"""Read-only public wallet balance."""

import pytest

from wallet_balance_public import fetch_readonly_wallet_balance


@pytest.mark.asyncio
async def test_invalid_address():
    row = await fetch_readonly_wallet_balance("not-an-address")
    assert row["ok"] is False
    assert row["read_only"] is True
    assert row["error"] == "invalid_address"
    assert "message" in row


@pytest.mark.asyncio
async def test_etherscan_balance(monkeypatch):
    async def fake_eth(address):
        return {"balance_eth": 1.5, "balance_wei": "1500000000000000000"}

    monkeypatch.setattr("etherscan_public_api.fetch_eth_balance_wei", fake_eth)
    monkeypatch.setattr(
        "etherscan_public_api.usage_stats",
        lambda: {"configured": True, "remaining_today": 1},
    )
    row = await fetch_readonly_wallet_balance("0x" + "a" * 40, chain="ethereum")
    assert row["ok"] is True
    assert row["balance_native"] == 1.5
    assert row["source"] == "etherscan_free"
    assert row["no_private_key"] is True


@pytest.mark.asyncio
async def test_blockscout_fallback(monkeypatch):
    async def no_eth(address):
        return None

    async def fake_summary(address, *, chain="ethereum"):
        return {"balance_native": 2.0, "native_symbol": "ETH"}

    monkeypatch.setattr("etherscan_public_api.fetch_eth_balance_wei", no_eth)
    monkeypatch.setattr("blockscout_public_api.fetch_address_summary", fake_summary)
    monkeypatch.setattr("blockscout_public_api.usage_stats", lambda: {"remaining_today": 1})
    row = await fetch_readonly_wallet_balance("0x" + "b" * 40, chain="polygon")
    assert row["ok"] is True
    assert row["source"] == "blockscout"


def test_wallet_balance_page():
    from dashboard import app
    from fastapi.testclient import TestClient

    client = TestClient(app, base_url="https://testserver")
    res = client.get("/wallet-balance")
    assert res.status_code == 200
    assert "private key" in res.text.lower() or "Read-only" in res.text


@pytest.mark.asyncio
async def test_public_wallet_balance_route(monkeypatch):
    from dashboard import app
    from fastapi.testclient import TestClient

    async def fake_fetch(address, *, chain="ethereum"):
        return {
            "ok": True,
            "address": address,
            "chain": chain,
            "balance_native": 1.0,
            "native_symbol": "ETH",
            "source": "etherscan_free",
            "read_only": True,
        }

    monkeypatch.setattr("wallet_balance_public.fetch_readonly_wallet_balance", fake_fetch)
    client = TestClient(app, base_url="https://testserver")
    res = client.get("/api/public/wallet/balance?address=0x" + "c" * 40)
    assert res.status_code == 200
    assert res.json()["balance_native"] == 1.0


@pytest.mark.asyncio
async def test_public_wallet_balance_invalid_http(monkeypatch):
    from dashboard import app
    from fastapi.testclient import TestClient

    async def fake_fetch(address, *, chain="ethereum"):
        return {
            "ok": False,
            "error": "invalid_address",
            "message": "Enter a valid EVM wallet address.",
            "read_only": True,
        }

    monkeypatch.setattr("wallet_balance_public.fetch_readonly_wallet_balance", fake_fetch)
    client = TestClient(app, base_url="https://testserver")
    res = client.get("/api/public/wallet/balance?address=bad")
    assert res.status_code == 400
    assert res.json()["detail"]["message"]
