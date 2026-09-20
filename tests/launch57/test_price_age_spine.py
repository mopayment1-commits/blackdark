"""#22 → #41 price age wiring — freshness must not be UNKNOWN when age is knowable."""

from __future__ import annotations

from datetime import timedelta

import pytest

from failure.freshness import FreshnessState
from launch57.decision_common import load_decision_spine
from launch57.freshness_common import assess_freshness, resolve_quote_age_sec
from launch57.temporal_common import to_rfc3339, utc_now


def test_resolve_quote_age_zero_with_event_is_not_missing():
    event = to_rfc3339(utc_now())
    age_sec, source_iso = resolve_quote_age_sec(age_sec=0.0, event_time=event)
    assert age_sec is not None
    assert age_sec >= 0.0
    assert source_iso == event
    assessment = assess_freshness(age_sec=age_sec, source_time=source_iso)
    assert assessment.freshness_state != FreshnessState.UNKNOWN
    assert assessment.presented_as_live is True


def test_resolve_quote_age_from_provider_event_time():
    event = utc_now() - timedelta(seconds=2)
    age_sec, source_iso = resolve_quote_age_sec(event_time=to_rfc3339(event))
    assert age_sec is not None
    assert 1.0 <= age_sec <= 5.0
    assessment = assess_freshness(age_sec=age_sec, source_time=source_iso)
    assert assessment.freshness_state == FreshnessState.LIVE
    assert assessment.presented_as_live is True


@pytest.mark.asyncio
async def test_real_time_prices_with_close_time_not_unknown(monkeypatch):
    from launch57.data_batch1 import real_time_prices

    async def fake_connector(*, symbol: str, params=None):
        return {"success": True, "selected_provider": "binance"}

    async def fake_ticker(pair: str):
        return {
            "price": 42000.0,
            "source": "binance:api.binance.com",
            "event_time": int(utc_now().timestamp() * 1000),
            "change_24h": 0.5,
        }

    monkeypatch.setattr("launch57.data_batch1.unified_exchange_connector", fake_connector)
    monkeypatch.setattr("launch57.data_batch1.fetch_binance_ticker", fake_ticker)

    out = await real_time_prices(symbol="BTC", params={})
    assert out.get("price") == 42000.0
    assert out.get("freshness_state") != FreshnessState.UNKNOWN.value
    assert out.get("data_age_sec") is not None
    assert out.get("presented_as_live") is True


@pytest.mark.asyncio
async def test_load_decision_spine_passes_age_to_freshness_assurance(monkeypatch):
    captured: dict = {}

    async def fake_prices(*, symbol: str, params=None):
        return {
            "price": 100.0,
            "freshness_state": FreshnessState.LIVE.value,
            "presented_as_live": True,
            "data_age_sec": 1.5,
            "event_timestamp": to_rfc3339(utc_now()),
            "temporal": {
                "observed_time": to_rfc3339(utc_now()),
                "ingested_at": to_rfc3339(utc_now()),
                "availability_state": "KNOWN",
            },
        }

    async def fake_freshness(*, symbol: str, params=None):
        captured.update(params or {})
        return {
            "freshness_state": FreshnessState.LIVE.value,
            "presented_as_live": True,
        }

    monkeypatch.setattr("launch57.data_batch1.real_time_prices", fake_prices)
    monkeypatch.setattr("launch57.data_batch2.freshness_update_assurance", fake_freshness)

    spine = await load_decision_spine("BTC", {})
    assert captured.get("age_sec") == 1.5
    assert captured.get("source_time")
    assert spine["freshness_state"] == FreshnessState.LIVE.value
    assert spine["presented_as_live"] is True


@pytest.mark.asyncio
async def test_load_decision_spine_stale_never_presented_as_live(monkeypatch):
    async def fake_prices(*, symbol: str, params=None):
        return {
            "price": 100.0,
            "freshness_state": FreshnessState.STALE.value,
            "presented_as_live": True,
            "data_age_sec": 120.0,
            "event_timestamp": to_rfc3339(utc_now() - timedelta(seconds=120)),
        }

    async def fake_freshness(*, symbol: str, params=None):
        return {
            "freshness_state": FreshnessState.STALE.value,
            "presented_as_live": False,
        }

    monkeypatch.setattr("launch57.data_batch1.real_time_prices", fake_prices)
    monkeypatch.setattr("launch57.data_batch2.freshness_update_assurance", fake_freshness)

    spine = await load_decision_spine("BTC", {})
    assert spine["freshness_state"] == FreshnessState.STALE.value
    assert spine["presented_as_live"] is False


@pytest.mark.asyncio
async def test_load_decision_spine_unknown_never_presented_as_live(monkeypatch):
    async def fake_prices(*, symbol: str, params=None):
        return {
            "price": 100.0,
            "freshness_state": FreshnessState.UNKNOWN.value,
            "presented_as_live": True,
            "data_age_sec": None,
        }

    async def fake_freshness(*, symbol: str, params=None):
        return {
            "freshness_state": FreshnessState.UNKNOWN.value,
            "presented_as_live": False,
        }

    monkeypatch.setattr("launch57.data_batch1.real_time_prices", fake_prices)
    monkeypatch.setattr("launch57.data_batch2.freshness_update_assurance", fake_freshness)

    spine = await load_decision_spine("BTC", {})
    assert spine["freshness_state"] == FreshnessState.UNKNOWN.value
    assert spine["presented_as_live"] is False
