"""Trust OS pricing ladder — FREE / PRO / ELITE / QUANT / INSTITUTIONAL."""

from __future__ import annotations


def test_pricing_catalog_five_official_tiers():
    from pricing_catalog import pricing_catalog

    cat = pricing_catalog()
    assert cat["option"] == "B"
    assert cat["honesty"]["guaranteed_accuracy_claimed"] is False
    ids = [t["id"] for t in cat["tiers"]]
    assert ids == ["free", "pro", "elite", "quant", "institutional"]
    by_id = {t["id"]: t for t in cat["tiers"]}
    assert by_id["free"]["price_usd_month"] == 0
    assert by_id["pro"]["price_usd_month"] == 19.99
    assert by_id["pro"]["trial_days"] == 7
    assert by_id["elite"]["price_usd_month"] == 49.99
    assert by_id["elite"]["trial_days"] == 7
    assert by_id["quant"]["price_usd_month"] == 149.99
    assert by_id["quant"]["trial_days"] == 7
    assert by_id["institutional"]["self_serve"] is False
    assert by_id["institutional"]["price_usd_month_from"] == 999
    assert len(cat["signup_plans"]) == 5


def test_option_b_upgrade_ladder_and_signup_next():
    from pricing_catalog import next_upgrade, normalize_signup_plan, signup_next_after_register

    free_up = next_upgrade("free")
    assert free_up["next_id"] == "pro"
    pro_up = next_upgrade("pro")
    assert pro_up["next_id"] == "elite"
    elite_up = next_upgrade("elite")
    assert elite_up["next_id"] == "quant"
    quant_up = next_upgrade("quant")
    assert quant_up["next_id"] == "institutional"
    assert next_upgrade("institutional")["has_upgrade"] is False

    assert normalize_signup_plan("whale") == "elite"
    assert normalize_signup_plan("decision_pro") == "pro"
    assert signup_next_after_register("free")["start_paid_trial"] is False
    assert signup_next_after_register("pro")["start_paid_trial"] is True
    assert signup_next_after_register("elite")["start_paid_trial"] is True
    assert signup_next_after_register("quant")["action"] == "paid_trial"
    assert signup_next_after_register("institutional")["action"] == "data_room"


def test_tier_features_official_labels():
    from auth_service import TIER_FEATURES, normalize_tier

    assert TIER_FEATURES["free"]["label"] == "FREE"
    assert TIER_FEATURES["pro"]["label"] == "PRO"
    assert TIER_FEATURES["elite"]["label"] == "ELITE"
    assert TIER_FEATURES["quant"]["label"] == "QUANT"
    assert TIER_FEATURES["institutional"]["label"] == "INSTITUTIONAL"
    assert normalize_tier("whale") == "elite"
    assert TIER_FEATURES["free"]["oracle_daily_limit"] == 3
    assert TIER_FEATURES["pro"]["portfolio_ai"] is True
    assert TIER_FEATURES["elite"]["b2b_api"] is True
    assert TIER_FEATURES["quant"]["quant_backtest"] is True


def test_billing_self_serve_amounts():
    from billing_service import STRIPE_TIERS

    assert STRIPE_TIERS["pro"]["amount"] == 1999
    assert STRIPE_TIERS["elite"]["amount"] == 4999
    assert STRIPE_TIERS["quant"]["amount"] == 14999
    assert STRIPE_TIERS["whale"]["amount"] == 4999
    assert "institutional" not in STRIPE_TIERS
