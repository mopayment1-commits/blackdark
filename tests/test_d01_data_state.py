"""D-01 — explicit data states and circuit breaker."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from blackdark.data import circuit_breaker as cb
from blackdark.data.response_metadata import (
    DATA_STATE_LIVE,
    DATA_STATE_MISSING,
    DATA_STATE_STALE,
    DATA_STATE_UNKNOWN,
    resolve_data_state,
)


def test_missing_not_zero():
    state, reason = resolve_data_state(count=0, dataset="ohlcv")
    assert state == DATA_STATE_MISSING
    assert reason == "no_ohlcv_records_for_query"


def test_unknown_when_upstream_circuit_open():
    state, reason = resolve_data_state(count=0, dataset="ohlcv", upstream_unknown=True)
    assert state == DATA_STATE_UNKNOWN
    assert "upstream" in reason


def test_stale_not_live():
    old = (datetime.now(UTC) - timedelta(hours=5)).isoformat()
    state, reason = resolve_data_state(count=10, dataset="ohlcv", latest_record_at=old)
    assert state == DATA_STATE_STALE
    assert "exceeds_sla" in reason


def test_live_when_fresh():
    recent = (datetime.now(UTC) - timedelta(minutes=5)).isoformat()
    state, _ = resolve_data_state(count=3, dataset="ohlcv", latest_record_at=recent)
    assert state == DATA_STATE_LIVE


def test_states_are_distinct():
    assert len({DATA_STATE_LIVE, DATA_STATE_MISSING, DATA_STATE_STALE, DATA_STATE_UNKNOWN}) == 4


def test_circuit_breaker_opens_after_failures():
    cb._circuits.clear()
    for i in range(3):
        cb.record_failure("test-source", f"fail-{i}")
    assert cb.is_open("test-source") is True


def test_circuit_breaker_resets_on_success():
    cb._circuits.clear()
    cb.record_failure("src", "x")
    cb.record_failure("src", "y")
    cb.record_success("src")
    assert cb.is_open("src") is False
