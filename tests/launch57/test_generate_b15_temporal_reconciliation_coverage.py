"""Behavioral coverage for governance.launch57.generate_b15_temporal_reconciliation."""

from __future__ import annotations

import copy

import governance.launch57.generate_b15_temporal_reconciliation as b15


def test_finding_bucket_and_blockers():
    bucket = b15._finding_bucket()
    assert bucket["naive_datetime_findings"] == []
    blockers = b15._external_blockers()
    assert any(b["gate"] == "production_host_clock_sync" for b in blockers)
    gaps = b15._unresolved_gaps()
    assert gaps[0]["id"] == "B14-ENVELOPE-COVERAGE"


def test_batch_verdicts_and_final_fields():
    verdicts = b15._batch_verdicts()
    assert "B1" in verdicts
    assert len(verdicts) == len(b15.BATCH_VERDICT_KEYS)
    fields = b15._final_verdict_fields()
    assert "final_status" in fields
    assert fields["PASS_LIVE_NOT_CLAIMED"] is True


def test_build_reconciliation_and_report():
    sha = b15._git_sha()
    spec_sha = b15._spec_sha256()
    verdicts = {k: "PASS_ENGINEERING" for k in b15.BATCH_VERDICT_KEYS}
    tests = {"success": True, "passed": 10, "collected": 10, "failed": 0}
    recon = b15.build_reconciliation(sha, spec_sha, tests, verdicts)
    assert recon["all_batches_b1_b14_pass_engineering"] is True
    assert recon["integrated_temporal_reconciliation_pass"] is True
    report = b15.build_report(sha, spec_sha, tests, verdicts, recon)
    assert "B15" in report
    assert "PASS_ENGINEERING" in report


def test_build_reconciliation_fails_when_batch_missing_pass():
    sha = "abc123"
    spec_sha = "def456"
    verdicts = {k: "PASS_ENGINEERING" for k in b15.BATCH_VERDICT_KEYS}
    verdicts["B2"] = "FAIL"
    tests = {"success": True}
    recon = b15.build_reconciliation(sha, spec_sha, tests, verdicts)
    assert recon["all_batches_b1_b14_pass_engineering"] is False
    assert recon["integrated_temporal_reconciliation_pass"] is False
