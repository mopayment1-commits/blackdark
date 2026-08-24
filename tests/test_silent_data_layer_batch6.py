"""Tests — silent data layer batch 6 (#104 Twelve Data, #105 Behavioral Learning)."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from blackdark.ingestion.twelvedata_connector import (
    _correlation_narrative,
    fetch_twelvedata_macro_context,
    twelvedata_connector_status,
)
from bd_platform.user_behavioral_learning import (
    _MIN_VISITS_FOR_BOOST,
    behavioral_learning_status,
    opt_in_behavioral_learning,
    opt_out_behavioral_learning,
    ranked_topics_for_user,
    record_behavior_event,
)


def test_correlation_narrative_btc_dxy_negative():
    quotes = {"dxy": {"change_pct": 0.5}}
    line = _correlation_narrative(btc_change_pct=-3.0, quotes=quotes)
    assert line is not None
    assert "Bitcoin down" in line
    assert "DXY up" in line
    assert "negative correlation" in line


def test_correlation_narrative_risk_on():
    quotes = {"dxy": {"change_pct": -0.4}}
    line = _correlation_narrative(btc_change_pct=2.0, quotes=quotes)
    assert line is not None
    assert "risk-on" in line


@pytest.mark.asyncio
async def test_twelvedata_fallback_without_key():
    with patch(
        "blackdark.ingestion.polygon_io_connector.fetch_polygon_macro_context",
        new=AsyncMock(
            return_value={
                "ok": True,
                "change_pct": -1.2,
                "headline": "AI detected S&P 500 down 1.2%",
            }
        ),
    ):
        out = await fetch_twelvedata_macro_context()
    assert out["feature"] == "#104"
    assert out["data_state"] == "DEGRADED"
    assert out["fallback"]["ok"] is True


@pytest.mark.asyncio
async def test_twelvedata_live_quote_mock():
    fake_payload = [
        {"symbol": "SPX", "percent_change": "0.5", "close": "5200"},
        {"symbol": "DXY", "percent_change": "0.3", "close": "104"},
        {"symbol": "XAU/USD", "percent_change": "-0.1", "close": "2400"},
        {"symbol": "IXIC", "percent_change": "0.8", "close": "18000"},
        {"symbol": "VIX", "percent_change": "2.0", "close": "15"},
    ]
    with patch.dict("os.environ", {"TWELVEDATA_API_KEY": "test-key"}), patch(
        "blackdark.ingestion.twelvedata_connector._twelvedata_get",
        new=AsyncMock(return_value={"ok": True, "data": fake_payload, "cache_hit": False}),
    ), patch(
        "blackdark.ingestion.twelvedata_connector._fetch_btc_change_pct",
        new=AsyncMock(return_value=-3.0),
    ):
        from blackdark.ingestion import twelvedata_connector as td

        td._CACHE._store.clear()
        out = await fetch_twelvedata_macro_context()

    assert out["ok"] is True
    assert out["data_state"] == "LIVE"
    assert out["quotes"]["sp500"]["change_pct"] == 0.5
    assert "negative correlation" in (out.get("correlation_narrative") or "")


def test_twelvedata_connector_status():
    status = twelvedata_connector_status()
    assert status["feature"] == "#104"
    assert "SPX" in status["symbols"]


def test_behavioral_learning_requires_opt_in(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "bd_platform.user_behavioral_learning._PREFS_PATH",
        tmp_path / "prefs.json",
    )
    monkeypatch.setattr(
        "bd_platform.user_behavioral_learning._EVENTS_PATH",
        tmp_path / "events.enc.jsonl",
    )
    monkeypatch.setattr("bd_platform.user_behavioral_learning._DATA_BASE", tmp_path)
    monkeypatch.setattr("bd_platform.user_behavioral_learning._MEMORY_PREFS", {})
    monkeypatch.setattr("bd_platform.user_behavioral_learning._TOPIC_COUNTS", {})

    denied = record_behavior_event(user_id="alice", topic="SOL", surface="market")
    assert denied["ok"] is False
    assert denied["error"] == "opt_in_required"

    opt_in_behavioral_learning(user_id="alice")
    st = behavioral_learning_status(user_id="alice")
    assert st["opted_in"] is True

    for _ in range(_MIN_VISITS_FOR_BOOST):
        record_behavior_event(user_id="alice", topic="SOL", surface="market")

    ranked = ranked_topics_for_user(user_id="alice", candidates=["BTC", "SOL", "ETH"])
    assert ranked["ok"] is True
    assert ranked["ranked"][0]["topic"] == "SOL"
    assert ranked["ranked"][0]["boosted"] is True
    assert ranked["headline"] is not None

    opt_out_behavioral_learning(user_id="alice", purge_events=True)
    st2 = behavioral_learning_status(user_id="alice")
    assert st2["opted_in"] is False


@pytest.mark.asyncio
async def test_market_radar_includes_macro_context():
    with patch(
        "blackdark.ingestion.twelvedata_connector.fetch_twelvedata_macro_context",
        new=AsyncMock(
            return_value={
                "ok": True,
                "headline": "Bitcoin down 3% while DXY up 0.5% — strong negative correlation",
                "correlation_narrative": "Bitcoin down 3% while DXY up 0.5% — strong negative correlation",
                "quotes": {"dxy": {"change_pct": 0.5}},
            }
        ),
    ), patch("plan_audit._fetch_sector_change", new=AsyncMock(return_value=None)):
        from plan_audit import market_radar_narrative

        out = await market_radar_narrative()
    assert out.get("macro_context") is not None
    assert "DXY" in out["bullets"][0] or "Bitcoin" in out["bullets"][0]
