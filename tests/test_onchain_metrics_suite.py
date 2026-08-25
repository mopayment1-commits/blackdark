"""Tests — #750 Realized Cap Model merged into On-Chain Metrics Suite."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from bd_platform import onchain_metrics_suite as oms


@pytest.fixture
def isolated_onchain_seed(tmp_path, monkeypatch):
    seed = tmp_path / "onchain_metrics_seed.json"
    seed.write_text(
        json.dumps({
            "methodology": {
                "version": "v1.0",
                "competitor_reference": "Glassnode Realized Cap",
                "description": "SMA200 cost-basis proxy",
                "data_sources": ["Binance klines"],
            },
            "supply_estimates": {
                "BTC": {"circulating": 19800000, "source": "CoinGecko"},
            },
            "alert_thresholds": {
                "mvrv_z_overheated": 2.0,
                "mvrv_z_undervalued": -1.0,
            },
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(oms, "_SEED_PATH", seed)
    return seed


@pytest.fixture
def mock_advanced_metrics(monkeypatch):
    async def fake_metrics(asset="BTC", **kwargs):
        return {
            "asset": asset,
            "price": 100000.0,
            "mvrv": {"ratio": 2.0, "z_score": 2.5, "signal": "overheated"},
            "nupl_proxy": {"value": 0.5, "signal": "euphoria"},
            "sopr_proxy": {"ratio": 1.02, "signal": "neutral"},
            "puell_proxy": {"ratio": 1.1, "signal": "neutral"},
            "hodl_waves": {"accumulation_signal": False},
        }

    monkeypatch.setattr("bd_platform.onchain_advanced.compute_advanced_metrics", fake_metrics)


@pytest.mark.asyncio
async def test_not_standalone(isolated_onchain_seed):
    status = oms.onchain_metrics_suite_status()
    assert status["standalone"] is False
    assert status["feature_id"] == 750
    assert "On-Chain Metrics Suite" in status["merged_into"]


@pytest.mark.asyncio
async def test_realized_cap_computation(isolated_onchain_seed, mock_advanced_metrics):
    result = await oms.compute_realized_cap("BTC")
    assert result["ok"] is True
    assert result["realized_price"] == 50000.0
    assert result["realized_cap_usd"] == 50000.0 * 19_800_000
    assert result["market_cap_usd"] == 100000.0 * 19_800_000
    assert "Realized Cap:" in result["true_network_value_display"]


@pytest.mark.asyncio
async def test_glassnode_competitor_reference(isolated_onchain_seed, mock_advanced_metrics):
    result = await oms.compute_realized_cap("BTC")
    assert "Glassnode" in result["competitor_reference"]


@pytest.mark.asyncio
async def test_sla_met(isolated_onchain_seed, mock_advanced_metrics):
    result = await oms.compute_realized_cap("BTC")
    assert "sla_met" in result
    assert result["latency_ms"] <= oms._SLA_MS + 100
    assert result["accuracy_target_pct"] == 95
    assert result["uptime_target_pct"] == 99


@pytest.mark.asyncio
async def test_alerts_on_overheated(isolated_onchain_seed, mock_advanced_metrics):
    result = await oms.compute_realized_cap("BTC")
    assert result["alert_count"] >= 1
    codes = [a["code"] for a in result["alerts"]]
    assert "REALIZED_CAP_OVERHEATED" in codes or "MVRV_EXTREME" in codes


@pytest.mark.asyncio
async def test_methodology_documented(isolated_onchain_seed):
    meth = oms.get_methodology()
    assert meth["competitor_reference"] == "Glassnode Realized Cap"
    assert "SMA200" in meth["display"] or "Realized Cap" in meth["display"]


@pytest.mark.asyncio
async def test_full_suite(isolated_onchain_seed, mock_advanced_metrics, monkeypatch):
    async def fake_realignment(asset="BTC"):
        return {
            "realignment_signal": "none",
            "regime": "overheated",
            "z_score": 2.5,
            "alerts": [],
        }

    monkeypatch.setattr(
        "bd_platform.mvrv_realignment.compute_mvrv_realignment",
        fake_realignment,
    )
    suite = await oms.get_onchain_metrics_suite("BTC")
    assert suite["ok"] is True
    assert "realized_cap" in suite
    assert "mvrv" in suite
    assert len(suite["integrated_metrics"]) >= 5


@pytest.mark.asyncio
async def test_source_metadata(isolated_onchain_seed, mock_advanced_metrics):
    result = await oms.compute_realized_cap("BTC")
    assert "Source:" in result["source_line"]
    assert "CoinGecko" in result["source_line"]


def test_full_seed_exists():
    seed = json.loads(Path("data/onchain_metrics_seed.json").read_text(encoding="utf-8"))
    assert seed["methodology"]["competitor_reference"] == "Glassnode Realized Cap"
    assert "BTC" in seed["supply_estimates"]


def test_api_routes(isolated_onchain_seed, mock_advanced_metrics, monkeypatch):
    async def fake_realignment(asset="BTC"):
        return {"realignment_signal": "none", "regime": "neutral", "z_score": 0, "alerts": []}

    monkeypatch.setattr(
        "bd_platform.mvrv_realignment.compute_mvrv_realignment",
        fake_realignment,
    )

    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    status = c.get("/api/platform/onchain/metrics-suite/status")
    assert status.status_code == 200
    assert status.json()["standalone"] is False

    cap = c.get("/api/platform/onchain/metrics-suite/realized-cap?asset=BTC")
    assert cap.status_code == 200
    assert cap.json()["model"] == "realized_cap"
