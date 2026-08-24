"""Tests — Price Aggregation (#133) + Live Refresh (#127) + Unified Connector Layer (#194)."""

from __future__ import annotations

from dataclasses import replace

import pytest

from bd_platform.price_aggregation_engine import (
    _SNAPSHOT_PATH,
    aggregate_prices,
    detect_outliers,
    price_aggregation_status,
    refresh_live_price,
    volume_weighted_average,
)
from bd_platform.unified_connector_layer import (
    CanonicalPriceQuote,
    ConnectorFetchResult,
    connector_layer_status,
)


def _quote(
    connector_id: str,
    price: float,
    *,
    volume: float = 1_000_000.0,
    exchange: str | None = None,
) -> CanonicalPriceQuote:
    return CanonicalPriceQuote(
        connector_id=connector_id,
        exchange=exchange or connector_id,
        asset="BTC",
        pair="BTCUSDT",
        price_usd=price,
        volume_24h_usd=volume,
        source=f"{connector_id}:test",
        fetched_at="2026-08-24T00:00:00+00:00",
    )


def test_detect_outliers_removes_extreme_price():
    quotes = [
        _quote("binance", 100_000.0),
        _quote("okx", 100_100.0),
        _quote("bad_api", 150_000.0),
    ]
    clean, outliers = detect_outliers(quotes)
    assert len(clean) == 2
    assert len(outliers) == 1
    assert outliers[0]["connector_id"] == "bad_api"
    assert outliers[0]["reason"] == "isolated_extreme_price_likely_api_error"


def test_detect_outliers_keeps_one_when_all_flagged():
    quotes = [
        _quote("a", 100.0),
        _quote("b", 200.0),
        _quote("c", 300.0),
    ]
    clean, outliers = detect_outliers(quotes)
    assert len(clean) == 1
    assert len(outliers) == 2


def test_volume_weighted_average_prefers_volume():
    quotes = [
        _quote("binance", 100.0, volume=9_000_000.0),
        _quote("small", 200.0, volume=1_000_000.0),
    ]
    result = volume_weighted_average(quotes)
    assert result["weighting"] == "volume"
    assert result["vwap_usd"] == 110.0
    assert result["sources_used"] == 2


def test_volume_weighted_average_equal_when_no_volume():
    quotes = [
        _quote("a", 100.0, volume=0.0),
        _quote("b", 200.0, volume=0.0),
    ]
    result = volume_weighted_average(quotes)
    assert result["weighting"] == "equal"
    assert result["vwap_usd"] == 150.0


def test_connector_layer_status_not_user_facing():
    status = connector_layer_status()
    assert status["ok"] is True
    assert status["feature_id"] == 194
    assert status["user_facing"] is False
    assert "binance" in status["registered_connectors"]
    assert status["expansion_target_exchanges"] == 400


def test_price_aggregation_status_pipeline():
    status = price_aggregation_status()
    assert status["ok"] is True
    assert status["user_facing"] is False
    assert "133" in status["features"]
    assert "127" in status["features"]
    assert status["connector_layer"]["feature_id"] == 194


@pytest.mark.asyncio
async def test_aggregate_prices_with_mocked_connectors(monkeypatch, tmp_path):
    monkeypatch.setattr("bd_platform.price_aggregation_engine._SNAPSHOT_PATH", tmp_path / "snap.jsonl")

    async def fake_fetch(asset: str):
        return [
            ConnectorFetchResult(connector_id="binance", ok=True, quote=_quote("binance", 100_000.0, volume=5e9)),
            ConnectorFetchResult(connector_id="okx", ok=True, quote=_quote("okx", 100_050.0, volume=3e9)),
            ConnectorFetchResult(connector_id="bybit", ok=True, quote=_quote("bybit", 99_950.0, volume=2e9)),
            ConnectorFetchResult(connector_id="kraken", ok=False, error="no_data"),
        ]

    monkeypatch.setattr(
        "bd_platform.price_aggregation_engine.fetch_all_connector_quotes",
        fake_fetch,
    )

    result = await aggregate_prices("BTC", use_cache=False)
    assert result["ok"] is True
    assert result["user_facing"] is False
    assert result["mode"] == "infrastructure"
    assert result["sla_met"] is True
    assert result["price_usd"] > 0
    assert result["source_metadata"]["connectors_ok"] == 3
    assert result["source_metadata"]["connectors_polled"] == 4
    assert result["accuracy_estimate"] >= 0.95


@pytest.mark.asyncio
async def test_aggregate_prices_cache_hit(monkeypatch, tmp_path):
    monkeypatch.setattr("bd_platform.price_aggregation_engine._SNAPSHOT_PATH", tmp_path / "snap.jsonl")

    calls = {"n": 0}

    async def fake_fetch(asset: str):
        calls["n"] += 1
        return [
            ConnectorFetchResult(connector_id="binance", ok=True, quote=_quote("binance", 50_000.0)),
        ]

    monkeypatch.setattr(
        "bd_platform.price_aggregation_engine.fetch_all_connector_quotes",
        fake_fetch,
    )

    first = await aggregate_prices("ETH", use_cache=True)
    second = await aggregate_prices("ETH", use_cache=True)
    assert first["cache_hit"] is False
    assert second["cache_hit"] is True
    assert calls["n"] == 1


@pytest.mark.asyncio
async def test_refresh_live_price_prefers_ws(monkeypatch, tmp_path):
    monkeypatch.setattr("bd_platform.price_aggregation_engine._SNAPSHOT_PATH", tmp_path / "snap.jsonl")

    ws_quote = _quote("ws_binance", 100_123.0, volume=0.0)
    ws_quote = replace(ws_quote, connector_id="ws_binance", source="ws:binance:redis")

    async def fake_fetch(asset: str):
        return [
            ConnectorFetchResult(connector_id="ws_binance", ok=True, quote=ws_quote),
            ConnectorFetchResult(connector_id="binance", ok=True, quote=_quote("binance", 100_000.0)),
        ]

    monkeypatch.setattr(
        "bd_platform.price_aggregation_engine.fetch_all_connector_quotes",
        fake_fetch,
    )

    result = await refresh_live_price("BTC")
    assert result["ok"] is True
    assert result["mode"] == "invisible_infrastructure"
    assert result["user_facing"] is False
    assert result["refresh_mode"] == "live_ws_redis"
    assert result["price_usd"] == 100_123.0
    assert result["sla_met"] is True
    assert result["source_quality"]["connectors_ok"] == 2


@pytest.mark.asyncio
async def test_aggregate_insufficient_sources(monkeypatch, tmp_path):
    monkeypatch.setattr("bd_platform.price_aggregation_engine._SNAPSHOT_PATH", tmp_path / "snap.jsonl")

    async def fake_fetch(asset: str):
        return [ConnectorFetchResult(connector_id="binance", ok=False, error="timeout")]

    monkeypatch.setattr(
        "bd_platform.price_aggregation_engine.fetch_all_connector_quotes",
        fake_fetch,
    )

    result = await aggregate_prices("BTC", use_cache=False)
    assert result["ok"] is False
    assert result["error"] == "insufficient_sources"
