"""Launch-57 temporal consistency — Phase 1 Data Batch B1 tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from launch57.temporal_common import (
    AvailabilityState,
    MonotonicTimer,
    TemporalEnvelope,
    TimestampUnit,
    attach_temporal_envelope,
    build_market_temporal_envelope,
    deterministic_order_key,
    infer_timestamp_unit,
    local_render_instant,
    parse_rfc3339,
    point_in_time_eligible,
    require_aware,
    resolve_available_at,
    resolve_user_timezone,
    sort_by_temporal_key,
    to_rfc3339,
    utc_now,
    validate_provider_timestamp,
)


def test_reject_naive_datetime():
    naive = datetime(2026, 9, 17, 12, 0, 0)
    with pytest.raises(ValueError, match="naive_datetime_rejected"):
        require_aware(naive)


def test_utc_round_trip_rfc3339():
    now = utc_now()
    text = to_rfc3339(now)
    parsed = parse_rfc3339(text)
    assert parsed.tzinfo is not None
    assert text.endswith("Z") or "+00:00" in text


def test_parse_rfc3339_with_offset():
    dt = parse_rfc3339("2026-09-17T12:34:56+02:00")
    assert dt.hour == 10


def test_invalid_timezone_fallback():
    zone, source = resolve_user_timezone(
        request_override="Not/AZone",
        account_preference="Europe/London",
    )
    assert zone == "Europe/London"
    assert source == "account_preference"


def test_timezone_precedence_request_over_account():
    zone, source = resolve_user_timezone(
        request_override="America/New_York",
        account_preference="Europe/London",
    )
    assert zone == "America/New_York"
    assert source == "request_override"


def test_timestamp_unit_inference():
    assert infer_timestamp_unit(1_700_000_000) == TimestampUnit.SECONDS
    assert infer_timestamp_unit(1_700_000_000_000) == TimestampUnit.MILLISECONDS


def test_provider_future_timestamp_rejected():
    future_ms = int((utc_now() + timedelta(hours=2)).timestamp() * 1000)
    result = validate_provider_timestamp(future_ms)
    assert result.ok is False
    assert result.error == "future_timestamp"


def test_deterministic_equal_time_ordering():
    t = utc_now()
    a = deterministic_order_key(t, source_sequence=1, ingestion_sequence=0, immutable_event_id="a")
    b = deterministic_order_key(t, source_sequence=2, ingestion_sequence=0, immutable_event_id="b")
    assert a < b


def test_available_at_unknown_without_observation():
    available, state = resolve_available_at(source_time=utc_now(), observed_time=None, ingested_at=None)
    assert available is None
    assert state == AvailabilityState.UNKNOWN


def test_available_at_not_fabricated_from_source_only():
    source = utc_now()
    available, state = resolve_available_at(source_time=source, observed_time=None, ingested_at=None)
    assert available is None
    assert state == AvailabilityState.UNKNOWN


def test_available_at_known_from_ingestion():
    source = utc_now() - timedelta(seconds=5)
    ingested = utc_now()
    available, state = resolve_available_at(source_time=source, observed_time=None, ingested_at=ingested)
    assert state == AvailabilityState.KNOWN
    assert available is not None
    assert parse_rfc3339(available) <= ingested


def test_point_in_time_rejects_future_available_at():
    decision = to_rfc3339(utc_now())
    future_available = to_rfc3339(utc_now() + timedelta(minutes=1))
    assert point_in_time_eligible(future_available, decision) is False


def test_point_in_time_accepts_valid_available_at():
    past = to_rfc3339(utc_now() - timedelta(minutes=1))
    decision = to_rfc3339(utc_now())
    assert point_in_time_eligible(past, decision) is True


def test_local_render_does_not_change_canonical_order():
    a = utc_now()
    b = a + timedelta(hours=1)
    cairo_a = local_render_instant(a, "Africa/Cairo")
    cairo_b = local_render_instant(b, "Africa/Cairo")
    assert parse_rfc3339(cairo_a) < parse_rfc3339(cairo_b)


def test_sort_by_temporal_key_milliseconds():
    rows = [
        {"open_time_ms": 3, "source_sequence": 0},
        {"open_time_ms": 1, "source_sequence": 0},
        {"open_time_ms": 2, "source_sequence": 0},
    ]
    ordered = sort_by_temporal_key(rows, time_field="open_time_ms")
    assert [r["open_time_ms"] for r in ordered] == [1, 2, 3]


def test_monotonic_timer_elapsed():
    timer = MonotonicTimer()
    assert timer.elapsed_sec() >= 0.0


def test_leap_second_normalization():
    result = validate_provider_timestamp("2026-06-30T23:59:60Z")
    assert result.ok is True
    assert result.leap_second_normalized is True


def test_attach_temporal_envelope_roundtrip():
    env = TemporalEnvelope(observed_time=to_rfc3339(utc_now()), availability_state=AvailabilityState.KNOWN)
    out = attach_temporal_envelope({"ok": True}, env)
    assert "temporal" in out
    assert out["temporal"]["availability_state"] == "KNOWN"


def test_build_market_temporal_envelope_from_epoch_ms():
    ms = int(utc_now().timestamp() * 1000)
    env = build_market_temporal_envelope(source_raw=ms, source_unit=infer_timestamp_unit(ms))
    assert env.source_time is not None
    assert env.availability_state == AvailabilityState.KNOWN


@pytest.mark.asyncio
async def test_real_time_prices_attaches_temporal_envelope(monkeypatch):
    from launch57.data_batch1 import real_time_prices

    async def fake_connector(*, symbol: str, params=None):
        return {"success": True, "selected_provider": "binance"}

    async def fake_ticker(pair: str):
        return {
            "price": 100.0,
            "source": "binance:api.binance.com",
            "age_sec": 1.0,
            "timestamp": to_rfc3339(utc_now()),
        }

    monkeypatch.setattr("launch57.data_batch1.unified_exchange_connector", fake_connector)
    monkeypatch.setattr("launch57.data_batch1.fetch_binance_ticker", fake_ticker)

    out = await real_time_prices(symbol="BTC", params={})
    assert "temporal" in out
    assert out["temporal"]["availability_state"] == "KNOWN"
    assert out["temporal"]["source_time"] is not None
    assert out["legacy_runtime_dependencies"] == 0
    assert out.get("b1_to_41_reconciliation", {}).get("status") == "BOUND_TO_LAUNCH57_41"
    assert out["freshness_owner"] == "launch57.freshness_common"


@pytest.mark.asyncio
async def test_real_time_prices_rejects_future_provider_timestamp(monkeypatch):
    from launch57.data_batch1 import real_time_prices

    async def fake_connector(*, symbol: str, params=None):
        return {"success": True, "selected_provider": "binance"}

    async def fake_ticker(pair: str):
        return {
            "price": 100.0,
            "source": "binance:api.binance.com",
            "age_sec": 1.0,
            "timestamp": to_rfc3339(utc_now() + timedelta(hours=3)),
        }

    monkeypatch.setattr("launch57.data_batch1.unified_exchange_connector", fake_connector)
    monkeypatch.setattr("launch57.data_batch1.fetch_binance_ticker", fake_ticker)

    out = await real_time_prices(symbol="BTC", params={})
    assert out["success"] is False
    assert "provider_timestamp_invalid" in out["error"]


@pytest.mark.asyncio
async def test_ohlcv_temporal_ordering(monkeypatch):
    from launch57.data_batch1 import ohlcv

    bars = [
        {"open_time_ms": 3000, "open": 3, "high": 4, "low": 2, "close": 3, "volume": 1},
        {"open_time_ms": 1000, "open": 1, "high": 2, "low": 1, "close": 1, "volume": 1},
        {"open_time_ms": 2000, "open": 2, "high": 3, "low": 2, "close": 2, "volume": 1},
    ]

    async def fake_connector(*, symbol: str, params=None):
        return {"success": True}

    async def fake_klines(pair, interval="1h", limit=100):
        return bars, "data-api.binance.vision"

    monkeypatch.setattr("launch57.data_batch1.unified_exchange_connector", fake_connector)
    monkeypatch.setattr("launch57.data_batch1.fetch_binance_klines_bars", fake_klines)

    out = await ohlcv(symbol="BTC", params={"interval": "1h"})
    assert [b["open_time_ms"] for b in out["bars"]] == [1000, 2000, 3000]
    assert out["temporal"]["timestamp_unit"] == "ms"


def test_temporal_control_removal_breaks_point_in_time_guard():
    """Behavioral guard: without resolve_available_at, UNKNOWN availability must not pass PIT."""
    available, state = resolve_available_at(source_time=utc_now(), observed_time=None, ingested_at=None)
    assert state == AvailabilityState.UNKNOWN
    assert point_in_time_eligible(available, to_rfc3339(utc_now())) is False
