"""Stripe TEST cycle drill: secret-free receipts; FAIL closed without a valid TEST key."""

from __future__ import annotations

import json
from types import SimpleNamespace


def test_stripe_cycle_fail_closed_on_rejected_key(monkeypatch, tmp_path):
    monkeypatch.setenv("STRIPE_TEST_EVIDENCE_PATH", str(tmp_path / "stripe.json"))
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_dummyplaceholder0000000000")
    monkeypatch.setenv("STRIPE_PRICE_PRO", "price_dummyplaceholder000")
    from launch_drills import drill_stripe_sandbox

    row = drill_stripe_sandbox()
    assert row["id"] == "stripe_sandbox"
    assert row["verdict"] == "FAIL"
    assert row["verdict"] != "NOT_TESTED"
    blob = json.dumps(row)
    assert "sk_test_dummyplaceholder0000000000" not in blob
    assert "price_dummyplaceholder000" not in blob
    stamped = json.loads((tmp_path / "stripe.json").read_text(encoding="utf-8"))
    assert stamped["verdict"] == "FAIL"
    assert "sk_test_dummy" not in json.dumps(stamped)


def test_stripe_cycle_refuses_live_key(monkeypatch, tmp_path):
    monkeypatch.setenv("STRIPE_TEST_EVIDENCE_PATH", str(tmp_path / "stripe.json"))
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_live_" + ("x" * 24))
    monkeypatch.setenv("STRIPE_PRICE_PRO", "price_1234567890abcdef")
    from billing_service import prove_stripe_test_cycle

    receipt = prove_stripe_test_cycle()
    assert receipt["ok"] is False
    assert receipt["reason"] == "sk_live_refused"
    assert "xxxxxxxx" not in json.dumps(receipt)


def test_stripe_cycle_pass_on_mocked_subscription(monkeypatch, tmp_path):
    monkeypatch.setenv("STRIPE_TEST_EVIDENCE_PATH", str(tmp_path / "stripe.json"))
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_" + ("a" * 24))
    monkeypatch.setenv("STRIPE_PRICE_PRO", "price_1TestProPrice00000")

    class _Acct:
        livemode = False
        id = "acct_test"

    class _Price:
        livemode = False
        type = "recurring"
        recurring = SimpleNamespace(interval="month")
        active = True
        id = "price_1TestProPrice00000"

    class _Session:
        id = "cs_test_checkout1"
        url = "https://checkout.stripe.com/c/pay/cs_test_checkout1"
        mode = "subscription"

    class _Customer:
        id = "cus_testprobe1"

    class _PM:
        id = "pm_testvisa1"

    class _Sub:
        def __init__(self, status="active"):
            self.id = "sub_testprobe1"
            self.status = status

    class _Stripe:
        api_key = ""

        class Account:
            @staticmethod
            def retrieve():
                return _Acct()

        class Price:
            @staticmethod
            def retrieve(_pid):
                return _Price()

        class checkout:
            class Session:
                @staticmethod
                def create(**_k):
                    return _Session()

                @staticmethod
                def retrieve(_sid):
                    return _Session()

                @staticmethod
                def expire(_sid):
                    return SimpleNamespace(status="expired")

        class Customer:
            @staticmethod
            def create(**_k):
                return _Customer()

            @staticmethod
            def modify(*_a, **_k):
                return _Customer()

            @staticmethod
            def delete(_cid):
                return SimpleNamespace(deleted=True)

        class PaymentMethod:
            @staticmethod
            def create(**_k):
                return _PM()

            @staticmethod
            def attach(_pid, customer=None):
                return _PM()

        class Subscription:
            @staticmethod
            def create(**_k):
                return _Sub("active")

            @staticmethod
            def cancel(_sid):
                return _Sub("canceled")

    import billing_service as bs

    monkeypatch.setattr(bs, "stripe", _Stripe)
    from launch_drills import drill_stripe_sandbox

    row = drill_stripe_sandbox()
    assert row["verdict"] == "PASS", row
    assert str(row.get("checkout_session_prefix") or "").startswith("cs_")
    assert str(row.get("subscription_prefix") or "").startswith("sub_")
    assert row.get("subscription_canceled") is True
    blob = json.dumps(row)
    assert "sk_test_aaaaaaaa" not in blob
    assert "price_1TestProPrice00000" not in blob
    from billing_service import stripe_test_cycle_proved

    assert stripe_test_cycle_proved() is True
