"""Tests — #730 #733 #734 #736 #737 DeFi & on-chain intelligence batch."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import (
    datashare_enterprise,
    defi_economics,
    entity_profiler,
    market_radar_indicators,
    onchain_metrics_suite,
)


@pytest.fixture
def defi_seed(tmp_path, monkeypatch):
    p = tmp_path / "defi_economics_seed.json"
    p.write_text(json.dumps({
        "protocols": {
            "aave": {
                "name": "Aave",
                "revenue_usd": 1000,
                "gas_cost_usd": 100,
                "incentives_usd": 200,
                "token_emission_cost_usd": 50,
                "fee_db_linked": True,
                "coverage": {"includes": ["Ethereum"], "excludes": ["NFT"]},
                "earnings_trend": [],
            },
        },
    }), encoding="utf-8")
    monkeypatch.setattr(defi_economics, "_SEED_PATH", p)
    return p


@pytest.fixture
def radar_seed(tmp_path, monkeypatch):
    p = tmp_path / "market_radar_indicators_seed.json"
    p.write_text(json.dumps({
        "exchange_cluster": {"version": "1.0"},
        "exchanges": {
            "binance": {
                "name": "Binance",
                "unique_addresses_deduped": True,
                "unique_addresses_change_pct": 10,
                "tx_count_change_pct": 8,
                "chain_validation": {"ethereum": {"validated": True, "rules": []}},
            },
        },
    }), encoding="utf-8")
    monkeypatch.setattr(market_radar_indicators, "_SEED_PATH", p)
    return p


@pytest.fixture
def entity_seed(tmp_path, monkeypatch):
    p = tmp_path / "entity_profiler_seed.json"
    p.write_text(json.dumps({
        "exchange_labels": {"version": "1.0"},
        "entities": {
            "whale_001": {
                "entity_type": "whale",
                "venue_interactions": [
                    {"venue": "binance", "volume_usd": 1000, "internal_flow": False},
                    {"venue": "internal", "volume_usd": 500, "internal_flow": True},
                ],
            },
        },
    }), encoding="utf-8")
    monkeypatch.setattr(entity_profiler, "_SEED_PATH", p)
    return p


@pytest.fixture
def onchain_seed(tmp_path, monkeypatch):
    p = tmp_path / "onchain_metrics_suite_seed.json"
    p.write_text(json.dumps({
        "assets": {
            "BTC": {
                "hodl_waves": {
                    "bands": {"<1d": 2, "1y-2y": 20, "5y+": 10},
                    "last_updated": "2026-08-26",
                },
            },
        },
    }), encoding="utf-8")
    monkeypatch.setattr(onchain_metrics_suite, "_SEED_PATH", p)
    return p


def test_730_deferred():
    status = datashare_enterprise.datashare_enterprise_status()
    assert status["status"] == "deferred"
    assert status["wave"] == 3
    assert status["schema_contracts"]["change_contracts"]["breaking_change_notice_days"] == 30


def test_733_proxy_label(defi_seed):
    panel = defi_economics.build_defi_economics_panel("aave")
    assert panel["earnings_proxy"]["not_gaap"] is True
    assert "Not GAAP" in panel["methodology"]["proxy_label"]
    assert panel["disclaimer_hideable"] is False
    assert panel["fee_db_linked"] is True


def test_733_no_profit_alone(defi_seed):
    earnings = defi_economics.compute_economic_profit_proxy({
        "revenue_usd": 1000, "gas_cost_usd": 100, "incentives_usd": 200, "token_emission_cost_usd": 50,
    })
    assert earnings["never_use_profit_alone"] is True
    assert earnings["economic_profit_proxy_usd"] == 650


def test_734_exchange_activity(radar_seed):
    ind = market_radar_indicators.build_exchange_activity_indicator("binance")
    assert ind["unique_addresses_deduped"] is True
    assert ind["exchange_cluster"]["address_dedupe"] is True
    assert ind["activity_state"] == "expansion"


def test_736_entity_profiler(entity_seed):
    panel = entity_profiler.build_entity_profiler_panel("whale_001")
    assert panel["exchange_usage"]["internal_flows_excluded"] == 1
    assert panel["exchange_labels"]["internal_flows_filtered"] is True


def test_737_hodl_waves(onchain_seed):
    panel = onchain_metrics_suite.build_onchain_metrics_panel("BTC")
    assert panel["hodl_waves"]["independent_calculation"] is True
    assert panel["hodl_waves"]["not_competitor_copy"] is True


def test_api_routes(defi_seed, radar_seed, entity_seed, onchain_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/intelligence-ledger/datashare/status").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/defi-economics?protocol=aave").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/market-radar/exchange-activity?exchange=binance").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/entity-profiler?entity_id=whale_001").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/onchain-metrics?asset=BTC").status_code == 200


def test_full_seeds_exist():
    assert json.loads(Path("data/defi_economics_seed.json").read_text())["feature_id"] == 733
