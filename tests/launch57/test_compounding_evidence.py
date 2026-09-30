"""Launch-57 Compounding Evidence & Track-Record baseline tests."""

from __future__ import annotations

import json
from pathlib import Path

from launch57.compounding_evidence_common import (
    CANONICAL_ASSET_CLASSES,
    INTERNAL_COMPOUNDING_COMPONENTS,
    acceptance_criteria_status,
    attach_compounding_evidence_envelope,
    build_capability_verification_index,
    build_compounding_touchpoint_matrix,
    build_evidence_lineage_index,
    build_live_sim_separation_index,
    record_compounding_signal,
    verify_compounding_scope,
    verify_decision_certificate_linkage,
    verify_live_sim_separation,
    verify_pit_integrity,
)


def test_internal_components_registry():
    from launch57.compounding_evidence_common import build_compounding_component_registry

    registry = build_compounding_component_registry()
    assert len(registry) == len(INTERNAL_COMPOUNDING_COMPONENTS)
    for row in registry:
        assert row["launch_scope"] == "LAUNCH57"


def test_live_sim_separation_blocks_contamination():
    ok = verify_live_sim_separation(evidence_label="LIVE", presented_as_live=True)
    bad = verify_live_sim_separation(
        evidence_label="SIM",
        presented_as_live=True,
        raw_evidence_class="SIMULATED",
    )
    assert ok["live_sim_separated"] is True
    assert bad["sim_cannot_contaminate_live"] is False
    assert bad["fail_closed_on_contamination"] is True


def test_pit_integrity_no_lookahead():
    from launch57.temporal_common import to_rfc3339, utc_now

    now = to_rfc3339(utc_now())
    result = verify_pit_integrity(available_at=now, decision_time=now)
    assert result["pit_integrity_ok"] is True
    assert result["no_lookahead"] is True


def test_compounding_scope_launch57_only():
    in_scope = verify_compounding_scope(4)
    parked = verify_compounding_scope(999)
    assert in_scope["in_launch57_scope"] is True
    assert parked["parked_contamination"] is True


def test_decision_certificate_no_second_authority():
    linkage = verify_decision_certificate_linkage({"decision_state": "ACT"})
    assert linkage["second_certificate_authority"] is False
    assert linkage["linkage_supported"] is True


def test_asset_classes_defined():
    assert "decision_evidence" in CANONICAL_ASSET_CLASSES
    assert "public_accuracy_history" in CANONICAL_ASSET_CLASSES
    assert len(CANONICAL_ASSET_CLASSES) >= 17


def test_evidence_lineage_index():
    index = build_evidence_lineage_index()
    assert any(row["lineage_id"] == "decision_to_public_accuracy" for row in index)


def test_live_sim_separation_index():
    idx = build_live_sim_separation_index()
    assert idx["replay_cannot_become_live"] is True
    assert idx["public_accuracy_live_only"] is True


def test_capability_verification_index():
    index = build_capability_verification_index()
    assert all(row["launch57_only"] for row in index)
    assert any(row["launch_item_id"] == 4 for row in index)


def test_attach_envelope_public_ledger():
    body = {
        "launch_item_id": 4,
        "success": True,
        "public_accuracy_ledger": {"cumulative": {"total": 10}},
        "presented_as_live": True,
        "evidence_class": "PRODUCTION_OBSERVED",
    }
    out = attach_compounding_evidence_envelope(body, launch_item_id=4)
    envelope = out["launch57_compounding_evidence"]
    assert envelope["strategic_asset_not_user_capability"] is True
    assert envelope["live_sim_separation"]["live_sim_separated"] is True
    assert envelope["pass_live_not_claimed"] is True


def test_attach_envelope_sim_contamination_reported():
    body = {
        "launch_item_id": 4,
        "success": True,
        "presented_as_live": True,
        "evidence_class": "SIMULATED",
    }
    out = attach_compounding_evidence_envelope(body, launch_item_id=4)
    envelope = out["launch57_compounding_evidence"]
    assert envelope["live_sim_separation"]["fail_closed_on_contamination"] is True


def test_touchpoint_matrix():
    matrix = build_compounding_touchpoint_matrix()
    by_id = {row["launch_item_id"]: row for row in matrix}
    assert by_id[4]["wired"] is True
    assert by_id[51]["wired"] is True


def test_record_compounding_signal(tmp_path, monkeypatch):
    store = tmp_path / "signals.jsonl"
    monkeypatch.setattr(
        "launch57.compounding_evidence_common._SIGNAL_STORE",
        store,
    )
    row = record_compounding_signal(
        signal_type="decision_evidence_recorded",
        launch_item_id=2,
        asset_class="decision_evidence",
        detail="oracle_act",
    )
    assert row["asset_class"] == "decision_evidence"
    lines = store.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1


def test_acceptance_criteria_engineering_gate():
    acceptance = acceptance_criteria_status()
    assert acceptance["ac01_launch57_assets_only"] is True
    assert acceptance["ac06_live_delayed_sim_separated"] is True
    assert acceptance["ac19_no_legacy_registry_recreated"] is True
    assert acceptance["ac22_no_false_pass_live"] is True
