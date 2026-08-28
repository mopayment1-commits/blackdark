"""Tests — #833 API Throttling + #834 Data Engine Data Pipe."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import api_gateway_throttling as throttle
from bd_platform import data_engine_data_pipe as pipe


@pytest.fixture
def gw_seed() -> dict:
    return json.loads(Path("data/api_gateway_seed.json").read_text(encoding="utf-8"))


@pytest.fixture
def pipe_seed() -> dict:
    return json.loads(Path("data/data_engine_data_pipe_seed.json").read_text(encoding="utf-8"))


# --- #833 ---


def test_833_status(gw_seed):
    status = throttle.throttling_status_833(seed=gw_seed)
    assert status["standalone_rejected"] is True
    assert status["component"] == "throttling_middleware"
    assert status["429_with_retry_after"] is True
    assert status["cache_backend"] == "redis"


def test_833_tier_rate_limits(gw_seed):
    assert throttle.get_rate_limit_for_role("free", seed=gw_seed) == 100
    assert throttle.get_rate_limit_for_role("pro", seed=gw_seed) == 1000
    assert throttle.get_rate_limit_for_role("institution", seed=gw_seed) == 10000


def test_833_429_retry_after(gw_seed):
    throttle.reset_throttle_for_tests()
    for _ in range(100):
        t = throttle.check_throttle_833("u1", "free", seed=gw_seed)
        if t.get("allowed"):
            throttle.increment_throttle_833("u1", "free", seed=gw_seed)
    denied = throttle.check_throttle_833("u1", "free", seed=gw_seed)
    resp = throttle.build_throttle_response_429_833(denied, seed=gw_seed)
    assert resp["status_code"] == 429
    assert resp["headers"]["Retry-After"] == "60"


def test_833_cache_ttl_range(gw_seed):
    ttl = throttle.get_cache_ttl_for_endpoint("market_overview", seed=gw_seed)
    assert 3600 <= ttl <= 86400


def test_833_fallback(gw_seed):
    result = throttle.fetch_with_fallback_833(
        "market_overview",
        primary_fn=lambda: {"ok": False},
        secondary_fn=lambda: {"ok": True, "data": "cached"},
        seed=gw_seed,
    )
    assert result["fallback_used"] is True
    assert result["source"] == "secondary"


def test_833_developer_tier_ref(gw_seed):
    panel = throttle.build_throttling_panel_833(seed=gw_seed)
    assert panel["developer_tier_ref"] == 831


def test_833_e2e(gw_seed):
    e2e = throttle.run_throttling_e2e_833(seed=gw_seed)
    assert e2e["all_passed"] is True


# --- #834 ---


def test_834_status(pipe_seed):
    status = pipe.data_pipe_status_834(seed=pipe_seed)
    assert status["standalone_rejected"] is True
    assert status["component"] == "data_pipe"
    assert status["streaming_transport"] == "websocket"
    assert status["delivery_guarantee"] == "at_least_once"
    assert status["backpressure_no_drop"] is True


def test_834_streaming_websocket(pipe_seed):
    stream = pipe.build_streaming_feed_config_834("BTC", seed=pipe_seed)
    assert stream["ok"] is True
    assert stream["transport"] == "websocket"
    assert stream["no_polling"] is True


def test_834_batch_export(pipe_seed):
    daily = pipe.build_batch_export_config_834("daily", seed=pipe_seed)
    hourly = pipe.build_batch_export_config_834("hourly", seed=pipe_seed)
    assert daily["ok"] is True
    assert hourly["ok"] is True


def test_834_schema_versions(pipe_seed):
    v10 = pipe.get_schema_contract_834("v1.0", seed=pipe_seed)
    v11 = pipe.get_schema_contract_834("v1.1", seed=pipe_seed)
    assert v10["ok"] is True
    assert v11["backward_compatible"] is True


def test_834_replay_deterministic(pipe_seed):
    replay = pipe.replay_feed_from_checkpoint_834("ckpt-btc-20260827", seed=pipe_seed)
    assert replay["ok"] is True
    assert replay["deterministic"] is True
    assert replay["message_count"] == 3


def test_834_message_quality_flags(pipe_seed):
    msg = pipe.emit_normalized_feed_message_834(
        "price_stream_btc", {"price": 60287.03}, seed=pipe_seed,
    )
    envelope = msg["message"]
    assert "timestamp" in envelope
    assert envelope["quality"]["freshness"] == "live"


def test_834_backpressure_no_drop(pipe_seed):
    bp = pipe.simulate_backpressure_834(consumer_lag_ms=5000, seed=pipe_seed)
    assert bp["backpressure_triggered"] is True
    assert bp["message_dropped"] is False
    assert bp["action"] == "queue_and_alert"


def test_834_e2e(pipe_seed):
    e2e = pipe.run_data_pipe_e2e_834(seed=pipe_seed)
    assert e2e["all_passed"] is True


def test_833_834_api_routes():
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/intelligence-ledger/api-gateway/throttling/status").status_code == 200
    e2e833 = c.get("/api/platform/intelligence-ledger/api-gateway/throttling/e2e")
    assert e2e833.status_code == 200
    assert e2e833.json()["all_passed"] is True

    assert c.get("/api/platform/intelligence-ledger/data-engine/data-pipe/status").status_code == 200
    stream = c.get("/api/platform/intelligence-ledger/data-engine/data-pipe/streaming?asset=BTC")
    assert stream.status_code == 200
    assert stream.json()["transport"] == "websocket"
    e2e834 = c.get("/api/platform/intelligence-ledger/data-engine/data-pipe/e2e")
    assert e2e834.status_code == 200
    assert e2e834.json()["all_passed"] is True
