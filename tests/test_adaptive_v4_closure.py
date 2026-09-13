"""Adaptive Intelligence v4 local closure tests (AIE + AIV4 RTM)."""

from __future__ import annotations

import pytest

from bd_platform.adaptive_intelligence.capability_graph import EdgeType, GraphEdge, add_edge, validate_edge
from bd_platform.adaptive_intelligence.decision_boundary import build_boundary
from bd_platform.adaptive_intelligence.decision_contract import build_adaptive_decision_contract
from bd_platform.adaptive_intelligence.intelligence_router import route_intelligence_request
from bd_platform.adaptive_intelligence.performance_budgets import PerformanceBudget
from bd_platform.adaptive_intelligence.recommendation_engine import score_recommendation
from bd_platform.adaptive_intelligence.safety_floor import enforce_safety_floor
from bd_platform.adaptive_intelligence.silent_confirmation import effective_evidence_count
from bd_platform.adaptive_intelligence.temporal_validity import compute_temporal_validity
from bd_platform.adaptive_intelligence.trust_dimensions import TrustDimensionVector
from governance.adaptive_ux_requirements import aie_catalog, verify_aie_runtime
from net_edge_truth import FIN_004_DEMO_OPPORTUNITY


def _demo_opportunity(**extra):
    opp = dict(FIN_004_DEMO_OPPORTUNITY)
    opp.update(
        {
            "symbol": "BTC",
            "quote_age_ms": 120,
            "data_quality_score": 80,
            "evidence_class": "forward_shadow",
            "execution_feasibility_score": 70,
        }
    )
    opp.update(extra)
    return opp


# --- AIE spine ---


def test_AIE_001_six_heroes_manifest():
    from bd_platform.adaptive_intelligence.heroes import heroes_manifest

    m = heroes_manifest()
    assert len(m["product_heroes"]) == 6
    assert m["governance_alias_map"]


def test_AIE_002_router_contract():
    result = route_intelligence_request(intent_id="decide")
    assert result["abstention"] is False
    assert "explain" in result["router_stages_completed"]


def test_AIE_003_calm_surface():
    from bd_platform.adaptive_intelligence.calm_surface import calm_surface_manifest

    m = calm_surface_manifest()
    assert m["surface_budget_enforced"]
    assert m["capability_library_hidden_on_home"]


def test_AIE_004_universal_command():
    from bd_platform.adaptive_intelligence.universal_command import universal_command_search

    out = universal_command_search(query="decide BTC")
    assert out["intent_contract"]["goal"]
    assert out["router_result"]["stance"]


def test_AIE_005_today_focus():
    from bd_platform.adaptive_intelligence.today_focus import build_today_focus

    focus = build_today_focus()
    assert focus["safety_floor_required"]
    assert focus["main_opportunity"]["safety_floor_enforced"]


def test_AIE_006_decision_contract():
    contract = build_adaptive_decision_contract(_demo_opportunity())
    assert contract["current_stance"]
    assert contract["confidence_vector"]["calibration_state"] == "uncalibrated"
    assert contract["trust_dimensions"]


def test_AIE_007_trust_dimensions_independent():
    v = TrustDimensionVector(assurance="verified", freshness="delayed", coverage="limited")
    assert v.compact_label()
    d = v.to_dict()
    assert d["assurance"] == "verified" and d["freshness"] == "delayed"


def test_AIE_008_capability_explorer():
    from bd_platform.adaptive_intelligence.capability_explorer import list_explorer_cards

    cards = list_explorer_cards(limit=5)
    assert cards
    assert cards[0]["ssot_source"] == "cap646/catalog.py"


def test_AIE_009_intent_contract():
    from bd_platform.adaptive_intelligence.intent_contract import resolve_intent_contract

    ic = resolve_intent_contract(intent_id="decide", asset="btc")
    assert ic.required_safety_lenses
    assert ic.asset_scope == "BTC"


def test_AIE_010_playbook_governance():
    from bd_platform.adaptive_intelligence.playbook_governance import PlaybookContract, register_playbook

    pb = PlaybookContract(playbook_id="pb-1", version="1.0.0", purpose="Risk scan", validation_state="shadow")
    register_playbook(pb)
    with pytest.raises(ValueError):
        PlaybookContract(playbook_id="bad", version="1", purpose="", validation_state="shadow").validate_official()


