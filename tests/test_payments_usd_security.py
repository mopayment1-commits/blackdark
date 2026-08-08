"""USD payments architecture + PCI posture + webhook idempotency."""

from __future__ import annotations

import asyncio


def test_payments_architecture_usd_no_pan():
    from payments_usd import BILLING_CURRENCY, payments_architecture, refund_policy_public

    assert BILLING_CURRENCY == "usd"
    arch = payments_architecture()
    assert arch["currency"] == "USD"
    assert arch["security"]["stores_pan"] is False
    assert arch["security"]["stores_cvv"] is False
    assert arch["security"]["pci_target"] == "SAQ_A"
    assert arch["self_serve_skus"]["pro"]["amount_usd"] == 29
    assert arch["self_serve_skus"]["whale"]["amount_usd"] == 199
    assert arch["institutional"]["self_serve"] is False
    assert "card" in {m["id"] for m in arch["payment_methods_launch"]}
    refund = refund_policy_public()
    assert refund["currency"] == "USD"
    assert refund["legal_page"] == "/refund"


def test_billing_tiers_currency_usd():
    from billing_service import BILLING_CURRENCY, STRIPE_TIERS

    assert BILLING_CURRENCY == "usd"
    assert STRIPE_TIERS["pro"]["currency"] == "usd"
    assert STRIPE_TIERS["whale"]["amount"] == 19900


def test_pricing_catalog_currency():
    from pricing_catalog import pricing_catalog

    assert pricing_catalog()["currency"] == "USD"


def test_refund_legal_page():
    from legal_content import LEGAL_PAGES

    assert "refund" in LEGAL_PAGES
    assert "USD" in LEGAL_PAGES["refund"]["html"]


def test_stripe_webhook_idempotent(tmp_path, monkeypatch):
    import database
    from billing_service import handle_stripe_webhook_event

    monkeypatch.setattr(database.config, "DB_PATH", str(tmp_path / "pay.db"))

    async def _run():
        await database.init_db()
        event = {
            "id": "evt_test_dup_1",
            "type": "invoice.payment_failed",
            "data": {"object": {"subscription": "sub_x"}},
        }
        first = await handle_stripe_webhook_event(event)
        second = await handle_stripe_webhook_event(event)
        assert first.get("action") == "payment_failed"
        assert second.get("action") == "duplicate_ignored"

    asyncio.run(_run())


def test_lemon_signature_verification(monkeypatch):
    import hashlib
    import hmac

    from billing_service import verify_lemon_webhook_signature

    secret = "test_lemon_secret"
    body = b'{"meta":{"event_name":"subscription_created"}}'
    monkeypatch.setenv("LEMON_SQUEEZY_WEBHOOK_SECRET", secret)
    sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    assert verify_lemon_webhook_signature(body, sig) is True
    assert verify_lemon_webhook_signature(body, "deadbeef") is False


def test_setup_script_exists():
    from pathlib import Path

    assert Path("scripts/setup_payments_usd.py").is_file()
    assert Path("docs/PAYMENTS_USD_SECURITY.md").is_file()
