"""P5 Decision Product Experience behavior tests."""

from __future__ import annotations

import re

import pytest

from decision_truth import govern_decision_payload
from decision_truth.govern import govern_stats
from decision_truth.product.causality import contains_unsupported_causality, sanitize_causal_language
from decision_truth.product.delivery import resolve_user_local_delivery
from decision_truth.product.rejection_engine import build_rejection_engine
from decision_truth.product.why_not import build_why_not_engine


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


def _product(out):
    return (out.get("product_experience") or (out.get("decision_truth") or {}).get("product_experience") or {})


def test_rejected_opportunity_flows_into_rejection_engine():
    before = govern_stats()["evaluated"]
    out = govern_decision_payload(_complete_payload(quote_age_ms=999999, max_quote_age_ms=100), run_data_governance=False)
    product = _product(out)
    engine = product["rejection_engine"]
    assert govern_stats()["evaluated"] >= before + 1
    assert engine["derived_from"] == "canonical_govern_pipeline"
    assert engine["fabricated_metrics"] is False
    assert out["decision_truth_state"] in {"REJECTED", "ABSTAINED", "DEGRADED", "UNAVAILABLE"}


def test_rejection_metrics_from_canonical_records():
    out = govern_decision_payload(_complete_payload(), run_data_governance=False)
    engine = _product(out)["rejection_engine"]
    assert "total_evaluated" in engine
    assert "admitted" in engine
    assert "rejection_reason_categories" in engine
    assert engine["methodology_version"]


def test_why_not_reason_codes_and_human_explanation():
    out = govern_decision_payload(_complete_payload(liquidity_ok=False, depth_usd=1), run_data_governance=False)
    why = _product(out)["why_not_engine"]
    assert "machine_readable" in why
    assert "human_explanation" in why
    assert why["derived_from"] == "canonical_decision_contract"
    assert isinstance(why["machine_readable"]["reason_codes"], list)


def test_stale_conflict_rejection_explanation():
    out = govern_decision_payload(
        _complete_payload(data_quality_state="CONFLICTING", quote_age_ms=999999, max_quote_age_ms=100),
        run_data_governance=False,
    )
    why = _product(out)["why_not_engine"]
    human = str(why["human_explanation"]).lower()
    assert why["decision_state"] in {"REJECTED", "ABSTAINED", "DEGRADED", "UNAVAILABLE"}
    assert "conflict" in human or "fresh" in human or "blocking" in human


def test_six_heroes_consume_canonical_dts():
    out = govern_decision_payload(_complete_payload(), run_data_governance=False)
    heroes = _product(out)["six_heroes"]
    assert heroes["no_ui_recomputation"] is True
    assert len(heroes["heroes"]) == 6
    for key in heroes["hero_keys"]:
        assert key in heroes["heroes"]


def test_missing_hero_data_governed_unavailable():
    out = govern_decision_payload({"symbol": "BTC"}, context="api", run_data_governance=False)
    heroes = _product(out)["six_heroes"]["heroes"]
    assert heroes["best_verified_opportunity"]["state"] in {"UNAVAILABLE", "DEGRADED"}


def test_command_view_uses_canonical_outputs():
    out = govern_decision_payload(
        _complete_payload(),
        run_data_governance=False,
    )
    out["user_preferences"] = {"command_view_enabled": True}
    out2 = govern_decision_payload(out, run_data_governance=False)
    cv = _product(out2).get("command_view")
    assert cv is not None
    assert cv["parallel_logic"] is False
    assert cv["derived_from"] == "canonical_decision_truth"


def test_no_duplicate_decision_calculation_in_ui():
    out = govern_decision_payload(_complete_payload(), run_data_governance=False)
    product = _product(out)
    assert product["projection_source"] == "canonical_decision_truth"
    assert product["no_parallel_logic"] is True


def test_smart_money_treated_as_context():
    out = govern_decision_payload(
        _complete_payload(
            smart_money_context={
                "wallet": {"label": "0xabc", "confidence": 0.3, "source": "chain"},
                "funding": {"rate": 0.01},
            }
        ),
        run_data_governance=False,
    )
    sm = _product(out)["smart_money_context"]
    assert sm["context_only"] is True
    assert sm["not_standalone_decision_driver"] is True


def test_attribution_confidence_present():
    out = govern_decision_payload(
        _complete_payload(smart_money_context={"whale": {"label": "whale-A", "confidence": 0.8, "source": "labels"}}),
        run_data_governance=False,
    )
    attrs = _product(out)["smart_money_context"]["attributions"]
    assert attrs
    assert attrs[0]["confidence"] == 0.8
    assert attrs[0]["source"] == "labels"


def test_uncertain_attribution_state():
    out = govern_decision_payload(
        _complete_payload(smart_money_context={"cluster": {"label": "cluster-x"}}),
        run_data_governance=False,
    )
    attrs = _product(out)["smart_money_context"]["attributions"]
    assert attrs[0]["confidence_state"] == "ATTRIBUTION_UNCERTAIN"


