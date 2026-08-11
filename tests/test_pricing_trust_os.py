"""Trust OS pricing ladder — Proof Pass / Decision Pro / Decision Desk $49 / Institutional."""

from __future__ import annotations


def test_pricing_catalog_four_depths():
    from pricing_catalog import pricing_catalog

    cat = pricing_catalog()
    assert cat["option"] == "A"
    assert cat["honesty"]["guaranteed_accuracy_claimed"] is False
    assert cat["honesty"]["no_fifteen_dollar_tier"] is True
    ids = [t["id"] for t in cat["tiers"]]
    assert ids == ["free", "pro", "whale", "institutional"]
    by_id = {t["id"]: t for t in cat["tiers"]}
    assert by_id["free"]["price_usd_month"] == 0
    assert by_id["free"]["name"] == "Proof Pass"
    assert by_id["free"]["limits"]["oracle_daily_limit"] == 3
    assert by_id["pro"]["price_usd_month"] == 29
    assert by_id["pro"]["name"] == "Decision Pro"
    assert by_id["pro"]["trial_days"] == 7
    assert by_id["whale"]["price_usd_month"] == 49
    assert by_id["whale"]["name"] == "Decision Desk"
    assert by_id["institutional"]["self_serve"] is False
    assert by_id["institutional"]["price_usd_month_from"] == 3000
    assert "open" in by_id["institutional"]["price_display"].lower()
    assert cat["integration_addendum"]
    assert len(cat["signup_plans"]) == 4
    assert "why_29_is_fair" in cat["value_equation"]


def test_option_a_upgrade_ladder_and_signup_next():
    from pricing_catalog import next_upgrade, normalize_signup_plan, signup_next_after_register

    free_up = next_upgrade("free")
    assert free_up["next_id"] == "pro"
    assert free_up["checkout_tier"] == "pro"
    pro_up = next_upgrade("pro")
    assert pro_up["next_id"] == "whale"
    whale_up = next_upgrade("whale")
    assert whale_up["next_id"] == "institutional"
    assert whale_up["checkout_tier"] is None
    assert next_upgrade("institutional")["has_upgrade"] is False

    assert normalize_signup_plan("decision_pro") == "pro"
    assert signup_next_after_register("free")["start_pro_trial"] is False
    assert signup_next_after_register("pro")["start_pro_trial"] is True
    assert signup_next_after_register("whale")["action"] == "checkout"
    assert signup_next_after_register("institutional")["action"] == "data_room"


def test_tier_features_proof_pass_limits():
    from auth_service import TIER_FEATURES

    free = TIER_FEATURES["free"]
    pro = TIER_FEATURES["pro"]
    whale = TIER_FEATURES["whale"]

    assert free["label"] == "Proof Pass"
    assert free["oracle_daily_limit"] == 3
    assert free["portfolio_ai"] is False
    assert free["proof_watermark"] is True
    assert free["b2b_api"] is False

    assert pro["label"] == "Decision Pro"
    assert pro["oracle_daily_limit"] is None
    assert pro["portfolio_ai"] is True
    assert pro["proof_watermark"] is False

    assert whale["label"] == "Decision Desk"
    assert whale["b2b_api"] is True
    assert whale["evidence_pack"] is True


def test_billing_self_serve_amounts():
    from billing_service import STRIPE_TIERS

    assert STRIPE_TIERS["pro"]["amount"] == 2900
    assert STRIPE_TIERS["pro"]["name"] == "Decision Pro"
    assert STRIPE_TIERS["whale"]["amount"] == 4900
    assert STRIPE_TIERS["whale"]["name"] == "Decision Desk"
    assert "essential" not in STRIPE_TIERS
    assert "institutional" not in STRIPE_TIERS


def test_free_certificate_has_watermark():
    from decision_certificate import build_decision_certificate

    free = build_decision_certificate(
        {
            "symbol": "BTC",
            "prediction_id": 7,
            "chain_hash": "abc",
            "decision_action": "ACT",
            "decision_sentence": "ACT on BTC.",
            "opportunity_score": 72,
            "tier": "free",
        }
    )
    assert free["watermark"] == "Free Proof"
    assert free["upgrade_cta"]
    assert "Free Proof" in free["share_text"]

    pro = build_decision_certificate(
        {
            "symbol": "BTC",
            "prediction_id": 7,
            "chain_hash": "abc",
            "decision_action": "ACT",
            "decision_sentence": "ACT on BTC.",
            "opportunity_score": 72,
            "tier": "pro",
        }
    )
    assert pro["watermark"] is None
    assert pro["upgrade_cta"] is None
    assert "Free Proof" not in pro["share_text"]
    assert free["certificate_hash"]
    assert pro["certificate_hash"]


def test_landing_pricing_copy():
    from pathlib import Path

    html = Path("templates/landing.html").read_text(encoding="utf-8")
    start = html.index('id="pricing"')
    pricing = html[start : start + 6500]
    # Names may be i18n keys after localization wiring; EN catalog still holds literals.
    from i18n_service import EN

    assert ("Proof Pass" in pricing) or ("pricing.proof_pass" in pricing)
    assert ("Decision Pro" in pricing) or ("pricing.decision_pro" in pricing)
    assert ("Decision Desk" in pricing) or ("pricing.decision_desk" in pricing)
    assert "$49" in pricing
    assert "$199" not in pricing
    assert ("Trust OS Institutional" in pricing) or ("pricing.institutional" in pricing)
    assert ("From $3,000" in pricing) or ("pricing.from_open" in pricing) or ("3,000" in EN.get("pricing.from_open", ""))
    assert "Essential" not in pricing
    assert "$15" not in pricing
    assert "Oracle 10×/day" not in pricing
    assert "institutionalInquiryForm" in pricing


def test_morning_binding_doc_locks_49():
    from pathlib import Path

    doc = Path("docs/MORNING_SESSION_FINAL_BINDING.md").read_text(encoding="utf-8")
    assert "$29" in doc
    assert "$49" in doc
    assert "$3,000" in doc
    assert "$199" not in doc
