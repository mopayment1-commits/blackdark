"""Tests — Single-Sentence Financial Oracle (#125) + Monetization Tiers (#126)."""

from __future__ import annotations

import pytest

from bd_platform.monetization_tiers_core import (
    TIER_ENTITLEMENTS,
    entitlements_for_commercial_tier,
    monetization_catalog,
    resolve_ab_variant,
)
from bd_platform.single_sentence_financial_oracle import (
    MANDATORY_DISCLAIMER,
    _pick_single_reason,
    _score_to_analysis,
    oracle_feature_status,
)


def test_score_to_analysis_labels():
    assert _score_to_analysis(80, "BUY") == "Bullish"
    assert _score_to_analysis(30, "SELL") == "Bearish"
    assert _score_to_analysis(55, "WAIT") == "Neutral"


def test_pick_single_reason_always_returns_data():
    reason_en, reason_ar = _pick_single_reason(
        asset="BTC",
        change_24h=-5.2,
        quote_volume=2_000_000_000,
        hub_reasons=[],
        funding_rate_pct=0.05,
    )
    assert reason_en
    assert reason_ar
    assert "5.2" in reason_en or "2.0B" in reason_en or "funding" in reason_en.lower()


def test_mandatory_disclaimer_present():
    status = oracle_feature_status()
    assert status["disclaimer_mandatory"] is True
    assert "DYOR" in MANDATORY_DISCLAIMER
    assert "توصية مالية" in MANDATORY_DISCLAIMER


def test_monetization_three_tiers():
    cat = monetization_catalog(variant="A")
    assert cat["tier_count"] == 3
    ids = [t["id"] for t in cat["tiers"]]
    assert ids == ["free", "pro", "institution"]
    pro = next(t for t in cat["tiers"] if t["id"] == "pro")
    inst = next(t for t in cat["tiers"] if t["id"] == "institution")
    assert pro["price_usd_month"] == 29
    assert inst["price_usd_month"] == 199


def test_free_tier_entitlements():
    ent = TIER_ENTITLEMENTS["free"]
    assert ent["oracle_daily_limit"] == 3
    assert ent["market_radar_delay_minutes"] == 15
    assert ent["alerts_max"] == 3


def test_pro_tier_entitlements():
    ent = TIER_ENTITLEMENTS["pro"]
    assert ent["oracle_daily_limit"] is None
    assert ent["market_radar_realtime"] is True
    assert ent["alerts_max"] == 10
    assert ent["portfolio_ai"] is True


def test_institution_tier_entitlements():
    ent = TIER_ENTITLEMENTS["institution"]
    assert ent["api_access"] is True
    assert ent["onchain_intelligence"] is True
    assert ent["white_label_reports"] is True


def test_ab_variant_deterministic():
    assert resolve_ab_variant(email="test@example.com") == resolve_ab_variant(email="test@example.com")
    assert resolve_ab_variant(email="a@x.com") in {"A", "B"}


def test_ab_variant_b_pricing():
    cat = monetization_catalog(variant="B")
    pro = next(t for t in cat["tiers"] if t["id"] == "pro")
    assert pro["price_usd_month"] == 24.99


def test_canonical_mapping():
    ent = entitlements_for_commercial_tier("elite")
    assert ent["canonical_plan"] == "elite"


@pytest.mark.asyncio
async def test_single_sentence_oracle_live(monkeypatch):
    from bd_platform.single_sentence_financial_oracle import query_single_sentence_oracle

    async def _fake_quota(_user):
        return True, "ok"

    monkeypatch.setattr("auth_service.check_oracle_quota", _fake_quota)

    result = await query_single_sentence_oracle("BTC", user={"tier": "pro", "email": "test@test.com"})
    assert result["ok"] is True
    assert result["feature_id"] == 125
    assert result["analysis"] in {"Bullish", "Neutral", "Bearish"}
    assert result["confidence_percent"] >= 0
    assert result["reason"]
    assert result["disclaimer_mandatory"] is True
    assert "Buy Now" not in result["sentence"]
    assert "اشتر" not in result["sentence"]
    assert "sla_met" in result
