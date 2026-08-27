"""Tests — #780+#783 Social Sentiment Intelligence, #781 Signal Attribution."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import market_radar_indicators as mri
from bd_platform import natural_language_interpreter as nli
from bd_platform import signal_attribution_layer as sal
from bd_platform import social_sentiment_intelligence as ssi


@pytest.fixture
def ssi_seed():
    return json.loads(Path("data/social_sentiment_intelligence_seed.json").read_text(encoding="utf-8"))


@pytest.fixture
def sal_seed():
    return json.loads(Path("data/signal_attribution_layer_seed.json").read_text(encoding="utf-8"))


@pytest.fixture
def mri_seed():
    return json.loads(Path("data/market_radar_indicators_seed.json").read_text(encoding="utf-8"))


@pytest.fixture
def nli_seed():
    return json.loads(Path("data/natural_language_interpreter_seed.json").read_text(encoding="utf-8"))


# --- #783 (absorbs #780) ---


def test_783_rule_based_no_nlp(ssi_seed):
    panel = ssi.build_sentiment_intelligence_panel_783("BTC", seed=ssi_seed)
    assert panel["ok"] is True
    assert panel["no_nlp_model"] is True
    assert panel["rule_based_only"] is True
    assert panel["duplicate_of_780_rejected"] is True


def test_783_rule_version_documented(ssi_seed):
    panel = ssi.build_sentiment_intelligence_panel_783("BTC", seed=ssi_seed)
    assert panel["rule_version_not_hideable"] is True
    assert "Sentiment Rule Set v1.0" in panel["rule_documentation"]
    assert "500 EN + 300 AR" in panel["rule_documentation"]
    assert "Last Updated:" in panel["rule_documentation"]


def test_783_confidence_tiers(ssi_seed):
    panel = ssi.build_sentiment_intelligence_panel_783("BTC", seed=ssi_seed)
    assert panel["mention_count"] >= 1000
    assert panel["confidence_pct"] == 90.0
    assert panel["confidence_tier"] == "Very High"


def test_783_structured_display(ssi_seed):
    panel = ssi.build_sentiment_intelligence_panel_783("BTC", seed=ssi_seed)
    assert "الأصل: BTC" in panel["display"]
    assert "الثقة:" in panel["display"]
    assert "منشن" in panel["display"]


def test_783_source_weighting_explicit(ssi_seed):
    panel = ssi.build_sentiment_intelligence_panel_783("BTC", seed=ssi_seed)
    sw = panel["source_weighting"]
    assert sw["tier1_weight"] == 3
    assert sw["tier2_weight"] == 1
    assert sw["explicit_in_response"] is True


def test_783_spam_bot_exclusion(ssi_seed):
    panel = ssi.build_sentiment_intelligence_panel_783("BTC", seed=ssi_seed)
    assert panel["spam_handling"]["bots_excluded"] > 0


def test_783_low_sample_insufficient(ssi_seed):
    panel = ssi.build_sentiment_intelligence_panel_783("LOW_SAMPLE", seed=ssi_seed)
    assert panel["sentiment_label"] == "Insufficient Data"
    assert panel["sentiment_score"] is None
    assert panel["insufficient_data"] is True


# --- #782 (merged into #783) ---


def test_782_balance_formula(ssi_seed):
    panel = ssi.build_sentiment_intelligence_panel_783("BTC", seed=ssi_seed)
    balance = panel["sentiment_balance_782"]
    assert balance["formula_documented"] is True
    assert "Positive_Weighted" in balance["formula"]
    assert balance["deterministic"] is True
    assert balance["no_ai_balance"] is True


def test_782_balance_range_and_band(ssi_seed):
    panel = ssi.build_sentiment_intelligence_panel_783("BTC", seed=ssi_seed)
    balance = panel["sentiment_balance_782"]
    assert -100 <= balance["balance_value"] <= 100
    assert balance["balance_band"] in ("Very Positive", "Positive", "Neutral", "Negative", "Very Negative")


def test_782_low_sample_na(ssi_seed):
    panel = ssi.build_sentiment_intelligence_panel_783("LOW_SAMPLE", seed=ssi_seed)
    balance = panel["sentiment_balance_782"]
    assert balance["balance_value"] == "N/A"
    assert balance["zero_sample_protected"] is True


def test_782_historical_bands_documented(ssi_seed):
    panel = ssi.build_sentiment_intelligence_panel_783("BTC", seed=ssi_seed)
    bands = panel["sentiment_balance_782"]["historical_bands"]
    assert len(bands) == 5
    assert any(b["band"] == "Neutral" for b in bands)


def test_782_market_radar_balance_widget(ssi_seed):
    widget = ssi.build_market_radar_sentiment_balance_widget_782("BTC", seed=ssi_seed)
    assert widget["widget_ar"] == "مؤشر التوازن المزاجي"


def test_782_asset_card_sparkline(ssi_seed):
    card = ssi.build_asset_card_balance_sparkline_782("BTC", seed=ssi_seed)
    assert card["tab_ar"] == "التوازن"
    assert len(card["sparkline"]) >= 5
    assert card["range"] == [-100, 100]


def test_783_asset_card_badge(ssi_seed):
    badge = ssi.build_asset_card_sentiment_badge_783("BTC", seed=ssi_seed)
    assert badge["badge_ar"] == "المزاج السائد"
    assert badge["confidence_pct"] is not None


def test_783_sentiment_label_and_trend(ssi_seed):
    panel = ssi.build_sentiment_intelligence_panel_783("BTC", seed=ssi_seed)
    assert panel["sentiment_label"] in ("Positive", "Neutral", "Negative")
    assert panel["sentiment_trend"] in ("rising", "falling", "flat")


def test_783_market_radar_overlay(ssi_seed):
    overlay = ssi.build_market_radar_sentiment_overlay_783("BTC", seed=ssi_seed)
    assert overlay["widget_ar"] == "التحليل المزاجي"
    assert overlay["surface"] == "market_radar"


def test_783_market_radar_panel_integration(mri_seed):
    panel = mri.build_market_radar_panel("binance", "BTC", seed=mri_seed)
    assert panel["sentiment_intelligence_783"]["ok"] is True


def test_783_multilingual_qa(ssi_seed):
    panel = ssi.build_sentiment_intelligence_panel_783("BTC", seed=ssi_seed)
    qa = panel["multilingual_qa"]
    assert "EN" in qa["languages_tested"]
    assert "AR" in qa["languages_tested"]
    assert qa["ar_accuracy_pct"] >= qa["ar_min_accuracy_pct"]
    assert qa["qa_passed"] is True


def test_783_evidence_middleware(ssi_seed):
    panel = ssi.build_sentiment_intelligence_panel_783("BTC", seed=ssi_seed)
    assert "evidence_confidence_777" in panel


def test_783_qa_suite(ssi_seed):
    qa = ssi.run_sentiment_intelligence_qa_783(seed=ssi_seed)
    assert qa["all_passed"] is True


# --- #781 ---


def test_781_attribution_panel_ok(sal_seed):
    panel = sal.build_signal_attribution_panel_781("BTC", seed=sal_seed)
    assert panel["ok"] is True
    assert panel["no_generic_text"] is True
    assert panel["no_ml_explanation"] is True


def test_781_contributing_metrics_timestamped(sal_seed):
    panel = sal.build_signal_attribution_panel_781("BTC", seed=sal_seed)
    metrics = panel["contributing_metrics"]
    assert len(metrics) >= 2
    for m in metrics:
        assert "metric" in m
        assert "timestamp" in m
        assert m.get("value") is not None or m.get("trend_label")


def test_781_no_generic_phrases(sal_seed):
    panel = sal.build_signal_attribution_panel_781("BTC", seed=sal_seed)
    text = " ".join(panel["attribution_reasons"]).lower()
    assert "the market looks bullish" not in text
    assert "ai reasoning" not in text


def test_781_rule_reasoning_visible(sal_seed):
    panel = sal.build_signal_attribution_panel_781("BTC", seed=sal_seed)
    assert panel["rule_version_visible"] is True
  # At least one reason should contain actual RSI value or MACD data
    reasons = " ".join(panel["attribution_reasons"])
    assert "RSI" in reasons or "MACD" in reasons


def test_781_signal_card_panel(sal_seed):
    card = sal.build_signal_card_attribution_panel_781("BTC", seed=sal_seed)
    assert card["panel_title_ar"] == "لماذا هذه الإشارة؟"
    assert card["expandable"] is True


def test_781_asset_card_panel(sal_seed):
    card = sal.build_asset_card_attribution_details_781("BTC", seed=sal_seed)
    assert card["tab_ar"] == "تفاصيل التحليل"


def test_781_evidence_attached(sal_seed):
    panel = sal.build_signal_attribution_panel_781("BTC", seed=sal_seed)
    assert "evidence_confidence_777" in panel


def test_781_chat_integration(nli_seed):
    data = sal.build_attribution_data_for_chat_781("BTC")
    assert data["integration"] == "natural_language_interpreter_766_771"
    assert data["no_generic_text"] is True


def test_781_explain_signal_uses_attribution(nli_seed):
    explanation = nli.build_explain_signal_explanation_771("BTC", user_tier="pro", seed=nli_seed)
    assert explanation["ok"] is True
    assert explanation.get("attribution_781") is not None
    assert any("Signal Attribution" in (e.get("metric") or "") for e in explanation["evidence"])


def test_781_qa_suite(sal_seed):
    qa = sal.run_signal_attribution_qa_781(seed=sal_seed)
    assert qa["all_passed"] is True


def test_781_api_routes():
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/intelligence-ledger/signals/attribution/status").status_code == 200
    resp = c.get("/api/platform/intelligence-ledger/signals/attribution?asset=BTC")
    assert resp.status_code == 200
    assert resp.json()["no_generic_text"] is True


def test_783_api_routes():
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/intelligence-ledger/market-radar/sentiment/status").status_code == 200
    resp = c.get("/api/platform/intelligence-ledger/market-radar/sentiment?asset=BTC")
    assert resp.status_code == 200
    assert resp.json()["no_nlp_model"] is True
