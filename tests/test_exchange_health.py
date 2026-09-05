"""Tests — Exchange Health & Certification Engine (#53 / CAP-916)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform.exchange_health_engine import (
    assess_all_exchanges,
    assess_exchange,
    collapse_validation_metrics,
    exchange_health_overview,
)
from ml.exchange_health_features import extract_exchange_features, risk_badge


def _sample_ref() -> dict:
    return {
        "por_status": "attested_merkle",
        "regulatory_tier": "tier1_licensed",
        "hack_incidents": 0,
        "blacklisted": False,
    }


def test_risk_badge_tiers():
    assert risk_badge(85) == "Certified"
    assert risk_badge(70) == "Caution"
    assert risk_badge(45) == "High Risk"
    assert risk_badge(90, blacklisted=True) == "Blacklisted"


def test_feature_count_100_plus():
    pack = extract_exchange_features(
        exchange_id="binance",
        name="Binance",
        trust_score=9,
        volume_24h_btc=200_000,
        reference=_sample_ref(),
        operational_healthy=True,
        withdrawal_known=True,
        ingress_banned=False,
    )
    assert pack["feature_count"] >= 100
    assert pack["composite_health"] > 70


def test_ftx_blacklisted():
    pack = extract_exchange_features(
        exchange_id="ftx",
        name="FTX",
        trust_score=None,
        volume_24h_btc=0,
        reference={
            "por_status": "fraud",
            "regulatory_tier": "collapsed",
            "hack_incidents": 1,
            "blacklisted": True,
        },
        operational_healthy=False,
        withdrawal_known=False,
        ingress_banned=True,
    )
    assert pack["composite_health"] <= 15
    assert risk_badge(pack["composite_health"], blacklisted=True) == "Blacklisted"


def test_collapse_validation_metrics():
    assessments = [
        {"exchange_id": "ftx", "health_score": 10, "risk_badge": "Blacklisted"},
        {"exchange_id": "binance", "health_score": 85, "risk_badge": "Certified"},
        {"exchange_id": "coinbase", "health_score": 90, "risk_badge": "Certified"},
    ]
    metrics = collapse_validation_metrics(assessments)
    assert metrics["recall"] >= 0.80
    assert metrics["false_positive_rate"] <= 0.10
    assert metrics["recall_met"] is True
    assert metrics["fp_rate_met"] is True


@pytest.mark.asyncio
async def test_assess_exchange_mock(monkeypatch):
    async def fake_cg(*, pages=3):
        return [
            {
                "id": "binance",
                "name": "Binance",
                "trust_score": 9,
                "trade_volume_24h_btc": 150_000,
            }
        ]

    async def fake_ops():
        return {"healthy_sample": ["binance"]}

    monkeypatch.setattr(
        "bd_platform.exchange_health_engine._fetch_coingecko_exchanges", fake_cg
    )
    monkeypatch.setattr(
        "bd_platform.exchange_health_engine._operational_health_set",
        fake_ops,
    )
    monkeypatch.setattr(
        "bd_platform.exchange_health_engine._withdrawal_known_set",
        lambda: {"binance"},
    )
    monkeypatch.setattr(
        "bd_platform.exchange_health_engine._ingress_banned_set", lambda: set()
    )

    out = await assess_exchange("binance")
    assert out["ok"] is True
    assert out["feature"] == "#53"
    assert out["health_score"] >= 60
    assert out["risk_badge"] in ("Certified", "Caution")
    assert "explanation" in out
    assert out["features"]["count"] >= 100


@pytest.mark.asyncio
async def test_assess_all_exchanges_mock(monkeypatch, tmp_path):
    snap = tmp_path / "snapshots.jsonl"
    monkeypatch.setattr("bd_platform.exchange_health_engine._SNAPSHOT_PATH", snap)

    rows = []
    for i in range(55):
        rows.append(
            {
                "id": f"exchange_{i}",
                "name": f"Exchange {i}",
                "trust_score": 7 + (i % 3),
                "trade_volume_24h_btc": 10_000 + i * 1000,
            }
        )
    rows.append(
        {
            "id": "binance",
            "name": "Binance",
            "trust_score": 9,
            "trade_volume_24h_btc": 200_000,
        }
    )

    async def fake_cg(*, pages=3):
        return rows

    async def fake_ops():
        return {"healthy_sample": ["binance"]}

    monkeypatch.setattr(
        "bd_platform.exchange_health_engine._fetch_coingecko_exchanges", fake_cg
    )
    monkeypatch.setattr(
        "bd_platform.exchange_health_engine._operational_health_set", fake_ops
    )
    monkeypatch.setattr(
        "bd_platform.exchange_health_engine._withdrawal_known_set",
        lambda: {"binance"},
    )
    monkeypatch.setattr(
        "bd_platform.exchange_health_engine._ingress_banned_set", lambda: set()
    )

    out = await assess_all_exchanges(min_coverage=50)
    assert out["ok"] is True
    assert out["count"] >= 50
    assert out["coverage_met"] is True
    assert "collapse_validation" in out
    assert out["acceptance"]["collapse_recall_met"] is True


@pytest.mark.asyncio
async def test_overview_mock(monkeypatch):
    async def fake_assess(exchange_id, **kwargs):
        return {
            "ok": True,
            "exchange_id": exchange_id,
            "health_score": 80,
            "risk_badge": "Certified",
            "explanation": "test",
            "features": {"count": 110},
            "dimensions": {},
            "alerts": [],
        }

    async def fake_all(**kwargs):
        return {
            "exchanges": [{"exchange_id": "binance", "health_score": 80}],
            "count": 1,
        }

    monkeypatch.setattr("bd_platform.exchange_health_engine.assess_exchange", fake_assess)
    monkeypatch.setattr("bd_platform.exchange_health_engine.assess_all_exchanges", fake_all)

    out = await exchange_health_overview("binance")
    assert out["ok"] is True
    assert out["universe_rank"] == 1


def test_api_routes(monkeypatch):
    async def fake_assess(exchange_id, **kwargs):
        return {"ok": True, "exchange_id": exchange_id, "health_score": 75, "risk_badge": "Caution", "features": {"count": 110}, "dimensions": {}, "alerts": [], "explanation": "ok"}

    async def fake_all(**kwargs):
        return {
            "ok": True,
            "headline": "test",
            "ranking": [],
            "count": 55,
            "acceptance": {"coverage_met": True, "collapse_recall_met": True, "false_positive_rate_met": True},
            "collapse_validation": {"recall": 1.0, "false_positive_rate": 0.0},
            "latency_ms": 50,
        }

    async def fake_overview(exchange_id):
        return {"ok": True, "exchange": {"health_score": 75}, "universe_rank": 1, "universe_count": 55, "latency_ms": 80}

    monkeypatch.setattr("bd_platform.exchange_health_engine.assess_exchange", fake_assess)
    monkeypatch.setattr("bd_platform.exchange_health_engine.assess_all_exchanges", fake_all)
    monkeypatch.setattr("bd_platform.exchange_health_engine.exchange_health_overview", fake_overview)

    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/exchange-health/assess?exchange_id=binance").status_code == 200
    assert c.get("/api/platform/exchange-health/ranking").status_code == 200
    assert c.get("/api/platform/exchange-health/overview?exchange_id=binance").status_code == 200
    r = c.get("/exchange-health")
    assert r.status_code == 200
    assert "Exchange Health" in r.text


def test_reference_registry_exists():
    path = Path("data/exchange_health_reference.json")
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert "ftx" in data.get("exchanges", {})
    assert data["exchanges"]["ftx"]["blacklisted"] is True
