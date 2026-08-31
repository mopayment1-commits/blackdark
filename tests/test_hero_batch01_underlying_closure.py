"""Independent underlying-unit tests for hero batch-01 WRAPPER-ONLY closure (#629 priority).

These tests exercise the *underlying* modules/functions directly — not hero wrappers.
Required for retrospective deep-audit VERIFIED-DEEP classification.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

SEED = json.loads(Path("data/legal_retail_commercial_seed.json").read_text(encoding="utf-8"))


# ─── #629 Oracle hero (absolute priority) ─────────────────────────────────────


def test_629_compliant_oracle_sentence_neutral_live():
    from regulatory_compliance_guard import (
        PUBLIC_VERDICT_NEUTRAL,
        compliant_oracle_sentence,
    )

    sentence = compliant_oracle_sentence("BTC", "NEUTRAL", "Funding neutral; volume stable")
    assert "BTC" in sentence
    assert PUBLIC_VERDICT_NEUTRAL in sentence
    assert "monitoring signal" in sentence.lower() or "not investment advice" in sentence.lower()
    assert "Buy Now" not in sentence


def test_629_compliant_oracle_sentence_sanitizes_buy_now():
    from regulatory_compliance_guard import compliant_oracle_sentence, to_public_verdict

    sentence = compliant_oracle_sentence("ETH", "BUY", "Buy Now at resistance breakout")
    assert to_public_verdict("BUY") in sentence
    assert "Buy Now" not in sentence


@pytest.mark.asyncio
async def test_629_live_execute_capability():
    from pdf_capability_registry import execute_capability

    result = await execute_capability(629)
    assert result["ok"] is True
    assert "regulatory_compliance_guard" in str(result.get("binding", ""))


# ─── #2 / #330 trade_simulator.simulate_spot_trade ────────────────────────────


@pytest.mark.asyncio
async def test_2_simulate_spot_trade_underlying(monkeypatch):
    from trade_simulator import simulate_spot_trade

    async def fake_ticker(pair: str):
        return {"price": 50_000.0, "change_24h": 1.5}

    monkeypatch.setattr("trade_simulator._fetch_ticker", fake_ticker)
    monkeypatch.setattr("trade_simulator._fee_usd", lambda n, **_: n * 0.001)

    out = await simulate_spot_trade("BTC", "buy", 1000.0)
    assert out["symbol"] == "BTC"
    assert out["entry_price"] == 50_000.0
    assert "scenarios" in out


@pytest.mark.asyncio
async def test_330_simulate_spot_trade_underlying(monkeypatch):
    from trade_simulator import simulate_spot_trade

    async def fake_ticker(pair: str):
        return {"price": 3200.0, "change_24h": -0.5}

    monkeypatch.setattr("trade_simulator._fetch_ticker", fake_ticker)
    monkeypatch.setattr("trade_simulator._fee_usd", lambda n, **_: n * 0.001)

    out = await simulate_spot_trade("ETH", "sell", 500.0)
    assert out["symbol"] == "ETH"
    assert out["side"] == "sell"


# ─── #10 instant_alert_engine.engine_stats ────────────────────────────────────


def test_10_engine_stats_underlying():
    from instant_alert_engine import engine_stats

    stats = engine_stats()
    assert "enabled" in stats
    assert "interval_sec" in stats
    assert isinstance(stats["running"], bool)


# ─── #13 / #27 / #30 / #37 pro_trader_layer.evaluate_flexible_alert_75 ────────


def test_13_evaluate_flexible_alert_75_underlying():
    from bd_platform.pro_trader_layer import evaluate_flexible_alert_75

    out = evaluate_flexible_alert_75(user_tier="pro", alerts_sent_today=0, seed=SEED)
    assert out["ok"] is True
    assert out["allowed"] is True
    assert out["feature_ref"] == 75


def test_27_evaluate_flexible_alert_75_free_limit():
    from bd_platform.pro_trader_layer import evaluate_flexible_alert_75

    out = evaluate_flexible_alert_75(user_tier="free", alerts_sent_today=99, seed=SEED)
    assert out["ok"] is False
    assert out["allowed"] is False


def test_30_evaluate_flexible_alert_75_trigger():
    from bd_platform.pro_trader_layer import evaluate_flexible_alert_75

    out = evaluate_flexible_alert_75(
        user_tier="pro",
        trigger={"rule": "price spike"},
        seed=SEED,
    )
    assert "why_alert" in out


def test_37_evaluate_flexible_alert_75_policy():
    from bd_platform.pro_trader_layer import evaluate_flexible_alert_75

    out = evaluate_flexible_alert_75(user_tier="elite", seed=SEED)
    assert out["policy"]["tier"] == "elite"


# ─── #14 market_context.whale_alert_message ───────────────────────────────────


def test_14_whale_alert_message_underlying():
    from market_context import whale_alert_message

    assert "Whale accumulation" in whale_alert_message(60_000_000, 2.0)
    assert "Moderate whale" in whale_alert_message(15_000_000, 1.0)
    assert "distribution" in whale_alert_message(1_000_000, -8.0).lower()


# ─── #17 alert_service.subscribe_alerts ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_17_subscribe_alerts_underlying(monkeypatch):
    from alert_service import subscribe_alerts

    async def fake_insert(**kwargs):
        return "sub_test_17"

    monkeypatch.setattr("database.insert_alert_subscription", fake_insert)
    monkeypatch.setattr("alert_service.send_telegram_message", lambda *a, **k: True)

    out = await subscribe_alerts({"email": "audit@blackdark.local", "channel": "in_app"})
    assert out["success"] is True
    assert out["subscription_id"] == "sub_test_17"


# ─── #18 / #21 alert_orchestration.alert_orchestration_status_18 ──────────────


def test_18_alert_orchestration_status_underlying():
    from bd_platform.alert_orchestration import alert_orchestration_status_18

    out = alert_orchestration_status_18()
    assert out["ok"] is True
    assert out["capability_id"] == 18
    assert "channels" in out
    assert "engine" in out


def test_21_alert_orchestration_channels_underlying():
    from bd_platform.alert_orchestration import alert_orchestration_status_18

    out = alert_orchestration_status_18()
    assert out["channels"]["in_app"] is True


# ─── #49 flash_crash_protection.flash_crash_protection_status_49 ──────────────


def test_49_flash_crash_protection_status_underlying(monkeypatch):
    from bd_platform.flash_crash_protection import flash_crash_protection_status_49

    monkeypatch.setattr("risk_manager.is_trading_frozen", lambda: False)
    monkeypatch.setattr(
        "bd_platform.drawdown_guard.drawdown_status",
        lambda: {"drawdown_pct": 2.1, "ok": True},
    )
    monkeypatch.setattr(
        "obi_predictor.forecast_flash_crash",
        lambda **_: {"ok": True, "risk": "low"},
    )

    out = flash_crash_protection_status_49(symbol="BTC")
    assert out["ok"] is True
    assert out["symbol"] == "BTC"
    assert out["trading_frozen"] is False


# ─── #55 due_diligence_bundle.build_full_due_diligence_bundle ─────────────────


@pytest.mark.asyncio
async def test_55_build_full_due_diligence_bundle_underlying(monkeypatch):
    from due_diligence_bundle import build_full_due_diligence_bundle

    async def fake_acquisition():
        return {"assets": 3}

    async def fake_moat():
        return {"score": 0.7}

    async def fake_evidence():
        return {"pack": "ok"}

    monkeypatch.setattr(
        "acquisition_assets_service.build_acquisition_asset_audit",
        fake_acquisition,
    )
    monkeypatch.setattr("data_moat_guard.build_moat_build_status", fake_moat)
    monkeypatch.setattr("due_diligence.due_diligence_report", lambda: {"checks": 5})
    monkeypatch.setattr("retention_service.retention_guard_status", lambda: {"ok": True})
    monkeypatch.setattr("flywheel_saturation_guard.flywheel_saturation_status", lambda: {"ok": True})
    monkeypatch.setattr("observability.observability_status", lambda: {"ok": True})
    monkeypatch.setattr("acquirer_evidence_pack.build_acquirer_evidence_pack", fake_evidence)

    out = await build_full_due_diligence_bundle()
    assert out["architecture_verdict"] == "ACCEPTABLE_WITH_DEBT"
    assert "due_diligence_checks" in out


# ─── #56 market_analysis_layer.attach_market_health_bundle_106_112_114 ────────


def test_56_attach_market_health_bundle_underlying():
    from bd_platform.market_analysis_layer import attach_market_health_bundle_106_112_114

    bundle = attach_market_health_bundle_106_112_114(seed=SEED)
    assert "contagion" in bundle
    assert "gcli" in bundle
    assert "whale_ls_ratio" in bundle


# ─── #299 news_classifier.classify_headlines ──────────────────────────────────


@pytest.mark.asyncio
async def test_299_classify_headlines_underlying(monkeypatch):
    from bd_platform.news_classifier import classify_headlines

    class FakeItem:
        def __init__(self):
            self.asset = "BTC"
            self.source = "test"
            self.raw_text = "Bitcoin ETF approval macro headline"

    class FakeAnalysis:
        sentiment_score = 0.2

    async def fake_news(assets):
        return [FakeItem()]

    async def fake_sentiment(text):
        return FakeAnalysis()

    monkeypatch.setattr("sentiment_engine.fetch_market_sentiment_news", fake_news)
    monkeypatch.setattr("sentiment_engine.analyze_sentiment_score_async", fake_sentiment)

    out = await classify_headlines(limit=5)
    assert out["count"] >= 1
    assert out["headlines"][0]["topic"] in {"regulation", "general", "macro"}


# ─── #437 correlation_mindshare.compute_mindshare_correlation_288 ─────────────


@pytest.mark.asyncio
async def test_437_compute_mindshare_correlation_288_underlying(monkeypatch):
    from bd_platform.correlation_mindshare import compute_mindshare_correlation_288

    async def fake_lunar(**_):
        return {"ok": True, "galaxy_score": 72}

    monkeypatch.setattr("bd_platform.onchain_hub.lunarcrush_metrics", fake_lunar)

    out = await compute_mindshare_correlation_288(symbol="BTC")
    assert out["ok"] is True
    assert out["symbol"] == "BTC"
    assert out["correlation_ready"] is True


# ─── #584 news_classifier.coindesk_feed ───────────────────────────────────────


@pytest.mark.asyncio
async def test_584_coindesk_feed_underlying(monkeypatch):
    from bd_platform.news_classifier import coindesk_feed

    async def fake_rss(limit=10):
        return [{"title": "CoinDesk macro headline", "link": "https://example.com"}]

    class FakeAnalysis:
        sentiment_score = 0.1

    async def fake_sentiment(text):
        return FakeAnalysis()

    monkeypatch.setattr("bd_platform.free_market_data.coindesk_rss", fake_rss)
    monkeypatch.setattr("sentiment_engine.analyze_sentiment_score_async", fake_sentiment)

    out = await coindesk_feed(limit=3)
    assert out["success"] is True
    assert out["count"] >= 1
    assert out["source"] == "coindesk_rss"
