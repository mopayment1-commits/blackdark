"""Tests — #795 Telegram Connector, #796 merged into #788."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import alert_engine as ae
from bd_platform import social_sentiment_intelligence as ssi
from blackdark.ingestion import telegram_connector as tg


@pytest.fixture
def tg_seed() -> dict:
    path = Path("data/telegram_connector_seed.json")
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture
def alert_seed() -> dict:
    path = Path("data/alert_engine_seed.json")
    return json.loads(path.read_text(encoding="utf-8"))


# --- #795 ---


def test_795_connector_status(tg_seed):
    status = tg.telegram_connector_status()
    assert status["standalone_rejected"] is True
    assert status["no_user_dashboard"] is True
    assert status["public_channels_only"] is True
    assert status["rate_limit"]["max_per_minute"] == 30
    assert status["implementation"]["telethon_pyrogram_hidden"] is True


def test_795_mention_words(tg_seed):
    result = tg.get_telegram_mention_words_795("BTC", seed=tg_seed)
    assert result["ok"] is True
    assert result["mention_count"] > 0
    assert result["public_channels_only"] is True
    assert "#783" in str(result.get("feeds"))


def test_795_fallback_chain(tg_seed):
    result = tg.get_telegram_mention_words_795("BTC", seed=tg_seed, use_fallback=True)
    assert result["fallback_used"] is True
    assert result["mention_count"] > 0
    assert "twitter" in result.get("source", "").lower() or "rss" in result.get("source", "").lower()


def test_795_normalize_rejects_private():
    out = tg.normalize_telegram_message({"text": "secret", "is_public": False})
    assert out["ok"] is False
    assert out["privacy"] == "public_channels_only"


def test_795_cache_ttl_range(tg_seed):
    status = tg.telegram_connector_status()
    ttl = status["cache_ttl_seconds"]
    assert 3600 <= ttl <= 86400


@pytest.mark.asyncio
async def test_795_fetch_messages_sla():
    result = await tg.fetch_telegram_public_channel_messages("BTC")
    assert result["ok"] is True
    assert result["sla_met"] is True
    assert result["latency_ms"] <= 3000


@pytest.mark.asyncio
async def test_795_ingest_pass():
    result = await tg.run_telegram_sentiment_ingest()
    assert result["ok"] is True
    assert "BTC" in result["assets"]
    assert result["sla_met"] is True


def test_795_qa_suite():
    qa = tg.run_telegram_connector_qa_795()
    assert qa["all_passed"] is True


def test_795_sentiment_integration():
    panel = ssi.build_sentiment_intelligence_panel_783("BTC")
    tg_meta = (panel.get("trending_words_758") or {}).get("telegram_streams_795") or {}
    assert tg_meta.get("telegram_connector_795") is True
    assert tg_meta.get("telegram_mention_count", 0) > 0


def test_795_api_routes():
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/ingestion/telegram/status").status_code == 200
    resp = c.get("/api/platform/ingestion/telegram/mentions?asset=BTC")
    assert resp.status_code == 200
    assert resp.json()["feature_ref"] == 795


# --- #796 merged into #788 ---


def test_796_absorbed_into_788(alert_seed):
    status = ae.custom_metric_alerts_status_788()
    assert 796 in status["absorbed_feature_ids"]
    assert status["no_unified_alert_center"] is True
    assert status["no_unified_center_branding"] is True
    assert status["no_smart_alerts_branding"] is True
    assert status["panel_name_ar"] == "تنبيهات مخصصة"


def test_796_panel_rejects_unified_branding(alert_seed):
    panel = ae.build_custom_metric_alerts_panel_788("default", seed=alert_seed)
    assert panel["duplicate_of_796_rejected"] is True
    assert panel["no_unified_center_branding"] is True
    assert panel["panel_name_ar"] == "تنبيهات مخصصة"
    assert "Unified" not in panel.get("panel_name_ar", "")
