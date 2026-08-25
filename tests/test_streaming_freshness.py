"""Tests — Sprint 0 Streaming Infrastructure (#218 + #222) + Freshness Assurance (#219)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import freshness_assurance as fa
from bd_platform import streaming_infrastructure as si


@pytest.fixture
def isolated_streaming_seed(tmp_path, monkeypatch):
    seed = tmp_path / "streaming_infrastructure_seed.json"
    seed.write_text(
        json.dumps({
            "slos": {
                "latency_ms": 500,
                "reconnect_ms": 3000,
                "slo_display": "Latency: < 500ms | Gap: auto-backfill | Reconnect: < 3s",
            },
            "rate_limits": {"messages_per_second": 50},
            "feeds": {
                "market:multiplex": {
                    "assets": ["BTC", "ETH"],
                    "multiplexed": True,
                },
            },
            "sample_gaps": [
                {
                    "feed_id": "chain:ethereum",
                    "gap_start": 100,
                    "gap_end": 102,
                    "backfilled": True,
                    "backfill_blocks": [100, 101, 102],
                },
            ],
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(si, "_SEED_PATH", seed)
    return seed


@pytest.fixture
def isolated_freshness_seed(tmp_path, monkeypatch):
    seed = tmp_path / "freshness_assurance_seed.json"
    store = tmp_path / "freshness_assurance.json"
    seed.write_text(
        json.dumps({
            "clock_sync": {"synced": True, "max_drift_ms": 50, "display": "NTP-synced"},
            "stale_thresholds_ms": {"market:multiplex": 500, "default": 1000},
            "health_check_interval_minutes": 5,
            "sample_feeds": [
                {
                    "feed_id": "market:multiplex",
                    "asset": "BTC",
                    "source_timestamp_utc": "2026-08-25T14:00:00.000+00:00",
                    "received_timestamp_utc": "2026-08-25T14:00:00.250+00:00",
                    "latency_ms": 250,
                },
            ],
            "stale_feed_sample": {
                "feed_id": "market:multiplex",
                "asset": "SOL",
                "stale": True,
                "age_ms": 300000,
            },
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(fa, "_SEED_PATH", seed)
    monkeypatch.setattr(fa, "_STORE_PATH", store)
    fa._feed_state.clear()
    fa._latency_history.clear()
    return seed


# ── #218 + #222 Streaming Infrastructure ─────────────────────────────────────


def test_stream_slos(isolated_streaming_seed):
    slos = si.get_stream_slos()
    assert slos["latency_ms"] == 500
    assert "auto-backfill" in slos["slo_display"]
    assert "Reconnect" in slos["slo_display"]


def test_multiplex_single_connection(isolated_streaming_seed):
    cfg = si.get_multiplex_feed_config(["BTC", "ETH"])
    assert cfg["multiplexed"] is True
    assert cfg["single_connection"] is True
    assert cfg["transport"] == "websocket"
    assert "BTC" in cfg["assets"]


def test_backfill_on_reconnect(isolated_streaming_seed):
    result = si.backfill_on_reconnect("chain:ethereum")
    assert result["backfilled"] is True
    assert result["no_data_loss"] is True
    assert "auto-backfilled" in result["backfill_display"]


def test_rate_limiting(isolated_streaming_seed):
    si._rate_counters.clear()
    for _ in range(50):
        assert si.check_rate_limit("test-client")["allowed"] is True
    assert si.check_rate_limit("test-client")["rate_limited"] is True


def test_connection_health(isolated_streaming_seed):
    si._connection_registry.clear()
    si.register_connection("c1", assets=["BTC"])
    health = si.get_connection_health()
    assert health["active_connections"] == 1
    assert "Latency" in health["health_display"]


def test_streaming_status(isolated_streaming_seed):
    status = si.streaming_infrastructure_status()
    assert 218 in status["feature_ids"]
    assert 222 in status["feature_ids"]
    assert status["stream_multiplexing"] is True


# ── #219 Freshness Assurance ───────────────────────────────────────────────────


def test_clock_sync(isolated_freshness_seed):
    clock = fa.get_clock_sync_status()
    assert clock["ntp_synced"] is True
    assert "NTP" in clock["display"]


def test_timestamp_separation(isolated_freshness_seed):
    event = fa.record_freshness_event(
        feed_id="market:multiplex",
        asset="BTC",
        source_timestamp_utc="2026-08-25T14:00:00.000+00:00",
        received_timestamp_utc="2026-08-25T14:00:00.250+00:00",
    )
    assert "Source:" in event["freshness_display"]
    assert "Received:" in event["freshness_display"]
    assert event["latency_ms"] == 250.0


def test_no_stale_to_zero(isolated_freshness_seed):
    fa._feed_state["market:multiplex:SOL"] = {
        "feed_id": "market:multiplex",
        "asset": "SOL",
        "stale": True,
        "value": None,
        "status": "Data Stale",
    }
    result = fa.get_feed_freshness("market:multiplex", "SOL")
    assert result["value"] is None
    assert result["no_stale_to_zero"] is True
    assert result["status"] == "Data Stale"


def test_fail_closed_policy(isolated_freshness_seed):
    fa._feed_state["market:multiplex:STALE"] = {
        "stale": True, "value": None, "latency_ms": 2000,
    }
    result = fa.get_feed_freshness("market:multiplex", "STALE")
    assert result["fail_closed"] is True


def test_percentile_evidence(isolated_freshness_seed):
    for lat in [200, 220, 250, 300, 800, 1500]:
        fa._latency_history["market:multiplex:BTC"].append(float(lat))
    pct = fa.get_percentile_latency("market:multiplex", "BTC")
    assert "p50:" in pct["percentile_display"]
    assert "p95:" in pct["percentile_display"]
    assert "p99:" in pct["percentile_display"]


def test_historical_retention(isolated_freshness_seed):
    hist = fa.get_freshness_history("market:multiplex")
    assert hist["retention_max"] == 500
    assert len(hist["historical_events"]) >= 1


def test_automated_health_check(isolated_freshness_seed):
    check = fa.run_freshness_health_check()
    assert check["health_check_interval_minutes"] == 5
    assert check["stale_policy_check"]["no_stale_to_zero"] is True
    test_types = {r.get("test") for r in check["results"]}
    assert "delayed_feed" in test_types
    assert "missing_feed" in test_types
    assert "out_of_order_feed" in test_types


def test_freshness_dashboard(isolated_freshness_seed, isolated_streaming_seed):
    dash = fa.get_freshness_dashboard()
    assert dash["fail_closed_policy"] is True
    assert dash["transport"] == "websocket"
    assert len(dash["feeds"]) >= 1


def test_freshness_status(isolated_freshness_seed):
    status = fa.freshness_assurance_status()
    assert status["feature_id"] == 219
    assert status["no_stale_to_zero"] is True


def test_api_routes(isolated_streaming_seed, isolated_freshness_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/streaming/status").status_code == 200
    assert c.get("/api/platform/streaming/slos").status_code == 200
    assert c.get("/api/platform/freshness/status").status_code == 200
    assert c.get("/api/platform/freshness/dashboard").status_code == 200
    assert c.get("/api/platform/freshness/health-check").status_code == 200


def test_full_seeds_exist():
    s1 = json.loads(Path("data/streaming_infrastructure_seed.json").read_text(encoding="utf-8"))
    s2 = json.loads(Path("data/freshness_assurance_seed.json").read_text(encoding="utf-8"))
    assert "market:multiplex" in s1["feeds"]
    assert s2["clock_sync"]["synced"] is True
