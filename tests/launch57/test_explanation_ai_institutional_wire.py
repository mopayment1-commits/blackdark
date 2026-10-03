"""Launch-57 Phase 6 — institutional intercept for explanation+AI caps."""

from __future__ import annotations

import pytest

from cap646.institutional_official_production import execute
from failure.freshness import FreshnessState


def _live_spine(symbol: str = "BTC"):
    return {
        "symbol": symbol,
        "freshness_state": FreshnessState.LIVE.value,
        "live_eligible": True,
        "presented_as_live": True,
        "price": 50000.0,
        "change_24h": 1.0,
        "data_spine": {},
    }


@pytest.mark.asyncio
async def test_institutional_intercepts_cap25_batch1(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    async def fake_footprint(symbol):
        return {"ok": True}

    def fake_why(payload):
        return {"ready": True}

    monkeypatch.setattr("launch57.explanation_ai_common.load_decision_spine", fake_spine)
    monkeypatch.setattr("bd_platform.footprint_analytics.footprint_snapshot", fake_footprint)
    monkeypatch.setattr("heroes_quality.build_oqs_why_block", fake_why)
    out = await execute(25, params={"symbol": "BTC"})
    assert out["handler_module"] == "launch57.explanation_ai_batch1"
    assert out["launch_item_id"] == 34


@pytest.mark.asyncio
async def test_institutional_intercepts_cap24_research_agent(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    async def fake_report():
        return {"oracle_audit": {"total_predictions": 2}}

    monkeypatch.setattr("launch57.explanation_ai_common.load_decision_spine", fake_spine)
    monkeypatch.setattr("research_lab.build_research_lab_report", fake_report)
    out = await execute(24, params={"symbol": "BTC"})
    assert out["handler_module"] == "launch57.explanation_ai_batch1"
    assert out["launch_item_id"] == 36
    assert out["platform_data_only"] is True


@pytest.mark.asyncio
async def test_institutional_intercepts_cap65_portal(monkeypatch):
    def fake_track():
        return {"cumulative": {"resolved_predictions": 5, "hit_rate_percent": 60.0}}

    monkeypatch.setattr("oracle_track_record.public_track_record", fake_track)
    out = await execute(65, params={"symbol": "BTC"})
    assert out["handler_module"] == "launch57.explanation_ai_batch1"
    assert out["launch_item_id"] == 51
