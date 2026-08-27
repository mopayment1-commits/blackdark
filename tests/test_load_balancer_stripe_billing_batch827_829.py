"""Tests — #827 Infrastructure Load Balancer + #829 Stripe Multi-Currency Billing."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import infrastructure_load_balancer as lb
from billing import stripe_multi_currency_billing as mcb


@pytest.fixture
def lb_seed() -> dict:
    return json.loads(Path("data/infrastructure_load_balancer_seed.json").read_text(encoding="utf-8"))


@pytest.fixture
def mcb_seed() -> dict:
    return json.loads(Path("data/stripe_multi_currency_billing_seed.json").read_text(encoding="utf-8"))


# --- #827 ---


def test_827_status(lb_seed):
    status = lb.load_balancer_status_827(seed=lb_seed)
    assert status["standalone_rejected"] is True
    assert status["cdn_provider"] == "cloudflare"
    assert status["reverse_proxy"] == "nginx"
    assert status["auto_remove_failed_instances"] is True
    assert status["no_user_surface"] is True


def test_827_health_pool_auto_remove(lb_seed):
    pool = lb.reconcile_backend_pool_827(seed=lb_seed)
    assert pool["ok"] is True
    assert "web-03" in pool["removed_instances"]
    assert "web-01" in pool["active_instances"]
    assert pool["auto_remove_failed"] is True


def test_827_cdn_and_nginx(lb_seed):
    panel = lb.build_load_balancer_panel_827(seed=lb_seed)
    assert panel["cdn"]["static_asset_caching"] is True
    assert panel["reverse_proxy"]["provider"] == "nginx"
    assert panel["reverse_proxy"]["algorithm"] == "least_conn"


def test_827_internal_targets(lb_seed):
    panel = lb.build_load_balancer_panel_827(seed=lb_seed)
    targets = panel["internal_targets"]
    assert targets["internal_only"] is True
    assert targets["within_response_target"] is True
    assert targets["within_uptime_target"] is True


def test_827_e2e(lb_seed):
    e2e = lb.run_load_balancer_e2e_827(seed=lb_seed)
    assert e2e["all_passed"] is True


# --- #829 ---


def test_829_status(mcb_seed):
    status = mcb.stripe_multi_currency_status_829(seed=mcb_seed)
    assert status["standalone_rejected"] is True
    assert status["gateway"] == "stripe"
    assert status["no_separate_ui"] is True
    assert status["multi_currency_via_stripe"] is True
    assert status["crypto_payments_deferred"] is True


def test_829_stripe_no_separate_gateway(mcb_seed):
    config = mcb.build_stripe_billing_config_829(seed=mcb_seed)
    assert config["no_separate_gateway"] is True
    assert config["checkout_surface"] == "stripe_checkout"
    assert config["multi_currency"]["stripe_handles_conversion"] is True


def test_829_supported_currencies(mcb_seed):
    config = mcb.build_stripe_billing_config_829(seed=mcb_seed)
    currencies = config["multi_currency"]["supported_currencies"]
    assert "USD" in currencies
    assert "EUR" in currencies
    assert config["multi_currency"]["stripe_currency_count"] >= 135


def test_829_crypto_deferred(mcb_seed):
    config = mcb.build_stripe_billing_config_829(seed=mcb_seed)
    crypto = config["crypto_payments"]
    assert crypto["enabled"] is False
    assert crypto["deferred"] is True


def test_829_checkout_options(mcb_seed):
    checkout = mcb.build_checkout_currency_options_829("pro", seed=mcb_seed)
    assert checkout["gateway"] == "stripe"
    assert len(checkout["currency_options"]) >= 3
    assert checkout["no_separate_ui"] is True


def test_829_fee_db(mcb_seed):
    config = mcb.build_stripe_billing_config_829(seed=mcb_seed)
    fee = config["fee_db"]
    assert "stripe_fee_pct" in fee
    assert "fx_fee_pct" in fee


def test_829_e2e(mcb_seed):
    e2e = mcb.run_stripe_multi_currency_e2e_829(seed=mcb_seed)
    assert e2e["all_passed"] is True


def test_829_billing_api_routes():
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/billing/multi-currency/status").status_code == 200
    config = c.get("/api/billing/multi-currency/config")
    assert config.status_code == 200
    assert config.json()["gateway"] == "stripe"
    e2e = c.get("/api/billing/multi-currency/e2e")
    assert e2e.status_code == 200
    assert e2e.json()["all_passed"] is True
