"""Adaptive v4 falsification / adversarial / performance / a11y / HV tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from bd_platform.adaptive_intelligence.intelligence_router import route_intelligence_request
from bd_platform.adaptive_intelligence.performance_budgets import PerformanceBudget, check_budget


def test_AIV4_R01_router_observability_under_load():
    results = [route_intelligence_request(intent_id="decide") for _ in range(20)]
    assert all(r.get("router_explanation", {}).get("budget", {}).get("within_budget") for r in results if not r.get("abstention"))


def test_AIV4_R03_human_validation_protocol_complete():
    from bd_platform.adaptive_intelligence.human_validation import (
        delete_sessions,
        export_sessions,
        infrastructure_status,
        record_session,
        task_protocol,
    )

    st = infrastructure_status()
    assert st["implementation_complete"]
    assert len(task_protocol()) >= 3
    assert st["export_supported"] and st["delete_supported"]
    row = record_session(
        task_id="hv-decide-btc",
        task_success=True,
        time_to_insight_sec=30.0,
        comprehension_score=0.8,
        critical_omission=False,
        decision_reversal=False,
        over_reliance_indicator=False,
        perceived_control=0.9,
        accessibility_task_completed=True,
        consent=True,
    )
    assert row["genuine_participant_evidence"] is False
    assert export_sessions()
    delete_sessions()


def test_AIV4_R04_local_performance_benchmarks():
    from bd_platform.adaptive_intelligence.performance_benchmarks import run_local_benchmarks

    bench = run_local_benchmarks()
    assert bench["status"] == "LOCAL_PERFORMANCE_ENGINEERING_COMPLETE"
    assert bench["router"]["p50_ms"] < 500
    assert bench["router"]["iterations"] >= 50


def test_AIV4_007_local_manual_accessibility():
    from bd_platform.adaptive_intelligence.accessibility import run_local_manual_verification

    result = run_local_manual_verification()
    assert result["status"] == "LOCAL_MANUAL_ACCESSIBILITY_VERIFICATION_COMPLETE"
    assert result["all_templates_ok"]
    assert result["cmd_k_discoverable_alternative"]


# --- adversarial router ---


def test_adversarial_stale_data_abstain():
    r = route_intelligence_request(intent_id="decide", force_degraded=True)
    assert r["stance"] == "ABSTAIN"


def test_adversarial_entitlement_denied():
    r = route_intelligence_request(intent_id="decide", force_entitlement_denied=True)
    assert r["stance"] == "ABSTAIN"
    assert r["reason"] == "no_eligible_candidates"


def test_adversarial_empty_candidates():
    r = route_intelligence_request(force_empty_candidates=True)
    assert r["abstention"]


def test_adversarial_budget_exhaustion():
    with pytest.raises(ValueError, match="budget_latency_exceeded"):
        check_budget(PerformanceBudget(max_latency_ms=0.001), candidate_count=1, selected_count=1, elapsed_ms=10.0)


def test_adversarial_correlated_evidence_clustered():
    from bd_platform.adaptive_intelligence.silent_confirmation import effective_evidence_count

    signals = [{"source_cluster": "x"} for _ in range(5)]
    eff = effective_evidence_count(signals)
    assert eff["effective_independent_evidence"] == 1


def test_adversarial_recommendation_feedback_loop_guard():
    from bd_platform.adaptive_intelligence.recommendation_engine import score_recommendation

    s = score_recommendation(popularity=1.0, relevance=0.0, trust_quality=0.0)
    assert s["why_recommended"]["financial_ground_truth"] is False


def test_role_preferences_not_restrictive():
    from bd_platform.adaptive_intelligence.role_preferences import get_role_preferences

    r = get_role_preferences("institutional")
    assert r["restricts_capabilities"] is False


def test_contextual_capabilities_canonical():
    from bd_platform.adaptive_intelligence.contextual_capabilities import contextual_capabilities

    c = contextual_capabilities("risk")
    assert c["canonical_semantics_unchanged"]
    assert c["entitlement_authority"]


def test_progressive_disclosure_safety_floor_level1():
    from bd_platform.adaptive_intelligence.progressive_disclosure import build_disclosure_levels

    d = build_disclosure_levels({"stance": "NEUTRAL", "why": ["test"]})
    assert d["level_1_answer"]["safety_floor_enforced"]


def test_playbook_official_registered():
    from bd_platform.adaptive_intelligence.playbook_governance import list_playbooks

    pbs = list_playbooks()
    assert any(p["playbook_id"] == "official-risk-scan-v1" for p in pbs)


def test_api_benchmarks_endpoint():
    import dashboard

    client = TestClient(dashboard.app)
    r = client.get("/api/adaptive/benchmarks")
    assert r.status_code == 200
    assert r.json()["status"] == "LOCAL_PERFORMANCE_ENGINEERING_COMPLETE"


def test_api_accessibility_local():
    import dashboard

    client = TestClient(dashboard.app)
    r = client.get("/api/adaptive/accessibility/local-verification")
    assert r.status_code == 200
    assert r.json()["all_templates_ok"]
