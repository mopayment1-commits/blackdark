"""Spine database auth/billing coverage — CLOSURE-MANDATE-LAST item 2."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest


@pytest.fixture
async def spine_db(tmp_path, monkeypatch):
    import config
    import database

    db_path = tmp_path / "spine.db"
    monkeypatch.setattr(config, "DB_PATH", str(db_path))
    monkeypatch.delenv("DATABASE_URL", raising=False)
    await database.init_db()
    return database


@pytest.mark.asyncio
async def test_billing_subscription_lifecycle(spine_db):
    email = "billing@blackdark.local"
    uid = await spine_db.create_user(email, "hash", name="Billing User")
    sub_id = await spine_db.activate_paid_subscription(
        email,
        "pro",
        "sub_stripe_001",
        stripe_customer_id="cus_001",
    )
    assert sub_id > 0
    await spine_db.upsert_subscription_by_stripe_id(
        "sub_stripe_001",
        tier="pro",
        status="past_due",
    )
    await spine_db.upsert_subscription_by_stripe_id(
        "sub_stripe_001",
        status="active",
    )
    active = await spine_db.fetch_active_subscription_for_email(email)
    assert active is not None
    await spine_db.cancel_subscription_by_stripe_id("sub_stripe_001")
    assert await spine_db.claim_billing_webhook_event(provider="stripe", event_id="evt_1", event_type="invoice.paid")
    assert not await spine_db.claim_billing_webhook_event(provider="stripe", event_id="evt_1")
    await spine_db.expire_subscription(sub_id)


@pytest.mark.asyncio
async def test_user_profile_and_sessions(spine_db):
    email = "profile@blackdark.local"
    uid = await spine_db.create_user(email, "hash", name="Profile User")
    await spine_db.update_user_profile_fields(uid, {"name": "Updated", "username": "profileuser"})
    await spine_db.mark_email_verified(uid)
    profile = await spine_db.fetch_user_profile(email)
    assert profile is not None
    by_id = await spine_db.fetch_user_by_id(uid)
    assert by_id is not None
    by_username = await spine_db.fetch_user_by_username("profileuser")
    assert by_username is not None
    expires = (datetime.now(UTC) + timedelta(hours=1)).isoformat()
    session_id = await spine_db.insert_user_session(uid, "sess-token-abc", expires)
    assert session_id > 0
    session_user = await spine_db.fetch_user_by_session("sess-token-abc")
    assert session_user is not None
    await spine_db.touch_user_login(uid)
    await spine_db.delete_user_session("sess-token-abc")
    assert await spine_db.delete_user_sessions_for_user(uid) >= 0


@pytest.mark.asyncio
async def test_auth_tokens_and_oauth_state(spine_db):
    uid = await spine_db.create_user("auth@blackdark.local", "hash")
    expires = (datetime.now(UTC) + timedelta(hours=1)).isoformat()
    await spine_db.insert_auth_token(user_id=uid, token_type="reset", token_hash="hash123", expires_at=expires)
    consumed = await spine_db.consume_auth_token_row("hash123", "reset")
    assert consumed == uid
    assert await spine_db.consume_auth_token_row("hash123", "reset") is None
    oauth_exp = (datetime.now(UTC) + timedelta(minutes=10)).isoformat()
    await spine_db.insert_oauth_state(provider="google", state="state-xyz", expires_at=oauth_exp)
    assert await spine_db.consume_oauth_state(provider="google", state="state-xyz")


@pytest.mark.asyncio
async def test_institutional_inquiry_and_telegram(spine_db):
    inquiry_id = await spine_db.insert_institutional_inquiry(
        email="inst@blackdark.local",
        company="Acme Capital",
        message="Enterprise inquiry",
    )
    assert inquiry_id > 0
    email = "telegram@blackdark.local"
    await spine_db.create_user(email, "hash")
    await spine_db.update_user_telegram_chat_id(email, "12345")
    await spine_db.upsert_telegram_free_subscriber(chat_id="12345", username="tguser")
    sub = await spine_db.fetch_telegram_free_subscriber("12345")
    assert sub is not None
    enabled = await spine_db.fetch_enabled_telegram_free_subscribers()
    assert isinstance(enabled, list)
    await spine_db.increment_telegram_free_alert_usage("12345", datetime.now(UTC).strftime("%Y-%m-%d"), 10)
    assert await spine_db.count_telegram_free_subscribers() >= 1
    await spine_db.set_telegram_free_subscriber_enabled("12345", enabled=False)


@pytest.mark.asyncio
async def test_platform_user_stats_and_stripe_lookup(spine_db):
    email = "stripe@blackdark.local"
    await spine_db.create_user(email, "hash")
    await spine_db.activate_paid_subscription(email, "pro", "sub_lookup", stripe_customer_id="cus_lookup")
    assert await spine_db.fetch_user_stripe_customer_id(email) == "cus_lookup"
    stats = await spine_db.fetch_platform_user_stats()
    assert isinstance(stats, dict)
    users = await spine_db.fetch_users_with_telegram()
    assert isinstance(users, list)


@pytest.mark.asyncio
async def test_mfa_lifecycle(spine_db):
    uid = await spine_db.create_user("mfa@blackdark.local", "hash")
    await spine_db.set_user_mfa_pending_secret(uid, "pending-enc")
    await spine_db.enable_user_mfa(uid, "secret-enc")
    await spine_db.set_user_mfa_recovery_hashes(uid, ["hash-a", "hash-b"])
    row = await spine_db.fetch_user_mfa_row(uid)
    assert row is not None
    assert row.get("mfa_enabled") is True
    await spine_db.consume_mfa_recovery_hash(uid, "hash-a")
    await spine_db.clear_user_mfa(uid)
    cleared = await spine_db.fetch_user_mfa_row(uid)
    assert cleared is not None
    assert cleared.get("mfa_enabled") is False


@pytest.mark.asyncio
async def test_erase_user_personal_data(spine_db):
    email = "erase@blackdark.local"
    await spine_db.create_user(email, "hash", name="Erase Me")
    result = await spine_db.erase_user_personal_data(email)
    assert isinstance(result, dict)


@pytest.mark.asyncio
async def test_oauth_user_flow(spine_db):
    uid = await spine_db.create_oauth_user(
        "oauth-new@blackdark.local",
        name="OAuth User",
        provider="google",
        subject="google-sub-999",
    )
    assert uid > 0
    await spine_db.link_user_oauth(uid, "google", "google-sub-999")
    found = await spine_db.fetch_user_by_oauth("google", "google-sub-999")
    assert found is not None
    assert found["email"] == "oauth-new@blackdark.local"


@pytest.mark.asyncio
async def test_oracle_usage_counters(spine_db):
    email = "usage@blackdark.local"
    await spine_db.create_user(email, "hash")
    count = await spine_db.fetch_oracle_usage_today(email)
    assert count >= 0
    await spine_db.increment_oracle_usage(email)
    assert await spine_db.fetch_oracle_usage_today(email) >= 1
    month = await spine_db.fetch_oracle_usage_month(email)
    assert month >= 1
    assert await spine_db.fetch_user_by_oauth("", "") is None
