"""Launch-57 Phase 6 Adaptive Batch 1 — builder verification tests (#34→#36, #51)."""

from __future__ import annotations

import pytest

from failure.freshness import FreshnessState
from launch57.explanation_ai_batch1 import (
    ai_research_agent_grounded,
    price_move_explanation,
    research_intelligence_portal,
    signal_explanation_workflow,
)


def _live_spine(symbol: str = "BTC", change_24h: float = 4.2):
    return {
        "symbol": symbol,
        "freshness_state": FreshnessState.LIVE.value,
        "live_eligible": True,
        "presented_as_live": True,
        "price": 50000.0,
        "change_24h": change_24h,
        "data_spine": {"phase1_batch1": "launch57.data_batch1:real_time_prices"},
    }


@pytest.mark.asyncio
async def test_capability_34_inference_not_presented_as_causal_fact(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    async def fake_footprint(symbol):
        return {"ok": True, "bid_pressure": 1.2}

    def fake_why(payload):
        return {
            "ready": True,
            "top_3_factors": [
                {"factor": "Order-flow context", "detail": "live book footprint", "source": "footprint"},
                {"factor": "Volume + funding alignment", "detail": "checked", "source": "market"},
            ],
        }

    monkeypatch.setattr("launch57.explanation_ai_common.load_decision_spine", fake_spine)
    monkeypatch.setattr("bd_platform.footprint_analytics.footprint_snapshot", fake_footprint)
    monkeypatch.setattr("heroes_quality.build_oqs_why_block", fake_why)

    out = await signal_explanation_workflow(symbol="BTC", params={})
    assert out["launch_item_id"] == 34
    assert out["explanation_contract"]["causal_certainty_established"] is False
    assert out["adaptive_disclosure"]["level_1"]["answer_state"] == "INFERENCE_QUALIFIED"
    inference = out["inferences"][0]
    assert inference["proposition_class"] == "inference"
    assert inference["presented_as_established_fact"] is False
    assert "(inference, not causal fact)" in out["explanation"]["why_text"]


@pytest.mark.asyncio
async def test_capability_34_unsupported_causality_rejected(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    async def fake_footprint(symbol):
        return {"ok": True}

    def fake_why(payload):
        return {
            "ready": True,
            "top_3_factors": [
                {"factor": "Macro shock caused move", "detail": "checked", "source": "market"},
            ],
        }

    monkeypatch.setattr("launch57.explanation_ai_common.load_decision_spine", fake_spine)
    monkeypatch.setattr("bd_platform.footprint_analytics.footprint_snapshot", fake_footprint)
    monkeypatch.setattr("heroes_quality.build_oqs_why_block", fake_why)

    out = await signal_explanation_workflow(
        symbol="BTC",
        params={"assert_causality": True, "causal_claim": "macro shock established"},
    )
    assert out["launch_item_id"] == 34
    assert out["success"] is False
    assert out["adaptive_disclosure"]["level_1"]["answer_state"] == "UNSUPPORTED_CAUSALITY_REJECTED"
    assert out["adaptive_disclosure"]["signal_explanation_disclosure"]["unsupported_causal_rejected"] is True


@pytest.mark.asyncio
async def test_capability_35_observed_facts_distinct_from_inference(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    async def fake_sentiment(asset):
        return {"sentiment_compound_index": {asset: {"score": 0.5}}}

    monkeypatch.setattr("launch57.explanation_ai_common.load_decision_spine", fake_spine)
    monkeypatch.setattr("sentiment_engine.build_sentiment_context_safe", fake_sentiment)

    out = await price_move_explanation(symbol="BTC", params={})
    assert out["launch_item_id"] == 35
    pme = out["price_move_explanation"]
    assert pme["observed_facts"]["proposition_class"] == "observed"
    assert pme["observed_facts"]["change_24h_pct"] == 4.2
    assert all(row["proposition_class"] == "inference" for row in pme["inferences"])
    assert "strong_24h_rally" not in pme["observed_facts"]
    assert out["adaptive_disclosure"]["price_move_explanation_disclosure"]["inference_not_observed_fact"] is True


@pytest.mark.asyncio
async def test_capability_36_unapproved_input_cannot_change_supported_claims(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    report = {"oracle_audit": {"total_predictions": 3}, "sentiment": {"score": 0.4}}

    async def fake_report():
        return report

    monkeypatch.setattr("launch57.explanation_ai_common.load_decision_spine", fake_spine)
    monkeypatch.setattr("research_lab.build_research_lab_report", fake_report)

    baseline = await ai_research_agent_grounded(symbol="BTC", params={})
    injected = await ai_research_agent_grounded(
        symbol="BTC",
        params={
            "external_research": {"claim": "SECRET ALPHA 99% win rate"},
            "confidence_override": 0.99,
            "autonomous_scope": ["options_chain", "dark_pool_mesh"],
        },
    )

    assert baseline["research_agent"]["supported_claims"] == injected["research_agent"]["supported_claims"]
    assert baseline["research_agent"]["agent_summary"] == injected["research_agent"]["agent_summary"]
    assert injected["adaptive_disclosure"]["level_1"]["answer_state"] == "UNSUPPORTED_INPUT_REJECTED"
    assert injected["success"] is False
    assert "SECRET ALPHA" not in str(injected["research_agent"])


@pytest.mark.asyncio
async def test_capability_51_unapproved_evidence_cannot_alter_brief(monkeypatch):
    def fake_track():
        return {
            "cumulative": {
                "resolved_predictions": 40,
                "hit_rate_percent": 67.5,
                "metrics_scope": "live_only",
            }
        }

    monkeypatch.setattr("oracle_track_record.public_track_record", fake_track)

    baseline = await research_intelligence_portal(symbol="ETH", params={})
    injected = await research_intelligence_portal(
        symbol="ETH",
        params={"custom_hit_rate": 99.0, "custom_summary": "External alpha feed says 99%"},
    )

    assert baseline["shareable_brief"]["summary"] == injected["shareable_brief"]["summary"]
    assert "67.5%" in injected["shareable_brief"]["summary"]
    assert "99%" not in injected["shareable_brief"]["summary"]
    assert injected["adaptive_disclosure"]["level_1"]["answer_state"] == "UNSUPPORTED_EVIDENCE_REJECTED"
    assert injected["adaptive_disclosure"]["research_portal_disclosure"]["separate_research_platform"] is False
