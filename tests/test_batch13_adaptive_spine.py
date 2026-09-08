"""Adaptive intelligence spine local tests."""

from __future__ import annotations

from bd_platform.adaptive_intelligence import (
    apply_progressive_disclosure,
    build_capability_graph,
    build_decision_contract,
    route_intelligence_request,
    search_intent,
)


def test_intent_search_liquidation() -> None:
    result = search_intent("liquidation screener")
    assert result["abstain"] is False
    assert any(m["capability_id"] == 613 for m in result["matches"])


def test_router_abstains_on_empty() -> None:
    result = route_intelligence_request(goal="")
    assert result["abstain"] is True


def test_decision_contract_has_safety_floor() -> None:
    contract = build_decision_contract(goal="funding", symbol="BTC", candidates=[{"capability_id": 609, "relevance_score": 2}])
    assert "confidence_dimensions" in contract
    assert contract["confidence_dimensions"]["evidence_class"] == "BACKTESTED"


def test_capability_graph_no_causal_edges() -> None:
    graph = build_capability_graph(track="T05", limit=20)
    assert all(e.get("causal") is False for e in graph["edges"])


def test_progressive_disclosure_keeps_disclaimer() -> None:
    payload = {"disclaimer": "Analysis only", "detail": "x" * 100, "evidence_class": "BACKTESTED"}
    out = apply_progressive_disclosure(payload, level="summary")
    assert out["disclaimer"] == "Analysis only"
