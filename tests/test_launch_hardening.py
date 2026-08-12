"""Experimental-launch hardening regressions (audit residuals)."""

from __future__ import annotations

import hashlib
import hmac
import inspect

import pytest


def test_cex_dex_cycle_forwards_dry_run():
    import platform_api
    from bd_platform.cex_dex_executor import run_cex_dex_cycle

    assert "dry_run" in inspect.signature(run_cex_dex_cycle).parameters
    src = inspect.getsource(platform_api.cex_dex_execute)
    assert "dry_run=dry_run" in src
    assert "run_cex_dex_cycle" in src


def test_lemon_webhook_signature_and_handler(monkeypatch):
    from billing_service import verify_lemon_webhook_signature

    secret = "test-lemon-secret"
    monkeypatch.setenv("LEMON_SQUEEZY_WEBHOOK_SECRET", secret)
    body = b'{"meta":{"event_name":"subscription_created"},"data":{"id":"99","attributes":{"user_email":"a@b.com","status":"active","product_name":"Pro"}}}'
    sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    assert verify_lemon_webhook_signature(body, sig) is True
    assert verify_lemon_webhook_signature(body, "bad") is False


@pytest.mark.asyncio
async def test_lemon_webhook_activates_subscription(monkeypatch):
    from billing_service import handle_lemon_webhook_event

    calls: list[tuple] = []

    async def _activate(email, tier, sub_id, **kwargs):
        calls.append((email, tier, sub_id))
        return 1

    async def _claim(*_args, **_kwargs):
        return True

    monkeypatch.setattr(
        "database.activate_paid_subscription",
        _activate,
        raising=False,
    )
    monkeypatch.setattr(
        "database.claim_billing_webhook_event",
        _claim,
        raising=False,
    )
    # Patch where handler imports from
    import database

    monkeypatch.setattr(database, "activate_paid_subscription", _activate)
    monkeypatch.setattr(database, "claim_billing_webhook_event", _claim)

    event = {
        "meta": {"event_name": "subscription_created", "webhook_id": "wh_test_unique_activate"},
        "data": {
            "id": "12345-unique-activate",
            "attributes": {
                "user_email": "buyer@example.com",
                "status": "active",
                "product_name": "BLACKDARK Pro",
            },
        },
    }
    result = await handle_lemon_webhook_event(event)
    assert result["handled"] is True
    assert calls
    assert calls[0][0] == "buyer@example.com"
    assert calls[0][1] == "pro"
    assert calls[0][2].startswith("lemon_")


def test_session_plaintext_fallback_gated():
    import auth_service

    src = inspect.getsource(auth_service.get_user_from_token)
    assert "ALLOW_PLAINTEXT_SESSION_LOOKUP" in src
    assert "is_production_env" in src
    logout_src = inspect.getsource(auth_service.logout_user)
    assert "ALLOW_PLAINTEXT_SESSION_LOOKUP" in logout_src


def test_track_record_correct_only(clean_chain_tr):
    import oracle_track_record as tr

    tr.on_prediction_resolved(
        1,
        asset="BTC",
        verdict="BUY",
        price_at_prediction=100,
        price_after=105,
        outcome="correct",
        accuracy_score=90,
        label="correct",
    )
    tr.on_prediction_resolved(
        2,
        asset="ETH",
        verdict="BUY",
        price_at_prediction=100,
        price_after=101,
        outcome="partial",
        accuracy_score=50,
        label="partial",
    )
    stats = tr.public_track_record()
    assert stats["cumulative"]["hit_definition"] == "correct_only"
    assert stats["cumulative"]["resolved_predictions"] == 2
    assert stats["cumulative"]["hit_rate_percent"] == 50.0
    assert stats["cumulative"]["partial_rate_percent"] == 50.0


def test_audit_chain_append_locked():
    import oracle_audit_chain as chain

    assert hasattr(chain, "_APPEND_LOCK")
    src = inspect.getsource(chain.append_prediction_record)
    assert "_APPEND_LOCK" in src


def test_production_guard_requires_billing_webhook(monkeypatch):
    monkeypatch.setenv("LEMON_SQUEEZY_CHECKOUT_PRO", "https://example.com/checkout")
    monkeypatch.delenv("LEMON_SQUEEZY_WEBHOOK_SECRET", raising=False)
    monkeypatch.delenv("STRIPE_WEBHOOK_SECRET", raising=False)
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
    # Other tests may setenv Soft Launch permanently; isolate this assertion.
    monkeypatch.delenv("SOFT_LAUNCH", raising=False)
    monkeypatch.setenv("SERVICE_MODE", "web")
    monkeypatch.setenv("SECRETS_MASTER_KEY", "k")
    monkeypatch.setenv("SESSION_TOKEN_PEPPER", "p")
    monkeypatch.setenv("ADMIN_API_KEY", "a")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)

    from production_guard import evaluate_production_guard

    report = evaluate_production_guard()
    ids = {c["id"]: c for c in report["checks"]}
    assert "billing_entitlement_webhook" in ids
    assert ids["billing_entitlement_webhook"]["ok"] is False


def test_telegram_webhook_requires_secret_in_prod():
    import api.routers.telegram as tg

    src = inspect.getsource(tg.telegram_webhook)
    assert "TELEGRAM_WEBHOOK_SECRET required in production" in src


def test_tv_webhook_uses_compare_digest():
    import platform_api

    src = inspect.getsource(platform_api.tv_webhook)
    assert "compare_digest" in src
    assert "TRADINGVIEW_WEBHOOK_SECRET required in production" in src


@pytest.fixture
def clean_chain_tr(tmp_path, monkeypatch):
    import oracle_audit_chain as chain

    path = tmp_path / "chain.jsonl"
    monkeypatch.setattr(chain, "CHAIN_PATH", path)
    return path
