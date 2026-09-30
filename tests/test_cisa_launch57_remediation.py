"""Launch-57 CISA remediation regression gates."""

from __future__ import annotations

import json
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
    inv = report.get("cisa_remediation_inventory") or {}
    assert inv.get("finding_count") == 19
    assert inv.get("program_complete") is False
    assert "FINDING-01" in (inv.get("open_finding_ids") or [])


def test_launch57_closure_status_api_authenticated(strict_client: TestClient, monkeypatch):
    async def _fake_user(_token: str):
        return {"email": "reviewer@example.test", "tier": "pro", "mfa_enrolled": True}

    monkeypatch.setattr("auth_service.get_user_from_token", _fake_user)
    r = strict_client.get(
        "/api/security/launch57-closure-status",
        headers={"Authorization": "Bearer test-launch57-closure"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body.get("cisa_remediation_inventory", {}).get("finding_count") == 19


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


def test_release_attestation_82_gate():
    import subprocess
    import sys

    root = Path(__file__).resolve().parents[1]
    proc = subprocess.run(
        [sys.executable, str(root / "scripts/verify_launch57_release_attestation_82.py")],
        cwd=root,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    report = json.loads(proc.stdout)
    assert report["pass"] is True


def test_program_closure_81_honest_not_complete():
    import subprocess
    import sys

    root = Path(__file__).resolve().parents[1]
    proc = subprocess.run(
        [sys.executable, str(root / "scripts/verify_launch57_program_closure_81.py")],
        cwd=root,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 2
    report = json.loads(proc.stdout)
    assert report["program_complete_81"] is False


def test_evidence_class_register_gate():
    import subprocess
    import sys

    root = Path(__file__).resolve().parents[1]
    proc = subprocess.run(
        [sys.executable, str(root / "scripts/verify_launch57_evidence_class_register.py")],
        cwd=root,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout


def test_iv_signoff_recorder_dry_run(tmp_path, monkeypatch):
    import subprocess
    import sys

    root = Path(__file__).resolve().parents[1]
    proc = subprocess.run(
        [
            sys.executable,
            str(root / "scripts/record_launch57_independent_verification_signoff.py"),
            "--step",
            "V-2",
            "--signer-role",
            "QA",
            "--reference",
            "https://example.test/ci/1",
        ],
        cwd=root,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout


def test_independent_verification_gate():
    import subprocess
    import sys

    root = Path(__file__).resolve().parents[1]
    proc = subprocess.run(
        [sys.executable, str(root / "scripts/verify_launch57_independent_verification.py")],
        cwd=root,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    report = json.loads(proc.stdout)
    assert report["program_closure_verification_complete"] is False
    assert report["cisa_certification_claimed"] is False
    assert report["repo_automation_pass"] is True


def test_independent_verification_ar_cites_program_83():
    path = Path(__file__).resolve().parents[1] / "docs/governance/LAUNCH57_INDEPENDENT_VERIFICATION_AR.md"
    text = path.read_text(encoding="utf-8")
    assert "§8.3" in text
    assert "LAUNCH57_INDEPENDENT_VERIFICATION_REGISTER.json" in text


def test_normative_traceability_gate():
    import subprocess
    import sys

    root = Path(__file__).resolve().parents[1]
    proc = subprocess.run(
        [sys.executable, str(root / "scripts" / "verify_launch57_normative_traceability.py")],
        cwd=root,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout


def test_executive_summary_ar_cites_program_authority():
    path = Path(__file__).resolve().parents[1] / "docs/governance/LAUNCH57_REMEDIATION_EXECUTIVE_SUMMARY_AR.md"
    text = path.read_text(encoding="utf-8")
    assert "LAUNCH57_CISA_SECURE_BY_DEMAND_REMEDIATION_PROGRAM.md" in text
    assert "not CISA certification" in text


def test_merge_readiness_engineering_safe():
    import subprocess
    import sys

    root = Path(__file__).resolve().parents[1]
    subprocess.run(
        [sys.executable, str(root / "scripts" / "generate_launch57_completion_status.py")],
        cwd=root,
        check=True,
    )
    subprocess.run(
        [sys.executable, str(root / "scripts" / "generate_launch57_engineering_closure.py")],
        cwd=root,
        check=True,
    )
    proc = subprocess.run(
        [sys.executable, str(root / "scripts" / "verify_launch57_merge_readiness.py")],
        cwd=root,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    report = json.loads(proc.stdout)
    assert report["safe_to_merge_engineering"] is True
    assert report["program_complete"] is False


def test_record_pledge_submission_dry_run():
    import subprocess
    import sys

    root = Path(__file__).resolve().parents[1]
    proc = subprocess.run(
        [
            sys.executable,
            str(root / "scripts" / "record_pledge_submission.py"),
            "--pledge-url",
            "https://example.test/pledge",
        ],
        cwd=root,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0


def test_transition_rejects_fake_pentest_close():
    import subprocess
    import sys

    root = Path(__file__).resolve().parents[1]
    proc = subprocess.run(
        [
            sys.executable,
            str(root / "scripts" / "transition_launch57_finding_status.py"),
            "--finding",
            "FINDING-18",
        ],
        cwd=root,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 2


def test_generated_artifacts_freshness_gate():
    import subprocess
    import sys

    root = Path(__file__).resolve().parents[1]
    subprocess.run(
        [sys.executable, str(root / "scripts" / "generate_launch57_completion_status.py")],
        cwd=root,
        check=True,
    )
    subprocess.run(
        [sys.executable, str(root / "scripts" / "generate_launch57_engineering_closure.py")],
        cwd=root,
        check=True,
    )
    proc = subprocess.run(
        [sys.executable, str(root / "scripts" / "verify_launch57_generated_artifacts_fresh.py")],
        cwd=root,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout


def test_finding_inventory_lock_matches_index():
    import subprocess
    import sys

    root = Path(__file__).resolve().parents[1]
    proc = subprocess.run(
        [sys.executable, str(root / "scripts" / "verify_launch57_finding_inventory_lock.py")],
        cwd=root,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout


def test_engineering_closure_declaration_honest():
    import subprocess
    import sys

    root = Path(__file__).resolve().parents[1]
    proc = subprocess.run(
        [sys.executable, str(root / "scripts" / "generate_launch57_engineering_closure.py")],
        cwd=root,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    data = json.loads((root / "governance/launch57/LAUNCH57_ENGINEERING_CLOSURE.json").read_text(encoding="utf-8"))
    assert data["program_complete"] is False
    assert data["cisa_certification_claimed"] is False
    assert data["engineering_closure_declared"] is True
    assert "FINDING-18" in data["ops_and_executive_open"]


def test_completion_status_covers_19_findings():
    import subprocess
    import sys

    root = Path(__file__).resolve().parents[1]
    proc = subprocess.run(
        [sys.executable, str(root / "scripts" / "generate_launch57_completion_status.py")],
        cwd=root,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    data = json.loads((root / "governance/launch57/LAUNCH57_COMPLETION_STATUS.json").read_text(encoding="utf-8"))
    assert len(data["findings"]) == 19
    assert data["cisa_certification_claimed"] is False
    assert data["rollup"]["program_complete"] is False
    md = (root / "governance/launch57/LAUNCH57_REMEDIATION_COMPLETION_STATUS.md").read_text(encoding="utf-8")
    assert "FINDING-18" in md and "FINDING-01" in md


def test_publish_launch57_release_manifest():
    import subprocess
    import sys

    root = Path(__file__).resolve().parents[1]
    proc = subprocess.run(
        [sys.executable, str(root / "scripts" / "publish_launch57_release_evidence.py")],
        cwd=root,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    manifest = root / "docs/data-room/sbom/LAUNCH57_RELEASE_MANIFEST.json"
    assert manifest.is_file()
    data = json.loads(manifest.read_text(encoding="utf-8"))
    assert data.get("cisa_certification_claimed") is False
    assert data.get("artifacts", {}).get("python_cyclonedx_present") is True


def test_record_ops_attestation_writes_file(monkeypatch):
    import json
    import subprocess
    import sys

    monkeypatch.setenv("LAUNCH57_SKIP_ENGINEERING_BASELINE", "1")
    root = Path(__file__).resolve().parents[1]
    proc = subprocess.run(
        [sys.executable, str(root / "scripts" / "record_launch57_ops_attestation.py")],
        cwd=root,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    out_dir = root / "governance/launch57/evidence/ops_attestations"
    files = list(out_dir.glob("OPS_ATTESTATION_*.json"))
    assert files
    record = json.loads(files[-1].read_text(encoding="utf-8"))
    assert record["honesty"]["not_independent_pentest"] is True


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
