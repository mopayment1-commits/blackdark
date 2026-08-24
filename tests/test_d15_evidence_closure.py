"""D-15 — critical defects evidence closure registry."""

from __future__ import annotations

from critical_defects_closure import CRITICAL_DEFECTS, build_closure_report


def test_all_six_critical_defects_registered():
    assert CRITICAL_DEFECTS == ("D-01", "D-02", "D-06", "D-09", "D-13", "D-15")


def test_closure_report_all_closed():
    report = build_closure_report(run_tests=False)
    assert report["summary"]["total"] == 6
    assert report["summary"]["closed"] == 6
    for defect in report["critical_defects"]:
        assert defect["status"] == "CLOSED"
        assert defect["id"] in CRITICAL_DEFECTS
        assert "tests" in defect
        assert "limitations" in defect


def test_platform_verdict_pass_with_risk():
    report = build_closure_report(run_tests=False)
    assert report["summary"]["platform_verdict"] == "PASS WITH RISK"


def test_evidence_doc_referenced():
    report = build_closure_report(run_tests=False)
    d15 = next(d for d in report["critical_defects"] if d["id"] == "D-15")
    assert "docs/evidence/CRITICAL_DEFECTS_CLOSURE.md" in d15["implementation"]
