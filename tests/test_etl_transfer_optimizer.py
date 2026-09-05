"""Tests — Local Data ETL (#118) + Cross-Platform Transfer Optimizer (#119)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform.cross_platform_transfer_optimizer import (
    optimize_cross_platform_transfer,
    transfer_optimizer_status,
    _format_headline,
)
from bd_platform.local_data_etl import (
    transform_record,
    ensure_schema,
    query_clean_data,
    load_structured,
    etl_health_status,
    _validate_record,
)
from bd_platform.transfer_network_utility import (
    rank_transfer_networks,
    set_user_network_preference,
    get_user_network_preference,
    transfer_network_status,
    _composite_score,
)


def test_transform_record_market_valid():
    raw = {"asset": "BTC", "mark_price": 65000.0, "timestamp": "2026-01-01T00:00:00Z"}
    row = transform_record("market", "futures_snapshot", raw, source="test")
    assert row["valid"] is True
    assert row["asset"] == "BTC"
    assert row["quality_score"] >= 0.95
    assert len(row["checksum"]) == 64


def test_transform_record_rejects_bad_price():
    raw = {"asset": "BTC", "mark_price": -1.0, "timestamp": "2026-01-01T00:00:00Z"}
    valid, score, issues = _validate_record("market", "futures_snapshot", raw)
    assert valid is False or score < 1.0
    assert "non_positive_price" in issues


@pytest.mark.asyncio
async def test_etl_schema_and_load_query(tmp_path, monkeypatch):
    db_path = tmp_path / "etl_test.db"
    meta_path = tmp_path / "etl_meta.json"
    monkeypatch.setattr("config.DB_PATH", db_path)
    monkeypatch.setattr("config.DATA_DIR", tmp_path)
    monkeypatch.setattr("bd_platform.local_data_etl._ETL_META_PATH", meta_path)
    monkeypatch.setattr("config.DATABASE_URL", "")

    await ensure_schema()
    rows = [
        transform_record(
            "market",
            "futures_snapshot",
            {"asset": "ETH", "mark_price": 3000.0, "timestamp": "2026-01-01T00:00:00Z"},
            source="test",
        )
    ]
    result = await load_structured(rows)
    assert result["loaded"] == 1

    q = await query_clean_data(domain="market", asset="ETH", limit=10, use_cache=False)
    assert q["ok"] is True
    assert q["count"] >= 1
    assert q["sla_met"] is True
    assert q["records"][0]["asset"] == "ETH"


@pytest.mark.asyncio
async def test_etl_health_status():
    status = await etl_health_status()
    assert status["ok"] is True
    assert status["feature"] == "#118"
    assert status["user_facing"] is False
    assert "postgresql" in status["stores"]


def test_transfer_network_composite_score():
    score = _composite_score(speed=80, cost=90, security=95)
    assert 80 <= score <= 100


@pytest.mark.asyncio
async def test_rank_transfer_networks_usdt():
    result = await rank_transfer_networks("USDT", amount_usd=1000.0)
    assert result["ok"] is True
    assert result["feature"] == "#108"
    assert result["sla_met"] is True
    assert len(result["recommendations"]) >= 5
    assert result["best_network"]["rank"] == 1


def test_user_network_preference_roundtrip(tmp_path, monkeypatch):
    prefs = tmp_path / "prefs.json"
    monkeypatch.setattr("bd_platform.transfer_network_utility._PREFS_PATH", prefs)

    saved = set_user_network_preference("user-1", "USDT", "bep20")
    assert saved["ok"] is True
    assert saved["feature"] == "#120"

    pref = get_user_network_preference("user-1", "USDT")
    assert pref is not None
    assert pref["network_id"] == "bep20"


@pytest.mark.asyncio
async def test_cross_platform_optimizer_binance_kraken():
    result = await optimize_cross_platform_transfer(
        asset="USDT",
        source_cex="binance",
        dest_cex="kraken",
        amount_usd=1000.0,
    )
    assert result["ok"] is True
    assert result["feature"] == "#119"
    assert result["mode"] == "fee_saving_optimizer"
    assert result["sla_met"] is True
    assert "profit" not in result["headline"].lower()
    assert "ربح" not in result["headline"]
    assert result["optimal_path"]["total_cost_usd"] > 0
    assert result["optimal_path"]["duration_min"] > 0
    assert "disclaimer" in result
    assert "#108" in result["integrated_features"]


def test_format_headline_example():
    path = {
        "steps": ["Binance", "BEP20", "Bridge", "ERC20", "Kraken"],
        "total_cost_usd": 2.5,
        "duration_min": 4,
    }
    headline = _format_headline("USDT", "binance", "kraken", path)
    assert "Binance" in headline
    assert "Kraken" in headline
    assert "$2.5" in headline
    assert "4 minutes" in headline
    assert "profit" not in headline.lower()


def test_transfer_optimizer_status():
    status = transfer_optimizer_status()
    assert status["feature"] == "#119"
    assert "binance" in status["supported_cex"]
    assert status["mode"] == "fee_saving_optimizer"


def test_transfer_network_status():
    status = transfer_network_status()
    assert status["feature"] == "#108"
    assert "USDT" in status["supported_assets"]
