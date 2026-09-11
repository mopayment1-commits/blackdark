"""Decision Truth package tests (DTS-001..003 MVP)."""

from __future__ import annotations

import pytest

from decision_truth import evaluate_opportunity, pipeline_status
from decision_truth.contract import DecisionState
from net_edge_truth import FIN_004_DEMO_OPPORTUNITY


def test_pipeline_status_exposes_stages():
    status = pipeline_status()
    assert status["package"] == "decision_truth"
    assert "signal_admission_gate" in status["stages"]


def test_evaluate_opportunity_admits_demo_payload():
    opp = dict(FIN_004_DEMO_OPPORTUNITY)
    opp.update(
        {
            "symbol": "BTC",
            "quote_age_ms": 120,
            "data_quality_score": 80,
            "evidence_class": "VERIFIED_LOCAL",
            "execution_feasibility_score": 70,
        }
    )
    contract = evaluate_opportunity(opp, record=False)
    assert contract.decision_state in {DecisionState.AVAILABLE, DecisionState.DEGRADED}
    assert contract.net_edge


def test_evaluate_opportunity_rejects_stale_quote():
    opp = dict(FIN_004_DEMO_OPPORTUNITY)
    opp.update({"symbol": "ETH", "quote_age_ms": 99999, "max_quote_age_ms": 100})
    contract = evaluate_opportunity(opp, record=False)
    assert contract.decision_state in {DecisionState.REJECTED, DecisionState.ABSTAINED, DecisionState.DEGRADED}
    assert contract.why_not
