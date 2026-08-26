"""Tests — Quantitative Insights Layer #401 (rule-based, not standalone AI)."""

from __future__ import annotations

import json

import pytest

from bd_platform import quantitative_insights_layer as qil


@pytest.fixture
def signals_seed(tmp_path, monkeypatch):
    p = tmp_path / "intelligence_signals_seed.json"
    p.write_text(json.dumps({
        "backtest": {
            "years": 2.5, "sharpe": 0.9, "win_rate_pct": 53.0,
            "max_drawdown_pct": 18.0, "latency_minutes": 4.0, "fee_deduction_applied": True,
        },
        "walk_forward": {
            "months": 6, "sharpe": 0.85, "win_rate_pct": 52.5,
            "max_drawdown_pct": 19.0, "latency_minutes": 4.5, "fee_deduction_applied": True,
        },
        "signals": [{
            "signal_id": "test_001",
            "signal_type": "quantitative_insight",
            "asset": "BTC",
            "exchange_id": "binance",
            "confidence_score": 0.7,
            "gross_return_pct": 2.0,
            "exchange_fee_bps": 10,
            "slippage_bps": 5,
            "network_fee_usd": 2.5,
            "latency_minutes": 3.0,
            "rationale": "Funding divergence context — quantitative only.",
            "features_used": ["funding_rate_zscore", "sentiment_delta"],
            "surfaces": ["market_radar", "portfolio_ai"],
            "display": "Quantitative Insight — BTC",
        }],
    }), encoding="utf-8")
    monkeypatch.setattr(qil, "_SIGNALS_PATH", p)
    return p


def test_no_standalone_ai_engine(signals_seed):
    status = qil.quantitative_insights_status()
    assert status["no_standalone_ai_engine"] is True
    assert status["rule_based_v1"] is True
    assert status["ml_deferred_days"] == 90


def test_fee_deduction(signals_seed):
    fees = qil.apply_fee_deduction(5.0, exchange_fee_bps=10, slippage_bps=5, network_fee_usd=2.5)
    assert fees["fee_deduction_applied"] is True
    assert fees["net_return_pct"] < fees["gross_return_pct"]


def test_walk_forward_acceptance(signals_seed):
    wf = qil.build_walk_forward_validation()
    assert wf["all_acceptance_passed"] is True
    assert wf["acceptance_checks"]["sharpe_gte_0_8"] is True
    assert wf["acceptance_checks"]["win_rate_gte_52"] is True
    assert wf["acceptance_checks"]["max_drawdown_lte_20"] is True


def test_banned_terms_blocked(signals_seed):
    sig = qil.build_signal_output({
        "signal_id": "bad",
        "rationale": "AI predicts guaranteed profit buy now",
        "gross_return_pct": 1.0,
    })
    assert sig["banned_terms_blocked"] is True


def test_market_radar_surface(signals_seed):
    panel = qil.build_quantitative_insights_panel(asset="BTC", surface="market_radar")
    assert panel["ok"] is True
    assert panel["surface"] == "market_radar"
    assert panel["signal_count"] >= 1


def test_portfolio_ai_surface(signals_seed):
    panel = qil.build_quantitative_insights_panel(asset="BTC", surface="portfolio_ai")
    assert panel["ok"] is True
    assert panel["surface"] == "portfolio_ai"


def test_invalid_surface_rejected(signals_seed):
    panel = qil.build_quantitative_insights_panel(surface="oracle_api")
    assert panel["ok"] is False


def test_reconciliation(signals_seed):
    result = qil.run_reconciliation_tests()
    assert result["all_passed"] is True


def test_api_routes(signals_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/intelligence-ledger/market-radar/quantitative-insights/status").status_code == 200
    mr = c.get("/api/platform/intelligence-ledger/market-radar/quantitative-insights?asset=BTC")
    assert mr.status_code == 200
    assert mr.json().get("surface") == "market_radar"
    pa = c.get("/api/platform/intelligence-ledger/portfolio-ai/quantitative-insights?asset=BTC")
    assert pa.status_code == 200
    assert pa.json().get("surface") == "portfolio_ai"
