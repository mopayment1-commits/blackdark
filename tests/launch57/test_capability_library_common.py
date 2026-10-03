"""Unit coverage for launch57.capability_library_common."""

from __future__ import annotations

from launch57.capability_library_common import (
    acceptance_criteria_status,
    attach_capability_library_envelope,
    build_library_component_registry,
    compare_capabilities,
    load_canonical_library_entries,
    project_library_detail,
    project_library_record,
    project_library_search_row,
    resolve_library_visibility,
    search_library,
    verify_library_scope,
    verify_no_duplicate_ids,
)


def test_resolve_library_visibility_anonymous_free():
    vis = resolve_library_visibility({"user_key": "anonymous"})
    assert vis["anonymous"] is True
    assert vis["paid_detail"] is False
    assert vis["public_safe_only"] is True


def test_project_library_record_strips_paid_fields():
    record = {
        "launch_number": 4,
        "handler_module": "launch57.trust_batch1",
        "canonical_name": "Public Accuracy",
    }
    public = project_library_record(record, {"paid_detail": False})
    assert "handler_module" not in public
    assert public["public_safe_projection"] is True
    paid = project_library_record(record, {"paid_detail": True})
    assert paid["handler_module"] == "launch57.trust_batch1"
    assert paid["public_safe_projection"] is False


def test_project_library_search_row_never_leaks_handler_without_paid():
    row = project_library_search_row(
        {"launch_number": 5, "canonical_name": "Net Edge", "handler_module": "secret"},
        {"paid_detail": False},
    )
    assert "handler_module" not in row
    assert row["secondary_layer"] is True
    assert row["ssot_source"] == "governance/launch57/LAUNCH57_REGISTER.json"


def test_project_library_detail_not_found_passthrough():
    detail = project_library_detail({"found": False, "answer_state": "NOT_FOUND"})
    assert detail["found"] is False


def test_load_canonical_library_entries_count_and_scope():
    entries = load_canonical_library_entries()
    scope = verify_library_scope()
    assert scope["exactly_57"] is True
    assert scope["parked_exposed"] == 0
    assert len(entries) == 57
    assert verify_no_duplicate_ids()["no_duplicates"] is True


def test_search_library_by_launch_number():
    out = search_library(query="5")
    assert out["answer_state"] == "LIBRARY_GROUNDED"
    assert any(r.get("launch_number") == 5 for r in out.get("results") or [])


def test_compare_capabilities_limits_and_grounded():
    too_many = compare_capabilities(list(range(1, 8)))
    assert too_many["answer_state"] == "COMPARE_LIMIT_EXCEEDED"
    grounded = compare_capabilities([4, 5])
    assert grounded["answer_state"] == "COMPARE_GROUNDED"
    assert grounded["count"] == 2
    assert grounded["no_best_capability_ranking"] is True


def test_attach_capability_library_envelope_metadata():
    body = attach_capability_library_envelope({"launch_item_id": 52, "success": True})
    env = body["launch57_capability_library"]
    assert env["no_second_registry"] is True
    assert env["pass_engineering_not_granted_by_envelope"] is True


def test_build_library_component_registry_and_acceptance():
    registry = build_library_component_registry()
    assert any(row["component_id"] == "launch57_register_ssot" for row in registry)
    acceptance = acceptance_criteria_status()
    assert acceptance["ac01_library_count_57"] is True
    assert acceptance["ac04_no_second_ssot"] is True
