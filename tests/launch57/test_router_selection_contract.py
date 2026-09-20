"""Launch-57 Support Plane Phase 2 — §23 Router Selection Sufficiency Contract."""

from __future__ import annotations

import pytest

from failure.freshness import FreshnessState
from launch57.edge_ui_common import LAUNCH57_SCOPE_IDS
from launch57.router_selection_contract import (
    PIPELINE_STEPS,
    apply_budget,
    apply_conflict_coverage,
    apply_eligibility,
    build_intent_from_params,
    gather_candidates,
    run_router_selection_contract,
)


def _live_spine():
    return {
        "symbol": "BTC",
        "freshness_state": FreshnessState.LIVE.value,
        "live_eligible": True,
        "presented_as_live": True,
    }


def _stale_spine():
    return {
        "symbol": "BTC",
        "freshness_state": FreshnessState.STALE.value,
        "live_eligible": False,
        "presented_as_live": False,
    }


def test_pipeline_steps_order():
    assert PIPELINE_STEPS == (
        "intent",
        "candidates",
        "eligibility",
        "dependence",
        "conflict",
        "budget",
        "stop",
        "abstain",
        "explain",
    )


def test_happy_path_selects_eligible_candidates():
    intent = build_intent_from_params(goal="six_heroes_command_home", symbol="BTC")
    candidates = gather_candidates(intent=intent)
    assert candidates
    assert all(c["launch_id"] in LAUNCH57_SCOPE_IDS for c in candidates)
    eligible, excluded = apply_eligibility(
        candidates,
        intent=intent,
        spine=_live_spine(),
        oracle={"decision_action": "WAIT"},
    )
    assert eligible
    assert {6, 21}.issubset({c["launch_id"] for c in eligible})
    out = run_router_selection_contract(
        goal="six_heroes_command_home",
        symbol="BTC",
        spine=_live_spine(),
        oracle={"decision_action": "WAIT"},
    )
    block = out["router_selection_contract"]
    assert block["abstain"] is False
    assert block["answer_state"] == "SELECTED"
    assert 6 in block["selected_launch_ids"]
    assert 21 in block["selected_launch_ids"]
    assert block["builder_status"] == "PASS_ENGINEERING"


def test_ineligible_parked_excluded():
    intent = build_intent_from_params(goal="test", symbol="BTC")
    candidates = gather_candidates(intent=intent)
    parked = [c for c in candidates if c.get("parked")]
    eligible, excluded = apply_eligibility(
        candidates,
        intent=intent,
        spine=_live_spine(),
        oracle={"decision_action": "WAIT"},
    )
    for p in parked:
        assert p["launch_id"] in {e["launch_id"] for e in excluded}


def test_conflict_handling_abstains():
    conflict = apply_conflict_coverage(
        [],
        oracle={"governed_payload": {"critical_contradiction": {"summary": "bull vs bear"}}},
        spine=_live_spine(),
    )
    assert conflict["conflict_blocks_selection"] is True
    out = run_router_selection_contract(
        goal="six_heroes_command_home",
        symbol="BTC",
        spine=_live_spine(),
        oracle={
            "decision_action": "WAIT",
            "governed_payload": {"critical_contradiction": {"summary": "conflict"}},
        },
    )
    block = out["router_selection_contract"]
    assert block["abstain"] is True
    assert block["abstain_reason"] == "unresolved_material_conflict"


def test_budget_stop_limits_candidates():
    intent = build_intent_from_params(goal="test", symbol="BTC")
    candidates = gather_candidates(intent=intent)
    eligible, _ = apply_eligibility(
        candidates,
        intent=intent,
        spine=_live_spine(),
        oracle={"decision_action": "WAIT"},
    )
    budgeted, budget_meta = apply_budget(eligible, maximum_candidates=3)
    assert len(budgeted) <= 3
    assert budget_meta["maximum_candidates"] == 3
    clusters = {c["dependence_cluster"] for c in budgeted}
    assert "data_spine" in clusters
    assert "trust_surface" in clusters


def test_abstain_on_stale_spine():
    out = run_router_selection_contract(
        goal="six_heroes_command_home",
        symbol="BTC",
        spine=_stale_spine(),
        oracle={"decision_action": "WAIT"},
    )
    block = out["router_selection_contract"]
    assert block["abstain"] is True
    assert block["abstain_reason"] == "stale_or_not_live_eligible"
    assert block["abstain_explanation"]


def test_explain_step_present():
    out = run_router_selection_contract(
        goal="six_heroes_command_home",
        symbol="BTC",
        spine=_live_spine(),
        oracle={"decision_action": "WAIT"},
    )
    explain = out["router_selection_contract"]["explain"]
    assert explain["pipeline_steps"] == list(PIPELINE_STEPS)
    assert explain["isolation"]["parallel_product_router_not_source_of_truth"] is True


@pytest.mark.asyncio
async def test_command_home_wires_router(monkeypatch):
    from launch57.edge_ui_batch2 import six_heroes_command_home

    async def fake_spine(symbol, params=None):
        return _live_spine()

    async def fake_oracle(**kwargs):
        return {
            "decision_action": "WAIT",
            "single_sentence_oracle": {"action": "WAIT", "sentence": "BTC: WAIT"},
            "evidence_class": "SHADOW_LIVE_FORWARD",
        }

    monkeypatch.setattr("launch57.edge_ui_batch2.load_decision_spine", fake_spine)
    monkeypatch.setattr("launch57.edge_ui_batch2.single_sentence_oracle", fake_oracle)
    out = await six_heroes_command_home(symbol="BTC", params={})
    home = out["six_heroes_command_home"]
    router = home.get("router_selection_contract") or {}
    assert router.get("builder_status") == "PASS_ENGINEERING"
    assert "selected_launch_ids" in router
