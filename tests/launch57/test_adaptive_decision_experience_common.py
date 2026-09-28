"""Unit coverage for launch57.adaptive_decision_experience_common."""

from __future__ import annotations

from launch57.adaptive_decision_experience_common import (
    DOMAIN,
    TruthStatus,
    build_final_status,
    build_requirements_register,
    build_runtime_truth_table,
    compute_local_gaps,
    independent_verification,
)


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
