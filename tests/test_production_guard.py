"""Tests for production_guard."""

from __future__ import annotations

import os

import pytest


def test_production_guard_shape(monkeypatch):
    monkeypatch.setenv("LEMON_SQUEEZY_CHECKOUT_PRO", "https://example.com/checkout")
    monkeypatch.setenv("SERVICE_MODE", "web")
    monkeypatch.delenv("DATABASE_URL", raising=False)

    from production_guard import evaluate_production_guard

    report = evaluate_production_guard()
    assert "checks" in report
    assert report["service_mode"] == "web"
    ids = {c["id"] for c in report["checks"]}
    assert "postgres_database" in ids
    assert "billing_checkout" in ids


def test_production_guard_postgres_pass(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@host/db")
    monkeypatch.setenv("LEMON_SQUEEZY_CHECKOUT_PRO", "https://example.com/checkout")
    monkeypatch.setenv("SERVICE_MODE", "web")
    import config

    monkeypatch.setattr(config, "DATABASE_URL", "postgresql://u:p@host/db")
    monkeypatch.setattr(config, "SERVICE_MODE", "web")

    from production_guard import evaluate_production_guard

    report = evaluate_production_guard()
    assert report["database"] == "postgresql"
    assert "postgres_database" not in report["required_failures"]
    assert report["required_pass"] is True
