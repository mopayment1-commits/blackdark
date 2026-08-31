"""Tests — #738 #739 #740 #741 #742 #743 #744 batch."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import (
    ma_intelligence,
    market_data_indices,
    market_screener,
    onchain_metrics_suite,
    options_context,
    surveillance_engine,
)
from blackdark.data import historical_data_vault


@pytest.fixture
def vault_seed(tmp_path, monkeypatch):
    records = [
        {"date": "2026-08-20", "symbol": "BTC", "close": 65000},
        {"date": "2026-08-21", "symbol": "BTC", "close": 65500},
    ]
    payload = {
        "version": 1,
        "granularity": "daily",
        "records": records,
        "appended_at": "2026-08-26T00:00:00+00:00",
        "append_only": True,
    }
    checksum = historical_data_vault.sha256_checksum(
        json.dumps(payload, sort_keys=True, separators=(",", ":"))
    )
    result_payload = {
        "query_id": "btc_daily_close",
        "as_of_date": "2026-08-25",
        "granularity": "daily",
        "records": records,
        "pinned_version": 1,
    }
    result_checksum = historical_data_vault.sha256_checksum(
        json.dumps(result_payload, sort_keys=True, separators=(",", ":"))
    )
    p = tmp_path / "historical_data_vault_seed.json"
    p.write_text(json.dumps({
        "datasets": {
            "btc_daily": {
                "versions": [{**payload, "sha256_checksum": checksum, "overwrite_forbidden": True}],
                "latest_version": 1,
            },
        },
        "query_manifests": {
            "btc_daily_close": {
                "dataset_id": "btc_daily",
                "pinned_version": 1,
                "reference_date": "2026-08-25",
                "allowed_granularities": ["daily", "hourly", "tick"],
                "expected_result_checksum": result_checksum,
            },
        },
    }), encoding="utf-8")
    monkeypatch.setattr(historical_data_vault, "_SEED_PATH", p)
    return p


@pytest.fixture
def indices_seed(tmp_path, monkeypatch):
    p = tmp_path / "market_data_indices_seed.json"
    p.write_text(json.dumps({
        "indices": {
            "crypto_top100": {
                "name": "Top 100",
                "provider": "coingecko",
                "last_rebalance": "2026-08-01",
                "index_value": 1000,
                "methodology": {"version": "2.1", "rebalance_frequency": "monthly",
                                "weighting": "market_cap_weighted", "constituent_count": 100},
                "constituents": [{"symbol": "BTC", "weight_pct": 50}],
            },
        },
    }), encoding="utf-8")
    monkeypatch.setattr(market_data_indices, "_SEED_PATH", p)
    return p


@pytest.fixture
def ma_seed(tmp_path, monkeypatch):
    p = tmp_path / "ma_intelligence_seed.json"
    p.write_text(json.dumps({
        "deals": [
            {"deal_id": "deal_001", "target": "A", "buyer": "B", "sector": "infra",
             "deal_type": "acquisition", "status": "confirmed", "source": "CoinDesk",
             "date": "2026-06-01", "value_usd": 100, "value_disclosed": True},
            {"deal_id": "deal_002", "target": "C", "buyer": "D", "sector": "infra",
             "deal_type": "acquisition", "status": "rumored", "source": "The Block",
             "date": "2026-07-01", "value_usd": None, "value_disclosed": False},
        ],
        "trends": {"volume_by_quarter": [], "sector_heatmap": {}, "top_acquirers": []},
    }), encoding="utf-8")
    monkeypatch.setattr(ma_intelligence, "_SEED_PATH", p)
    return p


@pytest.fixture
def onchain_seed(tmp_path, monkeypatch):
    p = tmp_path / "onchain_metrics_suite_seed.json"
    p.write_text(json.dumps({
        "assets": {
            "BTC": {
                "hodl_waves": {"bands": {"<1d": 2, "1y-2y": 20, "5y+": 10}, "last_updated": "2026-08-26"},
                "mvrv": {
                    "price": 65000,
                    "realignment_window": 200,
                    "realized_price_history": [50000, 55000, 60000, 62000, 65000],
                },
            },
        },
    }), encoding="utf-8")
    monkeypatch.setattr(onchain_metrics_suite, "_SEED_PATH", p)
    return p


@pytest.fixture
def screener_seed(tmp_path, monkeypatch):
    p = tmp_path / "market_screener_seed.json"
    p.write_text(json.dumps({
        "assets": [
            {"symbol": "BTC", "bot_activity_score": 20, "exchange_quality_score": 90, "yield_pct": None},
            {"symbol": "ETH", "bot_activity_score": 50, "exchange_quality_score": 70, "yield_pct": 4.0},
        ],
        "saved_filters": {
            "low_bot": {"name": "Low Bot", "filters": {"bot_activity_score": {"max": 30}}},
        },
    }), encoding="utf-8")
    monkeypatch.setattr(market_screener, "_SEED_PATH", p)
    return p


@pytest.fixture
def surveillance_seed(tmp_path, monkeypatch):
    p = tmp_path / "surveillance_engine_seed.json"
    p.write_text(json.dumps({
        "bot_activity_layer": {"assets_tracked": 10},
        "cases": [{
            "case_id": "surv_001", "case_type": "wash_trading", "confidence_pct": 70,
            "venue_label": "Exchange X", "asset_label": "Asset Y",
            "evidence": {"trade_count": 100, "window_seconds": 10, "captured_at": "2026-08-25T00:00:00+00:00"},
            "review": {"status": "approved", "manual_review_complete": True},
        }],
    }), encoding="utf-8")
    monkeypatch.setattr(surveillance_engine, "_SEED_PATH", p)
    return p


@pytest.fixture
def options_seed(tmp_path, monkeypatch):
    p = tmp_path / "options_context_seed.json"
    p.write_text(json.dumps({
        "assets": {
            "BTC": {
                "spot": 65000,
                "strikes": [
                    {"strike": 64000, "call_oi": 1000, "put_oi": 800},
                    {"strike": 65000, "call_oi": 2000, "put_oi": 1800},
                    {"strike": 66000, "call_oi": 1200, "put_oi": 1500},
                ],
            },
        },
    }), encoding="utf-8")
    monkeypatch.setattr(options_context, "_SEED_PATH", p)
    return p


def test_738_checksums_and_reproducibility(vault_seed):
    status = historical_data_vault.historical_data_vault_status()
    assert status["checksums_mandatory"] is True
    assert status["append_only"] is True
    assert "forever" in status["retention_policy"]["display"]

    ds = historical_data_vault.get_dataset("btc_daily")
    assert ds["checksum_verified"] is True

    r1 = historical_data_vault.run_reproducible_query("btc_daily_close")
    r2 = historical_data_vault.run_reproducible_query("btc_daily_close")
    assert r1["result_checksum"] == r2["result_checksum"]
    assert r1["reproducible"] is True


def test_739_index_methodology(indices_seed):
    feed = market_data_indices.build_index_feed("crypto_top100")
    assert feed["standalone"] is False
    assert "v2.1" in feed["display_version"]
    assert feed["methodology"]["documented"] is True


def test_740_ma_no_fabricated_valuation(ma_seed):
    panel = ma_intelligence.build_ma_deal_panel("deal_002")
    assert panel["deal"]["value_display"] == "Value: Undisclosed"
    assert panel["deal"]["no_fabricated_valuation"] is True
    assert panel["disclaimer_hideable"] is False


def test_741_mvrv_z_score(onchain_seed):
    panel = onchain_metrics_suite.build_onchain_metrics_panel("BTC")
    assert panel["mvrv_z_score"]["dynamic_realignment"] is True
    assert panel["mvrv_z_score"]["independent_calculation"] is True
    assert panel["latency_within_target"] is True


def test_742_screener_deterministic(screener_seed):
    r1 = market_screener.run_screener(saved_filter_id="low_bot")
    r2 = market_screener.run_screener(saved_filter_id="low_bot")
    assert r1["result_checksum"] == r2["result_checksum"]
    assert "matching your criteria" in r1["display"]
    assert r1["not_opportunities_language"] is True


def test_743_surveillance_enterprise(surveillance_seed):
    free = surveillance_engine.build_surveillance_panel(tier="free")
    ent = surveillance_engine.build_surveillance_panel(tier="enterprise")
    assert free["summary_only"] is True
    assert len(ent["cases"]) == 1
    assert ent["bot_activity_submodule"]["absorbed_feature_id"] == 721
    assert ent["evidence_retention_days"] == 90


def test_744_options_no_causal(options_seed):
    panel = options_context.build_options_context_panel("BTC")
    assert panel["no_causal_guarantee"] is True
    assert panel["context_not_signal"] is True
    assert panel["disclaimer_hideable"] is False
    assert panel["max_pain"]["max_pain_strike"] is not None


def test_api_routes(vault_seed, indices_seed, ma_seed, onchain_seed, screener_seed, surveillance_seed, options_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/v1/data/historical-vault/status").status_code == 200
    assert c.get("/api/v1/data/historical-vault/datasets/btc_daily").status_code == 200
    assert c.get("/api/v1/data/historical-vault/query/btc_daily_close").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/market-data/indices").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/ma-intelligence/deals?deal_id=deal_001").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/market-radar/screener").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/surveillance?tier=enterprise").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/onchain-metrics?asset=BTC").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/options-context?asset=BTC").status_code == 200


def test_full_seeds_exist():
    assert json.loads(Path("data/historical_data_vault_seed.json").read_text())["feature_id"] == 738
    assert json.loads(Path("data/market_screener_seed.json").read_text())["feature_id"] == 742
