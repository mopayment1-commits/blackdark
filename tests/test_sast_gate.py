"""SAST Gate — static application security testing CI/CD gate."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

from sast_gate import SASTFinding, is_suppressed, run_sast_gate_e2e, sast_gate_status, scan_secrets


@pytest.fixture
def sast_env(monkeypatch, tmp_path):
    audit = tmp_path / "sast_scan_audit.jsonl"
    suppressions = tmp_path / "sast_suppressions.json"
    suppressions.write_text('{"suppressions": []}', encoding="utf-8")
    monkeypatch.setattr("sast_gate._AUDIT_PATH", audit)
    monkeypatch.setattr("sast_gate._SUPPRESSIONS_PATH", suppressions)
    return {"audit": audit, "suppressions": suppressions}


def test_seed_loads():
    from sast_gate import _load_seed

    seed = _load_seed()
    assert seed["standalone_rejected"] is True
    assert seed["sast_gate"]["policy"]["block_critical_high"] is True


def test_policy_status(sast_env):
    status = sast_gate_status()
    assert status["ok"] is True
    assert status["policy"]["max_scan_minutes"] <= 10
    assert "plaintext_api_keys" in status["rulesets"]


def test_secrets_scan_detects_hardcoded_key(tmp_path, sast_env):
    bad = tmp_path / "leak.py"
    bad.write_text('api_key = "sk_live_abcdefghijklmnopqrst"\n', encoding="utf-8")

    with patch("sast_gate._iter_source_files", return_value=[bad]):
        findings = scan_secrets()
    assert any(f.rule_id == "stripe_live_key" or f.rule_id == "hardcoded_api_key" for f in findings)
    assert any(f.severity == "critical" for f in findings)


def test_suppression_requires_security_lead(sast_env):
    finding = SASTFinding(
        rule_id="hardcoded_api_key",
        severity="critical",
        message="test",
        file="leak.py",
        line=1,
    )
    assert is_suppressed(finding) is False

    sast_env["suppressions"].write_text(
        json.dumps(
            {
                "suppressions": [
                    {
                        "rule_id": "hardcoded_api_key",
                        "file": "leak.py",
                        "line": 1,
                        "reason": "test fixture",
                        "approved_by_security_lead": True,
                        "approved_at": "2026-01-01T00:00:00Z",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    assert is_suppressed(finding) is True


def test_run_scan_without_bandit(sast_env):
    from sast_gate import run_sast_scan

    result = run_sast_scan(actor="test", include_bandit=False)
    assert "finding_counts" in result
    assert "scan_id" in result
    assert sast_env["audit"].is_file()


def test_production_gate(sast_env):
    from sast_gate import check_sast_production_gate

    gate = check_sast_production_gate()
    assert gate["checks"]["block_critical_high"] is True
    assert gate["ok"] is True


def test_e2e(sast_env):
    result = run_sast_gate_e2e()
    assert result["ok"] is True
    assert result["all_passed"] is True


def test_security_workflow_has_sast_gate():
    wf = Path(".github/workflows/security.yml").read_text(encoding="utf-8")
    assert "sast-gate:" in wf
    assert "run_sast_gate.py" in wf


@pytest.mark.asyncio
async def test_platform_sast_routes(sast_env):
    from dashboard import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for path in (
            "/api/platform/sast/status",
            "/api/platform/sast/gate",
            "/api/platform/sast/e2e",
        ):
            r = await client.get(path)
            assert r.status_code == 200, path
            body = r.json()
            assert body.get("ok") is True or body.get("all_passed") is True


def test_incident_trigger_on_blocked(sast_env):
    from sast_gate import trigger_production_vulnerability_incident

    low = trigger_production_vulnerability_incident(
        {"finding_counts": {"critical": 0, "high": 0}, "scan_id": "x"}
    )
    assert low["triggered"] is False

    high = trigger_production_vulnerability_incident(
        {"finding_counts": {"critical": 1, "high": 0}, "scan_id": "y"}
    )
    assert high["triggered"] is True
    assert high["integration_ref"] == 1017
