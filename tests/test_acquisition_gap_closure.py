"""Tests for acquisition readiness gap closure (OAuth/MFA/MRR/pgcrypto/compliance docs)."""

from __future__ import annotations

from pathlib import Path

import pytest


def test_oauth_status_without_credentials(monkeypatch):
    monkeypatch.delenv("OAUTH_GOOGLE_CLIENT_ID", raising=False)
    monkeypatch.delenv("OAUTH_GOOGLE_CLIENT_SECRET", raising=False)
    monkeypatch.delenv("OAUTH_GITHUB_CLIENT_ID", raising=False)
    monkeypatch.delenv("OAUTH_GITHUB_CLIENT_SECRET", raising=False)
    from oauth_service import oauth_configured, oauth_status

    assert oauth_configured() is False
    status = oauth_status()
    assert status["any"] is False


def test_oauth_authorize_url_google(monkeypatch):
    monkeypatch.setenv("OAUTH_GOOGLE_CLIENT_ID", "gid")
    monkeypatch.setenv("OAUTH_GOOGLE_CLIENT_SECRET", "gsecret")
    monkeypatch.setenv("APP_BASE_URL", "http://localhost:8080")
    from oauth_service import build_authorize_url, oauth_configured

    assert oauth_configured("google") is True
    payload = build_authorize_url("google")
    assert "accounts.google.com" in payload["authorize_url"]
    assert "state=" in payload["authorize_url"]


def test_admin_totp_roundtrip(monkeypatch):
    monkeypatch.setenv("SECRETS_MASTER_KEY", "test-master-key-for-unit-tests-only")
    import pyotp

    from admin_mfa import generate_totp_secret, verify_totp

    secret = generate_totp_secret()
    code = pyotp.TOTP(secret).now()
    assert verify_totp(secret, code) is True
    assert verify_totp(secret, "000000") is False


def test_system_admin_totp(monkeypatch):
    import pyotp

    secret = pyotp.random_base32()
    monkeypatch.setenv("ADMIN_TOTP_SECRET", secret)
    from admin_mfa import verify_system_admin_totp

    assert verify_system_admin_totp(pyotp.TOTP(secret).now()) is True


@pytest.mark.asyncio
async def test_mrr_and_churn_reports(monkeypatch):
    from datetime import datetime, timedelta, timezone

    now = datetime.now(timezone.utc)
    async def _rows():
        return [
            {
                "id": 1,
                "email": "a@x.com",
                "tier": "pro",
                "status": "active",
                "created_at": (now - timedelta(days=90)).isoformat(),
                "past_due_at": None,
            },
            {
                "id": 2,
                "email": "b@x.com",
                "tier": "whale",
                "status": "active",
                "created_at": (now - timedelta(days=80)).isoformat(),
                "past_due_at": None,
            },
            {
                "id": 3,
                "email": "c@x.com",
                "tier": "pro",
                "status": "expired",
                "created_at": (now - timedelta(days=40)).isoformat(),
                "past_due_at": (now - timedelta(days=10)).isoformat(),
            },
        ]

    monkeypatch.setattr("database.fetch_subscription_revenue_rows", _rows)
    from billing_service import compute_churn_rate, generate_mrr_report

    mrr = await generate_mrr_report()
    assert mrr["mrr_usd"] == 29.0 + 199.0
    assert mrr["active_paying_subscriptions"] == 2
    churn = await compute_churn_rate(window_days=60)
    assert churn["churned_in_window"] >= 1
    assert "churn_rate_percent" in churn


def test_pgcrypto_helpers_noop_without_postgres(monkeypatch):
    import config

    monkeypatch.setattr(config, "DATABASE_URL", "")
    from postgres_backend import use_postgres

    assert use_postgres() is False


def test_compliance_pack_and_architecture_exist():
    root = Path(__file__).resolve().parents[1]
    assert (root / "docs" / "SEC_MICA_COMPLIANCE_PACK.md").is_file()
    assert (root / "ARCHITECTURE.md").is_file()
    assert (root / "docker-compose.prod.yml").is_file()
    assert (root / "scripts" / "load_test_10k.py").is_file()
