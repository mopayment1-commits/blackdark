"""Tests — #307 Liquidation Cluster Analytics, #311 Basis sub-metric, #314 VC Flow."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import liquidation_cluster_analytics as lca
from bd_platform import private_market_vc_flow as pmvc
from bd_platform import derivatives_market_state as dms


@pytest.fixture
def liq_seed(tmp_path, monkeypatch):
    p = tmp_path / "liquidation_cluster_analytics_seed.json"
    p.write_text(json.dumps({
        "assets": {
            "BTC": {
                "sources": [{"venue": "binance", "confidence": "high"}],
                "clusters": [{
                    "cluster_id": "c1", "price_level": 60000, "side": "long",
                    "historical_liquidation_usd": 1e8, "current_open_interest_usd": 2e8,
                    "venue": "binance", "source": "Binance API", "confidence": "high",
                    "estimated_levels": [{"price": 59000, "estimated_oi_usd": 5e7, "probability_pct": 60}],
                }],
            },
        },
    }), encoding="utf-8")
    monkeypatch.setattr(lca, "_SEED_PATH", p)
    return p


@pytest.fixture
def vc_seed(tmp_path, monkeypatch):
    p = tmp_path / "private_market_vc_flow_seed.json"
    p.write_text(json.dumps({
        "rounds": [
            {"round_id": "r1", "company": "A", "sector": "defi", "amount_usd": 10000000,
             "original_currency": "USD", "announcement_date": "2026-01-01", "source": "crunchbase"},
            {"round_id": "r2", "company": "B", "sector": "defi", "amount_usd": 600000000,
             "original_currency": "USDC", "stablecoin_round": True, "announcement_date": "2026-02-01",
             "source": "theblock"},
            {"round_id": "r3", "company": "C", "sector": "infra", "amount_usd": 50000000,
             "original_currency": "ETH", "fx_rate_at_announcement": 3000, "announcement_date": "2026-03-01",
             "source": "messari", "revision_history": [{"date": "2026-03-05", "field": "amount_usd"}]},
        ],
    }), encoding="utf-8")
    monkeypatch.setattr(pmvc, "_SEED_PATH", p)
    return p


@pytest.fixture
def dms_seed(tmp_path, monkeypatch):
    p = tmp_path / "derivatives_market_state_seed.json"
    p.write_text(json.dumps({
        "backtest": {"false_positive_rate_pct": 20, "historical_events_tested": 10, "regime_accuracy_pct": 75},
        "assets": {
            "BTC": {
                "components": {
                    "spot_price": 64000, "perp_price": 64500,
                    "funding_rate": 0.0001, "oi_change_pct": 5,
                    "leverage_ratio": 1.2, "liquidation_usd_24h": 1e7,
                    "price_change_24h_pct": 1, "funding_z": 1, "oi_z": 1, "liquidation_z": 1,
                },
            },
        },
    }), encoding="utf-8")
    monkeypatch.setattr(dms, "_SEED_PATH", p)
    return p


def test_307_renamed_no_prediction(liq_seed):
    panel = lca.build_liquidation_cluster_panel("BTC")
    assert panel["renamed_from"] == "Imminent Liquidation Cluster Scanning"
    assert panel["no_prediction"] is True
    assert panel["no_imminent_language"] is True
    assert panel["clusters"][0]["estimated_levels"][0]["probability_only"] is True
    assert panel["latency_within_target"] is True


def test_307_sources_documented(liq_seed):
    panel = lca.build_liquidation_cluster_panel("BTC")
    assert panel["data_sources"]["confidence_per_venue"] is True


def test_311_basis_sub_metric_rejected_standalone(dms_seed):
    basis = dms.build_basis_sub_metric(
        {"spot_price": 64000, "perp_price": 64500, "days_to_expiry": 0},
        asset="BTC",
    )
    assert basis["standalone_rejected"] is True
    assert basis["expiry_time_alignment"] is True

    panel = dms.build_derivatives_market_state_panel("BTC")
    assert panel["basis_sub_metric"]["sub_task"] == "#311"


def test_314_currency_normalization(vc_seed):
    rnd = pmvc.build_round_entry({
        "round_id": "t", "amount_usd": 50000000, "original_currency": "ETH",
        "fx_rate_at_announcement": 3000, "announcement_date": "2026-01-01",
    })
    assert rnd["currency"]["not_current_usd"] is True
    assert rnd["currency"]["fx_documented"] is True


def test_314_mega_round_flagged(vc_seed):
    dashboard = pmvc.build_vc_flow_dashboard()
    mega = next(r for r in dashboard["rounds"] if r["round_id"] == "r2")
    assert mega["mega_round"]["is_mega_round"] is True
    assert "Strategic" in mega["mega_round"]["context"]


def test_314_revisions_visible(vc_seed):
    dashboard = pmvc.build_vc_flow_dashboard()
    revised = next(r for r in dashboard["rounds"] if r["round_id"] == "r3")
    assert revised["revised"] is True
    assert "revised on" in revised["revision_visible"]


def test_314_sector_flows_median_and_mean(vc_seed):
    dashboard = pmvc.build_vc_flow_dashboard()
    defi = next(s for s in dashboard["sector_flows"]["sectors"] if s["sector"] == "defi")
    assert defi["both_median_and_mean"] is True
    assert "hot_sectors" in dashboard["sector_flows"]


def test_api_routes(liq_seed, vc_seed, dms_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/intelligence-ledger/liquidation-clusters/status").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/liquidation-clusters?asset=BTC").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/private-market-vc/status").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/private-market-vc").status_code == 200


def test_full_seeds_exist():
    assert json.loads(Path("data/liquidation_cluster_analytics_seed.json").read_text())["feature_id"] == 307
    assert json.loads(Path("data/private_market_vc_flow_seed.json").read_text())["feature_id"] == 314
