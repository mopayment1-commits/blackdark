"""Tests — BLACKDARK Public API (#183) contract + auth."""

from __future__ import annotations

import os

import pytest
from fastapi import HTTPException

from blackdark.api.api_auth import verify_blackdark_api_key
from blackdark.api.unified_public_api import CONTRACT_SCHEMAS


def test_contract_schemas_defined():
    assert "price" in CONTRACT_SCHEMAS
    assert "market_health" in CONTRACT_SCHEMAS
    assert "risk_score" in CONTRACT_SCHEMAS
    assert "price_usd" in CONTRACT_SCHEMAS["price"]["nullable"]


def test_api_key_required():
    with pytest.raises(HTTPException) as exc:
        verify_blackdark_api_key(None)
    assert exc.value.status_code == 401


def test_api_key_valid(monkeypatch):
    monkeypatch.delenv("ADMIN_API_KEY", raising=False)
    monkeypatch.setenv("BLACKDARK_PUBLIC_API_KEY", "test-api-key-12345")
    auth = verify_blackdark_api_key("test-api-key-12345")
    assert auth["tier"] == "institutional"


@pytest.mark.asyncio
async def test_get_price_intelligence_mocked(monkeypatch):
    async def fake_agg(asset, use_cache=True):
        return {
            "ok": True,
            "weighted_price": 100000,
            "vwap_usd": 99900,
            "change_24h_pct": 1.5,
            "outlier_count": 0,
            "source_metadata": {"connectors_ok": 5, "primary_source": "binance"},
            "validation": {"price_verified": True},
            "latency_ms": 120,
            "data_state": "LIVE",
            "timestamp": "2026-01-01T00:00:00+00:00",
        }

    monkeypatch.setattr("bd_platform.price_aggregation_engine.aggregate_prices", fake_agg)
    from blackdark.api.canonical_intelligence import get_price_intelligence

    out = await get_price_intelligence("BTC")
    assert out["ok"] is True
    assert out["price_usd"] == 100000
    assert out["freshness"]["source"] == "binance"
    assert out["sla_met"] is True


@pytest.mark.asyncio
async def test_null_semantics_on_failure(monkeypatch):
    async def fake_agg(asset, use_cache=True):
        return {"ok": False, "error": "unavailable"}

    monkeypatch.setattr("bd_platform.price_aggregation_engine.aggregate_prices", fake_agg)
    from blackdark.api.canonical_intelligence import get_price_intelligence

    out = await get_price_intelligence("BTC")
    assert out["ok"] is False
    assert out["price_usd"] is None
    assert out["vwap_usd"] is None
