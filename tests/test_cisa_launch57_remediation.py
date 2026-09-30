"""Launch-57 CISA remediation regression gates."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def strict_client(monkeypatch):
    monkeypatch.setenv("SOFT_LAUNCH", "false")
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("USER_MFA_ENROLL_REQUIRED", "false")
    monkeypatch.setenv("APP_BASE_URL", "https://example.test")
    monkeypatch.setenv("AUDIT_SIGNING_KEY", "test-audit-signing-key-32chars-minimum-xx")
    from dashboard import app

    return TestClient(app, base_url="https://example.test")


def test_security_txt_route(strict_client: TestClient):
    r = strict_client.get("/.well-known/security.txt")
    assert r.status_code == 200
    assert "Contact:" in r.text
    assert "Policy:" in r.text


def test_sso_status_allowed_without_session(strict_client: TestClient, monkeypatch):
    monkeypatch.setenv("APP_BASE_URL", "https://example.test")
    r = strict_client.get("/api/institutional/sso/status")
    assert r.status_code == 200
    assert r.json().get("surface") == "enterprise_sso"


def test_anonymous_denial_includes_security_headers(strict_client: TestClient):
    r = strict_client.get("/api/user/profile")
    assert r.status_code == 401
    assert r.headers.get("X-Blackdark-Auth-Boundary") == "anonymous-denied"
    assert r.headers.get("X-Content-Type-Options") == "nosniff"
    assert r.headers.get("X-Security-Hardening") == "1"


def test_public_security_status_is_minimal(strict_client: TestClient):
    r = strict_client.get("/api/security/status")
    assert r.status_code == 200
    body = r.json()
    assert body.get("surface") == "security_posture_public"
    assert "checks" not in body
    assert "pentest_attestation" not in body
    assert body.get("honesty", {}).get("cisa_certification_claimed") is False


def test_public_vdp_endpoint(strict_client: TestClient):
    r = strict_client.get("/api/security/vdp")
    assert r.status_code == 200
    body = r.json()
    assert body.get("surface") == "vulnerability_disclosure_policy"
    assert body.get("security_txt") == "/.well-known/security.txt"
    assert body.get("honesty", {}).get("cisa_certification_claimed") is False


def test_security_log_retention_minimum():
    from security_events import security_log_retention_days

    assert security_log_retention_days() >= 180


def test_webauthn_status_reports_library(monkeypatch):
    pytest.importorskip("webauthn")
    monkeypatch.setenv("WEBAUTHN_RP_ID", "example.test")
    monkeypatch.setenv("APP_BASE_URL", "https://example.test")
    from webauthn_service import webauthn_status

    st = webauthn_status()
    assert st["library_available"] is True
    assert st["enabled"] is True


def test_launch57_closure_status_honest():
    from launch57_assurance_closure import launch57_closure_status

    report = launch57_closure_status()
    assert report["cisa_certification_claimed"] is False
    assert report["findings"]["pentest_attestation"]["status"] in {"OPEN", "CLOSED"}


def test_cisa_repo_evidence_index_paths_exist():
    from pathlib import Path
    import subprocess
    import sys

    root = Path(__file__).resolve().parents[1]
    proc = subprocess.run(
        [sys.executable, str(root / "scripts" / "verify_launch57_repo_evidence.py")],
        cwd=root,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout


def test_railway_cisa_env_spec_valid():
    import json

    spec_path = Path(__file__).resolve().parents[1] / "governance/launch57/RAILWAY_CISA_ENV_EXPECTATIONS.json"
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    names = {v["name"] for v in spec["variables"]}
    assert "WEBAUTHN_RP_ID" in names
    assert "SECURITY_LOG_RETENTION_DAYS" in names


def test_railway_env_evaluator_production_ok(monkeypatch):
    from scripts.verify_railway_launch57_env import evaluate

    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("APP_BASE_URL", "https://example.test")
    monkeypatch.setenv("WEBAUTHN_RP_ID", "example.test")
    monkeypatch.setenv("USER_MFA_ENROLL_REQUIRED", "true")
    monkeypatch.setenv("SECURITY_LOG_RETENTION_DAYS", "180")
    monkeypatch.setenv("BLACKDARK_RELEASE", "launch-57")
    monkeypatch.setenv("AUDIT_SIGNING_KEY", "x" * 32)
    import os

    report = evaluate(dict(os.environ), include_waf=False)
    assert report["mode"] == "production"
    assert report["ok"] is True


def test_launch57_closure_report_marks_runtime_open():
    import subprocess
    import sys

    root = Path(__file__).resolve().parents[1]
    proc = subprocess.run(
        [sys.executable, str(root / "scripts" / "launch57_closure_report.py")],
        cwd=root,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 2
    assert "RUNTIME_OPEN" in proc.stderr
    assert "cisa_certification_claimed" in proc.stdout


def test_pentest_deposit_launch57_guide_exists():
    path = Path(__file__).resolve().parents[1] / "docs/evidence/PENTEST_DEPOSIT_LAUNCH57.md"
    assert path.is_file()
    assert "FINDING-18" in path.read_text(encoding="utf-8")


def test_prod_surface_skips_without_url(monkeypatch):
    import subprocess
    import sys

    monkeypatch.delenv("LAUNCH57_PROD_URL", raising=False)
    root = Path(__file__).resolve().parents[1]
    proc = subprocess.run(
        [sys.executable, str(root / "scripts" / "verify_launch57_prod_surface.py")],
        cwd=root,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 3


def test_pledge_execution_checklist_present():
    path = Path(__file__).resolve().parents[1] / "docs/governance/SECURE_BY_DESIGN_PLEDGE_EXECUTION_CHECKLIST.md"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "FINDING-01" in text


def test_sbom_includes_git_commit_metadata():
    from pathlib import Path

    from scripts.generate_sbom import _parse_lock, build_sbom

    lock = Path("requirements.lock.txt")
    if not lock.is_file():
        pytest.skip("no lockfile")
    sha = __import__("hashlib").sha256(lock.read_bytes()).hexdigest()
    comps = _parse_lock(lock)
    bom = build_sbom(comps, lock_sha=sha)
    names = {p["name"] for p in bom["metadata"]["properties"]}
    assert "blackdark:git_commit" in names or "blackdark:release" in names
