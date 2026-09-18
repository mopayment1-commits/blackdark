"""SPEC_05 — Commercial Capability Inventory adversarial tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from launch57.commercial_capability_inventory_spec_common import (
    DOMAIN,
    build_final_status,
    build_requirements_register,
    build_runtime_truth_table,
    independent_verification,
)


def test_requirements_register_nonempty():
    reqs = build_requirements_register()
    assert len(reqs) >= 20
    assert all(r["mandatory"] for r in reqs)


def test_runtime_truth_all_yes():
    truth = build_runtime_truth_table()
    nos = [r for r in truth if r["status"] != "YES"]
    assert not nos, nos


def test_inventory_exactly_57():
    from launch57.commercial_inventory_common import build_reconciliation_counters

    counters = build_reconciliation_counters()
    assert counters["LAUNCH57_RECONCILED_COUNT"] == 57
    assert counters["LAUNCH57_INVENTORY_COMPLETE"] is True


def test_primary_type_external_internal_split():
    from launch57.commercial_inventory_common import build_primary_classification_summary

    summary = build_primary_classification_summary()
    assert summary["PRIMARY_CLASSIFICATION_VALID"] is True
    assert summary["EXTERNAL_TOTAL"] + summary["INTERNAL_TOTAL"] == 57
    assert summary["INTERNAL_TOTAL"] == 3
    assert summary["CLASSIFICATION_GRANULARITY_WARNING"] is False


def test_no_parked_as_launch_commercial():
    from launch57.commercial_inventory_common import verify_no_parked_commercial

    parked = verify_no_parked_commercial()
    assert parked["no_parked_as_launch_commercial"] is True
    assert parked["parked_exposed_in_inventory"] == []


def test_file03_file04_alignment():
    from launch57.commercial_inventory_common import verify_file03_file04_alignment

    alignment = verify_file03_file04_alignment()
    assert alignment["aligned"] is True
    assert alignment["file03_billing_touchpoints_subset_launch57"] is True
    assert alignment["file04_library_scope_matches_inventory"] is True


def test_machine_readable_export_valid():
    from launch57.commercial_inventory_common import build_machine_readable_inventory_export

    export = build_machine_readable_inventory_export()
    assert export["inventory_count"] == 57
    assert export["inventory_count_valid"] is True
    assert export["audit_only"] is True
    assert export["pass_live_not_claimed"] is True
    assert len(export["capabilities"]) == 57
    assert export["primary_classification"]["PRIMARY_CLASSIFICATION_VALID"] is True


def test_tier_variables_not_in_capability_count():
    from launch57.commercial_inventory_common import (
        build_commercial_capability_inventory,
        build_tier_variable_inventory,
    )

    tiers = build_tier_variable_inventory()
    cap_count = len(build_commercial_capability_inventory())
    assert cap_count == 57
    assert all(t.get("not_counted_as_capability") for t in tiers)


def test_external_internal_sample_records():
    from launch57.commercial_inventory_common import build_commercial_capability_inventory

    inv = {r["launch_number"]: r for r in build_commercial_capability_inventory()}
    assert inv[4]["primary_type"] == "EXTERNAL"
    assert inv[4]["entity_commercial_class"] == "CAPABILITY"
    assert inv[6]["primary_type"] == "INTERNAL"
    assert inv[6]["entity_commercial_class"] == "INTERNAL_ENABLER"
    assert inv[52]["primary_type"] == "EXTERNAL"


def test_independent_recomputation():
    from launch57.commercial_inventory_common import independent_recomputation

    recompute = independent_recomputation()
    assert recompute["INDEPENDENT_RECOMPUTATION_MATCH"] is True


def test_acceptance_criteria_all_pass():
    from launch57.commercial_inventory_common import acceptance_criteria_status

    ac = acceptance_criteria_status()
    assert all(ac.values())


def test_commercial_ready_for_tier_design_honest_false():
    from launch57.commercial_inventory_common import build_commercial_readiness

    readiness = build_commercial_readiness()
    assert readiness["LAUNCH57_COMMERCIAL_INVENTORY_AUDIT_CLOSED"] is True
    assert readiness["COMMERCIAL_READY_FOR_TIER_DESIGN"] is False
    assert readiness["PASS_LIVE_NOT_CLAIMED"] is True


def test_independent_verification_passes():
    iv = independent_verification()
    assert iv["INDEPENDENT_VERIFICATION_PASS"] is True


def test_final_status_closed_local():
    status = build_final_status(skip_tests=True)
    assert status["closure_status"] == "CLOSED_LOCAL"
    assert status["PASS_ENGINEERING"] is True
    assert status["LOCAL_ENGINEERING_GAP_COUNT"] == 0
    assert status["inventory_count_valid"] is True
    assert status["launch57_only_ok"] is True
    assert status["PASS_LIVE"] is False


def test_spec05_artifact_paths_exist():
    gov = Path("governance/launch57/SPEC_05_COMMERCIAL_CAPABILITY_INVENTORY")
    for name in (
        "REQUIREMENTS_REGISTER.json",
        "RUNTIME_TRUTH_TABLE.md",
        "LOCAL_CLOSURE_REPORT.md",
        "INDEPENDENT_VERIFICATION.json",
        "FINAL_STATUS.json",
    ):
        path = gov / name
        assert path.exists(), f"missing {path}"
        if name.endswith(".json") and name == "FINAL_STATUS.json":
            payload = json.loads(path.read_text(encoding="utf-8"))
            assert payload.get("domain") == DOMAIN
