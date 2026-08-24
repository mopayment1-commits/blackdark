"""Tests — On-Chain Intelligence API (#164)."""

from __future__ import annotations

import pytest
from fastapi import HTTPException

from blackdark.api.v1_onchain_intelligence import (
    _entity_schema,
    _transaction_schema,
    get_entity,
    get_transaction,
    onchain_intelligence_api_status,
)


def test_entity_schema_parity():
    ui = {
        "address": "0xabc",
        "chain": "ethereum",
        "chain_id": 1,
        "entity_label": "Test Entity",
        "total_usd": 1000.0,
        "balance": {"total_usd": 1000},
        "labels": {"labels": []},
        "data_state": "LIVE",
        "sla_met": True,
        "latency_ms": 50,
        "timestamp": "2026-01-01T00:00:00+00:00",
    }
    schema = _entity_schema(ui, address="0xabc", chain="ethereum")
    assert schema["type"] == "entity"
    assert schema["feature_id"] == 164
    assert schema["entity_label"] == "Test Entity"
    assert schema["address"] == "0xabc"


def test_transaction_schema_parity():
    decoded = {
        "decoded": {"hash": "0xdead"},
        "source": "blockchair",
        "success": True,
        "free_tier": True,
        "timestamp": "2026-01-01T00:00:00+00:00",
    }
    schema = _transaction_schema(decoded, tx_hash="0xdead", chain="ethereum")
    assert schema["type"] == "transaction"
    assert schema["tx_hash"] == "0xdead"
    assert schema["success"] is True


def test_onchain_intelligence_api_status():
    status = onchain_intelligence_api_status()
    assert status["feature_id"] == 164
    assert status["read_only"] is True
    assert "/api/v1/entities/{address}" in status["endpoints"][0]


@pytest.mark.asyncio
async def test_get_entity_mocked(monkeypatch):
    async def fake_search(address, chain="ethereum"):
        return {
            "ok": True,
            "address": address,
            "chain": chain,
            "chain_id": 1,
            "entity_label": "Whale",
            "total_usd": 5000,
            "balance": {},
            "labels": {},
            "clusters": {},
            "data_state": "LIVE",
            "sla_met": True,
            "latency_ms": 10,
            "timestamp": "2026-01-01T00:00:00+00:00",
        }

    monkeypatch.setattr("bd_platform.address_intelligence.search_address", fake_search)
    user = {"id": 1, "tier": "pro", "email": "test@example.com"}
    out = await get_entity("0x1234567890abcdef1234567890abcdef12345678", chain="ethereum", user=user)
    assert out["ok"] is True
    assert out["data"]["entity_label"] == "Whale"
    assert out["read_only"] is True


@pytest.mark.asyncio
async def test_get_transaction_mocked(monkeypatch):
    async def fake_decoder(*, tx_hash=None, chain="ethereum"):
        return {
            "decoded": {"hash": tx_hash},
            "source": "blockchair",
            "success": True,
            "free_tier": True,
            "timestamp": "2026-01-01T00:00:00+00:00",
        }

    monkeypatch.setattr("bd_platform.free_tier_capabilities.transaction_decoder", fake_decoder)
    user = {"id": 1, "tier": "pro", "email": "test@example.com"}
    out = await get_transaction("0xdeadbeef", chain="ethereum", user=user)
    assert out["ok"] is True
    assert out["data"]["tx_hash"] == "0xdeadbeef"


@pytest.mark.asyncio
async def test_get_entity_not_found(monkeypatch):
    async def fake_search(address, chain="ethereum"):
        return {"ok": False, "error": "invalid_address"}

    monkeypatch.setattr("bd_platform.address_intelligence.search_address", fake_search)
    user = {"id": 1, "tier": "pro", "email": "test@example.com"}
    with pytest.raises(HTTPException) as exc:
        await get_entity("0x1234567890abcdef1234567890abcdef12345678", user=user)
    assert exc.value.status_code == 404
