"""Tests — #908 Pay-Per-Request Data Access (Stripe metered billing)."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from billing import stripe_pay_per_request as ppr


@pytest.fixture
def ppr_seed() -> dict:
    return json.loads(Path("data/stripe_pay_per_request_seed.json").read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def reset_state():
    ppr.reset_pay_per_request_state_908()
    yield
    ppr.reset_pay_per_request_state_908()


def test_908_status(ppr_seed):
    status = ppr.pay_per_request_status_908(seed=ppr_seed)
    assert status["standalone_rejected"] is True
    assert status["gateway"] == "stripe"
    assert status["no_separate_gateway"] is True
    assert status["stripe_metered_billing"] is True
    assert status["transparent_pricing"] is True
    assert status["audit_retention_years"] == 2


def test_908_pricing_catalog(ppr_seed):
    catalog = ppr.get_endpoint_pricing_catalog_908(seed=ppr_seed)
    assert catalog["no_hidden_fees"] is True
    assert catalog["endpoint_count"] >= 6
    for ep in catalog["endpoints"]:
        assert ep["transparent"] is True
        assert ep["hidden_fees"] is False
        assert "price_usd" in ep


def test_908_charge_and_receipt(ppr_seed):
    result = ppr.charge_pay_per_request_908(
        user_id="user_pro_002",
        tier="pro",
        endpoint_id="market_overview",
        idempotency_key="idem-001",
        nonce="nonce-001",
        seed=ppr_seed,
    )
    assert result["ok"] is True
    assert result["receipt_id"]
    assert result["stripe_metered_event"]["type"] == "metered_usage"
    assert result["fee_db"]["margin_usd"] >= 0
    assert result["audit"]["user_id"] == "user_pro_002"


def test_908_idempotent_billing(ppr_seed):
    args = dict(
        user_id="user_pro_002",
        tier="pro",
        endpoint_id="onchain_metrics",
        idempotency_key="idem-same",
        nonce="nonce-a",
        seed=ppr_seed,
    )
    first = ppr.charge_pay_per_request_908(**args)
    second = ppr.charge_pay_per_request_908(**{**args, "nonce": "nonce-b"})
    assert first["receipt_id"] == second["receipt_id"]
    assert second["duplicate_charge_prevented"] is True


def test_908_replay_protection(ppr_seed):
    ok = ppr.charge_pay_per_request_908(
        user_id="user_pro_002",
        tier="pro",
        endpoint_id="risk_protocol",
        idempotency_key="idem-r1",
        nonce="nonce-replay",
        seed=ppr_seed,
    )
    assert ok["ok"] is True

    blocked = ppr.charge_pay_per_request_908(
        user_id="user_pro_002",
        tier="pro",
        endpoint_id="risk_protocol",
        idempotency_key="idem-r2",
        nonce="nonce-replay",
        seed=ppr_seed,
    )
    assert blocked["replay_rejected"] is True


def test_908_timestamp_window(ppr_seed):
    stale = (datetime.now(UTC) - timedelta(minutes=10)).isoformat()
    result = ppr.charge_pay_per_request_908(
        user_id="user_pro_002",
        tier="pro",
        endpoint_id="sla_metrics",
        idempotency_key="idem-stale",
        nonce="nonce-stale",
        request_timestamp=stale,
        seed=ppr_seed,
    )
    assert result["replay_rejected"] is True


def test_908_tier_limits(ppr_seed):
    status = ppr.pay_per_request_status_908(seed=ppr_seed)
    limits = status["tier_limits_per_day"]
    assert limits["free"] == 100
    assert limits["pro"] == 10000
    assert limits["institution"] is None


def test_908_webhook_balance(ppr_seed):
    result = ppr.charge_pay_per_request_908(
        user_id="user_inst_003",
        tier="institution",
        endpoint_id="audit_export",
        idempotency_key="idem-wh",
        nonce="nonce-wh",
        seed=ppr_seed,
    )
    assert result["webhook_balance_update"]["immediate"] is True
    assert result["webhook_balance_update"]["no_delay"] is True


def test_908_e2e(ppr_seed):
    e2e = ppr.run_pay_per_request_e2e_908(seed=ppr_seed)
    assert e2e["all_passed"] is True
