"""Security catastrophe P0 — financial platform fail-closed controls."""

from __future__ import annotations

import asyncio
import inspect
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient


def test_artifacts_and_wiring():
    assert Path("live_execution_gate.py").is_file()
    assert Path("security_catastrophe_closure.py").is_file()
    assert Path("docs/SECURITY_CATASTROPHE_P0_AR.md").is_file()
    from security_auth import require_admin

    assert "assert_admin_mfa" in inspect.getsource(require_admin)
    from platform_api import _force_safe_dry_run

    assert "live_execution_gate" in inspect.getsource(_force_safe_dry_run)
    dash = Path("dashboard.py").read_text(encoding="utf-8")
    assert "soft_launch_active" in dash
    assert "contact-sales" in dash
    assert "EXPOSE_B2B_DEMO_KEY" in dash
    assert "/api/security/catastrophe-p0" in dash


def test_soft_launch_blocks_live_execution(monkeypatch):
    monkeypatch.setenv("SOFT_LAUNCH", "true")
    monkeypatch.setenv("LIVE_EXECUTION_ALLOW_API", "true")
    from fastapi import HTTPException

    from live_execution_gate import force_safe_dry_run, soft_launch_forbids_live_money

    assert soft_launch_forbids_live_money() is True
    with pytest.raises(HTTPException) as exc:
        force_safe_dry_run(False)
    assert exc.value.status_code == 403
    detail = exc.value.detail
    assert isinstance(detail, dict)
    assert detail["error"] == "soft_launch_forbids_live_execution"


def test_live_allowed_only_without_soft_launch(monkeypatch):
    monkeypatch.delenv("SOFT_LAUNCH", raising=False)
    monkeypatch.setenv("LIVE_EXECUTION_ALLOW_API", "true")
    from live_execution_gate import force_safe_dry_run

    assert force_safe_dry_run(False) is False
    assert force_safe_dry_run(True) is True


@pytest.mark.asyncio
async def test_require_admin_enforces_mfa(monkeypatch):
    monkeypatch.setenv("ADMIN_MFA_REQUIRED", "true")
    monkeypatch.setenv("ADMIN_TOTP_SECRET", "JBSWY3DPEHPK3PXP")
    monkeypatch.setenv("ADMIN_API_KEY", "test-admin-key-catastrophe-p0")
    from fastapi import HTTPException

    from security_auth import require_admin

    with pytest.raises(HTTPException) as exc:
        await require_admin(user=None, x_admin_key="test-admin-key-catastrophe-p0", x_admin_totp=None)
    assert exc.value.status_code == 403

    import pyotp

    code = pyotp.TOTP("JBSWY3DPEHPK3PXP").now()
    admin = await require_admin(
        user=None,
        x_admin_key="test-admin-key-catastrophe-p0",
        x_admin_totp=code,
    )
    assert admin["is_admin"] is True


def test_closure_code_complete():
    from security_catastrophe_closure import build_security_catastrophe_closure

    closure = asyncio.run(build_security_catastrophe_closure())
    assert closure["surface"] == "security_catastrophe_p0_closure"
    assert closure["code_complete"] is True
    assert "soc2_certified" in closure["forbidden_claims"]
    assert closure["engineering_p0_complete"] is True
    ids = {i["id"] for i in closure["items"]}
    assert "p0_admin_mfa_wired" in ids
    assert "p0_live_execution_gate_wired" in ids
    assert "p0_edge_waf_declared" in ids


def test_production_guard_requires_catastrophe_ops(monkeypatch):
    monkeypatch.setenv("ENV", "production")
    monkeypatch.delenv("SOFT_LAUNCH", raising=False)
    monkeypatch.setenv("VIRAL_MODE", "false")
    monkeypatch.setenv("ADMIN_MFA_REQUIRED", "true")
    monkeypatch.setenv("ADMIN_TOTP_SECRET", "JBSWY3DPEHPK3PXP")
    monkeypatch.setenv("SERVICE_MODE", "web")
    monkeypatch.setenv("SECRETS_MASTER_KEY", "x" * 32)
    monkeypatch.setenv("SESSION_TOKEN_PEPPER", "y" * 16)
    monkeypatch.setenv("ADMIN_API_KEY", "z" * 24)
    monkeypatch.setenv("LEMON_SQUEEZY_CHECKOUT_PRO", "https://example.com/c")
    monkeypatch.setenv("LEMON_SQUEEZY_WEBHOOK_SECRET", "whsec")
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@h/db")
    monkeypatch.setenv("EXPOSE_B2B_DEMO_KEY", "false")
    monkeypatch.setenv("BLACKDARK_B2B_DEMO_KEY", "disabled")
    monkeypatch.delenv("CDN_WAF_ACTIVE", raising=False)
    monkeypatch.delenv("CLOUDFLARE_ZONE_ID", raising=False)
    monkeypatch.delenv("BACKUP_SCHEDULE_CONFIGURED", raising=False)
    monkeypatch.delenv("SENTRY_DSN", raising=False)
    monkeypatch.delenv("EXTERNAL_UPTIME_CONFIGURED", raising=False)
    import config

    monkeypatch.setattr(config, "DATABASE_URL", "postgresql://u:p@h/db")
    monkeypatch.setattr(config, "SERVICE_MODE", "web")
    monkeypatch.setattr(config, "B2B_DEMO_API_KEY", "disabled")
    from production_guard import evaluate_production_guard

    report = evaluate_production_guard()
    assert "edge_waf_declared" in report["required_failures"]
    assert "backup_ops_configured" in report["required_failures"]
    assert "monitoring_declared" in report["required_failures"]


def test_catastrophe_api_and_public_docs():
    from public_api_docs import path_is_public

    assert path_is_public("/api/security/catastrophe-p0") is True

    async def _run():
        from dashboard import app

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.get("/api/security/catastrophe-p0")
            assert r.status_code == 200
            body = r.json()
            assert body["code_complete"] is True
            s = await client.get("/api/security/status")
            assert s.status_code == 200
            assert s.json().get("catastrophe_p0") == "/api/security/catastrophe-p0"

    asyncio.run(_run())
