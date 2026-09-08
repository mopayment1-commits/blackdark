"""Temporal source-driven engineering — domain handler and closure verification."""

from __future__ import annotations

import json
from pathlib import Path

from bd_platform.temporal_persistent_registries import bootstrap_temporal_registries
from bd_platform.temporal_source_driven_engineering import (
    BUILDABLE_CLASSIFICATIONS,
    DOMAIN_HANDLERS,
    MATURITY_GATED_IDS,
    close_requirement_source_driven,
    load_implementation_index,
    load_matrix_register,
    temporal_binding,
    temporal_source_driven_status,
    verify_buildable_universe,
    verify_requirement,
)
from temporal_leakage_firewall import TemporalLeakageError, assert_no_temporal_leakage


def test_domain_handlers_cover_all_domains() -> None:
    expected = {
        "event_store",
        "pit_leakage",
        "contamination",
        "replay_walk_forward",
        "reproducibility",
        "signal_trace",
        "decision_trace",
        "outcome_factory",
        "evidence_ledger",
        "failure_surprise_abstention",
        "regime",
        "evidence_class",
        "champion_challenger",
        "forward_shadow",
        "calibration_promotion",
        "controlled_learning",
        "cross_cutting",
        "maturity_prerequisite",
    }
    assert set(DOMAIN_HANDLERS) == expected


def test_source_driven_status_bootstraps_registries() -> None:
    bootstrap_temporal_registries()
    status = temporal_source_driven_status()
    assert status["live_promotion"] is False
    assert status["pass_live_claimed"] is False
    assert status["registries"]["canonical_events"]["count"] >= 0


def test_implementation_index_covers_all_matrix_ids() -> None:
    index = load_implementation_index()
    bindings = index.get("bindings", {})
    matrix_ids = {r["canonical_requirement_id"] for r in load_matrix_register()["rows"]}
    assert len(bindings) == len(matrix_ids)
    assert set(bindings) == matrix_ids


def test_verify_buildable_universe_passes() -> None:
    report = verify_buildable_universe()
    assert report["ok"] is True, report.get("failures", [])[:10]
    assert report["verified_ok"] >= 237


def test_maturity_gated_ids_have_local_prerequisites() -> None:
    for uid in MATURITY_GATED_IDS:
        result = verify_requirement(uid)
        assert result["ok"] is True, f"{uid}: {result}"
        assert result.get("closure_state") == "MATURITY_GATED"


def test_event_store_closure_sample() -> None:
    row = next(
        r
        for r in load_matrix_register()["rows"]
        if r.get("classification") in BUILDABLE_CLASSIFICATIONS and "event" in str(r.get("semantic_requirement", "")).lower()
    )
    closure = close_requirement_source_driven(row["canonical_requirement_id"])
    assert closure["closure_state"] == "LOCAL_ENGINEERING_COMPLETE"
    assert closure["implementation_paths"]


def test_pit_firewall_rejects_lookahead_independently() -> None:
    assert_no_temporal_leakage(
        event_time="2026-01-01T00:00:00+00:00",
        evaluation_cutoff="2026-01-02T00:00:00+00:00",
        context="valid_pit",
    )
    try:
        assert_no_temporal_leakage(
            event_time="2026-01-03T00:00:00+00:00",
            evaluation_cutoff="2026-01-02T00:00:00+00:00",
            context="lookahead_probe",
        )
        raise AssertionError("expected TemporalLeakageError")
    except TemporalLeakageError:
        pass


def test_evidence_class_blocks_self_promotion() -> None:
    row = next(
        r
        for r in load_matrix_register()["rows"]
        if r.get("classification") in BUILDABLE_CLASSIFICATIONS
        and "evidence" in str(r.get("semantic_requirement", "")).lower()
    )
    result = verify_requirement(row["canonical_requirement_id"])
    assert result["ok"] is True, result


def test_forward_shadow_prerequisite_no_fabricated_elapsed() -> None:
    row = next(
        r
        for r in load_matrix_register()["rows"]
        if "shadow" in str(r.get("semantic_requirement", "")).lower()
        and r.get("classification") in BUILDABLE_CLASSIFICATIONS
    )
    closure = close_requirement_source_driven(row["canonical_requirement_id"])
    assert closure["closure_state"] == "LOCAL_ENGINEERING_COMPLETE"
    runtime = verify_requirement(row["canonical_requirement_id"]).get("runtime") or {}
    checks = runtime.get("checks") or {}
    assert checks.get("elapsed_evidence") is False or checks.get("shadow_id")


def test_v4_v2_closure_preserved_in_ledger() -> None:
    ledger_path = Path("docs/THREE_SPEC_INCREMENTAL_IMPLEMENTATION_LEDGER.json")
    if not ledger_path.is_file():
        return
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    v4 = [r for r in ledger["requirements"] if r.get("spec") == "v4_v2"]
    remaining = [
        r
        for r in v4
        if r.get("current_state")
        in {"PARTIALLY_BUILT_VALID", "PARTIALLY_IMPLEMENTED", "UNIMPLEMENTED", "UNVERIFIED", "UNWIRED"}
    ]
    assert len(remaining) == 0, [r["requirement_id"] for r in remaining[:5]]
    local = sum(1 for r in v4 if r.get("current_state") == "LOCAL_ENGINEERING_COMPLETE")
    assert local == 644


def test_temporal_binding_enforcement_tiers() -> None:
    buildable = next(r for r in load_matrix_register()["rows"] if r.get("classification") == "BUILDABLE_NOW")
    binding = temporal_binding(buildable["canonical_requirement_id"])
    assert binding.enforcement_tier in {"REJECT", "DOCUMENT_ONLY"}
    assert binding.implementation_intended is True
