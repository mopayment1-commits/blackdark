"""Tests — Security Verification Evidence (#191)."""

from __future__ import annotations

import json

import pytest

from bd_platform import security_verification_evidence as sve


@pytest.fixture
def isolated_evidence_paths(tmp_path, monkeypatch):
    findings = tmp_path / "findings.jsonl"
    packs = tmp_path / "packs.jsonl"
    suppressions = tmp_path / "suppressions.json"
    evidence_dir = tmp_path / "packs"
    monkeypatch.setattr(sve, "_FINDINGS_PATH", findings)
    monkeypatch.setattr(sve, "_PACKS_PATH", packs)
    monkeypatch.setattr(sve, "_SUPPRESSIONS_PATH", suppressions)
    monkeypatch.setattr(sve, "_EVIDENCE_DIR", evidence_dir)
    return findings, packs, suppressions, evidence_dir


def test_gate_inventory_reproducible():
    inventory = sve._gate_inventory()
    assert len(inventory) >= 5
    assert all(g.get("reproducible") for g in inventory)


def test_run_security_gates(isolated_evidence_paths):
    result = sve.run_security_gates()
    assert result["ok"] is True
    assert result["feature_id"] == 191
    assert result["gate_version"] == "1.0.0"
    assert "release_gate" in result


def test_release_gate_passes_without_critical(isolated_evidence_paths):
    gate = sve.release_gate_status()
    assert gate["ok"] is True
    assert "headline" in gate
    assert gate["findings_summary"]["critical_open"] == 0


def test_suppress_requires_signed_rationale(isolated_evidence_paths):
    # Too short rationale rejected
    denied = sve.suppress_finding(
        finding_id="test-finding-1",
        rationale="too short",
        signer="cto@blackdark.io",
    )
    assert denied["ok"] is False

    approved = sve.suppress_finding(
        finding_id="test-finding-1",
        rationale="Accepted risk: false positive in test fixture file, no production exposure.",
        signer="cto@blackdark.io",
    )
    assert approved["ok"] is True
    assert approved["signed"] is True


def test_remediation_marks_finding(isolated_evidence_paths):
    finding = sve._append_finding(
        {
            "gate": "secrets_scan",
            "severity": "medium",
            "rule": "test_rule",
            "status": "open",
            "detail": "test finding",
        }
    )
    result = sve.verify_remediation(
        finding_id=finding["id"],
        evidence="Removed hardcoded key, rotated credential, verified in CI.",
    )
    assert result["ok"] is True
    assert result["status"] == "remediated"


def test_evidence_pack_built(isolated_evidence_paths):
    pack = sve.build_evidence_pack()
    assert pack["feature_id"] == 191
    assert pack["retention_years"] == 3
    assert "release_gate" in pack
    assert pack["sla_met"] is True


def test_security_verification_status(isolated_evidence_paths):
    status = sve.security_verification_status()
    assert status["ok"] is True
    assert status["feature_id"] == 191
    assert "#192" in status["integrated_features"]
    assert status["sla_met"] is True
