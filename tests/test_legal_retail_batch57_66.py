"""Tests — Legal & Commercial (#57–#61) + Retail Intelligence (#62–#66)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import legal_commercial_layer as legal
from bd_platform import retail_intelligence_layer as retail


@pytest.fixture
def seed() -> dict:
    return json.loads(Path("data/legal_retail_commercial_seed.json").read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def reset(seed):
    legal.reset_legal_commercial_state()
    retail.reset_retail_intelligence_state()
    yield
    legal.reset_legal_commercial_state()
    retail.reset_retail_intelligence_state()


# ─── #57 Service Disclosure ───────────────────────────────────────────────────


def test_57_disclosure_text(seed):
    status = legal.service_disclosure_status_57(seed=seed)
    assert status["standalone"] is False
    assert "analytical tool" in status["disclosure_text"]["en"].lower()


def test_57_api_attach(seed):
    payload = legal.attach_service_disclosure_57({"ok": True}, seed=seed)
    assert "service_disclosure" in payload
    assert payload["service_disclosure"]["not_licensed_advisory"] is True


# ─── #58 GDPR ─────────────────────────────────────────────────────────────────


def test_58_consent_and_erasure(seed):
    consent = legal.record_gdpr_consent_58(user_email="a@b.com", seed=seed)
    assert consent["ok"] is True
    erasure = legal.request_erasure_58(user_email="a@b.com", confirmed=True, seed=seed)
    assert erasure["ok"] is True
    assert erasure["erasure"]["grace_days"] == 30


def test_58_eu_detection(seed):
    assert legal.is_eu_user_58(country="FR") is True
    assert legal.is_eu_user_58(country="US") is False


# ─── #59 AML ──────────────────────────────────────────────────────────────────


def test_59_aml_threshold(seed):
    ok = legal.evaluate_aml_gate_59(amount_usd=100.0, email="ok@test.com", seed=seed)
    assert ok["allowed"] is True
    blocked = legal.evaluate_aml_gate_59(amount_usd=600.0, email="sanctioned@test.com", seed=seed)
    assert blocked["allowed"] is False


# ─── #60 Subscription Tiers ───────────────────────────────────────────────────


def test_60_tier_limits(seed):
    free = legal.get_tier_limits_60("free", seed=seed)
    assert free["api_calls_per_day"] == 10
    pro = legal.get_tier_limits_60("pro", seed=seed)
    assert pro["api_calls_per_day"] == 500


# ─── #61 Payment Security ─────────────────────────────────────────────────────


def test_61_no_card_storage(seed):
    pci = legal.assert_no_card_storage_61()
    assert pci["stores_card_data"] is False


# ─── #62 Daily Top 3 ──────────────────────────────────────────────────────────


def test_62_daily_top3(seed):
    result = retail.build_daily_top3_62(seed=seed)
    assert result["count"] == 3
    assert all(o.get("no_execution") for o in result["opportunities"])


# ─── #63 One Clear Answer ─────────────────────────────────────────────────────


def test_63_clear_answer(seed):
    answer = retail.build_one_clear_answer_63(
        verdict="Risk",
        reasons=[{"point": "High volatility"}, {"point": "Low liquidity"}],
        risk_score=8.0,
        seed=seed,
    )
    assert answer["verdict"] == "Risk"
    assert len(answer["reasons"]) <= 3


# ─── #64 Simple Language ────────────────────────────────────────────────────────


def test_64_glossary(seed):
    manifest = retail.glossary_manifest_64()
    assert manifest["count"] >= 3
    rsi = retail.simplify_term_64("RSI")
    assert "simple" in rsi


# ─── #65 Contextual Alerts ──────────────────────────────────────────────────────


def test_65_contextual_alert(seed):
    fired = retail.evaluate_contextual_alert_65(
        price=50000, opportunity_level=8.5, volume_zscore=2.0, seed=seed
    )
    assert fired["alert_fired"] is True
    assert fired["alert"]["no_auto_action"] is True


# ─── #66 Discipline ───────────────────────────────────────────────────────────


def test_66_discipline_comparison(seed):
    result = retail.compare_discipline_66(
        user_action="bought",
        user_price=100.0,
        system_verdict="Opportunity",
        system_price=95.0,
        seed=seed,
    )
    assert result["comparison"]["non_custodial"] is True


# ─── E2E ──────────────────────────────────────────────────────────────────────


def test_legal_commercial_e2e(seed):
    assert legal.run_legal_commercial_e2e_57_61(seed=seed)["all_passed"] is True


def test_retail_intelligence_e2e(seed):
    assert retail.run_retail_intelligence_e2e_62_66(seed=seed)["all_passed"] is True
