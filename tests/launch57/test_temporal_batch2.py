"""Launch-57 temporal B2 tests — #40, #41, #39."""

from __future__ import annotations

from datetime import timedelta

import pytest

from launch57.freshness_common import assess_freshness, FreshnessState
from launch57.point_in_time_common import build_immutable_snapshot, reset_store_for_tests, retrieve_point_in_time
from launch57.provenance_common import build_provenance_record, QualityState
from launch57.temporal_common import to_rfc3339, utc_now


def test_provenance_unknown_when_source_missing():
    record, _ = build_provenance_record(symbol="BTC", params={})
    assert record.quality_state == QualityState.UNKNOWN
    assert record.quality_score is None


def test_freshness_stale_not_live():
    assessment = assess_freshness(age_sec=120.0, observed_at=to_rfc3339(utc_now()), available_at=to_rfc3339(utc_now()))
    assert assessment.freshness_state == FreshnessState.STALE
    assert assessment.presented_as_live is False


def test_freshness_future_source_fails_closed():
    future = to_rfc3339(utc_now() + timedelta(hours=2))
    assessment = assess_freshness(age_sec=1.0, source_time=future)
    assert assessment.success is False
    assert assessment.presented_as_live is False


def test_freshness_unknown_without_age():
    assessment = assess_freshness()
    assert assessment.freshness_state == FreshnessState.UNKNOWN
    assert assessment.presented_as_live is False


@pytest.mark.asyncio
async def test_pit_no_future_leakage():
    reset_store_for_tests()
    past = to_rfc3339(utc_now() - timedelta(minutes=5))
    snap = build_immutable_snapshot(symbol="BTC", metrics={"price": 1.0})
    as_of_old = to_rfc3339(utc_now() - timedelta(minutes=10))
    rows = retrieve_point_in_time("BTC", as_of=as_of_old)
    assert rows == []
    rows_now = retrieve_point_in_time("BTC", as_of=snap["snapshot_at"])
    assert rows_now


def test_freshness_control_removal_would_allow_unknown_as_live():
    assessment = assess_freshness(age_sec=None)
    assert assessment.presented_as_live is False
