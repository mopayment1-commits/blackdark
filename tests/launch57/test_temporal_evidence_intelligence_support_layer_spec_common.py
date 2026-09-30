"""Unit coverage for launch57.temporal_evidence_intelligence_support_layer_spec_common."""

from __future__ import annotations

from launch57.temporal_evidence_intelligence_support_layer_spec_common import (
    DOMAIN,
    TruthStatus,
    build_final_status,
    build_requirements_register,
    build_runtime_truth_table,
    build_specs_13_local_closure_ledger,
    compute_local_gaps,
    independent_verification,
)


def test_build_requirements_register_spec13():
    reqs = build_requirements_register()
    assert len(reqs) >= 20
    assert all(r["mandatory"] for r in reqs)
    assert reqs[0]["req_id"].startswith("REQ-S13-")


def test_runtime_truth_table_all_yes():
    rows = build_runtime_truth_table()
    nos = [r for r in rows if r["status"] != TruthStatus.YES.value]
    assert not nos, nos


def test_independent_verification_pass():
    iv = independent_verification()
    assert iv["INDEPENDENT_VERIFICATION_PASS"] is True
    assert iv["PASS_LIVE_NOT_CLAIMED"] is True


def test_compute_local_gaps_empty_when_iv_and_tests_pass():
    iv = independent_verification()
    gaps = compute_local_gaps(
        tests={"passed": True, "summary": "ok"},
        iv=iv,
        include_tests=True,
    )
    assert gaps == []


def test_build_specs_13_local_closure_ledger_injects_file13():
    ledger = build_specs_13_local_closure_ledger(
        file13_status={
            "domain": DOMAIN,
            "closure_status": "CLOSED_LOCAL",
            "PASS_ENGINEERING": True,
            "LOCAL_INSTITUTIONAL_CLOSURE": True,
            "LOCAL_WORK_REMAINING": 0,
            "PASS_LIVE": False,
            "LIVE_VALIDATION_PENDING": True,
            "final_sha": "abc",
        }
    )
    assert ledger["artifact"] == "SPECS_13_LOCAL_CLOSURE_LEDGER"
    assert ledger["PASS_LIVE_CLAIMED"] is False
    assert any(f.get("file") == "13" for f in ledger["files"])


def test_build_final_status_skip_tests():
    status = build_final_status(skip_tests=True)
    assert status["domain"] == DOMAIN
    assert status["PASS_LIVE"] is False
    assert status["LIVE_VALIDATION_PENDING"] is True
    assert "PASS_ENGINEERING" in status
