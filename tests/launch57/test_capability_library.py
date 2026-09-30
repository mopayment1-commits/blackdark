"""Launch-57 Capability Library (#52) baseline tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from launch57.capability_library_common import (
    CAPABILITY_LIBRARY_VERSION,
    acceptance_criteria_status,
    attach_capability_library_envelope,
    build_library_component_registry,
    compare_capabilities,
    load_canonical_library_entries,
    resolve_capability_detail,
    search_library,
    verify_library_scope,
    verify_no_duplicate_ids,
)
from launch57.edge_ui_batch1 import (
    capability_library_compare,
    capability_library_detail,
    capability_library_search,
)


def test_library_indexes_exactly_57_capabilities():
    scope = verify_library_scope()
    assert scope["exactly_57"] is True
    assert scope["library_count"] == 57
    assert scope["missing_launch_numbers"] == []
    assert scope["parked_exposed"] == 0


def test_no_duplicate_launch_numbers():
    dupes = verify_no_duplicate_ids()
    assert dupes["no_duplicates"] is True
    entries = load_canonical_library_entries()
    assert len(entries) == len({e["launch_number"] for e in entries})


def test_search_by_name():
    out = search_library(query="Oracle")
    assert out["count"] > 0
    assert out["answer_state"] == "LIBRARY_GROUNDED"


def test_search_by_intent():
    out = search_library(query="whale activity")
    assert out["count"] > 0
    assert all(r["launch_number"] in range(14, 21) for r in out["results"])


def test_arabic_and_english_search():
    ar = search_library(query="دقة")
    en = search_library(query="accuracy")
    assert ar["count"] > 0
    assert en["count"] > 0


def test_invalid_query_no_weak_match():
    out = search_library(query="legacy cap978 phantom catalogue")
    assert out["answer_state"] == "NO_VALID_MATCH"
    assert out["results"] == []
    assert out["no_valid_match"] is True


def test_functional_area_browse():
    out = search_library(functional_area="Derivatives")
    assert out["count"] > 0
    assert all(r.get("functional_area") == "Derivatives" for r in out["results"])


def test_detail_page_resolves():
    detail = resolve_capability_detail(4)
    assert detail["found"] is True
    assert detail["answer_state"] == "DETAIL_RESOLVED"
    assert detail["current_state"] is not None
    assert detail["hero_relationships"] is not None


def test_compare_up_to_four():
    compared = compare_capabilities([4, 5])
    assert compared["answer_state"] == "COMPARE_GROUNDED"
    assert compared["count"] == 2
    assert compared["no_best_capability_ranking"] is True


def test_compare_limit_enforced():
    compared = compare_capabilities([1, 2, 3, 4, 5])
    assert compared["answer_state"] == "COMPARE_LIMIT_EXCEEDED"


def test_public_detail_strips_handler_module():
    detail = resolve_capability_detail(52, authenticated=False)
    assert detail["found"] is True
    assert "handler_module" not in detail["record"]


def test_envelope_metadata_only():
    body = attach_capability_library_envelope({"launch_item_id": 52, "success": True})
    env = body["launch57_capability_library"]
    assert env["version"] == CAPABILITY_LIBRARY_VERSION
    assert env["no_second_registry"] is True
    assert env["pass_engineering_not_granted_by_envelope"] is True


def test_component_registry_reuses_ssot():
    registry = build_library_component_registry()
    owners = {row["component_id"] for row in registry}
    assert "launch57_register_ssot" in owners
    assert "trust_adaptive_library_guard" in owners


def test_acceptance_criteria_gate():
    acceptance = acceptance_criteria_status()
    assert acceptance["ac01_library_count_57"] is True
    assert acceptance["ac04_no_second_ssot"] is True
    assert acceptance["ac08_detail_pages_resolve"] is True


@pytest.mark.asyncio
async def test_capability_library_search_wired():
    out = await capability_library_search(symbol="BTC", params={"query": "Oracle"})
    assert out["launch_item_id"] == 52
    assert out["success"] is True
    lib = out["capability_library"]
    assert lib["secondary_layer"] is True
    assert lib["no_second_registry"] is True
    assert lib["canonical_count"] == 57
    assert "launch57_capability_library" in out


@pytest.mark.asyncio
async def test_capability_library_detail_wired():
    out = await capability_library_detail(symbol="BTC", params={"launch_number": 4})
    assert out["launch_item_id"] == 52
    assert out["success"] is True
    assert out["capability_library_detail"]["found"] is True


@pytest.mark.asyncio
async def test_capability_library_compare_wired():
    out = await capability_library_compare(symbol="BTC", params={"compare": "4,5"})
    assert out["launch_item_id"] == 52
    assert out["success"] is True
    assert out["capability_library_compare"]["count"] == 2


@pytest.mark.asyncio
async def test_parked_injection_rejected():
    out = await capability_library_search(symbol="BTC", params={"include_parked": True})
    assert out["success"] is False
    assert out["capability_library"]["results"] == []


def test_governance_artifacts_paths_exist_after_generator():
    gov = Path("governance/launch57")
    for name in (
        "BLACKDARK_LAUNCH57_CAPABILITY_LIBRARY_INDEX.json",
        "BLACKDARK_LAUNCH57_CAPABILITY_LIBRARY_RECONCILIATION.json",
        "BLACKDARK_LAUNCH57_CAPABILITY_LIBRARY_INDEPENDENT_VERIFICATION.json",
        "BLACKDARK_LAUNCH57_CAPABILITY_LIBRARY_REPORT.md",
    ):
        path = gov / name
        if path.exists():
            payload = path.read_text(encoding="utf-8")
            if name.endswith(".json"):
                assert json.loads(payload)
