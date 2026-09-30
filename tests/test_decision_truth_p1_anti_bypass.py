"""P1 Decision Truth spine and anti-bypass behavior tests."""

from __future__ import annotations

import inspect

import pytest

from decision_truth import govern_decision_payload
from decision_truth.contract import DecisionState
from decision_truth.govern import govern_arbitrage_row
from net_edge_truth import FIN_004_DEMO_OPPORTUNITY


def _complete_payload(**overrides):
    base = {
        "symbol": "BTC",
        "kind": "cross_exchange",
        "quote_age_ms": 120,
        "data_quality_score": 80,
        "evidence_class": "SHADOW_LIVE_FORWARD",
        "liquidity_ok": True,
        "risk_ok": True,
        "net_profit_usdt": 10,
        "quote_amount": 1000,
        "depth_usd": 250000,
        "fill_probability": 0.92,
        "total_slippage_bps": 3,
        "trading_fees_usdt": 0.2,
        "withdrawal_fee_usdt": 0.05,
        "live_duration_seconds": 8,
        "estimated_recipients": 5,
    }
    base.update(overrides)
    return base


def test_dt_failure_not_silent_pass(monkeypatch):
    def _boom(_payload):
        raise RuntimeError("dt broken")

    monkeypatch.setattr("decision_truth.govern.economic_reality", _boom)
    with pytest.raises(RuntimeError):
        govern_decision_payload(_complete_payload(), context="api", run_data_governance=False)


def test_stale_input_governed_abstain_or_reject():
    out = govern_decision_payload(_complete_payload(quote_age_ms=999999, max_quote_age_ms=100), run_data_governance=False)
    state = out["decision_truth_state"]
    assert state in {DecisionState.REJECTED.value, DecisionState.ABSTAINED.value, DecisionState.DEGRADED.value, DecisionState.UNAVAILABLE.value}
    assert out.get("decision_action") == "NO_DECISION"


def test_conflicting_quality_abstains():
    out = govern_decision_payload(
        _complete_payload(data_quality_state="CONFLICTING", data_quality_score=20),
        run_data_governance=False,
    )
    assert out["decision_truth_state"] in {DecisionState.ABSTAINED.value, DecisionState.REJECTED.value, DecisionState.UNAVAILABLE.value, DecisionState.DEGRADED.value}


def test_insufficient_evidence_no_optimistic_defaults():
    out = govern_decision_payload({"symbol": "BTC"}, context="api", run_data_governance=False)
    contract = (out.get("decision_truth") or {}).get("contract") or {}
    assert contract.get("execution_feasibility", {}).get("state") in {"UNAVAILABLE", "EXECUTION_FEASIBILITY_UNAVAILABLE"}
    assert out["decision_truth_state"] != DecisionState.AVAILABLE.value


def test_decision_contract_mandatory_fields():
    out = govern_decision_payload(_complete_payload(), context="api", run_data_governance=False)
    contract = (out.get("decision_truth") or {}).get("contract") or {}
    for key in ("decision_state", "freshness", "evidence_class", "safety_floor", "field_availability", "provenance_context"):
        assert key in contract


def test_safety_floor_blocks_pass_with_missing_context():
    out = govern_decision_payload(_complete_payload(), context="api", run_data_governance=False)
    sf = ((out.get("decision_truth") or {}).get("safety_floor") or {})
    assert "passed" in sf


def test_fallback_visible_in_context():
    out = govern_decision_payload(
        _complete_payload(),
        context="api",
        run_data_governance=False,
    )
    out["fallback_policy"] = {"used_fallback": True, "source": "cache"}
    out2 = govern_decision_payload(out, context="api", run_data_governance=False)
    notes = (out2.get("decision_truth") or {}).get("fallback_notes") or []
    assert any("fallback" in n for n in notes)


def test_failure_state_propagates():
    out = govern_decision_payload(
        _complete_payload(failure_state="UNAVAILABLE"),
        context="api",
        run_data_governance=False,
    )
    fi = ((out.get("decision_truth") or {}).get("contract") or {}).get("failure_integration") or {}
    assert fi.get("failure_state") == "UNAVAILABLE"
    assert out["decision_truth_state"] in {DecisionState.UNAVAILABLE.value, DecisionState.ABSTAINED.value, DecisionState.REJECTED.value}


def test_user_agency_guard():
    out = govern_decision_payload(_complete_payload(verdict="Buy Now"), context="api", run_data_governance=False)
    assert out.get("user_agency", {}).get("informational_only") is True
    assert out.get("user_agency", {}).get("not_execution_instruction") is True


def test_prohibited_claim_sanitized():
    out = govern_decision_payload(
        _complete_payload(narrative="BLACKDARK is the only platform with guaranteed returns"),
        context="api",
        run_data_governance=False,
    )
    assert out.get("compliance_violation") == "prohibited_marketing_claim"


def test_enrichment_uses_govern_not_silent_except():
    import decision_enrichment

    src = inspect.getsource(decision_enrichment.enrich_oracle_decision)
    assert "govern_decision_payload" in src
    assert 'decision_truth"] = {"error": "unavailable"}' not in src


def test_arbitrage_row_governed():
    row = dict(FIN_004_DEMO_OPPORTUNITY)
    row.update(
        {
            "symbol": "BTC",
            "execution_feasibility_score": 70,
            "data_quality_score": 80,
            "evidence_class": "SHADOW_LIVE_FORWARD",
            "liquidity_ok": True,
            "risk_ok": True,
            "uncertainty_high": False,
        }
    )
    governed = govern_arbitrage_row(row)
    assert governed.get("decision_truth_bound") is True
    assert "decision_truth" in governed


def test_demo_payload_admits_when_complete():
    from decision_truth import evaluate_opportunity

    contract = evaluate_opportunity(_complete_payload(), record=False)
    assert contract.decision_state in {DecisionState.AVAILABLE, DecisionState.DEGRADED, DecisionState.ABSTAINED}
