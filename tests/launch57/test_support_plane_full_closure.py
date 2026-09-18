"""Launch-57 Support Plane — full engineering closure verification."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]


def test_cross_path_router_on_trust_surface(monkeypatch):
    from failure.freshness import FreshnessState
    from dashboard import app

    async def fake_spine(symbol, params=None):
        return {
            "symbol": symbol,
            "freshness_state": FreshnessState.LIVE.value,
            "live_eligible": True,
            "presented_as_live": True,
            "price": 1.0,
            "change_24h": 0.0,
            "data_spine": {},
        }

    async def fake_oracle(**kwargs):
        return {
            "decision_action": "WAIT",
            "single_sentence_oracle": {"action": "WAIT", "sentence": "WAIT"},
            "evidence_class": "SHADOW_LIVE_FORWARD",
        }

    monkeypatch.setattr("launch57.edge_ui_batch2.load_decision_spine", fake_spine)
    monkeypatch.setattr("launch57.edge_ui_batch2.single_sentence_oracle", fake_oracle)

    client = TestClient(app)
    body = client.get("/api/launch57/command-home", params={"symbol": "BTC"}).json()
    router = body.get("router_selection_contract") or (body.get("six_heroes_command_home") or {}).get(
        "router_selection_contract"
    )
    assert router
    assert router.get("pipeline_steps")


def test_trust_batch_consumer_gets_l2_l5_and_router():
    from launch57.trust_adaptive_common import attach_adaptive_disclosure, build_level1_decision_disclosure

    body = {
        "launch_item_id": 5,
        "surface": "net_edge_truth_score",
        "symbol": "BTC",
        "success": True,
        "freshness_state": "LIVE",
        "live_eligible": True,
    }
    level1 = build_level1_decision_disclosure(
        body,
        launch_item_id=5,
        surface="net_edge_truth_score",
        answer_state="NET_EDGE_EVALUATED",
    )
    out = attach_adaptive_disclosure(body, level1)
    disc = out.get("adaptive_disclosure") or {}
    for layer in ("level_1", "level_2", "level_3", "level_4", "level_5"):
        assert layer in disc
    assert out.get("router_selection_contract")
    assert out.get("launch57_accessibility")


def test_router_records_measured_latency():
    from launch57.router_selection_contract import run_router_selection_contract

    out = run_router_selection_contract(
        goal="net_edge_truth_score",
        symbol="BTC",
        spine={"symbol": "BTC", "freshness_state": "LIVE", "live_eligible": True},
        oracle={"decision_action": "WAIT"},
    )
    block = out.get("router_selection_contract") or {}
    trace = block.get("composition_trace") or {}
    assert trace.get("latency_measurement", {}).get("hook") == "router_pipeline_latency_ms"


def test_data_spine_skips_router():
    from launch57.support_plane_envelope import attach_router_if_material

    body = {"launch_item_id": 21, "surface": "spot_metrics", "symbol": "BTC"}
    out = attach_router_if_material(body, launch_item_id=21, surface="spot_metrics")
    assert "router_selection_contract" not in out


def test_human_validation_engineering_harness():
    reg = json.loads(
        (ROOT / "governance/launch57/SUPPORT_PLANE_HUMAN_VALIDATION_REGISTER.json").read_text(encoding="utf-8")
    )
    evidence = ROOT / "governance/launch57/SUPPORT_PLANE_HUMAN_VALIDATION_EVIDENCE.json"
    assert evidence.exists()
    ev = json.loads(evidence.read_text(encoding="utf-8"))
    assert ev.get("study_status") == "ENGINEERING_PROXY_COMPLETE"
    for dim in reg.get("required_dimensions", {}):
        assert dim in (ev.get("dimension_results") or {})


def test_accessibility_evidence_chain():
    path = ROOT / "governance/launch57/SUPPORT_PLANE_ACCESSIBILITY_EVIDENCE.json"
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data.get("standard") == "WCAG 2.2 AA"
    assert data.get("engineering_verification_complete") is True
