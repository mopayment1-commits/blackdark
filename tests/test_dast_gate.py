"""DAST Gate — dynamic application security testing."""

from __future__ import annotations

import json

import pytest
from httpx import ASGITransport, AsyncClient

from dast_gate import (
    DASTFinding,
    is_suppressed,
    run_dast_gate_e2e,
    run_dast_scan_asgi,
    scan_response_leaks,
    scan_rbac_protected_paths,
    dast_gate_status,
)


@pytest.fixture
def dast_env(monkeypatch, tmp_path):
    audit = tmp_path / "dast_scan_audit.jsonl"
    suppressions = tmp_path / "dast_suppressions.json"
    suppressions.write_text('{"suppressions": []}', encoding="utf-8")
    monkeypatch.setattr("dast_gate._AUDIT_PATH", audit)
    monkeypatch.setattr("dast_gate._SUPPRESSIONS_PATH", suppressions)
    return {"audit": audit, "suppressions": suppressions}


def test_seed_loads():
    from dast_gate import _load_seed

    seed = _load_seed()
    assert seed["standalone_rejected"] is True
    assert seed["dast_gate"]["policy"]["production_read_only"] is True


def test_policy_status(dast_env):
    status = dast_gate_status()
    assert status["ok"] is True
    assert status["sast_cross_ref"] == 1042
    assert status["policy"]["weekly_automated_scan"] is True


def test_leak_scan_detects_stripe_key():
    findings = scan_response_leaks("/api/test", '{"key": "sk_live_abcdefghijklmnopqrst"}')
    assert any(f.rule_id == "stripe_secret_leak" for f in findings)
    assert any(f.severity == "critical" for f in findings)


def test_suppression_requires_security_lead(dast_env):
    finding = DASTFinding(
        rule_id="stripe_secret_leak",
        severity="critical",
        message="test",
        endpoint="/api/test",
    )
    assert is_suppressed(finding) is False

    dast_env["suppressions"].write_text(
        json.dumps(
            {
                "suppressions": [
                    {
                        "rule_id": "stripe_secret_leak",
                        "endpoint": "/api/test",
                        "reason": "false positive test fixture",
                        "approved_by_security_lead": True,
                        "approved_at": "2026-01-01T00:00:00Z",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    assert is_suppressed(finding) is True


@pytest.mark.asyncio
async def test_asgi_scan_runs(dast_env):
    result = await run_dast_scan_asgi(mode="ci", actor="test")
    assert "finding_counts" in result
    assert "scan_id" in result
    assert result["target"] == "asgi_local"
    assert dast_env["audit"].is_file()


@pytest.mark.asyncio
async def test_rbac_protected_paths_deny_anonymous():
    from httpx import ASGITransport, AsyncClient

    from dashboard import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        findings = await scan_rbac_protected_paths(
            client,
            ["/api/platform/keys/status"],
        )
    critical = [f for f in findings if f.rule_id == "rbac_unauthorized_access"]
    assert len(critical) == 0


def test_production_gate(dast_env):
    from dast_gate import check_dast_production_gate

    gate = check_dast_production_gate()
    assert gate["checks"]["production_read_only"] is True
    assert gate["ok"] is True


def test_e2e(dast_env):
    result = run_dast_gate_e2e()
    assert result["ok"] is True
    assert result["all_passed"] is True


def test_security_workflow_has_dast_gate():
    from pathlib import Path

    wf = Path(".github/workflows/security.yml").read_text(encoding="utf-8")
    assert "dast-gate:" in wf
    assert "run_dast_gate.py" in wf


@pytest.mark.asyncio
async def test_platform_dast_routes(dast_env):
    from dashboard import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for path in (
            "/api/platform/dast/status",
            "/api/platform/dast/gate",
            "/api/platform/dast/e2e",
        ):
            r = await client.get(path)
            assert r.status_code == 200, path
            body = r.json()
            assert body.get("ok") is True or body.get("all_passed") is True


def test_incident_trigger():
    from dast_gate import trigger_dast_incident

    low = trigger_dast_incident({"finding_counts": {"critical": 0, "high": 0}, "scan_id": "x"})
    assert low["triggered"] is False

    high = trigger_dast_incident({"finding_counts": {"critical": 1, "high": 0}, "scan_id": "y"})
    assert high["triggered"] is True
    assert high["integration_ref"] == 1017
