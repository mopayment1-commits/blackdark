"""Tests — #443 Event & Sentiment Monitor (merged into Intelligence Ledger)."""

from __future__ import annotations

from pathlib import Path

import pytest

from bd_platform import event_sentiment_monitor as esm
from bd_platform import unified_arbitrage_engine as uae


@pytest.fixture
def esm_seed(tmp_path, monkeypatch):
    main = Path("data/event_sentiment_monitor_seed.json")
    p = tmp_path / "event_sentiment_monitor_seed.json"
    p.write_text(main.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(esm, "_SEED_PATH", p)
    return p


@pytest.fixture
def uae_seed(tmp_path, monkeypatch):
    main = Path("data/unified_arbitrage_engine_seed.json")
    p = tmp_path / "unified_arbitrage_engine_seed.json"
    p.write_text(main.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(uae, "_SEED_PATH", p)
    return p


def test_443_status(esm_seed):
    status = esm.event_sentiment_monitor_status()
    assert status["feature_id"] == 443
    assert status["standalone"] is False
    assert "Arbitrage" not in status["legal_name"]
    assert status["alerts_only"] is True
    assert status["source_count"] >= 5
    assert status["cancelled_v1"]["google_trends"] is True


def test_443_nlp_sentiment(esm_seed):
    btc = esm.compute_nlp_sentiment("BTC")
    assert btc["ok"] is True
    assert btc["composite_sentiment_score"] is not None
    assert btc["source_count"] >= 4
    assert btc["nlp_accuracy_target_met"] is True
    assert btc["google_trends_cancelled_v1"] is True


def test_443_fear_greed(esm_seed):
    btc = esm.compute_fear_greed_index("BTC")
    assert btc["ok"] is True
    assert 0 <= btc["fear_greed_score"] <= 100
    assert btc["fear_greed_label"] in (
        "extreme_fear", "fear", "neutral", "greed", "extreme_greed"
    )


def test_443_asset_scoring_metrics(esm_seed):
    btc = esm.compute_asset_scoring_metrics("BTC")
    assert btc["mc_volume_ratio"] is not None
    assert btc["total_on_chain_value_usd"] > 0


def test_443_event_proximity(esm_seed):
    btc = esm.compute_event_proximity("BTC")
    assert btc["ok"] is True
    assert btc["event_count"] >= 1
    assert btc["nearest_event"]["alert_only"] is True


def test_443_event_calendar(esm_seed):
    cal = esm.build_event_calendar()
    assert cal["count"] >= 5
    assert cal["alerts_only"] is True
    types = set(e["event_type"] for e in cal["events"])
    assert "listing" in types
    assert "delisting" in types
    assert "regulatory" in types


def test_443_alerts_only(esm_seed):
    alerts = esm.build_alerts(hours_ahead=720)
    assert alerts["alerts_only"] is True
    assert alerts["worth_studying_not_execution"] is True
    for alert in alerts["alerts"]:
        assert alert["no_execution_recommendation"] is True
        display = alert["display"].lower()
        for term in ("buy", "sell", "automatic", "exploit"):
            assert term not in display


def test_443_archive(esm_seed):
    archive = esm.build_archive_panel()
    assert archive["retention_target_met"] is True
    assert archive["retention_days"] >= 365


def test_443_analyze_asset(esm_seed):
    analysis = esm.analyze_asset("ARB")
    assert analysis["ok"] is True
    assert analysis["sentiment"]["composite_sentiment_label"] == "positive"
    assert analysis["monitoring_only"] is True


def test_443_429_integration(esm_seed, uae_seed):
    ctx = esm.enrich_arbitrage_opportunity({"asset": "BTC"})
    assert "sentiment_context" in ctx
    assert "event_proximity" in ctx
    assert ctx["no_auto_execution"] is True

    feed = uae.build_unified_feed()
    opps = feed.get("opportunities") or []
    assert len(opps) >= 1
    esm_ctx = opps[0].get("event_sentiment_context_443") or {}
    assert "sentiment_context" in esm_ctx


def test_443_reconciliation(esm_seed):
    result = esm.run_reconciliation_tests()
    assert result["ok"] is True
    assert result["passed"] == result["total"]
