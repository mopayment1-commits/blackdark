"""Unit coverage for launch57.trust_adaptive_common shared spec guards and disclosure helpers."""

from __future__ import annotations

import launch57.trust_adaptive_common as tac
from launch57.trust_adaptive_common import (
    METHODOLOGY_VERSION,
    apply_capability_library_guard,
    apply_command_home_guard,
    apply_discipline_mirror_guard,
    apply_mvrv_provenance_guard,
    apply_personal_history_guard,
    apply_spot_perp_net_edge_semantics,
    attach_adaptive_disclosure,
    build_abstention_reject_disclosure,
    build_certificate_adaptive_fields,
    build_derivatives_composite_disclosure,
    build_discipline_mirror_disclosure,
    build_ledger_interpretation_context,
    build_level1_decision_disclosure,
    build_market_context_disclosure,
    build_mvrv_provenance_disclosure,
    build_net_edge_safety_floor,
    build_personal_history_disclosure,
    build_progressive_disclosure_stack,
    build_spot_perp_net_edge_disclosure,
    build_wallet_due_diligence_disclosure,
    compute_approved_token_due_diligence_verdict,
    compute_approved_wallet_due_diligence_verdict,
    compute_derivatives_sentiment_composite,
    extract_abstention_reason,
    extract_deeper_evidence_link,
    extract_material_contradiction,
    extract_material_limitation,
    validate_material_claims_from_payload,
)


def test_extract_helpers_and_governed_payload():
    payload = {
        "governed_payload": {"contradictions": [{"summary": "price vs sentiment"}]},
        "limitations": "stale feed",
        "evidence_link": "https://example.com/evidence",
    }
    assert extract_material_contradiction(payload)["summary"] == "price vs sentiment"
    assert extract_material_limitation(payload)["summary"] == "stale feed"
    assert extract_deeper_evidence_link(payload) == "https://example.com/evidence"
    assert extract_abstention_reason({"abstention_reason": "low confidence"}, action="ABSTAIN") == "low confidence"
    assert extract_abstention_reason({"abstention_reason": "low confidence"}, action="WAIT") is None


def test_build_level1_decision_disclosure_uncertainty_paths():
    payload = {"freshness_state": "LIVE", "uncertainty": "explicit"}
    l1 = build_level1_decision_disclosure(
        payload,
        launch_item_id=7,
        surface="market_regime_compass",
        answer_state="WAIT",
        decision_timing={"recheck_time": "2026-01-01T00:00:00Z"},
    )
    assert l1["layer"] == "level_1_decision"
    assert l1["uncertainty"] == "explicit"
    assert l1["safety_floor_visible"] is True
    assert l1["methodology_version"] == METHODOLOGY_VERSION

    abstain = build_level1_decision_disclosure(
        {"abstain_reason": "insufficient breadth"},
        launch_item_id=48,
        surface="abstain_reject",
        answer_state="ABSTAIN",
    )
    assert abstain["uncertainty"] == "insufficient_evidence"
    assert abstain["abstention_reason"] == "insufficient breadth"


def test_certificate_ledger_and_net_edge_safety_floor():
    cert = build_certificate_adaptive_fields(
        {"governed_payload": {"key_drivers": ["a"], "limitations": ["b"]}}
    )
    assert cert["key_drivers"] == ["a"]
    assert cert["limitations"] == ["b"]

    ledger = build_ledger_interpretation_context({"cumulative": {"metrics_scope": "live_only"}})
    assert ledger["metrics_scope"] == "live_only"
    assert ledger["shadow_not_production_history"] is True

    floor = build_net_edge_safety_floor(
        {"truth_edge": 1.0, "residual": 0.5, "net": 0.4, "pass": True, "reject": False},
        {},
    )
    assert floor["gross_edge_not_actionable_without_cost_treatment"] is True
    assert floor["cost_claim_allowed"] is True


def test_progressive_disclosure_stack_levels():
    stack = build_progressive_disclosure_stack(
        {"six_heroes_command_home": {"router_selection_contract": {"explain": {"selection_summary": "ok"}}}},
        launch_item_id=1,
        surface="six_heroes_command_home",
        answer_state="COMMAND_HOME_GROUNDED",
    )
    for key in ("level_1", "level_2", "level_3", "level_4", "level_5"):
        assert stack[key]["safety_floor_visible"] is True


def test_attach_adaptive_disclosure_without_support_plane():
    body = {"launch_item_id": 5, "surface": "net_edge_truth_score", "success": True}
    disclosure = build_level1_decision_disclosure(
        body,
        launch_item_id=5,
        surface="net_edge_truth_score",
        answer_state="ACT",
    )
    out = attach_adaptive_disclosure(
        body,
        disclosure,
        apply_full_support_plane=False,
    )
    assert out["adaptive_disclosure"]["level_1"]["launch_item_id"] == 5
    assert out["safety_floor_visible"] is True


def test_market_context_and_abstention_disclosures():
    ctx = build_market_context_disclosure({"macro_regime": "Risk-On"})
    assert ctx["context_only"] is True
    assert ctx["standalone_trade_instruction"] is False

    abst = build_abstention_reject_disclosure(
        {"decision_action": "ABSTAIN"},
        no_decision={"first_class_state": True, "reason_codes": ["LOW_EVIDENCE"]},
        rejection={"dominant_rejection_causes": ["stale"]},
    )
    assert abst["first_class_state"] is True
    assert abst["reason_codes"] == ["LOW_EVIDENCE"]


def test_validate_material_claims_delegates_or_falls_back():
    out = validate_material_claims_from_payload({"claims": []})
    assert "claims" in out
    assert out.get("all_grounded") is True or out.get("total_material_claims") is not None


