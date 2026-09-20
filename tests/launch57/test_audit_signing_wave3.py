"""Wave 3 — AUDIT_SIGNING_KEY must not break auth/register/login paths."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient


def test_register_succeeds_without_audit_signing_key_in_production(monkeypatch, tmp_path):
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("SECRETS_MASTER_KEY", "wave3-test-master-key-32-chars-min!")
    monkeypatch.delenv("AUDIT_SIGNING_KEY", raising=False)
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path / 'wave3.db'}")

    from dashboard import app

    c = TestClient(app, base_url="https://testserver")
    email = f"wave3-audit-{uuid.uuid4().hex[:10]}@example.com"
    res = c.post(
        "/api/auth/register",
        json={"email": email, "password": "SecurePass1234!", "accepted_terms": True,
            "accepted_privacy": True},
    )
    assert res.status_code == 200, res.text


@pytest.mark.asyncio
async def test_record_audit_log_degrades_without_signing_key(monkeypatch, tmp_path):
    monkeypatch.setenv("ENV", "production")
    monkeypatch.delenv("AUDIT_SIGNING_KEY", raising=False)
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path / 'audit_wave3.db'}")

    from audit_registry import record_audit_log

    row = await record_audit_log(
        actor="wave3-test",
        action="test.action",
        payload_hash="abc123",
        outcome="ok",
        request_path="/api/auth/register",
    )
    assert row.get("audit_signing_degraded") is True
    assert row.get("signature") == ""
