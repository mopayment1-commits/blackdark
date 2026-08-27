"""Institutional acceptance tests for Wave 01 data engine."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from blackdark.data.response_metadata import DATA_STATE_LIVE, DATA_STATE_MISSING, dataset_response


def test_dataset_response_live():
    recent = (datetime.now(UTC) - timedelta(minutes=5)).isoformat()
    body = dataset_response(
        count=2,
        data=[{"x": 1}, {"x": 2}],
        dataset="ohlcv",
        symbol="BTCUSDT",
        interval="1h",
        latest_record_at=recent,
    )
    assert body["data_state"] == DATA_STATE_LIVE
    assert body["count"] == 2
    assert "data_state_reason" not in body
    assert body["symbol"] == "BTCUSDT"


def test_dataset_response_missing_d01():
    body = dataset_response(count=0, data=[], dataset="funding_rates", symbol="BTCUSDT")
    assert body["data_state"] == DATA_STATE_MISSING
    assert body["data_state_reason"] == "no_funding_rates_records_for_query"
    assert body["count"] == 0
    assert body["data"] == []


def test_wave_01_institutional_status_shape():
    from blackdark.data.institutional import (
        OPEN_CRITICAL_DEFECTS,
        WAVE_01_CONTROL_SCOPE,
        wave_01_institutional_status,
    )
    from critical_defects_closure import CRITICAL_DEFECTS

    assert len(WAVE_01_CONTROL_SCOPE) >= 5
    assert OPEN_CRITICAL_DEFECTS == ()
    assert CRITICAL_DEFECTS == ("D-01", "D-02", "D-06", "D-09", "D-13", "D-15")

    import asyncio

    async def _run():
        assert callable(wave_01_institutional_status)

    asyncio.run(_run())
