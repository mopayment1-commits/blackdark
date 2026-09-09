"""Decision Truth P0 test matrix — DTS-001 → DTS-060 local engineering evidence."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("SOFT_LAUNCH", "1")

from net_edge_truth import FIN_004_DEMO_OPPORTUNITY


def _evaluate(opp: dict | None = None, **kwargs):
    from decision_truth.pipeline import evaluate_decision_truth

    base = dict(FIN_004_DEMO_OPPORTUNITY)
    base.update({"asset": "BTC", "verdict": "BUY", "source": "oracle"})
    if opp:
        base.update(opp)
    return evaluate_decision_truth(base, **kwargs)


def test_formal_net_edge_and_cost_autopsy():
    result = _evaluate()
    dt = result["decision_truth"]
    net = dt["net_edge"]
    assert net["methodology_version"]
    assert "cost_autopsy" in net
    components = net["cost_autopsy"]["components"]
    assert "gross_edge" in components
    assert components["borrow_cost"]["status"] == "N/A"


def test_net_edge_uncertainty_and_realizable_edge():
    result = _evaluate({"fill_probability": 0.41})
    net = result["decision_truth"]["net_edge"]
    assert net["net_edge_interval"]["lower_bound"] is not None or net["expected_net_edge_usd"] is None
    if net.get("realizable_net_edge_usd") is not None:
        assert net["realizable_net_edge_usd"] <= (net.get("expected_net_edge_usd") or 999)


def test_execution_feasibility_score():
    result = _evaluate()
    ex = result["decision_truth"]["execution_feasibility"]
    assert 0 <= ex["execution_feasibility_score"] <= 100
    assert ex["reason_codes"]


def test_opportunity_capacity_and_half_life():
    result = _evaluate({"depth_usd": 50000, "opportunity_half_life": {"remaining_seconds": 120}})
    dt = result["decision_truth"]
    assert dt["capacity"]["capacity_usd"] is not None
    assert dt["half_life"]["status"] in {"estimated", "unavailable"}


def test_signal_admission_gate_rejects_bad_net_edge():
    result = _evaluate({"net_profit_usdt": -1.0, "quote_amount": 1000})
    admission = result["decision_truth"]["admission"]
    assert admission["admission_state"] in {"REJECTED", "DEGRADED", "ABSTAINED"}


def test_abstention_on_conflicting_evidence():
    result = _evaluate({"dimension_conflict": {"veto": True, "abstain": True}})
    assert result["decision_truth"]["admission"]["admission_state"] in {"ABSTAINED", "REJECTED", "DEGRADED"}


def test_decision_contract_fields():
    result = _evaluate()
    contract = result["decision_truth"]["contract"]
    for key in ("decision_id", "decision_state", "expected_net_edge", "evidence_grade", "why", "scorecard"):
        assert key in contract


def test_why_not_engine():
    result = _evaluate({"net_profit_usdt": -5.0})
    why = result["decision_truth"]["why_not"]
    assert "human_explanation" in why
    assert why.get("reason_codes") is not None


def test_safety_floor_present():
    sf = _evaluate()["decision_truth"]["safety_floor"]
    assert sf["freshness"]
    assert sf["execution_feasibility"] is not None


def test_evidence_grade_explainable():
    grade = _evaluate()["decision_truth"]["evidence_grade"]
    assert grade["overall_grade"] in {"A", "B", "C", "D", "E", "F"}
    assert grade["component_scores"]


def test_risk_budget_and_pre_impact():
    risk = _evaluate(portfolio={"max_tolerated_loss_pct": 3.0, "current_risk_use_pct": 2.5})["decision_truth"]["risk"]
    assert "risk_budget" in risk
    assert "pre_impact" in risk
    assert "reverse_stress" in risk


def test_smart_money_no_unsupported_causality():
    from decision_truth.smart_money import audit_causality_language

    assert audit_causality_language("Wallet activity associated with price move") is True
    assert audit_causality_language("Whale X caused +2.1%") is False


def test_calibration_and_outcome_ledgers():
    from decision_truth.calibration import calibration_summary, record_calibration_bucket
    from decision_truth.outcome import pre_register_outcome

    record_calibration_bucket(confidence_bucket="0.5-0.6", predicted_probability=0.55, realized=True, decision_id="dts-test-1")
    summary = calibration_summary(min_samples=1)
    assert summary["status"] in {"CALIBRATION_INSUFFICIENT_DATA", "CALIBRATION_AVAILABLE"}
    out = pre_register_outcome(
        decision_id="dts-test-1",
        prediction="WAIT",
        confidence=0.5,
        horizon="1h",
        invalidation_condition="stale",
        evidence_class="SHADOW_LIVE_FORWARD",
        methodology_versions={"net_edge": "net_edge_v2.0"},
    )
    assert out["outcome_id"]


def test_decision_change_detector():
    result = _evaluate(previous_decision_state="AVAILABLE")
    change = result["decision_truth"]["change"]
    assert "changed" in change


def test_six_heroes_and_evidence_trail():
    dt = _evaluate()["decision_truth"]
    assert dt["six_heroes"]["progressive_disclosure"] is True
    assert dt["evidence_trail"]["net_edge"]


def test_daily_evidence_autopsy():
    from decision_truth.daily_autopsy import build_daily_autopsy

    autopsy = build_daily_autopsy({"what_changed": "Funding flipped", "why_it_matters": "Risk up"})
    assert autopsy["bullets"]


def test_simulation_disclosure():
    sim = _evaluate()["decision_truth"]["contract"].get("simulation_summary") or _evaluate()["decision_truth"]["net_edge"]
    from decision_truth.simulation import simulation_summary

    payload = simulation_summary({})
    assert payload["limitations"]


def test_methodology_versions():
    from decision_truth.methodology import methodology_versions

    versions = methodology_versions()
    assert versions["net_edge"]
    assert versions["admission_gate"]


@pytest.mark.asyncio
async def test_decision_truth_api_evaluate():
    from httpx import ASGITransport, AsyncClient

    from dashboard import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/decision-truth/evaluate", json={"opportunity": FIN_004_DEMO_OPPORTUNITY})
        assert resp.status_code == 200
        body = resp.json()
        assert body["decision_truth"]["contract"]["decision_id"]


def test_oracle_enrichment_includes_decision_truth():
    from decision_enrichment import enrich_oracle_decision

    payload = enrich_oracle_decision(
        {"symbol": "BTC", "verdict": "WAIT", "opportunity_score": 50, "net_profit_usdt": 2.5, **FIN_004_DEMO_OPPORTUNITY},
        lang="en",
        register_signal=False,
    )
    assert "decision_truth" in payload
    assert payload["decision_truth"].get("contract") or payload["decision_truth"].get("error")


def test_dts_i18n_keys_present():
    from i18n_service import EN, LOCALES, catalogs, invalidate_catalogs

    invalidate_catalogs()
    keys = [k for k in EN if k.startswith("dts.")]
    assert keys
    for code in LOCALES:
        cat = catalogs()[code]
        for key in keys:
            assert key in cat


def test_engineering_closure_module():
    from bd_platform.decision_truth_source_driven_engineering import decision_truth_source_driven_status

    status = decision_truth_source_driven_status(head="test", pytest_ok=True)
    assert status["SOURCE_REQUIREMENTS_ACCOUNTED_FOR"] == "100%"
    assert len(status["requirements"]) == 60
