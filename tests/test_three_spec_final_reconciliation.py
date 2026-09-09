"""Three-spec final cross-spec reconciliation tests."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.three_spec_final_reconciliation import (
    CANONICAL_OWNERS,
    STORAGE_OWNERS,
    build_cross_spec_graph,
    final_arithmetic,
    load_json,
    revalidate_gated_items,
    scan_cross_spec_duplicates,
    verify_canonical_ownership,
    verify_decision_trust_confidence,
    verify_router_capability,
    verify_storage_ssot,
    verify_temporal_consistency,
    verify_three_spec_baseline,
)

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "docs" / "THREE_SPEC_INCREMENTAL_IMPLEMENTATION_LEDGER.json"
FREEZE = ROOT / "docs" / "THREE_SPEC_FINAL_RECONCILIATION_FREEZE.json"
GRAPH = ROOT / "docs" / "THREE_SPEC_CROSS_SPEC_REQUIREMENT_GRAPH.json"


def test_baseline_reconciled() -> None:
    ledger = load_json(LEDGER)
    baseline = verify_three_spec_baseline(ledger)
    assert baseline["THREE_SPEC_BASELINE_RECONCILED"] is True, baseline.get("THREE_SPEC_UNEXPLAINED_BASELINE_DELTAS")
    assert baseline["V4_V2_REMAINING_LOCAL_REQUIREMENTS"] == 0
    assert baseline["TEMPORAL_REMAINING_LOCAL_REQUIREMENTS"] == 0
    assert baseline["ADAPTIVE_REMAINING_LOCAL_REQUIREMENTS"] == 0


def test_cross_spec_graph_complete() -> None:
    ledger = load_json(LEDGER)
    graph = build_cross_spec_graph(ledger)
    assert graph["node_count"] == 2533
    assert graph["CROSS_SPEC_REQUIREMENT_GRAPH_COMPLETE"] is True


def test_duplicate_scan_no_unresolved() -> None:
    ledger = load_json(LEDGER)
    scan = scan_cross_spec_duplicates(ledger)
    assert scan["FINAL_CROSS_SPEC_DUPLICATE_SCAN_COMPLETE"] is True
    assert scan["UNRESOLVED_CROSS_SPEC_DUPLICATES"] == []


def test_canonical_ownership_defined() -> None:
    result = verify_canonical_ownership()
    assert result["CANONICAL_OWNER_DEFINED_FOR_ALL_SHARED_CONCERNS"] is True
    assert result["CANONICAL_OWNER_CONFLICTS"] == []
    assert len(CANONICAL_OWNERS) >= 20


def test_storage_ssot_no_parallel_truth() -> None:
    result = verify_storage_ssot()
    assert result["PARALLEL_SSOT_SYSTEMS"] == []
    assert result["AMBIGUOUS_SOURCE_OF_TRUTH"] == []
    assert len(STORAGE_OWNERS) >= 10


def test_temporal_consistency_guards() -> None:
    result = verify_temporal_consistency()
    assert result["INVALID_EVIDENCE_CLASS_PROMOTION_PATHS"] == []


def test_decision_trust_no_fake_confidence() -> None:
    result = verify_decision_trust_confidence()
    assert result["MISLEADING_USER_DECISION_SURFACES"] == []


def test_router_capability_bindings() -> None:
    result = verify_router_capability()
    assert result["ROUTER_TO_CAPABILITY_BINDINGS_VALID"] is True
    assert result["ROUTER_ENTITLEMENT_BYPASSES"] == []


def test_gated_items_have_no_prerequisite_gaps() -> None:
    ledger = load_json(LEDGER)
    gated = revalidate_gated_items(ledger)
    assert gated["GATED_ITEMS_WITH_LOCAL_PREREQUISITE_GAPS"] == []


def test_final_arithmetic_consistent() -> None:
    ledger = load_json(LEDGER)
    arith = final_arithmetic(ledger)
    assert arith["COMBINED_THREE_SPEC_ARITHMETIC_CONSISTENT"] is True
    assert arith["combined_total"] == 2533
    assert arith["THREE_SPEC_PARTIALLY_IMPLEMENTED_LOCAL"] == 0


def test_freeze_artifact_when_present() -> None:
    if not FREEZE.is_file():
        return
    data = json.loads(FREEZE.read_text(encoding="utf-8"))
    assert data.get("THREE_SPEC_FINAL_LOCAL_COMPLETION") is True
    assert data.get("PASS_ENGINEERING") is True


def test_verify_universe_buildable() -> None:
    from scripts.three_spec_final_reconciliation import verify_universe_buildable

    result = verify_universe_buildable()
    assert result["ok"] is True, result.get("failures", [])[:5]


def test_second_source_pass_flags() -> None:
    for name in ("V4_V2_FULL_SOURCE_UNIVERSE.json", "TEMPORAL_FULL_SOURCE_UNIVERSE.json", "ADAPTIVE_FULL_SOURCE_UNIVERSE.json"):
        data = json.loads((ROOT / "docs" / name).read_text(encoding="utf-8"))
        assert data.get("source_item_count", 0) > 0


def test_all_freeze_artifacts_report_completion() -> None:
    for name, key in (
        ("V4_V2_SOURCE_DRIVEN_FINAL_FREEZE.json", "V4_V2_REMAINING_LOCAL_REQUIREMENTS"),
        ("TEMPORAL_SOURCE_DRIVEN_FINAL_FREEZE.json", "TEMPORAL_REMAINING_LOCAL_REQUIREMENTS"),
        ("ADAPTIVE_SOURCE_DRIVEN_FINAL_FREEZE.json", "ADAPTIVE_REMAINING_LOCAL_REQUIREMENTS"),
    ):
        data = json.loads((ROOT / "docs" / name).read_text(encoding="utf-8"))
        arith = data.get("arithmetic") or {}
        assert arith.get(key, 1) == 0


def test_graph_artifact_when_present() -> None:
    if not GRAPH.is_file():
        return
    data = json.loads(GRAPH.read_text(encoding="utf-8"))
    assert data.get("CROSS_SPEC_REQUIREMENT_GRAPH_COMPLETE") is True
