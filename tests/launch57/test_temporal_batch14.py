"""B14 temporal batch — infrastructure temporal (SPEC §23–§27, cross-cutting)."""

from __future__ import annotations

import ast
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from launch57.b14_infrastructure_temporal_bridge import finalize_b14_infrastructure_surface
from launch57.infrastructure_temporal_common import (
    ClockContext,
    DstGapFoldPolicy,
    LocalCivilState,
    MonotonicTimer,
    ScheduleIntent,
    TimestampUnit,
    build_clock_health_snapshot,
    build_infrastructure_temporal_context,
    classify_local_civil_state,
    classify_naive_timestamp,
    derive_next_utc_occurrence,
    is_api_bearing_body,
    measure_elapsed,
    prepare_db_civil_intent,
    prepare_db_instant_record,
    resolve_local_civil_time,
    serialize_api_instant,
    serialize_epoch_timestamp,
    store_schedule_intent,
    validate_api_timestamp_string,
    wall_clock_now,
)
from launch57.temporal_common import parse_rfc3339, to_rfc3339, utc_now


def test_serialize_api_instant_uses_utc_z():
    text = serialize_api_instant(utc_now())
    assert text.endswith("Z")


def test_reject_ambiguous_local_api_timestamp():
    result = validate_api_timestamp_string("2026-09-17T12:34:56")
    assert result.ok is False
    assert result.error == "ambiguous_local_timestamp_without_timezone"


def test_epoch_requires_explicit_unit_contract():
    result = serialize_epoch_timestamp(1_700_000_000_000, unit=TimestampUnit.MILLISECONDS)
    assert result.ok is True
    assert result.contract is not None
    assert result.contract.unit == TimestampUnit.MILLISECONDS
    assert result.serialized.endswith("Z")


def test_db_instant_and_civil_intent_separate():
    record = prepare_db_instant_record(utc_now())
    intent = prepare_db_civil_intent(
        local_wall_time="09:00",
        iana_zone="America/New_York",
        recurrence_rule="FREQ=DAILY",
    )
    assert record.storage_type == "timestamptz"
    assert intent.iana_zone == "America/New_York"
    assert intent.recurrence_rule == "FREQ=DAILY"


def test_naive_timestamp_classified_not_silently_reinterpreted():
    naive = datetime(2020, 1, 1, 12, 0, 0)
    classified = classify_naive_timestamp(naive, assumed_zone="UTC")
    assert classified["silent_reinterpret_forbidden"] is True
    assert classified["assumed_original_zone"] == "UTC"


def test_wall_clock_and_monotonic_separated():
    timer = MonotonicTimer()
    wall = wall_clock_now()
    elapsed = measure_elapsed(timer)
    assert wall.tzinfo is not None
    assert elapsed >= 0.0


def test_clock_skew_budget_fail_closed():
    snapshot = build_clock_health_snapshot(
        estimated_offset_sec=120.0,
        context=ClockContext.OPPORTUNITY_FRESHNESS,
    )
    assert snapshot.within_budget is False
    assert snapshot.skew_budget_sec == 5.0


def test_dst_gap_classified_nonexistent():
    state = classify_local_civil_state(2024, 3, 10, 2, 30, zone_id="America/New_York")
    assert state == LocalCivilState.NONEXISTENT


def test_dst_fold_classified_ambiguous():
    state = classify_local_civil_state(2024, 11, 3, 1, 30, zone_id="America/New_York")
    assert state == LocalCivilState.AMBIGUOUS


def test_dst_gap_reject_policy_fail_closed():
    resolved = resolve_local_civil_time(
        2024,
        3,
        10,
        2,
        30,
        zone_id="America/New_York",
        policy=DstGapFoldPolicy.REJECT,
    )
    assert resolved.ok is False
    assert resolved.error == "dst_gap_or_ambiguous_local_time"


def test_dst_fold_first_occurrence_policy():
    resolved = resolve_local_civil_time(
        2024,
        11,
        3,
        1,
        30,
        zone_id="America/New_York",
        policy=DstGapFoldPolicy.FIRST_OCCURRENCE,
    )
    assert resolved.ok is True
    assert resolved.instant_utc is not None


