"""Tests — #745 MDIA merged into On-Chain Metrics Suite."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import onchain_metrics_suite as oms


@pytest.fixture
def isolated_onchain_seed_with_mdia(tmp_path, monkeypatch):
    seed = tmp_path / "onchain_metrics_seed.json"
    seed.write_text(
        json.dumps({
            "methodology": {
                "version": "v1.0",
                "competitor_reference": "Glassnode Realized Cap",
                "description": "SMA200 cost-basis proxy",
                "data_sources": ["Binance klines"],
            },
            "supply_estimates": {"BTC": {"circulating": 19800000, "source": "CoinGecko"}},
            "alert_thresholds": {"mvrv_z_overheated": 2.0, "mvrv_z_undervalued": -1.0},
            "mdia_methodology": {
                "competitor_reference": "Glassnode Mean Dollar Invested Age",
                "valuation_methodology": "MDIA = Σ(coin_age × usd) / Σ(usd)",
                "proxy_note": "7d/90d proxy",
                "time_alignment": {
                    "snapshot_boundary_utc": "00:00:00",
                    "cadence": "daily",
                    "aligns_with_suite_metrics": ["realized_cap", "mvrv"],
                },
                "chain_coverage": {
                    "BTC": {"chain": "bitcoin", "mode": "utxo_native", "supported": True},
                    "SOL": {"chain": "solana", "mode": "account_proxy", "supported": False},
                },
                "baselines": {"BTC": 210},
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
            "mvrv": {"ratio": 2.0, "z_score": 2.5},
            "hodl_waves": {
                "short_term_7d_avg": 98000.0,
                "long_term_90d_avg": 95000.0,
                "accumulation_signal": True,
            },
        }

    monkeypatch.setattr("bd_platform.onchain_advanced.compute_advanced_metrics", fake_metrics)


@pytest.mark.asyncio
async def test_mdia_computation(isolated_onchain_seed_with_mdia, mock_advanced_metrics):
    result = await oms.compute_mdia("BTC")
    assert result["ok"] is True
    assert result["feature_id"] == 745
    assert result["mdia_days"] > 0
    assert "MDIA:" in result["mdia_display"]
    assert result["chain_coverage_explicit"] is True


@pytest.mark.asyncio
async def test_valuation_methodology_documented(isolated_onchain_seed_with_mdia, mock_advanced_metrics):
    result = await oms.compute_mdia("BTC")
    assert "MDIA" in result["valuation_methodology"]
    assert result["time_alignment"]["cadence"] == "daily"


@pytest.mark.asyncio
async def test_chain_coverage_explicit(isolated_onchain_seed_with_mdia, mock_advanced_metrics):
    btc = await oms.compute_mdia("BTC")
    assert btc["chain_coverage"]["supported"] is True
    sol = await oms.compute_mdia("SOL")
    assert sol["supported"] is False


@pytest.mark.asyncio
async def test_mdia_in_full_suite(isolated_onchain_seed_with_mdia, mock_advanced_metrics, monkeypatch):
    async def fake_realignment(asset="BTC"):
        return {"realignment_signal": "none", "regime": "neutral", "z_score": 0, "alerts": []}

    async def fake_realized(asset="BTC"):
        return {"ok": True, "alerts": []}

    monkeypatch.setattr("bd_platform.mvrv_realignment.compute_mvrv_realignment", fake_realignment)
    monkeypatch.setattr(oms, "compute_realized_cap", fake_realized)
    suite = await oms.get_onchain_metrics_suite("BTC")
    assert "mdia" in suite
    assert "mdia" in suite["integrated_metrics"]


@pytest.mark.asyncio
async def test_status_includes_mdia(isolated_onchain_seed_with_mdia):
    status = oms.onchain_metrics_suite_status()
    assert 745 in status["feature_ids"]
    assert status["mdia_model"] is True
    assert status["chain_coverage_explicit"] is True


def test_mdia_api_route(isolated_onchain_seed_with_mdia, mock_advanced_metrics):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    r = c.get("/api/platform/onchain/metrics-suite/mdia?asset=BTC")
    assert r.status_code == 200
    assert r.json()["model"] == "mean_dollar_invested_age"


def test_full_seed_has_mdia():
    seed = json.loads(Path("data/onchain_metrics_seed.json").read_text(encoding="utf-8"))
    assert "mdia_methodology" in seed
    assert seed["mdia_methodology"]["chain_coverage"]["BTC"]["supported"] is True
