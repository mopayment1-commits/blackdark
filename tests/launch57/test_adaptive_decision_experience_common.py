"""Unit coverage for launch57.adaptive_decision_experience_common."""

from __future__ import annotations

import launch57.adaptive_decision_experience_common as adaptive_decision_experience_common
from launch57.adaptive_decision_experience_common import (
    DOMAIN,
    TruthStatus,
    build_final_status,
    build_requirements_register,
    build_runtime_truth_table,
    compute_local_gaps,
    independent_verification,
    run_targeted_tests,
)


def test_module_import_path_is_production_package():
    assert adaptive_decision_experience_common.__name__ == "launch57.adaptive_decision_experience_common"
    assert adaptive_decision_experience_common.DOMAIN == "SPEC_01_ADAPTIVE_DECISION_EXPERIENCE"


def test_build_requirements_register_spec01():
    reqs = build_requirements_register()
    assert len(reqs) >= 25
    assert all(r["mandatory"] for r in reqs)
    req_ids = [r["req_id"] for r in reqs]
    assert len(req_ids) == len(set(req_ids))


def test_runtime_truth_table_all_yes():
    rows = build_runtime_truth_table()
    assert rows
    bad = [r for r in rows if r["status"] != TruthStatus.YES.value]
    assert not bad, bad


def test_independent_verification_pass():
    iv = independent_verification()
    assert iv["INDEPENDENT_VERIFICATION_PASS"] is True
    assert iv["failed_count"] == 0
    assert iv["PASS_LIVE_NOT_CLAIMED"] is True


def test_compute_local_gaps_empty_when_truth_and_iv_pass():
    iv = independent_verification()
    gaps = compute_local_gaps(
        tests={"passed": True, "summary": "ok"},
        iv=iv,
        include_tests=True,
    )
    assert gaps == []


def test_build_final_status_skip_tests():
    status = build_final_status(skip_tests=True)
    assert status["domain"] == DOMAIN
    assert status["PASS_LIVE"] is False
    assert status["LIVE_VALIDATION_PENDING"] is True
    assert "PASS_ENGINEERING" in status
    assert status["LOCAL_ENGINEERING_GAP_COUNT"] == status["LOCAL_WORK_REMAINING"]


def test_resolve_spec_path_and_register_rows():
    path = adaptive_decision_experience_common._resolve_spec_path()
    assert path is None or path.exists()
    rows = adaptive_decision_experience_common._register_rows()
    assert isinstance(rows, list)


def test_compute_local_gaps_truth_iv_and_test_branches(monkeypatch):
    monkeypatch.setattr(
        adaptive_decision_experience_common,
        "build_runtime_truth_table",
        lambda: [
            {
                "req_id": "REQ-S01-011",
                "title": "gap",
                "status": TruthStatus.NO.value,
                "evidence": "forced",
            }
        ],
    )
    gaps = compute_local_gaps(
        tests={"passed": False, "summary": "failed"},
        iv={
            "INDEPENDENT_VERIFICATION_PASS": False,
            "probes": [{"probe": "x", "pass": False, "detail": "iv fail"}],
        },
        include_tests=True,
    )
    assert any(g["req_id"] == "REQ-S01-011" for g in gaps)
    assert any(g["req_id"] == "IV" for g in gaps)
    assert any(g["req_id"] == "TESTS" for g in gaps)


def test_run_targeted_tests_invokes_real_pytest_suite(monkeypatch):
    captured: dict[str, str] = {}

    def fake_run(cmd, cwd=None, capture_output=True, text=True):
        captured["cmd"] = " ".join(cmd)
        class R:
            returncode = 0
            stdout = "1 passed"
            stderr = ""

        return R()

    monkeypatch.setattr(adaptive_decision_experience_common.subprocess, "run", fake_run)
    out = run_targeted_tests()
    assert out["passed"] is True
    assert "pytest" in captured["cmd"]