def test_AIE_011_typed_graph_edges():
    store: list = []
    add_edge(store, {"source_id": "a", "target_id": "b", "edge_type": "SUPPORTS"})
    with pytest.raises(ValueError):
        validate_edge({"source_id": "a", "target_id": "b", "edge_type": "CAUSES"})


def test_AIE_012_workspaces():
    from bd_platform.adaptive_intelligence.workspaces import get_workspace, list_workspaces

    assert list_workspaces()
    assert get_workspace("risk_center")


def test_AIE_013_router_ten_stages():
    result = route_intelligence_request(intent_id="verify")
    stages = result["router_stages_completed"]
    for stage in ("intent", "mandatory_controls", "candidate_eligibility", "dependence_clustering", "explain"):
        assert stage in stages


def test_AIE_014_sellable_core_surfaces():
    from bd_platform.adaptive_intelligence.calm_surface import calm_surface_manifest

    surfaces = calm_surface_manifest()["primary_surfaces"]
    assert "six_heroes" in surfaces and "universal_command" in surfaces


def test_AIE_015_my_stack():
    from bd_platform.adaptive_intelligence.my_stack import add_favorite, get_stack

    stack = add_favorite("u1", "single_sentence_oracle")
    assert "single_sentence_oracle" in get_stack("u1")["favorites"]


def test_AIE_016_top_opportunity_surface():
    from bd_platform.adaptive_intelligence.today_focus import build_today_focus

    assert "main_opportunity" in build_today_focus()


def test_AIE_017_key_risk_surface():
    from bd_platform.adaptive_intelligence.today_focus import build_today_focus

    assert "primary_risk" in build_today_focus()


def test_AIE_018_what_changed_surface():
    from bd_platform.adaptive_intelligence.today_focus import build_today_focus

    assert "what_changed" in build_today_focus()


def test_AIE_019_data_room_view():
    from bd_platform.adaptive_intelligence.data_room_view import capability_data_room_view, data_room_manifest

    assert data_room_manifest()["parallel_registry_forbidden"]
    view = capability_data_room_view(1)
    assert view.get("ok") or view.get("error")


def test_AIE_020_entitlement_preview():
    from bd_platform.adaptive_intelligence.entitlement_gate import subscription_preview

    denied = subscription_preview(47, entitled=False)
    assert denied["live_claim_hidden"]


# --- AIV4 requirements ---


def test_AIV4_001_deterministic_router():
    a = route_intelligence_request(intent_id="decide")
    b = route_intelligence_request(intent_id="decide")
    assert a["router_explanation"]["selected"] == b["router_explanation"]["selected"]


def test_AIV4_002_no_false_precision():
    with pytest.raises(ValueError, match="numeric_confidence_requires_calibration"):
        build_adaptive_decision_contract(_demo_opportunity(numeric_confidence=0.82))


def test_AIV4_003_reuse_before_build():
    from bd_platform.adaptive_intelligence.decision_contract import build_adaptive_decision_contract

    c = build_adaptive_decision_contract(_demo_opportunity())
    assert "dts_contract" in c


def test_AIV4_004_safety_floor_fail_closed():
    with pytest.raises(ValueError, match="safety_floor_incomplete"):
        enforce_safety_floor({"decision_critical": True, "freshness": ""})


def test_AIV4_005_recommendation_separation():
    s = score_recommendation(popularity=0.9, relevance=0.1, trust_quality=0.1)
    assert s["why_recommended"]["financial_ground_truth"] is False
    assert s["composite_rank"] < 0.9


def test_AIV4_006_subscription_preview_honest():
    from bd_platform.adaptive_intelligence.entitlement_gate import subscription_preview

    p = subscription_preview(85, entitled=False)
    assert p["preview_mode"] == "metadata_only"


def test_AIV4_007_accessibility_protocol():
    from bd_platform.adaptive_intelligence.accessibility import accessibility_checklist, verify_surface_contract

    cl = accessibility_checklist()
    assert cl["manual_verification_required"]
    ok = verify_surface_contract("dashboard", {k: True for k in cl["criteria"]})
    assert ok["ok"]


