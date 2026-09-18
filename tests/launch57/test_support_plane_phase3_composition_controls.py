"""Launch-57 Support Plane Phase 3 — §32 composition controls."""

from __future__ import annotations

import pytest

from failure.freshness import FreshnessState
from launch57.router_selection_contract import (
    DEFAULT_CACHE_POLICY,
    DEFAULT_COST_CEILING_UNITS,
    DEFAULT_LATENCY_CLASS,
    DEFAULT_MAX_CANDIDATE_SET,
    DEFAULT_MAX_SELECTED_SET,
    DEFAULT_SYNC_DEEP_BOUNDARY,
    annotate_candidate_profiles,
    apply_candidate_set_limit,
    apply_selected_set_and_cost_limits,
    apply_sync_deep_boundary,
    build_composition_controls,
    composition_control_defaults,
    run_router_selection_contract,
)


def _live_spine():
    return {
        "symbol": "BTC",
        "freshness_state": FreshnessState.LIVE.value,
        "live_eligible": True,
        "presented_as_live": True,
    }


def test_composition_defaults_documented():
    defaults = composition_control_defaults()
    assert defaults["max_candidate_set"] == DEFAULT_MAX_CANDIDATE_SET
    assert defaults["max_selected_set"] == DEFAULT_MAX_SELECTED_SET
    assert defaults["latency_class"] == DEFAULT_LATENCY_CLASS
    assert defaults["cache_policy"] == DEFAULT_CACHE_POLICY
    assert defaults["cost_ceiling_units"] == DEFAULT_COST_CEILING_UNITS
    assert defaults["sync_deep_boundary"] == DEFAULT_SYNC_DEEP_BOUNDARY
    assert defaults["engineering_only_not_measured_slo"] is True
    assert "rationale" in defaults


def test_candidate_set_limit_enforced():
    cands = [{"launch_id": i, "dependence_cluster": "data_spine"} for i in range(1, 20)]
    kept, meta = apply_candidate_set_limit(cands, controls={"max_candidate_set": 5})
    assert len(kept) == 5
    assert meta["truncated"] is True
    assert meta["candidates_after"] == 5


def test_selected_set_limit_enforced():
    selected = [
        {"launch_id": 6, "dependence_cluster": "trust_surface", "cost_units": 1},
        {"launch_id": 21, "dependence_cluster": "data_spine", "cost_units": 1},
        {"launch_id": 22, "dependence_cluster": "data_spine", "cost_units": 1},
        {"launch_id": 39, "dependence_cluster": "launch_39", "cost_units": 1},
    ]
    kept, meta, breached = apply_selected_set_and_cost_limits(
        selected,
        controls={"max_selected_set": 2, "cost_ceiling_units": 99},
        dependence_clusters={"trust_surface": [6], "data_spine": [21, 22], "launch_39": [39]},
    )
    assert len(kept) <= 2
    assert meta["max_selected_set"] == 2
    assert breached is True


def test_cost_ceiling_abstain_on_composite_path():
    out = run_router_selection_contract(
        goal="six_heroes_command_home",
        symbol="BTC",
        spine=_live_spine(),
        oracle={"decision_action": "WAIT"},
        params={"composition_controls": {"cost_ceiling_units": 1, "max_selected_set": 99}},
    )
    block = out["router_selection_contract"]
    assert block["abstain"] is True
    assert block["abstain_reason"] == "composition_controls_exceeded"
    assert block["composition_controls"]["cost_ceiling_units"] == 1


def test_sync_deep_boundary_excludes_deep_modules():
    deep = annotate_candidate_profiles(
        [
            {"launch_id": 34, "dependence_cluster": "explanation"},
            {"launch_id": 6, "dependence_cluster": "trust_surface"},
        ]
    )
    kept, excluded, meta = apply_sync_deep_boundary(deep, controls={"sync_deep_boundary": "sync_only"})
    assert meta["enforced"] is True
    assert any(c["launch_id"] == 34 for c in excluded)
    assert all(c["launch_id"] != 34 for c in kept)


def test_latency_class_and_cache_policy_on_router_output():
    out = run_router_selection_contract(
        goal="six_heroes_command_home",
        symbol="BTC",
        spine=_live_spine(),
        oracle={"decision_action": "WAIT"},
    )
    controls = out["router_selection_contract"]["composition_controls"]
    assert controls["latency_class"] == DEFAULT_LATENCY_CLASS
    assert controls["cache_policy"] == DEFAULT_CACHE_POLICY


def test_degradation_path_abstain_with_explain():
    out = run_router_selection_contract(
        goal="six_heroes_command_home",
        symbol="BTC",
        spine=_live_spine(),
        oracle={"decision_action": "WAIT"},
        params={
            "composition_controls": {
                "max_candidate_set": 1,
                "degradation_path": "abstain_with_explain",
            }
        },
    )
    block = out["router_selection_contract"]
    assert block["abstain"] is True
    assert block.get("abstain_reason") in {
        "composition_controls_exceeded",
        "selection_sufficiency_failed",
    }


@pytest.mark.asyncio
async def test_command_home_includes_composition_controls(monkeypatch):
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
    router = out["six_heroes_command_home"]["router_selection_contract"]
    assert "composition_controls" in router
    assert router["composition_controls"]["max_selected_set"] == DEFAULT_MAX_SELECTED_SET
