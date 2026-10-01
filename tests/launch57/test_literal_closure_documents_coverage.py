"""Behavioral coverage for governance.launch57.literal_closure_documents."""

from __future__ import annotations

from governance.launch57.literal_closure_documents import (
    financial_recon_public_document,
    spec10_final_status_public_document,
    spec10_iv_public_document,
    spec10_local_closure_report_lines,
    spec12_final_status_public_document,
    spec12_iv_public_document,
    spec12_local_closure_report_lines,
)


def test_financial_recon_public_document_shape():
    doc = financial_recon_public_document(
        generated_at="2026-01-01T00:00:00+00:00",
        implementation_sha="abc",
        baseline_sha="def",
    )
    assert doc["artifact"] == "BLACKDARK_LAUNCH57_FINANCIAL_DATA_SECURITY_RECONCILIATION"
    assert doc["launch57_support_only"] is True
    assert len(doc["external_blockers"]) >= 3
    assert "privileged_access" in doc["reuse_paths"]


def test_spec10_public_documents_and_report_lines():
    iv = spec10_iv_public_document(generated_at="t", verification_sha="sha")
    assert iv["INDEPENDENT_VERIFICATION_PASS"] is True
    status = spec10_final_status_public_document(
        generated_at="t",
        final_sha="sha",
        spec_version="v1",
        governing_spec="spec.md",
        branch="main",
    )
    assert status["PASS_LIVE"] is False
    assert status["closure_status"] == "CLOSED_LOCAL"
    lines = spec10_local_closure_report_lines(
        final_sha="sha",
        runtime_truth_yes_count=10,
        runtime_truth_total=12,
        test_command="pytest -q",
        test_exit_code=0,
        test_summary="ok",
    )
    assert lines[0] == "# SPEC_10 Local Closure Report"
    assert any("Runtime truth YES: 10/12" in ln for ln in lines)


def test_spec12_public_documents_and_report_lines():
    iv = spec12_iv_public_document(generated_at="t", verification_sha="sha")
    assert iv["domain"] == "SPEC_12_IDENTITY_AUTH_PROFILE"
    status = spec12_final_status_public_document(
        generated_at="t",
        final_sha="sha",
        spec_version="v1",
        governing_spec="spec.md",
        branch="main",
    )
    assert status["LOCAL_WORK_REMAINING"] == 0
    lines = spec12_local_closure_report_lines(
        final_sha="sha",
        runtime_truth_yes_count=5,
        runtime_truth_total=5,
        test_command="pytest -q",
        test_exit_code=0,
        test_summary="5 passed",
    )
    assert "Identity Auth Profile" in "\n".join(lines)