def test_apply_spot_perp_net_edge_semantics():
    semantics = apply_spot_perp_net_edge_semantics(
        [{"id": "opp-1", "spread_bps": 12}],
        net_edge_result={"net_edge": {"pass": True}, "blocked": False},
        params={"opportunity": {"id": "opp-1"}},
        spine={"presented_as_live": True, "live_eligible": True},
    )
    assert semantics["answer_state"] == "NET_EDGE_QUALIFIED"
    assert semantics["executable_count"] == 1
    disc = build_spot_perp_net_edge_disclosure(semantics)
    assert disc["gross_spread_not_executable_without_net_edge"] is True


def test_apply_mvrv_provenance_guard_blocked_external():
    guarded = apply_mvrv_provenance_guard(
        {"BTC": {"ok": True, "z_score": 1.1}},
        {},
        asset="BTC",
        spine={"presented_as_live": True, "live_eligible": True},
        params={},
    )
    assert guarded["answer_state"] == "BLOCKED_EXTERNAL_NO_LICENSED_SOURCE"
    assert guarded["no_phantom_live_values"] is True
    disc = build_mvrv_provenance_disclosure(guarded)
    assert disc["blocked_external_preserved"] is True


def test_personal_history_and_discipline_mirror_guards():
    history = apply_personal_history_guard([{"id": 1, "action": "WAIT"}], tier="free")
    assert history["history_only"] is True
    assert history["answer_state"] == "HISTORY_OBSERVABLE"
    assert build_personal_history_disclosure(history)["history_only"] is True

    rejected = apply_personal_history_guard([], params={"behavioral_learning": True})
    assert rejected["behavioral_learning_rejected"] is True
    assert rejected["answer_state"] == "UNSUPPORTED_LEARNING_SCOPE_REJECTED"

    mirror = apply_discipline_mirror_guard({"score": 0.5, "note": "reflect"})
    assert mirror["reflective_only"] is True
    assert mirror["answer_state"] == "MIRROR_OBSERVABLE"
    assert build_discipline_mirror_disclosure(mirror)["reflective_only"] is True


def test_apply_capability_library_guard_ssot_only():
    rows = [
        {"launch_number": 5, "engineering_status": "PASS_ENGINEERING", "title": "Net Edge"},
        {"launch_number": 99, "engineering_status": "PASS_ENGINEERING", "title": "Out of scope"},
        {"launch_number": 3, "engineering_status": "PARKED", "title": "Parked"},
    ]
    grounded = apply_capability_library_guard(rows)
    assert grounded["answer_state"] == "LIBRARY_GROUNDED"
    assert grounded["count"] >= 1
    assert grounded["launch57_scope_only"] is True
    assert grounded["ssot_source"] == "governance/launch57/LAUNCH57_REGISTER.json"

    rejected = apply_capability_library_guard(rows, params={"include_parked": True})
    assert rejected["answer_state"] == "UNSUPPORTED_REGISTRY_SCOPE_REJECTED"
    assert rejected["count"] == 0


def test_apply_command_home_guard_grounded_and_rejected():
    spine = {"live_eligible": True, "presented_as_live": True, "freshness_state": "LIVE"}
    oracle = {"evidence_class": "SHADOW_LIVE_FORWARD", "decision_action": "WAIT"}
    heroes = {"HERO_TRUTH": {"state": "grounded"}}
    grounded = apply_command_home_guard(heroes=heroes, command_view={"surface": "home"}, oracle=oracle, spine=spine)
    assert grounded["answer_state"] == "COMMAND_HOME_GROUNDED"
    assert grounded["launch57_scope_only"] is True
    assert grounded["excludes_parked"] is True

    rejected = apply_command_home_guard(
        heroes=heroes,
        command_view=None,
        oracle=oracle,
        spine=spine,
        params={"include_parked": True},
    )
    assert rejected["scope_rejected"] is True
    assert rejected["answer_state"] == "UNSUPPORTED_READINESS_SCOPE_REJECTED"


def test_wallet_and_token_due_diligence_verdicts():
    wallet = compute_approved_wallet_due_diligence_verdict(
        intel={"ok": False},
        surveillance={"surveillance_detected": False},
        spine={"live_eligible": True, "presented_as_live": True},
    )
    assert wallet["verdict"] == "review"
    assert wallet["decision_driving_approved_only"] is True
    wallet_disc = build_wallet_due_diligence_disclosure(wallet, spine={"live_eligible": True, "presented_as_live": True})
    assert wallet_disc["due_diligence_from_approved_launch57_evidence_only"] is True

    token = compute_approved_token_due_diligence_verdict(
        holders={"available": True, "metrics": {"locked_supply_pct": 80}},
        financial_models={"error": "gap"},
        spine={"live_eligible": True, "presented_as_live": True},
    )
    assert token["verdict"] == "review"
    assert "high_locked_supply" in token["risk_flags"]


def test_compute_derivatives_sentiment_composite_disagreement():
    semantics = compute_derivatives_sentiment_composite(
        sentiment={"score": 0.8, "bias": "bullish"},
        deriv_overview={"free_tier": {"funding_rate": -0.02, "taker_buy_sell_ratio": 0.4}},
        spine={"live_eligible": True, "presented_as_live": True},
    )
    assert semantics["answer_state"] in {"COMPONENT_DISAGREEMENT", "ALIGNED_COMPOSITE", "INSUFFICIENT_EVIDENCE"}
    assert semantics["methodology_version"] == METHODOLOGY_VERSION
    disc = build_derivatives_composite_disclosure(semantics)
    assert disc["derivatives_contract_visible"] is True


def test_methodology_version_constant():
    assert tac.METHODOLOGY_VERSION.startswith("launch57-trust-adaptive-common")
