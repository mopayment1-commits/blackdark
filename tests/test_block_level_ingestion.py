"""Tests — #212 Block-Level Ingestion Layer."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import block_level_ingestion as bli


@pytest.fixture
def isolated_block_store(tmp_path, monkeypatch):
    seed = tmp_path / "block_streams_seed.json"
    store = tmp_path / "block_level_ingestion.json"
    seed.write_text(
        json.dumps({
            "chains": {
                "ethereum": {
                    "chain_id": "ethereum",
                    "latest_block": 100,
                    "tier": "enterprise",
                    "blocks": [
                        {"height": 98, "hash": "0x98", "timestamp_utc": "2026-08-25T12:00:00+00:00", "tx_count": 10, "latency_ms": 300},
                        {"height": 99, "hash": "0x99", "timestamp_utc": "2026-08-25T12:00:12+00:00", "tx_count": 12, "latency_ms": 280},
                        {"height": 101, "hash": "0x101", "timestamp_utc": "2026-08-25T12:00:36+00:00", "tx_count": 11, "latency_ms": 320},
                        {"height": 102, "hash": "0x102", "timestamp_utc": "2026-08-25T12:00:48+00:00", "tx_count": 14, "latency_ms": 290},
                    ],
                    "reorgs": [],
                },
                "bitcoin": {
                    "chain_id": "bitcoin",
                    "latest_block": 50,
                    "tier": "basic",
                    "blocks": [
                        {"height": 48, "hash": "btc48", "timestamp_utc": "2026-08-25T12:00:00+00:00", "tx_count": 100, "latency_ms": 2500},
                        {"height": 49, "hash": "btc49", "timestamp_utc": "2026-08-25T12:05:00+00:00", "tx_count": 110, "latency_ms": 3200},
                        {"height": 50, "hash": "btc50", "timestamp_utc": "2026-08-25T12:10:00+00:00", "tx_count": 105, "latency_ms": 2800},
                    ],
                    "reorgs": [],
                },
            }
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(bli, "_SEED_PATH", seed)
    monkeypatch.setattr(bli, "_STORE_PATH", store)
    return store


def test_latency_slo_measured(isolated_block_store):
    slo = bli.measure_latency_slo(chain="ethereum")
    eth = slo["chains"]["ethereum"]
    assert eth["slo_measured"] is True
    assert "Block-to-API:" in eth["latency_slo_display"]
    assert "p95:" in eth["latency_slo_display"]


def test_no_false_realtime_enterprise(isolated_block_store):
    label = bli.classify_freshness_label(300, tier="enterprise")
    assert label == "Real-Time"


def test_no_false_realtime_basic(isolated_block_store):
    label = bli.classify_freshness_label(300, tier="basic")
    assert label == "Block-Level"


def test_near_realtime_over_1s(isolated_block_store):
    label = bli.classify_freshness_label(2500, tier="basic")
    assert label == "Near Real-Time"


def test_gap_detection(isolated_block_store):
    blocks = [
        {"height": 98}, {"height": 99}, {"height": 101},
    ]
    gaps = bli.detect_block_gaps(blocks)
    assert len(gaps) == 1
    assert gaps[0]["missing_count"] == 1
    assert gaps[0]["gap_start"] == 100


def test_reorg_handling(isolated_block_store):
    result = bli.handle_reorg("ethereum", 100, "0xold", "0xnew")
    assert "Chain Reorg Detected" in result["display"]
    assert "Block 100 replaced" in result["display"]


def test_gap_alerts_automated(isolated_block_store):
    alerts = bli.get_gap_alerts(chain="ethereum")
    assert alerts["automated"] is True
    assert alerts["alert_count"] >= 1


def test_sub_second_enterprise_only(isolated_block_store):
    feeds = bli.list_block_feeds()
    eth = next(f for f in feeds["feeds"] if f["chain_id"] == "ethereum")
    btc = next(f for f in feeds["feeds"] if f["chain_id"] == "bitcoin")
    assert any(b.get("sub_second") for b in eth["blocks"])
    assert not any(b.get("sub_second") for b in btc["blocks"])


def test_minute_aggregation(isolated_block_store):
    bars = bli.aggregate_minute_bars("ethereum")
    assert bars["ok"] is True
    assert bars["aggregation"] == "minute"
    assert len(bars["bars"]) >= 1


def test_status_policies(isolated_block_store):
    status = bli.block_level_ingestion_status()
    assert status["latency_slo_measured"] is True
    assert status["reorg_handling"] is True
    assert status["gap_detection"] is True
    assert status["no_false_realtime_claims"] is True
    assert status["sub_second_enterprise_only"] is True


def test_full_seed_file_exists():
    rows = json.loads(Path("data/block_streams_seed.json").read_text(encoding="utf-8"))
    assert len(rows["chains"]) >= 3


def test_api_routes():
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    status = c.get("/api/platform/block-ingestion/status")
    assert status.status_code == 200
    assert status.json()["feature_id"] == 212

    slo = c.get("/api/platform/block-ingestion/latency-slo")
    assert slo.status_code == 200
    assert slo.json()["latency_slo_measured"] is True

    gaps = c.get("/api/platform/block-ingestion/gaps")
    assert gaps.status_code == 200
