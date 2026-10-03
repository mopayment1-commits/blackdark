"""Behavioral coverage for governance.launch57.generate_phase0_truth (no main())."""

from __future__ import annotations

import json
from pathlib import Path

import governance.launch57.generate_phase0_truth as gen

ROOT = Path(__file__).resolve().parents[2]


def test_name_similarity_and_resolve_runtime_path():
    assert gen.name_similarity("Foo", "foo") == 1.0
    assert 0.0 < gen.name_similarity("alpha", "beta") < 1.0
    cap = {"canonical_owner": "cap646.institutional_official_production", "runtime_entry": "x"}
    assert gen.resolve_runtime_path(cap) == "cap646/institutional_official_production.py"


def test_generic_delegate_finding_and_scan_file_phantoms(tmp_path):
    finding = gen.generic_delegate_finding(
        "CAP-1",
        {
            "canonical_implementation": "explicit_option_a",
            "actual_consumer_paths": ["explicit_option_a"],
            "runtime_entry": "cap646/runtime.py",
            "canonical_owner": "owner",
        },
        3,
    )
    assert finding is not None
    assert finding["finding_type"] == "GENERIC_DELEGATE_WITHOUT_DISTINCT_CONSUMER_PATH"

    stub = ROOT / "tests" / "_phase0_truth_phantom_scan_fixture.py"
    stub.write_text("def x():\n    raise NotImplementedError\n", encoding="utf-8")
    try:
        phantoms = gen.scan_file_phantoms(stub, {"CAP-1"})
    finally:
        stub.unlink(missing_ok=True)
    assert any(p["finding_type"] == "NOT_IMPLEMENTED" for p in phantoms)


def test_load_json_and_git_head():
    ssot = gen.load_json(gen.SSOT_PATH)
    assert "canonical_capabilities" in ssot
    head = gen.git_head()
    assert len(head) >= 7


def test_find_tests_for_cap_returns_list():
    hits = gen.find_tests_for_cap("CAP-646", "cap646")
    assert isinstance(hits, list)


def test_build_register_and_scope_integrity_from_repo_ssot():
    ssot = gen.load_json(gen.SSOT_PATH)
    hero_matrix = gen.load_json(gen.HERO_MATRIX_PATH)
    phantom_doc = gen.load_json(gen.PHANTOM_PATH)
    register = gen.build_register(ssot, hero_matrix, phantom_doc)
    assert register["summary"]["TOTAL_LAUNCH57"] == 57
    assert len(register["launch57_register"]) == 57
    si = gen.compute_scope_integrity(ssot)
    assert si["LAUNCH57_COUNT"] == 57
    assert register["scope_integrity"]["LAUNCH57_COUNT"] == si["LAUNCH57_COUNT"]


def test_update_ssot_and_render_report_smoke():
    ssot = gen.load_json(gen.SSOT_PATH)
    hero_matrix = gen.load_json(gen.HERO_MATRIX_PATH)
    phantom_doc = gen.load_json(gen.PHANTOM_PATH)
    register = gen.build_register(ssot, hero_matrix, phantom_doc)
    updated = gen.update_ssot(ssot, register)
    assert updated["phase0_truth"]["phase"] == "0_TRUTH"
    report = gen.render_report(register)
    assert "Launch-57 Phase 0" in report
    assert "SCOPE_LEAKAGE_FOUND" in report
