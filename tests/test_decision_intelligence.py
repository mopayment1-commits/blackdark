"""Tests — Decision Intelligence Engine (#48)."""

from __future__ import annotations

import pytest

from ml.decision_features import _interaction_features, _technical_features, extract_decision_features
from ml.walk_forward import _compute_metrics, walk_forward_backtest


def test_technical_features_from_closes():
    closes = [100 + i * 0.5 + (i % 3) for i in range(60)]
    feats = _technical_features(closes)
    assert "rsi_14" in feats
    assert "macd" in feats
    assert len(feats) >= 20


def test_interaction_features():
    base = {
        "sentiment_score": 0.5,
        "obi_imbalance": 0.3,
        "whale_sii": 2.0,
        "onchain_netflow": 1000,
        "volatility": 2.0,
        "funding_spread_bps": 10,
        "macro_weight": 1.1,
        "ret_24h": 3.0,
    }
    feats = _interaction_features(base)
    assert "sent_x_obi" in feats
    assert "bull_regime" in feats


def test_compute_metrics():
    returns = [0.5, -0.3, 0.8, 0.2, -0.1, 0.4, 0.6, -0.2]
    m = _compute_metrics(returns)
    assert "sharpe" in m
    assert "max_drawdown_pct" in m
    assert 0 <= m["win_rate"] <= 1


def test_walk_forward_backtest_synthetic():
    closes = [100.0]
    for i in range(1, 500):
        ch = 0.1 if i % 20 < 10 else -0.08
        closes.append(closes[-1] * (1 + ch / 100))
    result = walk_forward_backtest(closes, train_window=100, test_window=20, step=20)
    assert result["ok"] is True
    assert result["folds"] >= 1
    assert "metrics" in result
    assert "pipeline_stage" in result


@pytest.mark.asyncio
async def test_extract_decision_features_mock(monkeypatch):
    async def fake_base(asset, *, price_at=None):
        return {
            "asset": asset,
            "price": 50000,
            "ret_1h": 0.5,
            "ret_4h": 1.2,
            "ret_24h": 2.0,
            "volatility": 1.5,
            "sentiment_score": 0.3,
            "sentiment_momentum": 0.1,
            "obi_score": 1.0,
            "obi_imbalance": 0.2,
            "macro_weight": 1.0,
            "funding_spread_bps": 5.0,
            "whale_sii": 1.5,
            "onchain_netflow": 500,
        }

    async def fake_closes(asset, *, limit=48):
        return [50000 + i * 10 for i in range(60)]

    async def fake_alpha(symbol):
        return {"momentum": 60, "sentiment_fg": 55, "entity_flow": 50, "liquidity": 70}

    monkeypatch.setattr("ml.decision_features.build_feature_vector", fake_base)
    monkeypatch.setattr("ml.feature_store._recent_closes", fake_closes)
    monkeypatch.setattr("ml.decision_features._alpha_features", fake_alpha)

    out = await extract_decision_features("BTC")
    assert out["feature_count"] >= 50
    assert "features" in out


@pytest.mark.asyncio
async def test_generate_decision_signal_mock(monkeypatch):
    async def fake_features(asset, **kwargs):
        return {"feature_count": 105, "meets_100_plus": True, "features": {"ret_24h": 2.0}}

    async def fake_ml(asset, **kwargs):
        return {"available": True, "prediction": "BUY", "confidence": 72, "engine": "ml_model"}

    async def fake_alpha(symbol):
        return {"ok": True, "bias": "bullish", "headline": "BTC alpha 65/100", "alpha_score": 65}

    async def fake_oracle(asset, price, qv, change):
        return {"score": 72, "verdict": "BUY", "engine_id": "unified_multimodal_v1"}

    async def fake_bt(asset, **kwargs):
        return {
            "ok": True,
            "pipeline_stage": "backtest",
            "acceptance_met": False,
            "metrics": {"sharpe": 1.2, "max_drawdown_pct": 18, "win_rate": 0.52},
            "acceptance_criteria": {"sharpe_min": 1.5},
        }

    monkeypatch.setattr("ml.decision_features.extract_decision_features", fake_features)
    monkeypatch.setattr("ml.inference.predict_direction", fake_ml)
    monkeypatch.setattr("bd_platform.alpha_engine.compute_alpha_signal", fake_alpha)
    monkeypatch.setattr("oracle_unified.compute_unified_oracle", fake_oracle)
    monkeypatch.setattr("ml.walk_forward.run_walk_forward_backtest", fake_bt)

    from bd_platform.decision_intelligence_engine import generate_decision_signal

    out = await generate_decision_signal("BTC", include_backtest=True)
    assert out["ok"] is True
    assert out["surface"] == "decision_intelligence_engine"
    assert out["signal"]["action"] in ("ACT", "WAIT", "AVOID")
    assert len(out["reasoning"]) >= 2
    assert out["features"]["meets_100_plus"] is True
    assert out["pipeline"]["stage"] == "backtest"


def test_decision_intelligence_api(tmp_path, monkeypatch):
    import asyncio

    import config
    import database

    db_path = tmp_path / "die.db"
    monkeypatch.setattr(config, "DB_PATH", db_path)
    monkeypatch.setattr(database.config, "DB_PATH", db_path)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("ENV", "test")
    asyncio.run(database.init_db())

    async def fake_signal(asset, **kwargs):
        return {
            "ok": True,
            "headline": "BTC ACT",
            "signal": {"action": "ACT", "confidence": 70, "verdict": "BUY", "score": 72},
            "reasoning": [{"factor": "test", "detail": "ok", "weight": "high"}],
            "features": {"count": 105, "meets_100_plus": True},
            "pipeline": {"stage": "prototype"},
            "risk_adjusted": {},
            "alerts": [],
            "data_sources": ["price"],
            "sla_met": True,
            "latency_ms": 100,
            "timestamp": "2026-08-24T12:00:00+00:00",
        }

    monkeypatch.setattr(
        "bd_platform.decision_intelligence_engine.generate_decision_signal", fake_signal
    )

    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/decision-intelligence/signal").status_code == 200
    r = c.get("/decision-intelligence")
    assert r.status_code == 200
    assert "Decision Intelligence" in r.text
