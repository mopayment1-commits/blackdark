"""Tests — CLI/API feature gating (#167, #173)."""

from __future__ import annotations

from auth_service import feature_allowed


def test_cli_access_institutional_only():
    assert feature_allowed({"tier": "institutional"}, "cli_access") is True
    assert feature_allowed({"tier": "quant"}, "cli_access") is True
    assert feature_allowed({"tier": "pro"}, "cli_access") is False
    assert feature_allowed({"tier": "free"}, "cli_access") is False


def test_due_diligence_reports_institutional():
    assert feature_allowed({"tier": "institutional"}, "due_diligence_reports") is True
    assert feature_allowed({"tier": "quant"}, "due_diligence_reports") is True
    assert feature_allowed({"tier": "pro"}, "due_diligence_reports") is False
