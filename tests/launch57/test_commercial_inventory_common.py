"""Unit coverage for launch57.commercial_inventory_common."""

from __future__ import annotations

import launch57.commercial_inventory_common as commercial_inventory_common
from launch57.commercial_inventory_common import (
    acceptance_criteria_status,
    build_audit_baseline,
    build_commercial_capability_inventory,
    build_commercial_readiness,
    build_commercial_value_matrix,
    build_cost_rights_matrix,
    build_machine_readable_inventory_export,
    build_primary_classification_summary,
    build_reconciliation_counters,
    build_tier_variable_inventory,
    detect_unwired_capabilities,
    verify_file03_file04_alignment,
    verify_no_parked_commercial,
    independent_recomputation,
    build_capability_audit_record,
)


def test_build_audit_baseline_fields():
    baseline = build_audit_baseline()
    assert "AUDIT_BASELINE_SHA" in baseline
    assert "AUDIT_BRANCH" in baseline
    assert baseline["AUDIT_MODE"] is not None
    assert isinstance(baseline["WORKTREE_DIRTY"], bool)


def test_reconciliation_counters_launch57_complete():
    counters = build_reconciliation_counters()
    assert counters["LAUNCH57_RECONCILED_COUNT"] == 57
    assert counters["LAUNCH57_INVENTORY_COMPLETE"] is True


def test_primary_classification_summary_valid():
    summary = build_primary_classification_summary()
    assert summary["PRIMARY_CLASSIFICATION_VALID"] is True
    assert summary["EXTERNAL_TOTAL"] + summary["INTERNAL_TOTAL"] == 57


def test_verify_no_parked_commercial():
    parked = verify_no_parked_commercial()
    assert parked["no_parked_as_launch_commercial"] is True
    assert parked["parked_exposed_in_inventory"] == []


def test_file03_file04_alignment():
    alignment = verify_file03_file04_alignment()
    assert alignment["aligned"] is True
    assert alignment["file04_library_scope_matches_inventory"] is True


def test_build_commercial_capability_inventory_length():
    inventory = build_commercial_capability_inventory()
    assert len(inventory) == 57
    assert all(isinstance(row.get("launch_number"), int) for row in inventory)


def test_machine_readable_export_audit_only():
    export = build_machine_readable_inventory_export()
    assert export["inventory_count"] == 57
    assert export["audit_only"] is True
    assert export["pass_live_not_claimed"] is True


def test_tier_variables_not_counted_as_capabilities():
    tiers = build_tier_variable_inventory()
    cap_count = len(build_commercial_capability_inventory())
    assert cap_count == 57
    assert tiers
    assert all(t.get("not_counted_as_capability") for t in tiers)


def test_value_and_cost_matrices_nonempty():
    value = build_commercial_value_matrix()
    cost = build_cost_rights_matrix()
    assert len(value) == 57
    assert len(cost) == 57


def test_detect_unwired_capabilities_structure():
    unwired = detect_unwired_capabilities()
    assert isinstance(unwired, list)


def test_module_import_path_is_production_package():
    assert commercial_inventory_common.__name__ == "launch57.commercial_inventory_common"
    assert commercial_inventory_common.LAUNCH57_EXPECTED_COUNT == 57


def test_independent_recomputation_matches_register():
    recompute = independent_recomputation()
    assert recompute["INDEPENDENT_RECOMPUTATION_MATCH"] is True
    assert recompute["inventory_count"] == 57


def test_build_capability_audit_record_real_register_row():
    item = next(
        row
        for row in commercial_inventory_common._load_register().get("launch57_register", [])
        if row.get("launch_number") == 4
    )
    record = build_capability_audit_record(item)
    assert record["launch_number"] == 4
    assert record["primary_type"] == "EXTERNAL"
    assert record["audit_only"] is True
    assert record["commercial_blockers"] is not None


def test_commercial_use_state_branches_on_synthetic_items():
    pending = commercial_inventory_common._commercial_use_state(
        {"current_engineering_status": "PENDING_VERIFICATION", "actual_consumer_paths": ["/x"]}
    )
    blocked = commercial_inventory_common._commercial_use_state(
        {"current_engineering_status": "BLOCKED_EXTERNAL", "actual_consumer_paths": ["/x"]}
    )
    limited = commercial_inventory_common._commercial_use_state(
        {"current_engineering_status": "PASS_ENGINEERING", "actual_consumer_paths": []}
    )
    not_surfaced = commercial_inventory_common._commercial_use_state(
        {"current_engineering_status": "UNKNOWN", "actual_consumer_paths": []}
    )
    assert pending == "NOT_READY_ENGINEERING"
    assert blocked == "BLOCKED_EXTERNAL"
    assert limited == "READY_WITH_LIMITATION"
    assert not_surfaced == "NOT_SURFACED"


def test_build_commercial_readiness_and_acceptance():
    readiness = build_commercial_readiness()
    assert readiness["LAUNCH57_INVENTORY_COMPLETE"] is True
    assert readiness["PASS_LIVE_NOT_CLAIMED"] is True
    acceptance = acceptance_criteria_status()
    assert acceptance["ac01_inventory_count_57"] is True
    assert acceptance["ac07_no_parked_commercial"] is True
