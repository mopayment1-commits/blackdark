"""Independent underlying tests for batch-03 hero wrappers (#214, #224, #245, #279, #299)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

SEED = json.loads(Path("data/legal_retail_commercial_seed.json").read_text(encoding="utf-8"))


def test_214_build_whale_narrative_71_underlying():
    from bd_platform.pro_trader_layer import build_whale_narrative_71

    out = build_whale_narrative_71(amount_eth=12000, direction="to_exchange", seed=SEED)
    assert out["ok"] is True
    assert "narrative" in out or "headline" in out


def test_224_coinmarketcal_status_245_underlying():
    from bd_platform.security_trust_data_layer import coinmarketcal_status_245

    out = coinmarketcal_status_245(seed=SEED)
    assert out["activation_not_build"] is True


def test_245_smb_institution_status_83_underlying():
    from bd_platform.whales_institutional_layer import smb_institution_status_83

    out = smb_institution_status_83(seed=SEED)
    assert out["ok"] is True


def test_279_build_share_card_68_underlying():
    from bd_platform.pro_trader_layer import build_share_card_68

    card = build_share_card_68(
        card_type="chart",
        title="BTC setup",
        summary="Shared chart snapshot",
        seed=SEED,
    )
    assert card["ok"] is True
    assert card["card"]["card_type"] == "chart"
    assert card["share"]["url"]


@pytest.mark.asyncio
async def test_299_classify_headlines_underlying(monkeypatch):
    from bd_platform.news_classifier import classify_headlines

    class FakeItem:
        def __init__(self):
            self.asset = "BTC"
            self.source = "test"
            self.raw_text = "Bitcoin regulation headline"

    class FakeAnalysis:
        sentiment_score = 0.1

    async def fake_news(assets):
        return [FakeItem()]

    async def fake_sentiment(text):
        return FakeAnalysis()

    monkeypatch.setattr("sentiment_engine.fetch_market_sentiment_news", fake_news)
    monkeypatch.setattr("sentiment_engine.analyze_sentiment_score_async", fake_sentiment)

    out = await classify_headlines(limit=3)
    assert out["count"] >= 1


@pytest.mark.asyncio
async def test_288_compute_mindshare_correlation_underlying(monkeypatch):
    from bd_platform.correlation_mindshare import compute_mindshare_correlation_288

    async def fake_lunar(**_):
        return {"ok": True, "galaxy_score": 70}

    monkeypatch.setattr("bd_platform.onchain_hub.lunarcrush_metrics", fake_lunar)

    out = await compute_mindshare_correlation_288(symbol="BTC")
    assert out["ok"] is True
    assert out["correlation_ready"] is True
