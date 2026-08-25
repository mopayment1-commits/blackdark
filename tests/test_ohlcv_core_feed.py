"""Tests — #217 OHLCV Core Feed."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import ohlcv_core_feed as ocf


@pytest.fixture
def isolated_ohlcv(tmp_path, monkeypatch):
    seed = tmp_path / "ohlcv_core_seed.json"
    store = tmp_path / "ohlcv_core_feed.json"
    seed.write_text(
        json.dumps([
            {
                "id": "test-1h",
                "asset": "BTC",
                "interval": "1h",
                "open_time_utc": "2026-08-25T11:00:00+00:00",
                "close_time_utc": "2026-08-25T12:00:00+00:00",
                "sources": {
                    "binance": {"open": 100.0, "high": 110.0, "low": 95.0, "close": 105.0, "volume": 100.0, "available": True},
                    "okx": {"open": 101.0, "high": 109.0, "low": 96.0, "close": 104.0, "volume": 90.0, "available": True},
                    "bybit": {"open": 100.5, "high": 108.0, "low": 95.5, "close": 104.5, "volume": 95.0, "available": True},
                },
                "onchain_volume_proxy": 280.0,
            },
            {
                "id": "test-gap",
                "asset": "BTC",
                "interval": "1h",
                "open_time_utc": "2026-08-25T12:00:00+00:00",
                "close_time_utc": "2026-08-25T13:00:00+00:00",
                "sources": {
                    "binance": {"open": 105.0, "high": 115.0, "low": 100.0, "close": 110.0, "volume": 120.0, "available": True},
                    "okx": {"open": 104.0, "high": 114.0, "low": 99.0, "close": 109.0, "volume": 100.0, "available": True},
                    "bybit": {"open": 0, "high": 0, "low": 0, "close": 0, "volume": 0, "available": False},
                },
                "onchain_volume_proxy": 300.0,
            },
        ]),
        encoding="utf-8",
    )
    monkeypatch.setattr(ocf, "_SEED_PATH", seed)
    monkeypatch.setattr(ocf, "_STORE_PATH", store)
    return store


def test_interval_exactness_1h(isolated_ohlcv):
    result = ocf.validate_interval_exactness(
        "2026-08-25T11:00:00+00:00",
        "2026-08-25T12:00:00+00:00",
        "1h",
    )
    assert result["exact"] is True
    assert result["boundary_ok"] is True


def test_interval_exactness_violation():
    result = ocf.validate_interval_exactness(
        "2026-08-25T11:00:00+00:00",
        "2026-08-25T11:37:00+00:00",
        "1h",
    )
    assert result["exact"] is False


def test_multi_source_aggregation(isolated_ohlcv):
    candle = ocf.get_ohlcv_candle("test-1h")["candle"]
    assert candle["multi_source"]["source_count"] == 3
    assert candle["ohlcv"]["high"] == 110.0
    assert candle["ohlcv"]["low"] == 95.0


def test_gap_handling_no_interpolation(isolated_ohlcv):
    candle = ocf.get_ohlcv_candle("test-gap")["candle"]
    assert "Interpolated: No" in candle["multi_source"]["gap_display"]
    assert candle["multi_source"]["interpolated"] is False


def test_volume_validation(isolated_ohlcv):
    candle = ocf.get_ohlcv_candle("test-1h")["candle"]
    assert "volume_validation" in candle
    assert candle["volume_validation"]["validated"] is True


def test_batch_not_realtime(isolated_ohlcv):
    status = ocf.ohlcv_core_feed_status()
    assert status["batch_not_realtime"] is True
    assert status["realtime_ticks_feature"] == 212


def test_list_filter_by_asset(isolated_ohlcv):
    feed = ocf.list_ohlcv_candles(asset="BTC")
    assert feed["count"] >= 1


def test_full_seed_exists():
    rows = json.loads(Path("data/ohlcv_core_seed.json").read_text(encoding="utf-8"))
    assert len(rows) >= 4


def test_api_routes():
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    status = c.get("/api/platform/ohlcv/status")
    assert status.status_code == 200
    assert status.json()["feature_id"] == 217

    candles = c.get("/api/platform/ohlcv/candles?asset=BTC&interval=1h")
    assert candles.status_code == 200
    assert candles.json()["interval_exactness_required"] is True
