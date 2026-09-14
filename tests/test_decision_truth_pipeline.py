"""Decision Truth package tests (P1 spine)."""

from __future__ import annotations

import pytest

from decision_truth import evaluate_opportunity, pipeline_status
from decision_truth.contract import DecisionState
from net_edge_truth import FIN_004_DEMO_OPPORTUNITY


def _complete_payload():
    opp = dict(FIN_004_DEMO_OPPORTUNITY)
    opp.update(
        {
            "symbol": "BTC",
            "kind": "cross_exchange",
            "quote_age_ms": 120,
            "data_quality_score": 80,
            "evidence_class": "SHADOW_LIVE_FORWARD",
            "liquidity_ok": True,
            "risk_ok": True,
            "depth_usd": 250000,
            "fill_probability": 0.92,
            "live_duration_seconds": 8,
            "estimated_recipients": 5,
        }
    )
    return opp


def test_pipeline_status_exposes_stages():
    status = pipeline_status()
    assert status["package"] == "decision_truth"
    assert status["canonical_owner"] == "decision_truth/govern.py"
    assert "safety_floor" in status["stages"]


def test_evaluate_opportunity_admits_complete_payload():
    contract = evaluate_opportunity(_complete_payload(), record=False)
    assert contract.decision_state in {DecisionState.AVAILABLE, DecisionState.DEGRADED, DecisionState.ABSTAINED}
    assert contract.net_edge
    assert contract.safety_floor


def test_evaluate_opportunity_rejects_stale_quote():
    opp = _complete_payload()
    opp.update({"quote_age_ms": 99999, "max_quote_age_ms": 100})
    contract = evaluate_opportunity(opp, record=False)
    assert contract.decision_state in {DecisionState.REJECTED, DecisionState.ABSTAINED, DecisionState.DEGRADED, DecisionState.UNAVAILABLE}
    assert contract.why_not
