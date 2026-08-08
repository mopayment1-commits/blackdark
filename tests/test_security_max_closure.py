"""Maximum security closure tests."""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_max_artifacts_present():
    required = [
        "admin_mfa.py",
        "security_events.py",
        "security_middleware.py",
        "nginx/blackdark.conf",
        "docker-compose.ha.yml",
        "deploy/k8s/network-policy.yaml",
        "deploy/k8s/ingress.yaml",
        "deploy/cloudflare/waf-rules.json",
        "docs/CDN_WAF_CHECKLIST.md",
        "docs/SECURITY_MAX_CHECKLIST.md",
        "docs/templates/pentest_scope.md",
        "scripts/backup_postgres.py",
        "scripts/restore_postgres.py",
        "scripts/security_max_audit.py",
    ]
    missing = [p for p in required if not (ROOT / p).is_file()]
    assert missing == []


@pytest.mark.asyncio
async def test_admin_mfa_blocks_without_totp(monkeypatch):
    monkeypatch.setenv("ADMIN_MFA_REQUIRED", "true")
    monkeypatch.setenv("ADMIN_TOTP_SECRET", "JBSWY3DPEHPK3PXP")
    from fastapi import HTTPException

    from admin_mfa import assert_admin_mfa

    with pytest.raises(HTTPException) as exc:
        await assert_admin_mfa(x_admin_totp="000000", user={"is_admin": True})
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_admin_mfa_accepts_valid_totp(monkeypatch):
    monkeypatch.setenv("ADMIN_MFA_REQUIRED", "true")
    secret = "JBSWY3DPEHPK3PXP"
    monkeypatch.setenv("ADMIN_TOTP_SECRET", secret)
    import pyotp

    from admin_mfa import assert_admin_mfa

    code = pyotp.TOTP(secret).now()
    await assert_admin_mfa(x_admin_totp=code, user={"is_admin": True})


def test_security_event_persist(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    from security_events import recent_security_events, record_security_event

    record_security_event("login_failure", severity="warning", actor="a@b.com")
    rows = recent_security_events(limit=5, kind="login_failure")
    assert rows
    assert rows[-1]["actor"] == "a@b.com"
    assert (tmp_path / "security_events.jsonl").is_file()


def test_security_max_audit_script_runs():
    import subprocess
    import sys

    proc = subprocess.run(
        [sys.executable, "scripts/security_max_audit.py"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    # Non-production env should pass engineering file gates
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "engineering_complete" in proc.stdout


def test_production_guard_requires_admin_totp_in_strict(monkeypatch):
    monkeypatch.setenv("ENV", "production")
    monkeypatch.delenv("SOFT_LAUNCH", raising=False)
    monkeypatch.setenv("VIRAL_MODE", "false")
    monkeypatch.setenv("ADMIN_MFA_REQUIRED", "true")
    monkeypatch.delenv("ADMIN_TOTP_SECRET", raising=False)
    monkeypatch.setenv("SERVICE_MODE", "web")
    monkeypatch.setenv("SECRETS_MASTER_KEY", "x" * 32)
    monkeypatch.setenv("SESSION_TOKEN_PEPPER", "y" * 16)
    monkeypatch.setenv("ADMIN_API_KEY", "z" * 24)
    monkeypatch.setenv("LEMON_SQUEEZY_CHECKOUT_PRO", "https://example.com/c")
    monkeypatch.setenv("LEMON_SQUEEZY_WEBHOOK_SECRET", "whsec")
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@h/db")
    import config

    monkeypatch.setattr(config, "DATABASE_URL", "postgresql://u:p@h/db")
    monkeypatch.setattr(config, "SERVICE_MODE", "web")
    from production_guard import evaluate_production_guard

    report = evaluate_production_guard()
    assert "admin_mfa_configured" in report["required_failures"]
