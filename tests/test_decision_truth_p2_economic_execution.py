"""P2 economic / execution truth behavior tests (DTS-006, 009-015)."""

from __future__ import annotations

from decision_truth import govern_decision_payload
from decision_truth.capacity import estimate_opportunity_capacity
from decision_truth.execution_feasibility import evaluate_execution_feasibility
from decision_truth.half_life import evaluate_opportunity_half_life
from decision_truth.net_edge import evaluate_formal_net_edge
from decision_truth.precision import round_value


def _arb_payload(**overrides):
    base = {
        "kind": "cross_exchange",
        "symbol": "BTC",
        "quote_amount": 1000,
        "net_profit_usdt": 2.5,
        "total_slippage_bps": 3,
        "trading_fees_usdt": 0.2,
        "withdrawal_fee_usdt": 0.05,
        "quote_age_ms": 120,
        "depth_usd": 200000,
        "fill_probability": 0.9,
        "data_quality_score": 80,
        "evidence_class": "SHADOW_LIVE_FORWARD",
        "liquidity_ok": True,
        "risk_ok": True,
        "live_duration_seconds": 6,
        "estimated_recipients": 5,
    }
    base.update(overrides)
    return base


def test_all_cost_components_present_or_na():
    result = evaluate_formal_net_edge(_arb_payload())
    autopsy = result["cost_autopsy"]
    ids = {row["component"] for row in autopsy}
    assert "gross_edge" in ids
    assert "trading_fees" in ids
    assert "expected_slippage" in ids
    bridge = next(r for r in autopsy if r["component"] == "bridge_costs")
    assert bridge["state"] == "NOT_APPLICABLE"


def test_unknown_cost_not_zero():
    result = evaluate_formal_net_edge(_arb_payload(trading_fees_usdt=None))
    del_payload = _arb_payload()
    del del_payload["trading_fees_usdt"]
    result = evaluate_formal_net_edge(del_payload)
    fees = next(r for r in result["cost_autopsy"] if r["component"] == "trading_fees")
    assert fees["state"] == "UNAVAILABLE"
    assert result["reject"] is True


def test_stale_input_affects_execution():
    exec_result = evaluate_execution_feasibility(_arb_payload(quote_age_ms=99999, max_quote_age_ms=100))
    assert exec_result["state"] == "AVAILABLE"
    assert "stale_quote" in exec_result["reason_codes"]


def test_uncertainty_interval_available():
    result = evaluate_formal_net_edge(_arb_payload())
    assert result["uncertainty"]["state"] == "AVAILABLE"
    assert result["uncertainty"]["low_usd"] <= result["expected_net_edge_usd"] <= result["uncertainty"]["high_usd"]


def test_uncertainty_unavailable_when_no_edge():
    result = evaluate_formal_net_edge({"kind": "cross_exchange"})
    assert result["uncertainty"]["state"] == "UNCERTAINTY_UNAVAILABLE"


def test_edge_separation_fields():
    result = evaluate_formal_net_edge(_arb_payload(fill_probability=0.8, capacity_usd=800))
    sep = result["edge_separation"]
    assert "THEORETICAL_EDGE" in sep
    assert "EXPECTED_NET_EDGE" in sep
    assert "REALIZABLE_NET_EDGE" in sep
    assert sep["EXPECTED_NET_EDGE"]["value_usd"] is not None


def test_execution_feasibility_strong_evidence():
    result = evaluate_execution_feasibility(_arb_payload())
    assert result["state"] == "AVAILABLE"
    assert 0 <= result["score"] <= 100


def test_execution_feasibility_insufficient_evidence():
    result = evaluate_execution_feasibility({"kind": "cross_exchange"})
    assert result["state"] == "EXECUTION_FEASIBILITY_UNAVAILABLE"
    assert result["score"] is None


def test_no_optimistic_execution_default_in_govern():
    out = govern_decision_payload({"symbol": "BTC", "kind": "cross_exchange"}, run_data_governance=False)
    exec_block = ((out.get("decision_truth") or {}).get("contract") or {}).get("execution_feasibility") or {}
    assert exec_block.get("state") in {"UNAVAILABLE", "EXECUTION_FEASIBILITY_UNAVAILABLE"}


def test_capacity_limiting_factor():
    cap = estimate_opportunity_capacity(_arb_payload())
    assert cap["state"] == "AVAILABLE"
    assert cap["limiting_factor"] in {"depth", "slippage_sensitivity", "edge_exhausted"}


def test_insufficient_depth_no_fabricated_capacity():
    cap = estimate_opportunity_capacity(_arb_payload(depth_usd=None))
    assert cap["state"] == "UNAVAILABLE"
    assert "capacity_usd" not in cap


def test_half_life_computable_with_live_duration():
    out = evaluate_opportunity_half_life(_arb_payload())
    hl = out["opportunity_half_life"]
    assert hl["local_engineering"] == "LOCAL_ENGINEERING_COMPLETE"
    assert hl["live_validation"] == "LIVE_VALIDATION_PENDING"
    assert hl["state"] == "AVAILABLE"


def test_half_life_unavailable_without_evidence():
    out = evaluate_opportunity_half_life({"kind": "cross_exchange", "symbol": "ZZZ"})
    hl = out["opportunity_half_life"]
    assert hl["state"] == "HALF_LIFE_UNAVAILABLE"


def test_extreme_slippage_reduces_execution_score():
    low = evaluate_execution_feasibility(_arb_payload(total_slippage_bps=3))["score"]
    high = evaluate_execution_feasibility(_arb_payload(total_slippage_bps=80))["score"]
    assert high < low


def test_partial_fill_cost_component():
    result = evaluate_formal_net_edge(_arb_payload(fill_probability=0.4))
    partial = next(r for r in result["cost_autopsy"] if r["component"] == "failed_partial_fill_cost")
    assert partial["state"] == "AVAILABLE"
    assert partial["value_usd"] > 0


def test_gas_cost_applicable_for_cex_dex():
    result = evaluate_formal_net_edge({"kind": "cex_dex", "gas_fee_usdt": 1.2, "net_profit_usdt": 5, "quote_amount": 1000, "total_slippage_bps": 4, "trading_fees_usdt": 0.3, "withdrawal_fee_usdt": 0.1})
    gas = next(r for r in result["cost_autopsy"] if r["component"] == "gas_network_fees")
    assert gas["state"] == "AVAILABLE"


def test_funding_cost_applicable():
    result = evaluate_formal_net_edge(_arb_payload(kind="funding", funding_cost_usdt=0.15))
    funding = next(r for r in result["cost_autopsy"] if r["component"] == "funding")
    assert funding["state"] == "AVAILABLE"


def test_decision_contract_integration():
    out = govern_decision_payload(_arb_payload(), run_data_governance=False)
    contract = (out.get("decision_truth") or {}).get("contract") or {}
    assert contract.get("net_edge", {}).get("cost_autopsy")
    assert contract.get("execution_feasibility", {}).get("methodology_version")
    assert contract.get("capacity", {}).get("state") in {"AVAILABLE", "UNAVAILABLE"}


def test_false_precision_guard():
    assert round_value(1.23456789) == 1.2346
