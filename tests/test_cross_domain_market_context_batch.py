"""Tests — #524 Cross-Domain Market Context Layer (absorbs #523-530)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import cross_domain_market_context_layer as cdmc


@pytest.fixture
def context_seed(tmp_path, monkeypatch):
    p = tmp_path / "cross_domain_market_context_layer_seed.json"
    p.write_text(json.dumps({
        "contexts": {
            "test_context": {
                "title": "Test Context",
                "asset": "BTC",
                "analysis_summary": "Cross-domain market context synthesis for testing.",
                "what_changed": [{"domain": "derivatives", "change": "Funding negative"}],
                "domain_signals": [
                    {"domain": "derivatives", "direction": "bullish", "metric": "funding", "value": -0.0002,
                     "source": "binance", "freshness_seconds": 120, "confidence_pct": 95, "weight": 0.5},
                    {"domain": "social", "direction": "bearish", "metric": "sentiment", "value": -0.3,
                     "source": "social_api", "freshness_seconds": 1800, "confidence_pct": 70, "weight": 0.5},
                ],
                "risk": {"volatility_regime": "elevated"},
                "context_relevance": [{
                    "factor": "Negative funding",
                    "hypothesis": "Accumulation thesis",
                    "relationship": "supports",
                    "evidence_refs": ["ev_001"],
                }],
                "epistemic_items": [
                    {
                        "epistemic_type": "fact",
                        "statement": "BTC funding rate is -0.02%",
                        "verified": True,
                        "freshness_seconds": 120,
                        "evidence": [{"evidence_id": "ev_001", "source": "Binance API"}],
                    },
                    {
                        "epistemic_type": "inference",
                        "statement": "Derivatives positioning suggests accumulation context",
                        "confidence_pct": 72,
                        "freshness_seconds": 300,
                        "supporting_fact_refs": ["ev_001"],
                        "evidence": [{"evidence_id": "ev_inf_001", "description": "Cross-domain synthesis"}],
                    },
                ],
            },
        },
        "sub_module_data": {
            "523": {
                "assets": {
                    "BTC": {
                        "what_changed": [{"domain": "derivatives", "change": "OI up 5%"}],
                        "why": ["Leverage increasing"],
                        "aggregate_confidence_pct": 76,
                        "domain_signals": [
                            {"domain": "derivatives", "direction": "bullish", "metric": "oi",
                             "source": "derivatives_feed", "freshness_seconds": 180, "confidence_pct": 90},
                        ],
                        "context_relevance": [],
                        "risk": {},
                    },
                },
            },
            "530": {
                "default": {
                    "what_changed": [{"domain": "market_wide", "change": "Breadth 0.62"}],
                    "why": ["Aggregated"],
                    "aggregate_confidence_pct": 79,
                    "domain_signals": [
                        {"domain": "derivatives", "source": "multi_venue", "freshness_seconds": 300,
                         "confidence_pct": 90, "weight": 0.3, "direction": "bullish", "metric": "funding"},
                        {"domain": "on_chain", "source": "onchain_agg", "freshness_seconds": 600,
                         "confidence_pct": 85, "weight": 0.3, "direction": "bullish", "metric": "flow"},
                        {"domain": "sentiment", "source": "sentiment_agg", "freshness_seconds": 1800,
                         "confidence_pct": 75, "weight": 0.4, "direction": "bearish", "metric": "sentiment"},
                    ],
                    "context_relevance": [],
                    "risk": {},
                },
            },
        },
    }), encoding="utf-8")
    monkeypatch.setattr(cdmc, "_SEED_PATH", p)
    return p


def test_524_epic_renamed_not_decision_intelligence(context_seed):
    panel = cdmc.build_market_context_panel(context_id="test_context")
    assert panel["title"] == "Cross-Domain Market Context Layer"
    assert panel["not_decision_intelligence"] is True
    assert panel["context_not_recommendation"] is True
    assert panel["no_standalone_ui"] is True
    assert panel["api_feed_for_ui_modules"] is True
    assert "523" in panel["absorbed_tickets"]
    assert "530" in panel["absorbed_tickets"]


def test_524_epistemic_separation_with_ui_labels(context_seed):
    panel = cdmc.build_market_context_panel(context_id="test_context")
    output = panel["output"]
    assert output["evidence"]["epistemic_separation"] is True
    assert output["not_decision"] is True
    items = output["evidence"]["items"]
    assert any(i["epistemic_type"] == "fact" for i in items)
    assert any(i["epistemic_type"] == "inference" for i in items)
    for item in items:
        assert "ui_label" in item
        assert item["ui_label"]["color"] in ("green", "blue", "amber")


def test_524_source_freshness_confidence_every_conclusion(context_seed):
    panel = cdmc.build_market_context_panel(context_id="test_context")
    for item in panel["output"]["evidence"]["items"]:
        assert "metadata" in item
        meta = item["metadata"]
        assert "source" in meta
        assert "freshness_seconds" in meta
        assert "confidence_pct" in meta
        assert meta["source_freshness_confidence_required"] is True


def test_524_context_relevance_not_recommendation(context_seed):
    panel = cdmc.build_market_context_panel(context_id="test_context")
    relevance = panel["context_relevance"][0]
    assert relevance["not_recommendation"] is True
    assert relevance["not_buy_sell"] is True
    assert "supports" in relevance["display"]


def test_524_no_forbidden_language(context_seed):
    panel = cdmc.build_market_context_panel(context_id="test_context")
    text = json.dumps(panel).lower()
    for term in ("buy", "sell", "recommendation"):
        assert f'"{term}"' not in text or term in cdmc._FORBIDDEN_TERMS


def test_524_stale_source_penalties(context_seed):
    signals = [
        {"source": "a", "freshness_seconds": 7200, "confidence_pct": 90, "weight": 1.0, "epistemic_type": "fact"},
    ]
    penalized = cdmc.apply_stale_source_penalty(signals)
    assert penalized[0]["stale_penalty_applied"] is True
    assert penalized[0]["confidence_pct"] < 90


def test_524_single_source_dominance_check(context_seed):
    dominated = cdmc.check_single_source_dominance([
        {"source": "only_source", "weight": 1.0},
        {"source": "only_source", "weight": 1.0},
    ])
    assert dominated["dominated"] is True
    assert dominated["no_single_source_domination"] is False


def test_524_sub_modules_as_tasks(context_seed):
    panel = cdmc.build_market_context_panel(context_id="test_context")
    feeds = panel["sub_modules"]["feeds"]
    assert feeds["523"]["task_not_ticket"] is True
    assert feeds["523"]["standalone_rejected"] is True
    assert feeds["523"]["not_decision_output"] is True


def test_524_output_structure(context_seed):
    panel = cdmc.build_market_context_panel(context_id="test_context")
    assert "what_changed" in panel
    assert "why" in panel
    assert "confirmation" in panel
    assert "risk" in panel
    assert "confidence" in panel
    assert "context_relevance" in panel
    assert panel["not_decision_output"] is True


def test_524_status(context_seed):
    status = cdmc.cross_domain_market_context_status()
    assert status["rule_based_only"] is True
    assert status["tasks_not_tickets"] is True
    assert len(status["sub_modules"]) == 8


def test_api_routes(context_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/intelligence-ledger/intelligence-layer/market-context/status").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/intelligence-layer/market-context?context_id=test_context").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/intelligence-layer/market-context/sub-module/523").status_code == 200


def test_full_seed_exists():
    data = json.loads(Path("data/cross_domain_market_context_layer_seed.json").read_text())
    assert data["not_decision_intelligence"] is True
    assert 524 == data["feature_id"]
    assert 523 in data["absorbed_tickets"]
    assert 530 in data["absorbed_tickets"]
