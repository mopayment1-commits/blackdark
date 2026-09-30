"""Launch-57 Phase 6 Explanation+AI Batch 1 — stale gate, AI type, compliance, kill-switch."""

from __future__ import annotations

import pytest

from failure.freshness import FreshnessState
from launch57.explanation_ai_batch1 import (
    LAUNCH57_EXPLANATION_AI_BATCH1_CAP_IDS,
    ai_research_agent_grounded,
    execute_launch57_explanation_ai_batch1,
    price_move_explanation,
    research_intelligence_portal,
    signal_explanation_workflow,
)


def _live_spine(symbol: str = "BTC"):
    return {
        "symbol": symbol,
        "freshness_state": FreshnessState.LIVE.value,
        "live_eligible": True,
        "presented_as_live": True,
        "price": 50000.0,
        "change_24h": 4.2,
        "data_spine": {},
    }


def _stale_spine(symbol: str = "BTC"):
    return {
        "symbol": symbol,
        "freshness_state": FreshnessState.STALE.value,
        "live_eligible": False,
        "presented_as_live": False,
        "data_spine": {},
    }


@pytest.mark.asyncio
async def test_signal_explanation_blocks_stale(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _stale_spine(symbol)

    monkeypatch.setattr("launch57.explanation_ai_common.load_decision_spine", fake_spine)
    out = await signal_explanation_workflow(symbol="BTC", params={})
    assert out["launch_item_id"] == 34
    assert out["success"] is False
    assert out["presented_as_live"] is False
    assert out["ai_system_type"] == "RULE_BASED"
    assert out["explanation_ai_layer"]["phase"] == "6_EXPLANATION_AI"


@pytest.mark.asyncio
async def test_price_move_explanation_rule_based_live(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    async def fake_sentiment(asset):
        return {"sentiment_compound_index": {asset: {"score": 0.5}}}

    monkeypatch.setattr("launch57.explanation_ai_common.load_decision_spine", fake_spine)
    out = await price_move_explanation(symbol="BTC", params={})
    assert out["launch_item_id"] == 35
    assert out["ai_system_type"] == "RULE_BASED"
    pme = out["price_move_explanation"]
    assert pme["observed_facts"]["change_24h_pct"] == 4.2
    assert any(r.get("reason") == "strong_24h_rally" for r in pme["inferences"])
    assert pme["observed_facts"]["price_source"] == "launch57.decision_common:load_decision_spine"
    assert out.get("evidence_class_visible") == "direct"


@pytest.mark.asyncio
async def test_ai_research_agent_platform_only_footer(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    async def fake_report():
        return {"oracle_audit": {"total_predictions": 1}, "sentiment": {}}

    monkeypatch.setattr("launch57.explanation_ai_common.load_decision_spine", fake_spine)
    monkeypatch.setattr("research_lab.build_research_lab_report", fake_report)
    out = await ai_research_agent_grounded(symbol="BTC", params={})
    assert out["launch_item_id"] == 36
    assert out["ai_system_type"] == "STATISTICAL"
    assert out["platform_data_only"] is True
    footer = out["copilot_compliance_footer"]
    assert footer["platform_data_only"] is True
    assert footer["llm_used"] is False
    assert footer["external_sources_as_fact"] == "FORBIDDEN"
    assert out["compliance_footer_visible"] is True


@pytest.mark.asyncio
async def test_research_portal_short_brief(monkeypatch):
    def fake_track():
        return {
            "cumulative": {
                "resolved_predictions": 40,
                "hit_rate_percent": 67.5,
                "metrics_scope": "live_only",
            }
        }

    monkeypatch.setattr("oracle_track_record.public_track_record", fake_track)
    out = await research_intelligence_portal(symbol="ETH", params={})
    assert out["launch_item_id"] == 51
    assert out["shareable_brief"]["shareable"] is True
    assert out["research_portal_scope"]["limited_launch_scope"] is True
    assert "67.5%" in out["shareable_brief"]["summary"]


@pytest.mark.asyncio
async def test_kill_switch_batch1(monkeypatch):
    async def broken(*a, **k):
        raise RuntimeError("kill_switch_explanation_ai_batch1")

    import launch57.explanation_ai_batch1 as mod

    monkeypatch.setattr(mod, "signal_explanation_workflow", broken)
    with pytest.raises(RuntimeError, match="kill_switch_explanation_ai_batch1"):
        await execute_launch57_explanation_ai_batch1(25, params={"symbol": "BTC"})


@pytest.mark.asyncio
async def test_dispatch_all_batch1_caps(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    async def fake_footprint(symbol):
        return {"ok": True}

    def fake_why(payload):
        return {"ready": True, "blocks": []}

    async def fake_sentiment(asset):
        return {"sentiment_compound_index": {}}

    async def fake_report():
        return {"oracle_audit": {}}

    def fake_track():
        return {"cumulative": {"resolved_predictions": 0}}

    monkeypatch.setattr("launch57.explanation_ai_common.load_decision_spine", fake_spine)
    monkeypatch.setattr("bd_platform.footprint_analytics.footprint_snapshot", fake_footprint)
    monkeypatch.setattr("heroes_quality.build_oqs_why_block", fake_why)
    monkeypatch.setattr("sentiment_engine.build_sentiment_context_safe", fake_sentiment)
    monkeypatch.setattr("research_lab.build_research_lab_report", fake_report)
    monkeypatch.setattr("oracle_track_record.public_track_record", fake_track)

    for cap_id in sorted(LAUNCH57_EXPLANATION_AI_BATCH1_CAP_IDS):
        out = await execute_launch57_explanation_ai_batch1(cap_id, params={"symbol": "BTC"})
        assert out["backend_module"] == "launch57.explanation_ai_batch1"
        assert out["binding_source"] == "launch57_phase6_explanation_ai_batch1"
