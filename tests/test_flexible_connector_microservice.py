"""Tests — Flexible Connector Microservice (#175)."""

from __future__ import annotations

import pytest

from bd_platform.flexible_connector_microservice import (
    BinanceAdapter,
    CanonicalConnectorAdapter,
    detect_schema_drift,
    execute_with_policy,
    fetch_with_failover,
    flexible_connector_status,
    get_adapter,
    list_adapters,
)
from bd_platform.unified_connector_layer import CanonicalPriceQuote, ConnectorFetchResult


def test_adapter_contract_interface():
    adapters = list_adapters()
    assert len(adapters) >= 10
    for adapter in adapters:
        assert isinstance(adapter, CanonicalConnectorAdapter)
        assert adapter.connector_id
        assert adapter.exchange
        assert hasattr(adapter, "fetch_quote")


def test_detect_schema_drift_missing_fields():
    quote = CanonicalPriceQuote(
        connector_id="test",
        exchange="test",
        asset="BTC",
        pair="BTCUSDT",
        price_usd=0,
        source="",
        fetched_at="",
    )
    issues = detect_schema_drift(quote)
    assert "invalid:price_usd" in issues
    assert "missing:source" in issues


def test_detect_schema_drift_valid_quote():
    quote = CanonicalPriceQuote(
        connector_id="binance",
        exchange="binance",
        asset="BTC",
        pair="BTCUSDT",
        price_usd=100000,
        source="binance:test",
        fetched_at="2026-01-01T00:00:00+00:00",
    )
    assert detect_schema_drift(quote) == []


def test_flexible_connector_status():
    status = flexible_connector_status()
    assert status["feature_id"] == 175
    assert status["policies"]["no_synthetic_success"] is True
    assert status["policies"]["retries"] == 3


@pytest.mark.asyncio
async def test_execute_with_policy_no_synthetic_success(monkeypatch):
    class FailingAdapter(BinanceAdapter):
        async def fetch_quote(self, asset, session):
            return None

    adapter = FailingAdapter()
    result = await execute_with_policy(adapter, "BTC")
    assert result.ok is False
    assert result.quote is None
    assert result.error == "no_data"


@pytest.mark.asyncio
async def test_execute_with_policy_success_mocked(monkeypatch):
    quote = CanonicalPriceQuote(
        connector_id="binance",
        exchange="binance",
        asset="BTC",
        pair="BTCUSDT",
        price_usd=100000,
        source="binance:test",
        fetched_at="2026-01-01T00:00:00+00:00",
    )

    async def fake_fetch(asset, session):
        return quote

    adapter = BinanceAdapter()
    monkeypatch.setattr(adapter, "fetch_quote", fake_fetch)
    result = await execute_with_policy(adapter, "BTC")
    assert result.ok is True
    assert result.quote.price_usd == 100000


@pytest.mark.asyncio
async def test_failover_no_synthetic_success(monkeypatch):
    async def fake_execute(adapter, asset, *, session=None):
        return ConnectorFetchResult(connector_id=adapter.connector_id, ok=False, error="down")

    monkeypatch.setattr(
        "bd_platform.flexible_connector_microservice.execute_with_policy",
        fake_execute,
    )
    out = await fetch_with_failover("BTC", preferred=["binance", "okx"])
    assert out["ok"] is False
    assert out["synthetic_success"] is False
    assert out["error"] == "all_connectors_failed"


def test_get_adapter_registry():
    assert get_adapter("binance") is not None
    assert get_adapter("unknown") is None
