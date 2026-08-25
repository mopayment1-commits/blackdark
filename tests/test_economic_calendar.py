"""Tests — #211 Economic Calendar (widget import + asset relevance)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import economic_calendar as ec


@pytest.fixture
def isolated_calendar_store(tmp_path, monkeypatch):
    store = tmp_path / "economic_calendar.json"
    seed = tmp_path / "economic_calendar_seed.json"
    seed.write_text(
        json.dumps([
            {
                "id": "cpi-test",
                "event": "US CPI (MoM)",
                "country": "US",
                "category": "inflation",
                "scheduled_at_utc": "2026-08-13T12:30:00+00:00",
                "timezone": "America/New_York",
                "timezone_display": "EST",
                "source": "BLS",
                "import_source": "TradingView Economic Calendar",
                "revision": "v1",
                "revision_label": "preliminary",
                "forecast": "0.2%",
                "previous": "0.1%",
                "actual": None,
                "impact": "high",
                "relevant_assets": ["BTC", "ETH"],
            },
            {
                "id": "fomc-test",
                "event": "FOMC Interest Rate Decision",
                "country": "US",
                "category": "monetary_policy",
                "scheduled_at_utc": "2026-09-17T18:00:00+00:00",
                "timezone": "America/New_York",
                "timezone_display": "EST",
                "source": "Federal Reserve",
                "import_source": "TradingView Economic Calendar",
                "revision": "v2",
                "revision_label": "final",
                "forecast": "4.25%",
                "previous": "4.50%",
                "actual": "4.50%",
                "impact": "high",
                "relevant_assets": ["BTC"],
            },
        ]),
        encoding="utf-8",
    )
    monkeypatch.setattr(ec, "_STORE_PATH", store)
    monkeypatch.setattr(ec, "_SEED_PATH", seed)
    return store


def test_factual_values_display(isolated_calendar_store):
    event = ec.get_economic_event("cpi-test")["event"]
    assert "Forecast: 0.2%" in event["values_display"]
    assert "Previous: 0.1%" in event["values_display"]
    assert "Actual: —" in event["values_display"]
    assert event["not_a_prediction"] is True


def test_source_timezone_revision_tracked(isolated_calendar_store):
    event = ec.get_economic_event("cpi-test")["event"]
    line = event["source_line"]
    assert "Event: US CPI (MoM)" in line
    assert "Source: BLS" in line
    assert "Timezone: EST" in line
    assert "Revision: v1 (preliminary)" in line


def test_not_trade_advice(isolated_calendar_store):
    listed = ec.list_economic_events()
    assert listed["not_a_prediction"] is True
    assert "not investment advice" in listed["disclaimer"].lower()
    assert listed["disclaimer_hideable"] is False
    for ev in listed["events"]:
        assert ev["not_trade_advice"] is True
        assert "buy" not in ev["values_display"].lower()
        assert "sell" not in ev["values_display"].lower()


def test_asset_relevance_layer(isolated_calendar_store):
    event = ec.get_economic_event("fomc-test")["event"]
    rel = event["asset_relevance"]["BTC"]
    assert rel["historical_volatility_24h_pct"] > 0
    assert "FOMC" in rel["display"]
    assert "volatility historically" in rel["display"]
    assert rel["not_a_prediction"] is True


def test_asset_filter(isolated_calendar_store):
    feed = ec.list_economic_events(asset="ETH")
    assert feed["count"] == 1
    assert feed["events"][0]["id"] == "cpi-test"


def test_widget_config_not_from_scratch(isolated_calendar_store):
    cfg = ec.tradingview_widget_config()
    assert "TradingView" in cfg["widget"]
    assert "embed-widget-events.js" in cfg["script_src"]
    status = ec.economic_calendar_status()
    assert status["build_from_scratch"] is False


def test_status_tracks_sources_and_revisions(isolated_calendar_store):
    status = ec.economic_calendar_status()
    assert status["timezone_tracked"] is True
    assert "BLS" in status["sources_tracked"]
    assert "Federal Reserve" in status["sources_tracked"]
    assert "v1" in status["revisions_tracked"]
    assert "v2" in status["revisions_tracked"]
    assert status["build_from_scratch"] is False


def test_asset_relevance_endpoint(isolated_calendar_store):
    result = ec.get_asset_calendar_relevance("BTC")
    assert result["event_count"] == 2
    assert len(result["relevance_lines"]) >= 1


def test_event_not_found(isolated_calendar_store):
    result = ec.get_economic_event("missing")
    assert result["ok"] is False
    assert result["error"] == "event_not_found"


def test_time_aligned(isolated_calendar_store):
    event = ec.get_economic_event("cpi-test")["event"]
    assert event["time_aligned"] is True
    assert event["scheduled_at_utc"] == "2026-08-13T12:30:00+00:00"
    assert event["timezone"] == "America/New_York"


def test_full_seed_file_exists():
    rows = json.loads(Path("data/economic_calendar_seed.json").read_text(encoding="utf-8"))
    assert len(rows) >= 10
    sample = rows[0]
    assert sample["source"]
    assert sample["timezone_display"]
    assert sample["revision"]


def test_api_routes():
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    status = c.get("/api/platform/economic-calendar/status")
    assert status.status_code == 200
    body = status.json()
    assert body["feature_id"] == 211
    assert body["build_from_scratch"] is False

    listed = c.get("/api/platform/economic-calendar?limit=5")
    assert listed.status_code == 200
    assert listed.json()["count"] >= 1

    widget = c.get("/api/platform/economic-calendar/widget")
    assert widget.status_code == 200
    assert "TradingView" in widget.json()["widget"]
