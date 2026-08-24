"""Tests — Due Diligence Report Engine (#173)."""

from __future__ import annotations

import pytest

from bd_platform.due_diligence_report_engine import (
    _METHODOLOGY_VERSION,
    _claim,
    build_due_diligence_report,
    due_diligence_report_status,
)


def test_claim_unknown_red_flag():
    row = _claim(
        section="team",
        claim="Founder identity",
        value="UNKNOWN",
        source="none",
        citation="No registry",
        unknown=True,
    )
    assert row["unknown"] is True
    assert row["red_flag"] is True


def test_methodology_version_present():
    status = due_diligence_report_status()
    assert status["feature_id"] == 173
    assert status["methodology_version"] == _METHODOLOGY_VERSION


@pytest.mark.asyncio
async def test_build_due_diligence_report_mocked(monkeypatch, tmp_path):
    async def fake_price(asset, use_cache=True):
        return {
            "ok": True,
            "weighted_price": 50000,
            "outlier_count": 0,
            "validation": {"price_verified": True},
            "source_metadata": {"primary_source": "binance"},
        }

    async def fake_health(asset="BTC"):
        return {
            "ok": True,
            "overall_score": 72,
            "overall_status": "healthy",
            "classification_reason": "Liquidity supportive",
            "portfolio_risk_109": {"recommended_action": "maintain"},
        }

    async def fake_confidence(asset):
        return {"ok": True, "confidence_score": 68}

    async def fake_financial(asset, *, notional=10_000):
        return {"mvrv": {"ratio": 2.1}, "nvt_ratio": 45}

    monkeypatch.setattr("bd_platform.price_aggregation_engine.aggregate_prices", fake_price)
    monkeypatch.setattr("bd_platform.market_health_engine.build_market_health_dashboard", fake_health)
    monkeypatch.setattr("bd_platform.confidence_engine.score_asset_confidence", fake_confidence)
    monkeypatch.setattr("research_lab.compute_financial_models", fake_financial)
    monkeypatch.setattr(
        "bd_platform.due_diligence_report_engine._REPORTS_PATH",
        tmp_path / "dd_reports.jsonl",
    )

    report = await build_due_diligence_report("BTC", mode="one_page")
    assert report["ok"] is True
    assert report["feature_id"] == 173
    assert report["methodology_version"] == _METHODOLOGY_VERSION
    assert report["unknown_explicitly_marked"] >= 2  # governance + team unknown
    assert report["one_page"]["top_risk_areas"]
    assert all("citation" in c for c in report["claims"])
    assert report["sla_met"] is True
