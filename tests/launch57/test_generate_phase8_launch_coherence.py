"""Unit coverage for governance.launch57.generate_phase8_launch_coherence."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

import governance.launch57.generate_phase8_launch_coherence as gen

ROOT = Path(__file__).resolve().parents[2]


def test_merge_roles_branches():
    assert gen._merge_roles("NOT_APPLICABLE", "GATE") == "GATE"
    assert gen._merge_roles("GATE", "NOT_APPLICABLE") == "GATE"
    assert gen._merge_roles("PRIMARY_FEED", "SECONDARY_FEED") == "PRIMARY_FEED"
    assert gen._merge_roles("SECONDARY_FEED", "PRIMARY_FEED") == "PRIMARY_FEED"


def test_engineering_status_and_phase_closure():
    assert gen._engineering_status(33) == "PASS_ENGINEERING_WITH_BLOCKED_EXTERNAL"
    assert gen._engineering_status(1) == "PASS_ENGINEERING"
    assert gen._engineering_status(999) == "PARKED_OUT_OF_LAUNCH"
    assert gen._phase_closure_for(1) == "phase7"
    assert gen._phase_closure_for(999) is None


def test_handler_for_item_resolves_build_chain():
    item = {
        "phase1_batch1_build": {},
        "phase3_batch1_build": {"handler_module": "launch57.decision_batch1"},
    }
    assert gen._handler_for_item(item) == "launch57.decision_batch1"
    assert gen._handler_for_item({"canonical_implementation": ["launch57.foo"]}) == "launch57.foo"
    assert gen._handler_for_item({}) is None


def test_build_hero_matrix_and_system_graph_from_register():
    register = json.loads(gen.REGISTER_PATH.read_text(encoding="utf-8"))
    heroes = [register["six_heroes"][k] for k in sorted(register["six_heroes"]) if k.startswith("HERO_")]
    cap_index = gen._load_cap_matrix_index()
    matrix = gen._build_hero_matrix(register, cap_index, heroes)
    graph = gen._build_system_graph(register, matrix)
    assert matrix["launch_item_count"] == 57
    assert matrix["artifact"] == "LAUNCH57_SIX_HERO_MATRIX"
    assert graph["artifact"] == "LAUNCH57_CAPABILITY_SYSTEM_GRAPH"
    assert graph["zero_orphan_material_in_launch_scope"] is True
    assert any(row.get("parked_hero_dependency") for row in matrix["rows"]) is False


def test_prelive_checklist_closed_and_gap_paths():
    register = json.loads(gen.REGISTER_PATH.read_text(encoding="utf-8"))
    heroes = [register["six_heroes"][k] for k in sorted(register["six_heroes"]) if k.startswith("HERO_")]
    cap_index = gen._load_cap_matrix_index()
    hero_matrix = gen._build_hero_matrix(register, cap_index, heroes)
    graph = gen._build_system_graph(register, hero_matrix)
    e2e = {"all_pass": True, "passed": 13, "total": 13}
    isolation = gen._isolation_proof(register)
    verdict, gaps = gen._prelive_checklist(hero_matrix, graph, e2e, isolation)
    assert verdict == "LAUNCH57_PRE_LIVE_CLOSED=YES"
    assert gaps == []

    bad_matrix = dict(hero_matrix, launch_item_count=56, zero_parked_hero_dependencies=False)
    bad_graph = dict(graph, zero_orphan_material_in_launch_scope=False, orphan_material_launch_nodes=["LAUNCH-99"])
    bad_e2e = {"all_pass": False, "passed": 0, "total": 13}
    bad_iso = dict(isolation, isolation_pass=False)
    verdict2, gaps2 = gen._prelive_checklist(bad_matrix, bad_graph, bad_e2e, bad_iso)
    assert verdict2 == "PRE_LIVE_NOT_CLOSED"
    assert "hero_matrix_count=56 expected 57" in gaps2
    assert "parked_hero_dependency_detected" in gaps2
    assert any("orphan_nodes=" in g for g in gaps2)
    assert any("e2e_passed=" in g for g in gaps2)
    assert "launch_surface_isolation_failed" in gaps2


def test_prelive_checklist_engineering_status_gap(monkeypatch):
    register = json.loads(gen.REGISTER_PATH.read_text(encoding="utf-8"))
    heroes = [register["six_heroes"][k] for k in sorted(register["six_heroes"]) if k.startswith("HERO_")]
    cap_index = gen._load_cap_matrix_index()
    hero_matrix = gen._build_hero_matrix(register, cap_index, heroes)
    graph = gen._build_system_graph(register, hero_matrix)
    e2e = {"all_pass": True, "passed": 13, "total": 13}
    isolation = gen._isolation_proof(register)

    real_status = gen._engineering_status

    def bad_status(ln: int) -> str:
        if ln == 5:
            return "PARKED_OUT_OF_LAUNCH"
        return real_status(ln)

    monkeypatch.setattr(gen, "_engineering_status", bad_status)
    verdict, gaps = gen._prelive_checklist(hero_matrix, graph, e2e, isolation)
    assert verdict == "PRE_LIVE_NOT_CLOSED"
    assert any(g.startswith("launch_5_status=") for g in gaps)


def test_run_tests_subprocess(monkeypatch):
    calls: list[list[str]] = []

    def fake_run(cmd, cwd, capture_output, text, env):
        calls.append(cmd)
        return MagicMock(returncode=0, stdout="1 passed\n", stderr="")

    monkeypatch.setattr(gen.subprocess, "run", fake_run)
    out = gen._run_tests()
    assert out["passed"] is True
    assert out["exit_code"] == 0
    assert "pytest" in calls[0]

    def fail_run(cmd, cwd, capture_output, text, env):
        return MagicMock(returncode=1, stdout="", stderr="boom")

    monkeypatch.setattr(gen.subprocess, "run", fail_run)
    out_fail = gen._run_tests()
    assert out_fail["passed"] is False
    assert out_fail["exit_code"] == 1


@pytest.mark.asyncio
async def test_run_e2e_records_journey_exception(monkeypatch):
    import launch57.trust_batch2 as t2

    def boom(**_k):
        raise ValueError("guest trust injected failure")

    monkeypatch.setattr(t2, "guest_trust_surface", boom)
    out = await gen._run_e2e_journeys()
    guest = next(j for j in out["journeys"] if j["journey"] == "guest_trust_surface")
    assert guest["status"] == "ERROR"
    assert "injected failure" in guest["error"]


def test_hero_matrix_parked_row_sets_dependency_flag():
    register = json.loads(gen.REGISTER_PATH.read_text(encoding="utf-8"))
    register = dict(register)
    register["launch57_register"] = list(register["launch57_register"]) + [
        {
            "launch_number": 999,
            "launch_name": "synthetic_parked",
            "matched_capability_ids": [],
            "hero_mapping_status": "PARKED",
        }
    ]
    heroes = [register["six_heroes"][k] for k in sorted(register["six_heroes"]) if k.startswith("HERO_")]
    matrix = gen._build_hero_matrix(register, gen._load_cap_matrix_index(), heroes)
    parked_row = next(r for r in matrix["rows"] if r["launch_number"] == 999)
    assert parked_row["parked_hero_dependency"] is True
    assert matrix["zero_parked_hero_dependencies"] is False


def test_generate_skip_tests_returns_payload(monkeypatch):
    monkeypatch.setattr(gen, "write_artifact_json", lambda path, data: None)
    monkeypatch.setattr(gen, "write_artifact_lines", lambda path, lines: None)

    async def mini_e2e():
        return {"all_pass": True, "passed": 13, "total": 13, "journeys": []}

    monkeypatch.setattr(gen, "_run_e2e_journeys", mini_e2e)
    payload = gen.generate(skip_tests=True)
    assert payload["verdict"] == "LAUNCH57_PRE_LIVE_CLOSED=YES"
    assert payload["tests"]["skipped"] is True
    assert "hero_matrix" in payload and "graph" in payload


@pytest.mark.asyncio
async def test_main_without_return_payload(monkeypatch):
    captured_lines: list[list[str]] = []
    monkeypatch.setattr(gen, "write_artifact_json", lambda path, data: None)
    monkeypatch.setattr(
        gen,
        "write_artifact_lines",
        lambda path, lines: captured_lines.append(list(lines)),
    )

    async def failing_e2e():
        return {"all_pass": False, "passed": 0, "total": 13, "journeys": []}

    monkeypatch.setattr(gen, "_run_e2e_journeys", failing_e2e)
    result = await gen.main(return_payload=False, skip_tests=True)
    assert result is None
    prelive = next(lines for lines in captured_lines if any("Pre-Live Checklist" in ln for ln in lines))
    assert any(ln.startswith("## Gaps") for ln in prelive)


def test_git_sha_nonempty():
    sha = gen._git_sha()
    assert isinstance(sha, str) and len(sha) >= 7
