"""Silent infrastructure tests — Feature #65 (HA) + Feature #79 (OHLCV)."""

from __future__ import annotations

import pytest


# --- Feature #79 OHLCV ---


def test_aggregate_trades_to_candles():
    from blackdark.data.ohlcv_aggregator import aggregate_trades_to_candles

    trades = [
        {"price": 100, "qty": 1, "ts_ms": 3_600_000},
        {"price": 105, "qty": 2, "ts_ms": 3_600_500},
        {"price": 98, "qty": 1, "ts_ms": 3_601_000},
        {"price": 110, "qty": 3, "ts_ms": 7_200_000},
    ]
    candles = aggregate_trades_to_candles(trades, interval="1h")
    assert len(candles) == 2
    assert candles[0]["o"] == 100
    assert candles[0]["h"] == 105
    assert candles[0]["l"] == 98
    assert candles[0]["c"] == 98
    assert candles[0]["v"] == 4
    assert candles[1]["o"] == 110


def test_detect_gaps():
    from blackdark.data.ohlcv_aggregator import detect_gaps

    candles = [{"t": 0}, {"t": 7_200_000}]
    gaps = detect_gaps(candles, interval="1h")
    assert len(gaps) == 1
    assert gaps[0]["missing_buckets"] == 1


def test_replay_fill_gaps():
    from blackdark.data.ohlcv_aggregator import replay_fill_gaps

    candles = [
        {"t": 0, "o": 100, "h": 100, "l": 100, "c": 100, "v": 1, "n": 1},
        {"t": 7_200_000, "o": 110, "h": 110, "l": 110, "c": 110, "v": 1, "n": 1},
    ]
    trades = [{"price": 105, "qty": 2, "ts_ms": 3_600_000}]
    merged, filled = replay_fill_gaps(candles, trades, interval="1h")
    assert filled == 1
    assert len(merged) == 3
    assert any(c["t"] == 3_600_000 for c in merged)


@pytest.mark.asyncio
async def test_ohlcv_spine_binance_fallback(monkeypatch):
    async def fake_klines(pair, interval="1h", limit=100):
        return [100.0, 101.0, 102.0]

    async def fake_candles(*args, **kwargs):
        return []

    monkeypatch.setattr("market_context.fetch_binance_klines", fake_klines)
    monkeypatch.setattr("redis_price_cache.get_ohlc_candles", fake_candles)

    from ohlcv_spine import fetch_ohlcv_candles

    pack = await fetch_ohlcv_candles("BTCUSDT", interval="1h", limit=10)
    assert pack["count"] >= 3
    assert "binance" in pack["source"]


@pytest.mark.asyncio
async def test_resolve_ohlcv_closes_cap646(monkeypatch):
    async def fake_fetch(symbol, interval="1h", limit=100):
        return [50.0, 51.0], "test_spine"

    monkeypatch.setattr("ohlcv_spine.fetch_ohlcv_closes", fake_fetch)
    from cap646.fallbacks import resolve_ohlcv_closes

    closes, src = await resolve_ohlcv_closes("BTC", interval="1h", limit=10)
    assert closes == [50.0, 51.0]
    assert src == "test_spine"


# --- Feature #65 HA ---


def test_ha_runtime_posture_structure():
    from uptime_monitor import ha_runtime_posture

    posture = ha_runtime_posture()
    assert "no_single_point_of_failure" in posture
    assert "multi_instance_proof" in posture
    assert "rto_rpo" in posture
    assert "failover_evidence" in posture
    assert "degraded_mode" in posture
    assert "live_dependencies" in posture


def test_ha_architecture_status_includes_posture():
    from uptime_monitor import ha_architecture_status

    status = ha_architecture_status()
    assert status.get("feature") == "#65-silent"
    assert "multi_instance_proof" in status
    assert "rto_rpo" in status


def test_viral_health_degraded_reasons():
    from viral_capacity import viral_health_payload

    payload = viral_health_payload()
    assert "degraded_reasons" in payload
    assert isinstance(payload["degraded_reasons"], list)


def test_failover_self_test():
    from uptime_monitor import run_failover_self_test

    result = run_failover_self_test()
    assert result["result"] in ("pass", "degraded", "fail")
    assert "duration_sec" in result


def test_scale_readiness_includes_ha_posture():
    from scale_readiness import scale_readiness_report

    report = scale_readiness_report()
    assert report.get("feature_ha") == "#65-silent"
    assert "ha_runtime_posture" in report
