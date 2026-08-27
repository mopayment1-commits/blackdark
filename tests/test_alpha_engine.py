"""Tests — Alpha Engine inputs (#13) with Alternative.me (#14) + Arkham (#15)."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from bd_platform.alpha_engine import compute_alpha_signal, gather_alpha_inputs
from blackdark.ingestion.alternative_me_connector import (
    fear_greed_alpha_score,
    fetch_fear_greed_index,
)
from blackdark.ingestion.arkham_connector import fetch_entity_intelligence_input


def test_fear_greed_alpha_contrarian():
    assert fear_greed_alpha_score(10) > 50
    assert fear_greed_alpha_score(90) < 50
    assert 45 <= fear_greed_alpha_score(50) <= 55


@pytest.mark.asyncio
async def test_fetch_fear_greed_mock():
    fake = {
        "ok": True,
        "rows": [{"value": 72, "value_classification": "Greed", "source": "alternative.me"}],
        "latency_ms": 40,
    }
    with patch(
        "blackdark.ingestion.alternative_me_connector._request",
        new=AsyncMock(return_value=fake),
    ):
        fg = await fetch_fear_greed_index()
    assert fg["ok"] is True
    assert fg["value"] == 72
    assert fg["alpha_engine_role"] == "sentiment_input"


@pytest.mark.asyncio
async def test_arkham_fallback_mock():
    with patch(
        "blackdark.ingestion.arkham_connector._api_key",
        return_value=None,
    ), patch(
        "database.fetch_latest_whale_alerts",
        new=AsyncMock(return_value=[]),
    ):
        row = await fetch_entity_intelligence_input("BTC")
    assert row["ok"] is True
    assert row["fallback"] is True
    assert row["alpha_engine_role"] == "entity_flow_input"


@pytest.mark.asyncio
async def test_alpha_engine_signal_mock():
    with patch(
        "bd_platform.alpha_engine.gather_alpha_inputs",
        new=AsyncMock(
            return_value={
                "symbol": "BTC",
                "features": {
                    "momentum_24h": 70,
                    "momentum_7d_proxy": 65,
                    "fear_greed": 55,
                    "entity_flow": 52,
                    "liquidity": 65,
                    "volume_ratio": 50,
                    "volatility_24h": 40,
                    "trend_strength": 68,
                },
                "factors": {
                    "momentum": 70,
                    "sentiment_fg": 55,
                    "entity_flow": 52,
                    "liquidity": 65,
                },
                "sources": {
                    "coingecko": {"price_usd": 65000, "change_24h_pct": 2},
                    "alternative_me_fear_greed": {"value": 60, "label": "Greed"},
                    "arkham_entity": {"entity_flow_score": 52, "source": "proxy"},
                },
            }
        ),
    ):
        out = await compute_alpha_signal("BTC")
    assert out["ok"] is True
    assert out["surface"] == "alpha_engine"
    assert 0 <= out["alpha_score"] <= 100
    assert "alternative.me" in out["input_sources"]
    assert "arkham" in out["input_sources"]
    assert len(out["explanations"]) >= 1
    assert out["feature_count"] == 8
    assert out["model"]["type"] == "weighted_ensemble_v1"


def test_alpha_api(tmp_path, monkeypatch):
    import config
    import database

    db_path = tmp_path / "alpha.db"
    monkeypatch.setattr(config, "DB_PATH", db_path)
    monkeypatch.setattr(database.config, "DB_PATH", db_path)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("ENV", "test")
    asyncio.run(database.init_db())

    fake_signal = {
        "ok": True,
        "surface": "alpha_engine",
        "asset": "BTC",
        "alpha_score": 62,
        "bias": "bullish",
        "input_sources": ["coingecko", "alternative.me", "arkham"],
        "sla_met": True,
    }
    with patch(
        "bd_platform.alpha_engine.compute_alpha_signal",
        new=AsyncMock(return_value=fake_signal),
    ):
        from fastapi.testclient import TestClient
        from dashboard import app

        c = TestClient(app)
        r = c.get("/api/platform/alpha/signal?asset=BTC")
        assert r.status_code == 200
        body = r.json()
        assert body["alpha_score"] == 62
        assert "alternative.me" in body["input_sources"]
