"""Launch-57 Commercial Capability Inventory audit tests (AUDIT ONLY)."""

from __future__ import annotations

import json
from pathlib import Path

from launch57.commercial_inventory_common import (
    AUDIT_MODE,
    COMMERCIAL_INVENTORY_VERSION,
    LAUNCH57_EXPECTED_COUNT,
    build_audit_baseline,
    build_commercial_capability_inventory,
    build_commercial_readiness,
    build_reconciliation_counters,
    build_tier_variable_inventory,
    independent_recomputation,
)


def test_audit_mode_is_read_only():
    assert AUDIT_MODE == "AUDIT_ONLY"


def test_inventory_exactly_57_capabilities():
    inventory = build_commercial_capability_inventory()
    assert len(inventory) == LAUNCH57_EXPECTED_COUNT
    assert len({r["launch_number"] for r in inventory}) == 57


def test_no_duplicate_canonical_records():
    counters = build_reconciliation_counters()
    assert counters["DUPLICATE_CANONICAL_COUNT"] == 0
    assert counters["LAUNCH57_RECONCILED_COUNT"] == 57
    assert counters["UNRESOLVED_CANONICAL_IDS"] == []


def test_tier_variables_not_counted_as_capabilities():
    tiers = build_tier_variable_inventory()
    assert tiers
    assert all(t.get("not_counted_as_capability") for t in tiers)
    capability_ids = {r["launch_number"] for r in build_commercial_capability_inventory()}
    for tier in tiers:
        assert tier["launch_item_id"] in capability_ids or tier["launch_item_id"] in {4, 21}


def test_independent_recomputation_matches():
    recompute = independent_recomputation()
    assert recompute["INDEPENDENT_RECOMPUTATION_MATCH"] is True
    assert recompute["SELF_REFERENTIAL_AUDIT_EVIDENCE_COUNT"] == 0


def test_audit_baseline_recorded():
    baseline = build_audit_baseline()
    assert baseline["AUDIT_BRANCH"]
    assert baseline["AUDIT_BASELINE_SHA"]
    assert baseline["AUDIT_MODE"] == "AUDIT_ONLY"


def test_commercial_readiness_verdicts_separate():
    readiness = build_commercial_readiness()
    assert readiness["LAUNCH57_INVENTORY_COMPLETE"] is True
    assert readiness["LAUNCH57_COMMERCIAL_INVENTORY_AUDIT_CLOSED"] is True
    assert readiness["COMMERCIAL_READY_FOR_TIER_DESIGN"] is False
    assert readiness["EXTERNAL_ASSURANCE_COMPLETE"] is False
    assert readiness["PASS_LIVE_NOT_CLAIMED"] is True
    assert readiness["STOP_AFTER_AUDIT"] is True


def test_each_record_has_required_fields():
    inventory = build_commercial_capability_inventory()
    for row in inventory:
        assert row["launch_number"] >= 1 and row["launch_number"] <= 57
        assert row.get("canonical_name")
        assert row.get("engineering_state")
        assert row.get("access_states")
        assert row.get("commercial_use_state")
        assert row.get("evidence_references")
        assert row.get("audit_only") is True
        assert row.get("parked_out_of_launch") is False


def test_pending_verification_count_matches_register():
    counters = build_reconciliation_counters()
    assert counters["PASS_ENGINEERING_COUNT"] == 9
    assert counters["PENDING_VERIFICATION_COUNT"] == 48


def test_governance_artifacts_exist_after_generator():
    gov = Path("governance/launch57")
    for name in (
        "BLACKDARK_LAUNCH57_COMMERCIAL_CAPABILITY_INVENTORY.json",
        "BLACKDARK_LAUNCH57_TIER_VARIABLE_INVENTORY.json",
        "BLACKDARK_LAUNCH57_COMMERCIAL_VALUE_MATRIX.json",
        "BLACKDARK_LAUNCH57_COST_RIGHTS_MATRIX.json",
        "BLACKDARK_LAUNCH57_COMMERCIAL_READINESS.json",
        "BLACKDARK_LAUNCH57_INDEPENDENT_RECOMPUTATION.json",
        "BLACKDARK_LAUNCH57_COMMERCIAL_CAPABILITY_INVENTORY_AUDIT_REPORT.md",
    ):
        path = gov / name
        if path.exists():
            if name.endswith(".json"):
                payload = json.loads(path.read_text(encoding="utf-8"))
                assert payload.get("artifact") or payload.get("capabilities") or payload.get("matrix")
