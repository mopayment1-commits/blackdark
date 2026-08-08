"""Tests for production_guard."""

from __future__ import annotations

import os

import pytest


def test_production_guard_shape(monkeypatch):
    monkeypatch.setenv("LEMON_SQUEEZY_CHECKOUT_PRO", "https://example.com/checkout")
    monkeypatch.setenv("LEMON_SQUEEZY_WEBHOOK_SECRET", "whsec-test")
    monkeypatch.setenv("SERVICE_MODE", "web")
    monkeypatch.setenv("SECRETS_MASTER_KEY", "test-master-key")
    monkeypatch.setenv("SESSION_TOKEN_PEPPER", "test-pepper")
    monkeypatch.setenv("ADMIN_API_KEY", "test-admin")
    monkeypatch.delenv("DATABASE_URL", raising=False)

    from production_guard import evaluate_production_guard

    report = evaluate_production_guard()
    assert "checks" in report
    assert report["service_mode"] == "web"
    ids = {c["id"] for c in report["checks"]}
    assert "postgres_database" in ids
    assert "billing_checkout" in ids
    assert "billing_entitlement_webhook" in ids
    assert "secrets_master_key" in ids


def test_production_guard_postgres_pass(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@host/db")
    monkeypatch.setenv("LEMON_SQUEEZY_CHECKOUT_PRO", "https://example.com/checkout")
    monkeypatch.setenv("LEMON_SQUEEZY_WEBHOOK_SECRET", "whsec-test")
    monkeypatch.setenv("SERVICE_MODE", "web")
    monkeypatch.setenv("SECRETS_MASTER_KEY", "test-master-key")
    monkeypatch.setenv("SESSION_TOKEN_PEPPER", "test-pepper")
    monkeypatch.setenv("ADMIN_API_KEY", "test-admin")
    import config

    monkeypatch.setattr(config, "DATABASE_URL", "postgresql://u:p@host/db")
    monkeypatch.setattr(config, "SERVICE_MODE", "web")

    from production_guard import evaluate_production_guard

    report = evaluate_production_guard()
    assert report["database"] == "postgresql"
    assert "postgres_database" not in report["required_failures"]
    assert report["required_pass"] is True


def test_soft_launch_allows_sqlite_without_postgres(monkeypatch):
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("SERVICE_MODE", "web")
    monkeypatch.setenv("SOFT_LAUNCH", "true")
    monkeypatch.setenv("SECRETS_MASTER_KEY", "x" * 32)
    monkeypatch.setenv("SESSION_TOKEN_PEPPER", "y" * 16)
    monkeypatch.setenv("ADMIN_API_KEY", "z" * 24)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("LEMON_SQUEEZY_CHECKOUT_PRO", raising=False)
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
    monkeypatch.delenv("LEMON_SQUEEZY_WEBHOOK_SECRET", raising=False)
    monkeypatch.delenv("IDENTITY_DEBUG_TOKENS", raising=False)

    from production_guard import evaluate_production_guard

    report = evaluate_production_guard()
    assert report["soft_launch"] is True
    assert report["required_pass"] is True
    assert "postgres_database" not in report["required_failures"]


def test_identity_debug_tokens_fail_in_production(monkeypatch):
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("SERVICE_MODE", "web")
    monkeypatch.setenv("SOFT_LAUNCH", "true")
    monkeypatch.setenv("SECRETS_MASTER_KEY", "x" * 32)
    monkeypatch.setenv("SESSION_TOKEN_PEPPER", "y" * 16)
    monkeypatch.setenv("ADMIN_API_KEY", "z" * 24)
    monkeypatch.setenv("IDENTITY_DEBUG_TOKENS", "true")
    monkeypatch.delenv("DATABASE_URL", raising=False)

    from production_guard import evaluate_production_guard

    report = evaluate_production_guard()
    assert "identity_debug_tokens_off" in report["required_failures"]
