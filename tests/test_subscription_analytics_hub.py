"""Tests — Subscription Analytics Hub (Feature #9, 3 phases)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest


def test_posthog_not_configured_by_default():
    from bd_platform.analytics_integrations import posthog_configured

    assert posthog_configured() is False


@pytest.mark.asyncio
async def test_posthog_capture_skips_when_unconfigured():
    from bd_platform.analytics_integrations import posthog_capture

    out = await posthog_capture(event="test", distinct_id="anon", properties={})
    assert out["ok"] is False
    assert out["provider"] == "posthog"


@pytest.mark.asyncio
async def test_analytics_dashboard():
    from bd_platform.analytics_integrations import analytics_dashboard

    out = await analytics_dashboard()
    assert out["ok"] is True
    assert out["feature"] == "#9-phase2"
    assert "visitors" in out["counts"]
    assert "registered_users" in out["counts"]
    assert "paid_subscribers" in out["counts"]
    assert out["latency_ms"] < 2000
    assert out["acceptance"]["sla_met"] is True


@pytest.mark.asyncio
async def test_user_lifecycle_status_free_user(billing_user):
    from bd_platform.subscription_lifecycle import user_lifecycle_status

    out = await user_lifecycle_status(int(billing_user["id"]))
    assert out["ok"] is True
    assert out["feature"] == "#9-phase1"
    assert out["effective_plan"] == "free"
    assert out["features_active"] is True
    assert out["renewal_warning_days"] == 5


@pytest.mark.asyncio
async def test_initiate_upgrade_ladder(billing_user):
    from bd_platform.subscription_lifecycle import initiate_upgrade

    out = await initiate_upgrade(int(billing_user["id"]))
    assert out["ok"] is True
    assert out["current_plan"] == "free"
    assert out["target_plan"] == "pro"
    assert "checkout_href" in out


@pytest.mark.asyncio
async def test_recommend_upgrade(billing_user):
    from bd_platform.upgrade_intelligence import recommend_upgrade

    out = await recommend_upgrade(int(billing_user["id"]))
    assert out["ok"] is True
    assert out["feature"] == "#9-phase3"
    assert out["recommended_plan"] == "pro"
    assert out["confidence"] >= 0.55
    assert out["explanation"]
    assert out["latency_ms"] < 2000


@pytest.mark.asyncio
async def test_renewal_warning_scan_idempotent(billing_user, monkeypatch, tmp_path):
    from billing.renewal_alerts import run_renewal_warning_scan
    from billing.subscription_engine import activate_checkout

    uid = int(billing_user["id"])
    email = billing_user["email"]
    period_end = (datetime.now(UTC) + timedelta(days=3)).isoformat()
    await activate_checkout(
        email=email,
        plan="pro",
        provider="stripe",
        provider_subscription_id=f"sub_warn_{datetime.now(UTC).timestamp()}",
        provider_event_id=f"evt_warn_{datetime.now(UTC).timestamp()}",
        user_id=uid,
        period_start=datetime.now(UTC).isoformat(),
        period_end=period_end,
        auto_renew_consent=True,
    )
    sent_path = tmp_path / "warnings.jsonl"
    monkeypatch.setattr("billing.renewal_alerts._SENT_PATH", sent_path)

    r1 = await run_renewal_warning_scan()
    r2 = await run_renewal_warning_scan()
    assert r1["sent"] >= 1
    assert r2["skipped"] >= 1


@pytest.mark.asyncio
async def test_track_subscription_event():
    from distribution_compounding import track_subscription_event

    row = await track_subscription_event(
        event_type="subscription_activated",
        user_id=None,
        payload={"plan": "pro"},
    )
    assert row["event_type"] == "subscription_activated"


@pytest.mark.asyncio
async def test_audit_fanout(monkeypatch):
    calls = []

    async def fake_track(**kwargs):
        calls.append(kwargs)
        return {}

    monkeypatch.setattr("distribution_compounding.track_subscription_event", fake_track)
    from billing.audit_ledger import record_audit

    await record_audit(
        action="ACTIVATE",
        actor="test",
        user_id=1,
        email="t@test.com",
        old_plan="free",
        new_plan="pro",
    )
    assert len(calls) == 1
    assert calls[0]["event_type"] == "subscription_activated"


def test_api_routes(monkeypatch):
    async def fake_dashboard():
        return {"ok": True, "counts": {"visitors": 1}, "funnel": {}, "providers": {}, "latency_ms": 10, "acceptance": {"sla_met": True}}

    async def fake_lifecycle(uid):
        return {"ok": True, "effective_plan": "free", "features_active": True, "acceptance": {}, "latency_ms": 5}

    async def fake_upgrade(uid, **kw):
        return {"ok": True, "checkout_href": "/create-checkout-session?tier=pro"}

    async def fake_recommend(uid):
        return {"ok": True, "explanation": "test", "recommended_plan": "pro", "confidence": 0.8, "latency_ms": 5}

    monkeypatch.setattr("bd_platform.analytics_integrations.analytics_dashboard", fake_dashboard)
    monkeypatch.setattr("bd_platform.subscription_lifecycle.user_lifecycle_status", fake_lifecycle)
    monkeypatch.setattr("bd_platform.subscription_lifecycle.initiate_upgrade", fake_upgrade)
    monkeypatch.setattr("bd_platform.upgrade_intelligence.recommend_upgrade", fake_recommend)

    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/analytics-hub/dashboard").status_code == 200
    r = c.get("/subscription-analytics")
    assert r.status_code == 200
    assert "Subscription Analytics Hub" in r.text


@pytest.fixture
async def billing_user():
    from database import create_user, init_db

    await init_db()
    email = f"sub-analytics-{datetime.now(UTC).timestamp()}@blackdark.test"
    uid = await create_user(email, "pbkdf2_sha256$260000$deadbeef$" + "a" * 64, "Sub Analytics")
    return {"id": uid, "email": email}
