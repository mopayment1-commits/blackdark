"""Launch-57 Phase 8 — launch coherence (matrix, graph, E2E, isolation, pre-live)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from governance.launch57.generate_phase8_launch_coherence import (
    BLOCKED_EXTERNAL_ITEMS,
    LAUNCH57_IDS,
    PRESERVED_PHASE_CLOSURE,
    generate,
)

ROOT = Path(__file__).resolve().parents[2]
GOV = ROOT / "governance" / "launch57"


@pytest.fixture(scope="module")
def phase8_artifacts():
    generate(skip_tests=True)
    return {
        "matrix": json.loads((GOV / "LAUNCH57_SIX_HERO_MATRIX.json").read_text(encoding="utf-8")),
        "graph": json.loads((GOV / "LAUNCH57_CAPABILITY_SYSTEM_GRAPH.json").read_text(encoding="utf-8")),
        "e2e": json.loads((GOV / "PHASE8_E2E_JOURNEYS.json").read_text(encoding="utf-8")),
        "isolation": json.loads((GOV / "PHASE8_LAUNCH_ISOLATION_EVIDENCE.json").read_text(encoding="utf-8")),
        "evidence": json.loads((GOV / "PHASE8_LAUNCH_COHERENCE_EVIDENCE.json").read_text(encoding="utf-8")),
        "checklist": (GOV / "PHASE8_PRE_LIVE_CHECKLIST.md").read_text(encoding="utf-8"),
    }


def test_six_hero_names_from_register(phase8_artifacts):
    reg = json.loads((GOV / "LAUNCH57_REGISTER.json").read_text(encoding="utf-8"))
    heroes = reg["six_heroes"]
    hero_names = [heroes[k] for k in sorted(heroes) if k.startswith("HERO_")]
    assert len(hero_names) == 6
    assert phase8_artifacts["matrix"]["canonical_product_heroes"] == hero_names


def test_matrix_complete_no_parked_dependency(phase8_artifacts):
    matrix = phase8_artifacts["matrix"]
    assert matrix["launch_item_count"] == 57
    assert matrix["zero_parked_hero_dependencies"] is True
    for row in matrix["rows"]:
        assert len(row["hero_matrix"]) == 6
        assert row.get("readiness_state")
        assert "runtime_handler" in row
        for role in row["hero_matrix"].values():
            assert role in {
                "PRIMARY_FEED",
                "SECONDARY_FEED",
                "CONTEXT",
                "CONFIDENCE_MODIFIER",
                "GATE",
                "VETO",
                "RISK_CAP",
                "DATA_QUALITY_GATE",
                "EXPLANATION_ONLY",
                "NOT_APPLICABLE",
            }


def test_matrix_launch1_has_phase7_adaptive_evidence(phase8_artifacts):
    row = next(r for r in phase8_artifacts["matrix"]["rows"] if r["launch_number"] == 1)
    assert row["adaptive_batch"] == "PHASE7_ADAPTIVE"
    assert row["runtime_handler"] == "launch57.edge_ui_batch2"
    assert row["readiness_state"] == "PASS_ENGINEERING"


def test_system_graph_no_orphans(phase8_artifacts):
    graph = phase8_artifacts["graph"]
    assert graph["zero_orphan_material_in_launch_scope"] is True
    assert graph["orphan_material_launch_nodes"] == []


def test_system_graph_edge_typing_policy(phase8_artifacts):
    policy = phase8_artifacts["graph"]["edge_typing_policy"]
    assert policy["causes_requires_independent_justification"] is True
    assert policy["no_untyped_causal_implication"] is True
    assert policy["documented_causes_edges"] == []


def test_e2e_journeys_pass(phase8_artifacts):
    e2e = phase8_artifacts["e2e"]
    assert e2e["all_pass"] is True
    assert e2e["total"] >= 13
    for journey in e2e["journeys"]:
        assert journey["status"] == "PASS"
    stale = next(j for j in e2e["journeys"] if j["journey"] == "stale_blocks_presented_as_live")
    assert stale["presented_as_live"] is False
    required = {
        "data_spine_trust_decision_command_home",
        "net_edge_to_spot_perp",
        "no_parked_home_reachability",
        "platform_grounding_36",
        "point_in_time_truth_39",
        "exchange_risk_only_57",
        "launch57_only_routing",
    }
    names = {j["journey"] for j in e2e["journeys"]}
    assert required.issubset(names)


def test_launch_surface_isolation(phase8_artifacts):
    iso = phase8_artifacts["isolation"]
    assert iso["home_ids_outside_scope"] == []
    assert iso["library_ids_outside_scope"] == []
    assert iso["parked_out_of_launch_not_in_home"] is True
    assert iso["isolation_pass"] is True


def test_pre_live_closed_without_pass_live(phase8_artifacts):
    ev = phase8_artifacts["evidence"]
    assert ev["pre_live_verdict"] == "LAUNCH57_PRE_LIVE_CLOSED=YES"
    assert ev["pass_live_granted"] is False
    assert ev["entry_gate"]["PHASE7_INDEPENDENT_VERDICT"] == "PASS_ENGINEERING"
    assert ev["confirmations"]["PHASE8_IMPLEMENTATION_STATUS"] == "PENDING_VERIFICATION"
    assert "NO PASS_LIVE" in phase8_artifacts["checklist"]


def test_blocked_external_documented(phase8_artifacts):
    blocked = phase8_artifacts["evidence"]["blocked_external"]
    assert blocked.get("33") or blocked.get(33)
    assert blocked.get("38") or blocked.get(38)
    assert {int(k): v for k, v in blocked.items()} == BLOCKED_EXTERNAL_ITEMS


def test_preserved_phase_closure_map():
    built = set()
    for phase in PRESERVED_PHASE_CLOSURE.values():
        built.update(phase["items"])
    assert built == set(LAUNCH57_IDS)
