"""Tests — Financial Data Ingestion Layer (#137) + Unified Connector enhancements (#194/#138)."""

from __future__ import annotations

import pytest

from bd_platform import financial_data_ingestion_layer as fdi
from bd_platform.unified_connector_layer import (
    CanonicalPriceQuote,
    ConnectorFetchResult,
    cross_reference_quotes,
    normalize_symbol,
    sanitize_user_facing_error,
)


@pytest.fixture
def isolated_ingestion_paths(tmp_path, monkeypatch):
    freshness = tmp_path / "freshness.json"
    dedup = tmp_path / "dedup.json"
    log = tmp_path / "ingest.jsonl"
    monkeypatch.setattr(fdi, "_FRESHNESS_PATH", freshness)
    monkeypatch.setattr(fdi, "_DEDUP_PATH", dedup)
    monkeypatch.setattr(fdi, "_INGEST_LOG", log)
    return freshness, dedup, log


def test_normalize_symbol_binance_coinbase():
    b = normalize_symbol("BTCUSDT")
    c = normalize_symbol("BTC-USD")
    assert b["canonical_asset"] == "BTC"
    assert c["canonical_asset"] == "BTC"
    assert b["internal_pair"] == c["internal_pair"]


def test_sanitize_user_facing_error_no_venue_leakage():
    assert "binance" not in sanitize_user_facing_error("binance API error 503").lower()
    assert sanitize_user_facing_error("binance API error") == "Source temporarily unavailable"
    assert sanitize_user_facing_error("rate_limit_exceeded") == "Source rate limited — retry shortly"


def test_cross_reference_primary_and_aggregator():
    results = [
        ConnectorFetchResult(
            connector_id="binance",
            ok=True,
            quote=CanonicalPriceQuote(
                connector_id="binance", exchange="binance", asset="BTC", pair="BTCUSDT",
                price_usd=100_000, source="t", fetched_at="2026-01-01T00:00:00+00:00",
            ),
        ),
        ConnectorFetchResult(
            connector_id="okx",
            ok=True,
            quote=CanonicalPriceQuote(
                connector_id="okx", exchange="okx", asset="BTC", pair="BTC-USDT",
                price_usd=100_100, source="t", fetched_at="2026-01-01T00:00:00+00:00",
            ),
        ),
        ConnectorFetchResult(
            connector_id="coingecko",
            ok=True,
            quote=CanonicalPriceQuote(
                connector_id="coingecko", exchange="coingecko", asset="BTC", pair="BTC",
                price_usd=100_050, source="t", fetched_at="2026-01-01T00:00:00+00:00",
            ),
        ),
    ]
    xref = cross_reference_quotes(results)
    assert xref["ok"] is True
    assert xref["cross_reference_verified"] is True
    assert xref["primary_source_count"] == 2
    assert xref["aggregator_source_count"] == 1


def test_deduplicate_records(isolated_ingestion_paths):
    records = [
        {"canonical_asset": "BTC", "price_usd": 100},
        {"canonical_asset": "BTC", "price_usd": 100},
    ]
    unique, skipped = fdi.deduplicate_records(records)
    assert len(unique) == 1
    assert skipped == 1


def test_track_freshness(isolated_ingestion_paths):
    records = [
        {
            "canonical_asset": "ETH",
            "timestamp": "2026-08-24T12:00:00+00:00",
            "source_tier": "primary",
            "connector_id": "binance",
        }
    ]
    result = fdi.track_freshness(records)
    assert result["tracked_assets"] >= 1


def test_normalize_market_record():
    rec = fdi.normalize_market_record(
        {
            "asset": "BTC",
            "pair": "BTCUSDT",
            "price_usd": 100000,
            "connector_id": "binance",
            "fetched_at": "2026-08-24T12:00:00+00:00",
        },
        source_tier="primary",
    )
    assert rec["schema"] == "canonical_market_v1"
    assert rec["canonical_asset"] == "BTC"
    assert rec["timestamp_tz"] == "UTC"


def test_ingestion_layer_status(isolated_ingestion_paths):
    status = fdi.ingestion_layer_status()
    assert status["feature_id"] == 137
    assert status["user_facing"] is False
    assert "#194" in status["integrated_features"]
    assert status["retention_days"] >= 730


def test_aggregator_status_merged():
    status = fdi.aggregator_cross_reference_status("BTC")
    assert status["feature_id"] == 138
    assert "backup" in status["policy"].lower()


@pytest.mark.asyncio
async def test_run_ingestion_cycle_mocked(isolated_ingestion_paths, monkeypatch):
    async def fake_collect(asset, **kwargs):
        return {
            "asset": asset,
            "primary_records": [
                fdi.normalize_market_record(
                    {
                        "asset": asset,
                        "pair": f"{asset}USDT",
                        "price_usd": 1000,
                        "connector_id": "binance",
                        "fetched_at": "2026-08-24T12:00:00+00:00",
                    },
                    source_tier="primary",
                )
            ],
            "aggregator_records": [],
            "cross_reference": {"ok": True, "cross_reference_verified": True},
        }

    monkeypatch.setattr(fdi, "collect_market_data", fake_collect)
    result = await fdi.run_ingestion_cycle(assets=["BTC"])
    assert result["ok"] is True
    assert result["accuracy_met"] is True
    assert result["feature_id"] == 137
