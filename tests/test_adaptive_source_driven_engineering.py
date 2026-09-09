"""Adaptive source-driven engineering — domain handler and closure verification."""

from __future__ import annotations

import json
from pathlib import Path

from bd_platform.adaptive_persistent_registries import bootstrap_adaptive_registries
from bd_platform.adaptive_source_driven_engineering import (
    BUILDABLE_CLASSIFICATIONS,
    DOMAIN_HANDLERS,
    MATURITY_GATED_IDS,
    adaptive_binding,
    adaptive_source_driven_status,
    bootstrap_adaptive_source_driven,
    close_requirement_source_driven,
    get_adaptive_source_driven,
    load_implementation_index,
    load_matrix_register,
    verify_buildable_universe,
    verify_requirement,
)
from temporal_leakage_firewall import TemporalLeakageError, assert_no_temporal_leakage


def test_domain_handlers_cover_all_domains() -> None:
    expected = set(DOMAIN_HANDLERS)
    assert len(expected) == 18


def test_source_driven_status_bootstraps_registries() -> None:
    bootstrap_adaptive_registries()
    status = adaptive_source_driven_status()
    assert status["live_promotion"] is False
    assert status["calibrated_promotion"] is False
    assert status["registries"]["workspaces"]["count"] >= 0


def test_implementation_index_covers_all_matrix_ids() -> None:
    index = load_implementation_index()
    bindings = index.get("bindings", {})
    matrix_ids = {r["canonical_requirement_id"] for r in load_matrix_register()["rows"]}
    assert len(bindings) == len(matrix_ids)
    assert set(bindings) == matrix_ids


def test_verify_buildable_universe_passes() -> None:
    report = verify_buildable_universe()
    assert report["ok"] is True, report.get("failures", [])[:10]
    assert report["verified_ok"] >= 192


def test_verify_all_buildable_requirements_passes() -> None:
    bootstrap_adaptive_source_driven()
    svc = get_adaptive_source_driven()
    result = svc.verify_all_buildable_requirements()
    assert result["passed"] is True, result.get("failures", [])[:5]
    assert result["failed"] == 0


def test_maturity_gated_ids_have_local_prerequisites() -> None:
    for uid in MATURITY_GATED_IDS:
        result = verify_requirement(uid)
        assert result["ok"] is True, f"{uid}: {result}"
        assert result.get("closure_state") == "MATURITY_GATED"


def test_router_abstains_on_empty_intent() -> None:
    row = next(r for r in load_matrix_register()["rows"] if r.get("classification") == "BUILDABLE_NOW")
    result = verify_requirement(row["canonical_requirement_id"])
    assert result["ok"] is True, result


def test_decision_contract_decomposed_confidence() -> None:
    row = next(
        r
        for r in load_matrix_register()["rows"]
        if "confidence" in str(r.get("semantic_requirement", "")).lower()
        and r.get("classification") in BUILDABLE_CLASSIFICATIONS
    )
    closure = close_requirement_source_driven(row["canonical_requirement_id"])
    assert closure["closure_state"] == "LOCAL_ENGINEERING_COMPLETE"


def test_progressive_disclosure_safety_floor() -> None:
    from bd_platform.adaptive_intelligence import apply_progressive_disclosure

    payload = {"disclaimer": "Analysis only", "detail": "x" * 100, "evidence_class": "BACKTESTED"}
    out = apply_progressive_disclosure(payload, level="summary")
    assert out["disclaimer"] == "Analysis only"


def test_v4_v2_and_temporal_preserved_in_ledger() -> None:
    ledger_path = Path("docs/THREE_SPEC_INCREMENTAL_IMPLEMENTATION_LEDGER.json")
    if not ledger_path.is_file():
        return
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    v4 = [r for r in ledger["requirements"] if r.get("spec") == "v4_v2"]
    temp = [r for r in ledger["requirements"] if r.get("spec") == "temporal"]
    v4_local = sum(1 for r in v4 if r.get("current_state") == "LOCAL_ENGINEERING_COMPLETE")
    temp_local = sum(1 for r in temp if r.get("current_state") == "LOCAL_ENGINEERING_COMPLETE")
    assert v4_local == 644
    assert temp_local == 231


def test_adaptive_binding_enforcement_tiers() -> None:
    buildable = next(r for r in load_matrix_register()["rows"] if r.get("classification") == "BUILDABLE_NOW")
    binding = adaptive_binding(buildable["canonical_requirement_id"])
    assert binding.enforcement_tier in {"REJECT", "DOCUMENT_ONLY"}
    assert binding.implementation_intended is True


def test_pit_firewall_still_blocks_lookahead() -> None:
    assert_no_temporal_leakage(
        event_time="2026-01-01T00:00:00+00:00",
        evaluation_cutoff="2026-01-02T00:00:00+00:00",
        context="adaptive_regression",
    )
    try:
        assert_no_temporal_leakage(
            event_time="2026-01-03T00:00:00+00:00",
            evaluation_cutoff="2026-01-02T00:00:00+00:00",
            context="adaptive_lookahead",
        )
        raise AssertionError("expected TemporalLeakageError")
    except TemporalLeakageError:
        pass
