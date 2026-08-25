"""Tests — #747 MTF Decision Convergence as Signal Engine validation layer."""

from __future__ import annotations

import pytest

from bd_platform import signal_validation_engine as sve


@pytest.fixture
def mock_mtf_confluence(monkeypatch):
    async def fake_confluence(asset: str) -> dict:
        return {
            "aligned": True,
            "score_penalty": 0.0,
            "frames": {
                "15m": {"bias": "bull", "bars": 96},
                "1h": {"bias": "bull", "bars": 120},
                "4h": {"bias": "flat", "bars": 90},
            },
        }

    monkeypatch.setattr(
        "technical_analysis.compute_timeframe_confluence",
        fake_confluence,
    )


@pytest.fixture
def mock_divergent_mtf(monkeypatch):
    async def fake_confluence(asset: str) -> dict:
        return {
            "aligned": False,
            "score_penalty": 8.0,
            "frames": {
                "15m": {"bias": "bull", "bars": 96},
                "1h": {"bias": "bear", "bars": 120},
                "4h": {"bias": "bull", "bars": 90},
            },
        }

    monkeypatch.setattr(
        "technical_analysis.compute_timeframe_confluence",
        fake_confluence,
    )


@pytest.mark.asyncio
async def test_not_standalone():
    status = sve.signal_validation_status()
    assert status["standalone"] is False
    assert status["feature_id"] == 747
    assert status["filter_not_feature"] is True


@pytest.mark.asyncio
async def test_mtf_validation_convergent(mock_mtf_confluence):
    result = await sve.validate_mtf_convergence("BTC")
    assert result["ok"] is True
    assert result["validation_passed"] is True
    assert result["filter_role"] == "validation_layer"
    assert result["not_a_prediction"] is True


@pytest.mark.asyncio
async def test_mtf_validation_divergent(mock_divergent_mtf):
    result = await sve.validate_mtf_convergence("BTC")
    assert result["mtf_regime"] == "divergent"
    assert result["validation_passed"] is False


@pytest.mark.asyncio
async def test_signal_validation_adjusts_score(mock_divergent_mtf):
    result = await sve.run_signal_validation("BTC", opportunity_score=70.0)
    assert result["adjusted_score"] == 62.0
    assert result["signal_trusted"] is False


@pytest.mark.asyncio
async def test_decision_intelligence_includes_validation(mock_mtf_confluence, monkeypatch):
    async def fake_features(sym, **kwargs):
        return {"features": {"price": 100000}, "feature_count": 100, "meets_100_plus": True}

    async def fake_ml(sym, **kwargs):
        return {"available": False, "reason": "test"}

    async def fake_alpha(sym):
        return {"ok": True, "bias": "bullish", "alpha_score": 60, "headline": "test"}

    async def fake_oracle(sym, price, quote_volume, change, **kwargs):
        return {"opportunity_score": 75, "verdict": "BUY", "engine_id": "test"}

    monkeypatch.setattr("ml.decision_features.extract_decision_features", fake_features)
    monkeypatch.setattr("ml.inference.predict_direction", fake_ml)
    monkeypatch.setattr("bd_platform.alpha_engine.compute_alpha_signal", fake_alpha)
    monkeypatch.setattr("oracle_unified.compute_unified_oracle", fake_oracle)

    from bd_platform.decision_intelligence_engine import generate_decision_signal

    sig = await generate_decision_signal("BTC", include_backtest=False)
    assert "signal_validation" in sig
    assert sig["signal_validation"]["feature_id"] == 747


def test_api_routes(mock_mtf_confluence):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    status = c.get("/api/platform/signal-engine/validation/status")
    assert status.status_code == 200
    assert status.json()["feature_id"] == 747

    mtf = c.get("/api/platform/signal-engine/validation/mtf?asset=BTC")
    assert mtf.status_code == 200
    assert mtf.json()["filter_role"] == "validation_layer"

    val = c.get("/api/platform/signal-engine/validation?asset=BTC&opportunity_score=65")
    assert val.status_code == 200
    assert "signal_trusted" in val.json()