def test_dst_gap_shift_next_valid_policy():
    resolved = resolve_local_civil_time(
        2024,
        3,
        10,
        2,
        30,
        zone_id="America/New_York",
        policy=DstGapFoldPolicy.SHIFT_NEXT_VALID,
    )
    assert resolved.ok is True
    assert resolved.dst_adjustment_explanation is not None
    from zoneinfo import ZoneInfo

    local_hour = parse_rfc3339(resolved.instant_utc).astimezone(ZoneInfo("America/New_York")).hour
    assert local_hour == 3


def test_schedule_intent_stores_civil_recurrence_not_fixed_offset():
    intent = store_schedule_intent(
        ScheduleIntent(
            local_wall_time="09:00",
            iana_zone="Europe/London",
            recurrence_rule="FREQ=DAILY",
        )
    )
    assert intent["storage_model"] == "civil_time_recurrence_not_fixed_offset"
    assert intent["iana_zone"] == "Europe/London"


def test_derive_next_utc_occurrence_from_civil_intent():
    intent = ScheduleIntent(local_wall_time="09:00", iana_zone="UTC", recurrence_rule="FREQ=DAILY")
    resolved = derive_next_utc_occurrence(intent, after_utc=datetime(2026, 1, 1, 0, 0, tzinfo=UTC))
    assert resolved.ok is True
    assert resolved.instant_utc is not None


def test_is_api_bearing_body_with_temporal():
    assert is_api_bearing_body({"temporal": {"event_time": to_rfc3339(utc_now())}}) is True
    assert is_api_bearing_body({"surface": "quote_data"}) is False


def test_infrastructure_violation_fail_closed_on_ambiguous_timestamp():
    body = {
        "success": True,
        "temporal": {"event_time": "2026-09-17T12:00:00"},
        "launch57_isolation_boundary": True,
    }
    out = finalize_b14_infrastructure_surface(body, payload={})
    assert out["infrastructure_temporally_consistent"] is False
    assert out["success"] is False
    assert out["b14_isolation_leakage"] == 0


def test_infrastructure_consistent_api_body():
    body = {
        "success": True,
        "temporal": {"event_time": to_rfc3339(utc_now())},
        "launch57_isolation_boundary": True,
    }
    out = finalize_b14_infrastructure_surface(body, payload={})
    assert out["infrastructure_temporally_consistent"] is True
    assert out["b14_infrastructure_temporal"]["activated"] is True
    assert out["clock_health"]["within_budget"] is True


def test_build_infrastructure_context_detects_skew_violation():
    body = {"temporal": {"event_time": to_rfc3339(utc_now())}}
    ctx = build_infrastructure_temporal_context(
        body,
        estimated_clock_offset_sec=100.0,
        clock_context=ClockContext.OPPORTUNITY_FRESHNESS,
    )
    assert ctx.infrastructure_temporally_consistent is False
    assert any("clock_skew_exceeds_budget" in v for v in ctx.violations)


@pytest.mark.asyncio
async def test_real_time_prices_includes_b14_infrastructure(monkeypatch):
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
    assert out["b14_infrastructure_temporal"]["activated"] is True
    assert out["infrastructure_temporally_consistent"] is True
    assert out["b14_temporal_owner"] == "launch57.infrastructure_temporal_common"


@pytest.mark.asyncio
async def test_ohlcv_still_has_b13_and_b14(monkeypatch):
    from launch57.data_batch1 import ohlcv

    bars = [{"open_time_ms": 1_700_000_000_000, "open": 1, "high": 2, "low": 1, "close": 1, "volume": 1}]

    async def fake_connector(*, symbol: str, params=None):
        return {"success": True}

    async def fake_klines(pair, interval="1h", limit=100):
        return bars, "data-api.binance.vision"

    monkeypatch.setattr("launch57.data_batch1.unified_exchange_connector", fake_connector)
    monkeypatch.setattr("launch57.data_batch1.fetch_binance_klines_bars", fake_klines)

    out = await ohlcv(symbol="BTC", params={"interval": "1h", "display_timezone": "UTC"})
    assert out["b13_chart_display_timing"]["activated"] is True
    assert out["b14_infrastructure_temporal"]["activated"] is True


def test_infrastructure_temporal_common_no_cap646_import():
    root = Path(__file__).resolve().parents[2]
    source = (root / "launch57" / "infrastructure_temporal_common.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    bad = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and "cap646" in node.module:
            bad.append(node.module)
    assert bad == []