def test_unsupported_causal_phrase_blocked():
    assert contains_unsupported_causality("The whale caused price rise by 2.1%")
    cleaned = sanitize_causal_language({"narrative": "This wallet moved market by 5%"})
    assert "association" in cleaned["narrative"].lower() or "[" in cleaned["narrative"]


def test_daily_brief_what_why_risk_structure():
    out = govern_decision_payload(_complete_payload(material_changes=[{"field": "net_edge", "detail": "improved"}]), run_data_governance=False)
    brief = _product(out)["daily_evidence_autopsy"]
    assert brief["structure"] == ["WHAT_CHANGED", "WHY_IT_MATTERS", "RISKS_INVALIDATION"]
    assert "WHAT_CHANGED" in brief
    assert brief["generic_ai_prose"] is False


def test_daily_brief_material_claims_grounded():
    out = govern_decision_payload(_complete_payload(), run_data_governance=False)
    brief = _product(out)["daily_evidence_autopsy"]
    for section in ("WHAT_CHANGED", "WHY_IT_MATTERS", "RISKS_INVALIDATION"):
        for item in brief.get(section) or []:
            assert item.get("grounded") is True
            assert item.get("evidence_ref")


def test_evidence_backed_sentence_traceability():
    out = govern_decision_payload(_complete_payload(), run_data_governance=False)
    claims = _product(out)["material_claims"]
    assert "claims" in claims
    for claim in claims["claims"]:
        if claim["status"] == "verified":
            assert claim["evidence"].get("source") or claim["evidence"].get("decision_id")


def test_user_local_configurable_delivery():
    out = govern_decision_payload(
        _complete_payload(delivery_preferences={"timezone": "America/New_York", "delivery_hour_local": 9, "opt_in": True}),
        run_data_governance=False,
    )
    delivery = _product(out)["user_local_delivery"]
    assert delivery["user_timezone"] == "America/New_York"
    assert delivery["delivery_hour_local"] == 9
    assert delivery["opt_in"] is True


def test_no_hardcoded_universal_08_00():
    delivery = resolve_user_local_delivery({}, preferences={"timezone": "Europe/London", "delivery_hour_local": 7})
    assert delivery["hardcoded_global_08_00"] is False
    assert delivery["delivery_hour_local"] == 7


def test_reject_bad_opportunity_from_real_record():
    out = govern_decision_payload(
        _complete_payload(net_profit_usdt=-1, raw_opportunity_bps=470, liquidity_ok=False, depth_usd=100),
        run_data_governance=False,
    )
    proof = _product(out)["reject_bad_opportunity"]
    if proof:
        assert proof["fabricated"] is False
        assert proof["derived_from"] == "canonical_govern_pipeline"
        assert "RAW_OPPORTUNITY" in proof["flow"]


def test_no_fabricated_public_proof():
    out = govern_decision_payload(_complete_payload(), run_data_governance=False)
    proof = _product(out).get("reject_bad_opportunity")
    assert proof is None or proof.get("fabricated") is False


def test_no_decision_first_class_state():
    out = govern_decision_payload(_complete_payload(quote_age_ms=999999, max_quote_age_ms=100), run_data_governance=False)
    nd = _product(out)["no_decision"]
    assert nd["first_class_state"] is True
    assert nd["hidden_as_error"] is False
    assert out.get("decision_action") == "NO_DECISION"


def test_full_evidence_trail_completeness_structure():
    out = govern_decision_payload(_complete_payload(), run_data_governance=False)
    trail = _product(out)["full_evidence_trail"]
    assert trail["ui_store_duplication"] is False
    assert trail["canonical_owner"] == "decision_truth.contract"
    for key in (
        "source",
        "timestamp",
        "freshness",
        "net_edge",
        "execution_feasibility",
        "evidence_grade",
        "invalidation_condition",
    ):
        assert key in trail["trail"]


def test_thirty_second_truth_consistency():
    out = govern_decision_payload(_complete_payload(), run_data_governance=False)
    ts = _product(out)["thirty_second_truth"]
    assert ts["independent_summary"] is False
    assert ts["derived_from"] == "canonical_decision_truth"
    assert "capital_position" in ts
    assert "main_risk" in ts
    assert "system_confidence" in ts


def test_calm_default_progressive_disclosure():
    out = govern_decision_payload(_complete_payload(), run_data_governance=False)
    calm = _product(out)["calm_default"]
    assert calm["default_mode"] == "calm"
    assert calm["all_metrics_at_once"] is False
    assert calm["command_view_optional"] is True


def test_optional_command_density_not_default():
    out = govern_decision_payload(_complete_payload(), run_data_governance=False)
    calm = _product(out)["calm_default"]
    assert calm["command_view_not_default"] is True
    assert _product(out).get("command_view") is None


def test_p1_regression_no_decision_on_bad_state():
    out = govern_decision_payload(_complete_payload(quote_age_ms=999999, max_quote_age_ms=100), run_data_governance=False)
    assert out.get("decision_action") == "NO_DECISION"
    assert "product_experience" in out


def test_govern_wires_product_experience():
    out = govern_decision_payload(_complete_payload(), run_data_governance=False)
    assert out.get("todays_decision_surface")
    assert _product(out)
    assert _product(out)["methodology_version"]
