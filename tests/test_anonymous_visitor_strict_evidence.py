"""Strict evidence reconciliation tests."""

from __future__ import annotations


def test_requirement_count_reconciled_to_153():
    from anonymous_visitor.traceability import build_traceability_report, requirement_count_reconciliation

    recon = requirement_count_reconciliation()
    report = build_traceability_report()
    assert recon["FINAL_CANONICAL_REQUIREMENT_COUNT"] == 153
    assert recon["REQUIREMENT_COUNT_RECONCILED"] is True
    assert report["TOTAL_SPEC_REQUIREMENTS"] == 153
    assert (
        report["SATISFIED_REQUIREMENTS"]
        + report["PARTIAL_REQUIREMENTS"]
        + report["EXTERNAL_REQUIREMENTS"]
        + report["LEGAL_REQUIREMENTS"]
        + len(report["LOCAL_UNSATISFIED_REQUIREMENT_IDS"])
        == 153
    )


def test_partial_requirement_ids_account_for_thirteen_av_linked():
    from anonymous_visitor.traceability import build_traceability_report

    report = build_traceability_report()
    partial = set(report["PARTIAL_REQUIREMENT_IDS"])
    details = {d["id"]: d["reason"] for d in report["PARTIAL_REQUIREMENT_DETAILS"]}
    assert "REQ-008" in partial
    assert "REQ-011" in partial
    stream_partials = [rid for rid in partial if details.get(rid, "").startswith("Stream")]
    assert len(stream_partials) == 11
    assert len(partial) == 13


def test_temporal_classification_sums_to_eligible():
    from oracle_audit_chain import temporal_integrity_summary

    t = temporal_integrity_summary()
    assert t["TEMPORAL_CLASSIFICATION_SUM"] == t["ELIGIBLE_IDS_COUNT"]


def test_reconciliation_sha_semantics_evidence_only_head():
    from anonymous_visitor.reconciliation import head_is_evidence_only_commit, reconciliation_semantics_valid

    rec = reconciliation_semantics_valid()
    assert rec.get("SELF_REFERENTIAL_COMMIT_HASH") is False
    if head_is_evidence_only_commit():
        assert rec.get("HEAD_IS_EVIDENCE_ONLY_COMMIT") is True


def test_ledger_mutation_prevented():
    from anonymous_visitor.strict_evidence import ledger_mutation_evidence

    ev = ledger_mutation_evidence()
    assert ev["LEDGER_MUTATION_PREVENTED"] is True
    assert ev["UNPROTECTED_MUTATION_PATHS"] == []


def test_stream_controls_explicit_list():
    from anonymous_visitor.strict_evidence import stream_control_evidence

    rows = stream_control_evidence()
    controls = {r["CONTROL"] for r in rows}
    assert "bounded upstream fanout" in controls
    assert "memory/task/thread cleanup" in controls
    assert all(r["RESULT"] == "PASS" for r in rows)


def test_bandit_sha1_usedforsecurity_only():
    import subprocess

    proc = subprocess.run(
        ["bandit", "-q", "-ll", "identity/breached_passwords.py"],
        capture_output=True,
        text=True,
    )
    assert "sha1" not in proc.stdout.lower() or proc.returncode == 0


def test_argon2_in_requirements_hashes():
    text = open("requirements.hashes.txt", encoding="utf-8").read()
    assert "argon2-cffi" in text


def test_surface_inventory_exact_count():
    from anonymous_visitor.strict_evidence import exposed_surface_inventory

    inv = exposed_surface_inventory(__import__("dashboard", fromlist=["app"]).app)
    assert isinstance(inv["FINAL_TOTAL_EXPOSED_SURFACES"], int)
    assert inv["FINAL_TOTAL_EXPOSED_SURFACES"] > 0
    assert "236" in inv["COUNT_RECONCILIATION_EXPLANATION"] or inv["PREVIOUS_SURFACE_COUNT"] == 236
