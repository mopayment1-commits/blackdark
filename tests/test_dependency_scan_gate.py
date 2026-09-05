"""Dependency & SBOM Scanning Gate (#1044) tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from dependency_scan_gate import (
    DependencyFinding,
    check_dependency_scan_production_gate,
    dependency_scan_gate_status,
    is_suppressed,
    record_dependency_scan_audit,
    run_dependency_scan_gate,
    run_dependency_scan_gate_e2e,
    trigger_dependency_cve_incident,
    verify_lockfile_pinning,
    _cvss_to_severity,
)


def test_cvss_to_severity_mapping():
    assert _cvss_to_severity(9.8) == "critical"
    assert _cvss_to_severity(7.5) == "high"
    assert _cvss_to_severity(5.0) == "medium"
    assert _cvss_to_severity(2.0) == "low"
    assert _cvss_to_severity(None) == "high"


def test_dependency_scan_gate_status():
    status = dependency_scan_gate_status()
    assert status["feature"] == "dependency_scan_gate"
    assert status["standalone_rejected"] is True
    assert status["policy"]["block_critical_cve"] is True
    assert status["policy"]["sbom_format"] == "CycloneDX"
    assert status["integrations"]["sast_gate_ref"] == 1042
    assert status["integrations"]["dast_gate_ref"] == 1043


def test_verify_lockfile_pinning_ok():
    findings = verify_lockfile_pinning()
    critical = [f for f in findings if f.severity == "critical"]
    assert not critical, [f.message for f in critical]


def test_suppression_requires_security_lead(tmp_path, monkeypatch):
    sup_path = tmp_path / "dependency_scan_suppressions.json"
    sup_path.write_text(
        json.dumps(
            {
                "suppressions": [
                    {
                        "cve_id": "CVE-TEST-001",
                        "dependency": "requests",
                        "reason": "not exploitable",
                        "approved_by_security_lead": True,
                        "approved_at": "2026-01-01",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr("dependency_scan_gate._SUPPRESSIONS_PATH", sup_path)
    finding = DependencyFinding(
        rule_id="cve_detected",
        severity="critical",
        message="test",
        dependency="requests",
        cve_id="CVE-TEST-001",
    )
    assert is_suppressed(finding) is True

    unapproved = tmp_path / "unapproved.json"
    unapproved.write_text(
        json.dumps(
            {
                "suppressions": [
                    {
                        "cve_id": "CVE-TEST-002",
                        "dependency": "*",
                        "reason": "dev attempt",
                        "approved_by_security_lead": False,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr("dependency_scan_gate._SUPPRESSIONS_PATH", unapproved)
    finding2 = DependencyFinding(
        rule_id="cve_detected",
        severity="critical",
        message="test",
        dependency="flask",
        cve_id="CVE-TEST-002",
    )
    assert is_suppressed(finding2) is False


def test_run_dependency_scan_gate_blocks_critical(monkeypatch):
    monkeypatch.setattr(
        "dependency_scan_gate.run_pip_audit",
        lambda **_: [
            DependencyFinding(
                rule_id="cve_detected",
                severity="critical",
                message="Log4Shell-class",
                dependency="vuln-pkg",
                cve_id="CVE-2021-44228",
                cvss_score=10.0,
            )
        ],
    )
    monkeypatch.setattr("dependency_scan_gate.verify_lockfile_pinning", lambda **_: [])
    monkeypatch.setattr(
        "dependency_scan_gate.scan_license_compliance",
        lambda **_: ([], {"ok": True, "copyleft_flags": []}),
    )
    monkeypatch.setattr(
        "dependency_scan_gate.generate_sbom_artifact",
        lambda **_: {"ok": True, "format": "CycloneDX"},
    )
    audit_path = Path("data/test_dependency_scan_audit.jsonl")
    if audit_path.is_file():
        audit_path.unlink()
    monkeypatch.setattr("dependency_scan_gate._AUDIT_PATH", audit_path)

    result = run_dependency_scan_gate(actor="test", skip_sbom=True)
    assert result["blocked"] is True
    assert result["ok"] is False
    assert result["finding_counts"]["critical"] == 1
    assert audit_path.is_file()


def test_run_dependency_scan_gate_passes_clean(monkeypatch):
    monkeypatch.setattr("dependency_scan_gate.run_pip_audit", lambda **_: [])
    monkeypatch.setattr("dependency_scan_gate.verify_lockfile_pinning", lambda **_: [])
    monkeypatch.setattr(
        "dependency_scan_gate.scan_license_compliance",
        lambda **_: ([], {"ok": True, "copyleft_flags": []}),
    )
    monkeypatch.setattr(
        "dependency_scan_gate.generate_sbom_artifact",
        lambda **_: {"ok": True, "format": "CycloneDX", "lockfile_sha256": "abc"},
    )
    audit_path = Path("data/test_dependency_scan_audit_clean.jsonl")
    if audit_path.is_file():
        audit_path.unlink()
    monkeypatch.setattr("dependency_scan_gate._AUDIT_PATH", audit_path)

    result = run_dependency_scan_gate(actor="test", skip_sbom=False)
    assert result["blocked"] is False
    assert result["ok"] is True
    assert result["security_trilogy"]["dependency_ref"] == 1044


def test_production_gate():
    gate = check_dependency_scan_production_gate()
    assert gate["feature"] == "dependency_scan_gate"
    assert gate["blocks_production"] is True
    assert "pip_audit" in gate["checks"]
    assert gate["checks"]["scan_enabled"] is True


def test_e2e_checks():
    e2e = run_dependency_scan_gate_e2e()
    assert e2e["feature"] == "dependency_scan_gate"
    assert e2e["all_passed"] is True
    ids = {c["id"] for c in e2e["checks"]}
    assert "sast_cross_ref" in ids
    assert "dast_cross_ref" in ids


def test_incident_trigger_on_critical():
    out = trigger_dependency_cve_incident(
        {"scan_id": "t1", "finding_counts": {"critical": 1, "high": 0}}
    )
    assert out["triggered"] is True
    assert out["integration_ref"] == 1017


def test_incident_not_triggered_when_clean():
    out = trigger_dependency_cve_incident(
        {"scan_id": "t2", "finding_counts": {"critical": 0, "high": 0, "medium": 1}}
    )
    assert out["triggered"] is False


def test_record_audit_append_only(tmp_path, monkeypatch):
    audit = tmp_path / "audit.jsonl"
    monkeypatch.setattr("dependency_scan_gate._AUDIT_PATH", audit)
    record_dependency_scan_audit(
        actor="ci",
        result={"ok": True, "blocked": False, "scan_id": "x", "finding_counts": {}},
        duration_seconds=1.5,
    )
    record_dependency_scan_audit(
        actor="ci",
        result={"ok": True, "blocked": False, "scan_id": "y", "finding_counts": {}},
        duration_seconds=2.0,
    )
    lines = audit.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["scan_id"] == "x"
    assert json.loads(lines[1])["scan_id"] == "y"
