"""Tests for gtm_service — MKT launch tracker."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_fetch_gtm_status_shape(monkeypatch):
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)

    async def _users():
        return {
            "registered_users": 1,
            "paid_subscribers": 0,
            "active_trials": 0,
            "alert_subscribers": 0,
        }

    async def _behavior(**_kwargs):
        return {"total_events": 5}

    async def _telegram():
        return 2

    async def _waitlist():
        return 3

    async def _oracle(**_kwargs):
        return {"live": {"resolved_predictions": 4}}

    monkeypatch.setattr("database.fetch_platform_user_stats", _users)
    monkeypatch.setattr("database.fetch_behavior_event_stats", _behavior)
    monkeypatch.setattr("database.count_telegram_free_subscribers", _telegram)
    monkeypatch.setattr("database.db_count_waitlist", _waitlist)
    monkeypatch.setattr("database.fetch_oracle_audit_stats", _oracle)

    from gtm_service import fetch_gtm_status

    status = await fetch_gtm_status()
    assert "stripe" in status
    assert "telegram" in status
    assert "mkt_verdicts" in status
    assert status["metrics"]["waitlist_signups"] == 3
    assert "MKT-006_customer_demand" in status["mkt_verdicts"]
    assert status["marketing_docs"]["icp"] is True