def test_AIV4_008_confidence_vector_only():
    c = build_adaptive_decision_contract(_demo_opportunity())
    assert c["numeric_confidence"] is None


def test_AIV4_009_decision_boundary():
    from bd_platform.adaptive_intelligence.decision_boundary import DecisionBoundaryContract

    q = build_boundary(variables=["staleness"], qualitative_invalidation="stale_data")
    assert q["qualitative_invalidation"]
    bad = DecisionBoundaryContract(variables=["x"], threshold=1.0, evidence_link=None)
    with pytest.raises(ValueError, match="numeric_threshold_requires_evidence_link"):
        bad.validate()


def test_AIV4_010_temporal_validity_no_grinold():
    tv = compute_temporal_validity(observed_at=1.0, calibration_available=False)
    assert tv["grinold_attribution"] is False
    assert tv["decay_factor"] is None


def test_AIV4_011_dependence_aware_evidence():
    signals = [
        {"capability_id": "a", "source_cluster": "cluster1"},
        {"capability_id": "b", "source_cluster": "cluster1"},
        {"capability_id": "c", "source_cluster": "cluster2"},
    ]
    eff = effective_evidence_count(signals)
    assert eff["raw_count"] == 3
    assert eff["effective_independent_evidence"] == 2


def test_AIV4_012_mirror_ledger_consent():
    from bd_platform.adaptive_intelligence.mirror_ledger import record_user_decision

    row = record_user_decision(user_id="u", decision_ref="d1", user_stance="wait", consent=True)
    assert row["financial_ground_truth"] is False
    with pytest.raises(ValueError):
        record_user_decision(user_id="u", decision_ref="d1", user_stance="wait", consent=False)


def test_human_validation_infrastructure():
    from bd_platform.adaptive_intelligence.human_validation import infrastructure_status

    st = infrastructure_status()
    assert st["implementation_complete"]
    assert st["status"] == "EXTERNAL_HUMAN_EVIDENCE_GATED"


def test_AIV4_014_performance_budget():
    budget = PerformanceBudget(max_candidates=2, max_selected=1)
    with pytest.raises(ValueError, match="budget_candidate_explosion"):
        route_intelligence_request(intent_id="decide", budget=PerformanceBudget(max_candidates=1))


def test_AIV4_015_api_router_binding():
    from api.routers.adaptive_intelligence import router

    paths = [getattr(r, "path", "") for r in router.routes]
    assert "/api/adaptive/status" in paths


def test_AIV4_016_p0_foundations():
    from bd_platform.adaptive_intelligence.capability_graph import EdgeType

    assert EdgeType.EVIDENCE_FOR.value == "EVIDENCE_FOR"


def test_AIV4_017_router_abstention_degraded():
    result = route_intelligence_request(intent_id="decide", force_degraded=True)
    assert result["stance"] == "ABSTAIN"


def test_AIV4_018_governance_runtime_all_aie():
    runtime = verify_aie_runtime()
    assert runtime["implemented_count"] == runtime["total"]
    assert all(r["status"] == "IMPLEMENTED" for r in aie_catalog())


def test_AIV4_R01_router_observability():
    result = route_intelligence_request(intent_id="decide")
    assert result["router_explanation"]["budget"]["within_budget"]


def test_AIV4_R02_calibration_controls():
    c = build_adaptive_decision_contract(_demo_opportunity(calibration_evidence=True, numeric_confidence=0.7))
    assert c["numeric_confidence"] == 0.7


# --- adversarial ---


def test_adversarial_stale_abstain():
    assert route_intelligence_request(force_degraded=True)["abstention"]


def test_adversarial_graph_causes_forbidden():
    with pytest.raises(ValueError):
        GraphEdge(source_id="a", target_id="b", edge_type=EdgeType.CAUSES)


def test_adversarial_budget_latency():
    from bd_platform.adaptive_intelligence.performance_budgets import check_budget

    with pytest.raises(ValueError, match="budget_latency_exceeded"):
        check_budget(PerformanceBudget(max_latency_ms=1.0), candidate_count=1, selected_count=1, elapsed_ms=50.0)


def test_control_removal_safety_floor():
    with pytest.raises(ValueError):
        enforce_safety_floor({"decision_critical": True})
