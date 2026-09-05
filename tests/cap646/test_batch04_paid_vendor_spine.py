"""Tests for paid-vendor spine — CryptoQuant #187/#188/#190 (design-complete, env-gated)."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from cap646.paid_vendor_spine import (
    CRYPTOQUANT_VENDOR,
    PENDING_PAYMENT_STATUS,
    build_pending_payment_payload,
    is_paid_vendor_active,
    paid_vendor_api_key,
)
from cap646.batch04_paid_cryptoquant_spine import (
    build_exchange_inflow_187,
    build_exchange_outflow_188,
    build_exchange_supply_balance_190,
)


@pytest.fixture(autouse=True)
def _clear_cryptoquant_key(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("CRYPTOQUANT_API_KEY", raising=False)


def test_paid_vendor_api_key_rejects_placeholder(monkeypatch: pytest.MonkeyPatch):
    assert paid_vendor_api_key("CRYPTOQUANT_API_KEY") is None
    monkeypatch.setenv("CRYPTOQUANT_API_KEY", "YourApiKeyToken")
    assert paid_vendor_api_key("CRYPTOQUANT_API_KEY") is None
    monkeypatch.setenv("CRYPTOQUANT_API_KEY", "cq-live-secret-token")
    assert paid_vendor_api_key("CRYPTOQUANT_API_KEY") == "cq-live-secret-token"


@pytest.mark.asyncio
async def test_cap187_pending_payment_without_key():
    payload = await build_exchange_inflow_187(symbol="BTC", params={"exchange": "binance"})
    assert payload["ok"] is True
    assert payload["vendor_status"] == PENDING_PAYMENT_STATUS
    assert "requires CryptoQuant subscription" in payload["status"]
    assert payload["data_available"] is False
    assert payload["live_vendor_call"] is False
    assert payload["inflow_usd"] is None
    assert payload["inflow_native"] is None
    assert payload["exchange_inflow_status"] == PENDING_PAYMENT_STATUS


@pytest.mark.asyncio
async def test_cap188_pending_payment_without_key():
    payload = await build_exchange_outflow_188(symbol="BTC", params={})
    assert payload["vendor_status"] == PENDING_PAYMENT_STATUS
    assert payload["outflow_usd"] is None
    assert payload["outflow_native"] is None


@pytest.mark.asyncio
async def test_cap190_pending_payment_without_key():
    payload = await build_exchange_supply_balance_190(symbol="BTC", params={})
    assert payload["vendor_status"] == PENDING_PAYMENT_STATUS
    assert payload["reserve_usd"] is None
    assert payload["reserve_native"] is None


@pytest.mark.asyncio
async def test_cap187_live_path_with_mocked_vendor(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("CRYPTOQUANT_API_KEY", "cq-live-secret-token")
    mock_body: dict[str, Any] = {
        "status": {"code": 200, "message": "success"},
        "result": {
            "window": "day",
            "data": [
                {
                    "date": "2026-09-03",
                    "inflow_total": 1234.5,
                    "inflow_mean": 12.3,
                    "inflow_top10": 900.0,
                }
            ],
        },
        "_latency_ms": 42.0,
    }
    with patch(
        "cap646.batch04_paid_cryptoquant_spine.paid_vendor_get_json",
        new=AsyncMock(return_value=mock_body),
    ):
        payload = await build_exchange_inflow_187(symbol="BTC", params={"exchange": "binance"})
    assert payload["vendor_status"] == "LIVE"
    assert payload["data_available"] is True
    assert payload["live_vendor_call"] is True
    assert payload["inflow_native"] == 1234.5
    assert payload["exchange_inflow_status"] == "live"


@pytest.mark.asyncio
async def test_cap188_live_path_with_mocked_vendor(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("CRYPTOQUANT_API_KEY", "cq-live-secret-token")
    mock_body = {
        "status": {"code": 200, "message": "success"},
        "result": {
            "window": "day",
            "data": [{"date": "2026-09-03", "outflow_total": 888.0, "outflow_mean": 8.8, "outflow_top10": 600.0}],
        },
        "_latency_ms": 30.0,
    }
    with patch(
        "cap646.batch04_paid_cryptoquant_spine.paid_vendor_get_json",
        new=AsyncMock(return_value=mock_body),
    ):
        payload = await build_exchange_outflow_188(symbol="ETH", params={"exchange": "binance"})
    assert payload["vendor_status"] == "LIVE"
    assert payload["outflow_native"] == 888.0


@pytest.mark.asyncio
async def test_cap190_live_reserve_with_mocked_vendor(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("CRYPTOQUANT_API_KEY", "cq-live-secret-token")
    mock_body = {
        "status": {"code": 200, "message": "success"},
        "result": {
            "window": "day",
            "data": [{"date": "2026-09-03", "reserve": 500000.0, "reserve_usd": 3.5e10}],
        },
        "_latency_ms": 25.0,
    }
    with patch(
        "cap646.batch04_paid_cryptoquant_spine.paid_vendor_get_json",
        new=AsyncMock(return_value=mock_body),
    ):
        payload = await build_exchange_supply_balance_190(symbol="BTC", params={"exchange": "binance"})
    assert payload["vendor_status"] == "LIVE"
    assert payload["reserve_usd"] == 3.5e10
    assert payload["exchange_supply"]["reserve"] == 500000.0


@pytest.mark.asyncio
async def test_runtime_dispatch_pending_payment_187_188_190():
    from cap646.runtime import execute_capability

    for cap_id, root in (
        (187, "exchange_inflow_intelligence"),
        (188, "exchange_outflow_intelligence"),
        (190, "exchange_supply_balance_intelligence"),
    ):
        result = await execute_capability(
            cap_id,
            skip_entitlement=True,
            params={"symbol": "BTC", "tier": "pro", "exchange": "binance"},
        )
        assert result["success"] is True
        payload = result[root]
        assert payload["vendor_status"] == PENDING_PAYMENT_STATUS
        assert payload["data_available"] is False
        assert "requires CryptoQuant subscription" in payload["status"]


def test_build_pending_payment_payload_registry_shape():
    from cap646.paid_vendor_spine import PaidCapabilitySpec

    spec = PaidCapabilitySpec(187, "exchange_inflow_intelligence", CRYPTOQUANT_VENDOR)
    payload = build_pending_payment_payload(spec, symbol="BTC")
    assert payload["env_var"] == "CRYPTOQUANT_API_KEY"
    assert is_paid_vendor_active("CRYPTOQUANT_API_KEY") is False
