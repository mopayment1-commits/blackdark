"""Coverage for SPEC closure generator markdown helpers (_md_*)."""

from __future__ import annotations

import importlib

import pytest

_SPEC_MODULES = [
    "governance.launch57.generate_spec01_adaptive_decision_closure",
    "governance.launch57.generate_spec02_anonymous_visitor_closure",
    "governance.launch57.generate_spec03_billing_subscription_entitlement_closure",
    "governance.launch57.generate_spec04_capability_library_closure",
    "governance.launch57.generate_spec05_commercial_capability_inventory_closure",
    "governance.launch57.generate_spec06_compounding_evidence_track_record_closure",
    "governance.launch57.generate_spec07_data_intelligence_governance_closure",
    "governance.launch57.generate_spec08_decision_truth_closure",
    "governance.launch57.generate_spec09_failure_degraded_recovery_closure",
    "governance.launch57.generate_spec10_financial_data_secret_security_closure",
    "governance.launch57.generate_spec11_global_time_temporal_consistency_closure",
    "governance.launch57.generate_spec12_identity_auth_profile_closure",
    "governance.launch57.generate_spec13_temporal_evidence_intelligence_support_layer_closure",
]


@pytest.mark.parametrize("module_name", _SPEC_MODULES)
def test_md_truth_table_and_local_closure(module_name: str):
    mod = importlib.import_module(module_name)
    rows = [
        {
            "req_id": "R1",
            "spec_section": "§1",
            "status": "YES",
            "evidence": "tests/launch57",
        }
    ]
    table = mod._md_truth_table(rows)
    assert "Runtime Truth Table" in table
    assert "**YES**" in table

    status = {
        "closure_status": "LOCAL_CLOSED",
        "PASS_ENGINEERING": True,
        "LOCAL_INSTITUTIONAL_CLOSURE": True,
        "LOCAL_WORK_REMAINING": False,
        "PASS_LIVE": False,
        "LIVE_VALIDATION_PENDING": True,
        "final_sha": "abc",
        "BUILDER_STATUS": "OK",
        "runtime_truth_yes_count": 1,
        "runtime_truth_total": 1,
        "public_surface_matrix_ok": True,
        "IV_STATUS": "PASS",
        "live_blockers_only": ["external gate"],
        "LOCAL_ENGINEERING_GAPS": [
            {"priority": "P2", "req_id": "G1", "title": "t", "evidence": "e"},
        ],
    }
    iv = {"passed_count": 3, "probe_count": 3, "INDEPENDENT_VERIFICATION_PASS": True}
    tests = {"command": "pytest -q", "exit_code": 0, "summary": "1 passed"}
    local_md = getattr(mod, "_md_local_closure", None)
    if local_md is not None:
        report = local_md(status, iv, tests)
        assert "Local Closure Report" in report
        assert "PASS_LIVE" in report
        assert "P2" in report
