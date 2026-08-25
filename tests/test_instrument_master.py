"""Tests — #268 Instrument Master merged into Wave 01 Data Engine."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from blackdark.data import instrument_master as im


@pytest.fixture
def isolated_seed(tmp_path, monkeypatch):
    seed = tmp_path / "instrument_master_seed.json"
    seed.write_text(
        json.dumps({
            "feature_id": 268,
            "last_updated": "2026-08-25",
            "compute_budget": "pre-defined cap",
            "auto_archive_threshold_usd": 1000,
            "auto_archive_days": 90,
            "cost_tiers": {"hot_pct": 5, "warm_pct": 15, "cold_pct": 80},
            "sla": {
                "latency_ms_top_5k": 500,
                "coverage_accuracy_pct": 99.2,
                "coverage_benchmark": "CoinGecko",
                "uptime_sla_pct": 99.9,
            },
            "coverage": {
                "validated_instruments": 48250,
                "accuracy_vs_coingecko_pct": 99.2,
            },
            "instruments": [
                {
                    "instrument_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                    "venue": "binance",
                    "venue_type": "CEX",
                    "asset_class": "spot",
                    "base": "BTC",
                    "quote": "USDT",
                    "mapping_confidence_pct": 99.5,
                    "min_confidence_pct": 80,
                    "last_verified": "2026-08-25T20:00:00+00:00",
                    "tier": "hot",
                    "daily_volume_usd": 28500000000,
                    "source_tag": "binance:spot:BTCUSDT",
                    "reused_table": "ohlcv_data",
                },
                {
                    "instrument_id": "f6a7b8c9-d0e1-2345-f012-456789012345",
                    "venue": "gateio",
                    "venue_type": "CEX",
                    "asset_class": "spot",
                    "base": "ALT",
                    "quote": "USDT",
                    "mapping_confidence_pct": 72.0,
                    "min_confidence_pct": 80,
                    "last_verified": "2026-08-20T08:00:00+00:00",
                    "tier": "cold",
                    "daily_volume_usd": 850,
                    "source_tag": "gateio:spot:ALTUSDT",
                    "reused_table": "ohlcv_data",
                },
            ],
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(im, "_SEED_PATH", seed)
    return seed


def test_scope_lock(isolated_seed):
    scope = im.build_scope_lock_display()
    assert "crypto spot + perps + options only" in scope["display"]
    assert "TradFi/equities = Wave 3" in scope["display"]
    assert scope["validated_count"] == 50_000
    assert scope["no_expansion_without_validation"] is True


def test_instrument_mapping_schema(isolated_seed):
    record = json.loads(isolated_seed.read_text())["instruments"][0]
    mapping = im.build_instrument_mapping(record)
    assert "Instrument ID:" in mapping["display"]
    assert "Venue: CEX" in mapping["display"]
    assert "Asset class: spot" in mapping["display"]
    assert "Mapping confidence: 99.5%" in mapping["display"]
    assert mapping["no_mapping_no_ingestion"] is True
    assert mapping["ingestion_allowed"] is True


def test_low_confidence_blocks_ingestion(isolated_seed):
    record = json.loads(isolated_seed.read_text())["instruments"][1]
    mapping = im.build_instrument_mapping(record)
    assert mapping["mapping_confidence_pct"] == 72.0
    assert mapping["ingestion_allowed"] is False


def test_deduplication_audit(isolated_seed):
    audit = im.build_deduplication_audit()
    assert "ohlcv_data" in audit["reused_tables"]
    assert audit["no_duplicate_pipelines"] is True
    assert audit["expand_not_rebuild"] is True


def test_cost_gate_tiers(isolated_seed):
    gate = im.build_cost_gate()
    assert gate["tiers"]["hot"]["share_pct"] == 5
    assert gate["tiers"]["warm"]["share_pct"] == 15
    assert gate["tiers"]["cold"]["share_pct"] == 80
    assert "Auto-archive" in gate["display"]
    assert gate["no_unbounded_cost"] is True


def test_acceptance_criteria_expanded(isolated_seed):
    criteria = im.build_acceptance_criteria()
    assert criteria["instrument_mappings"] is True
    assert criteria["latency_sla_ms_top_5k"] == 500
    assert criteria["coverage_accuracy_pct"] >= 99
    assert criteria["uptime_sla_pct"] == 99.9
    assert criteria["provenance_per_tick"] is True


def test_not_standalone_merged(isolated_seed):
    status = im.instrument_master_status()
    assert status["feature_id"] == 268
    assert status["standalone"] is False
    assert status["archived_standalone_ticket"] is True
    assert status["merged_into"] == "Wave 01 Data Engine"
    assert status["mapping_quality_is_product"] is True


def test_list_mappings_filter_tier(isolated_seed):
    result = im.list_instrument_mappings(tier="hot")
    assert result["count"] == 1
    assert result["instruments"][0]["tier"] == "hot"


def test_get_instrument_by_id(isolated_seed):
    result = im.get_instrument_mapping("a1b2c3d4-e5f6-7890-abcd-ef1234567890")
    assert result["ok"] is True
    assert result["provenance"]["no_duplicate_pipeline"] is True
    assert result["provenance"]["source_tag"] == "binance:spot:BTCUSDT"


def test_api_routes(isolated_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/v1/data/instrument-master/status").status_code == 200
    status = c.get("/api/v1/data/instrument-master/status").json()
    assert status["feature_id"] == 268
    assert status["standalone"] is False
    mappings = c.get("/api/v1/data/instrument-master/mappings?tier=hot")
    assert mappings.status_code == 200
    assert mappings.json()["count"] >= 1
    detail = c.get("/api/v1/data/instrument-master/mappings/a1b2c3d4-e5f6-7890-abcd-ef1234567890")
    assert detail.status_code == 200


def test_full_seed_exists():
    seed = json.loads(Path("data/instrument_master_seed.json").read_text(encoding="utf-8"))
    assert seed["feature_id"] == 268
    assert seed["standalone"] is False
    assert len(seed["instruments"]) >= 5
    assert seed["coverage"]["validated_instruments"] == 48250
