"""Tests — #510-#516 On-chain, AI Content, Protocol, Portfolio, Asset Profiles batch."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import (
    ai_content_engine as ace,
    asset_intelligence_profiles as aip,
    portfolio_intelligence_layer as pil,
    protocol_metrics_layer as pml,
    whale_flow_destination_tracker as wfdt,
)


@pytest.fixture
def whale_seed(tmp_path, monkeypatch):
    p = tmp_path / "whale_flow_destination_tracker_seed.json"
    p.write_text(json.dumps({
        "destination_rules": {"rules": ["known_exchange_address_match"]},
        "known_addresses": {
            "0xexchange": {"type": "exchange", "label": "Binance", "confidence": "heuristic_high"},
        },
        "flows": [{
            "whale_address": "0xwhale", "asset": "BTC", "amount_usd": 10000000,
            "destination_address": "0xexchange", "chain": "ethereum", "tx_hash": "0xabc",
        }],
    }), encoding="utf-8")
    monkeypatch.setattr(wfdt, "_SEED_PATH", p)
    return p


@pytest.fixture
def ai_seed(tmp_path, monkeypatch):
    p = tmp_path / "ai_content_engine_seed.json"
    p.write_text(json.dumps({
        "legal_review": {"complete": True},
        "evidence_items": [{
            "asset": "BTC", "statement": "Wallet moved $10M to Exchange",
            "amount_usd": 10000000, "destination": "Exchange",
            "transaction_refs": ["0xabc"], "entity_refs": ["0xwhale"],
            "source": "onchain", "freshness_seconds": 300,
        }],
        "digests": {
            "daily": {
                "period": "daily", "summary": "Test digest", "freshness_seconds": 1800,
                "claims": [{
                    "statement": "Test claim", "why_it_matters": "Context",
                    "source_links": ["http://evidence"], "transaction_refs": ["0xabc"],
                }],
            },
        },
        "screener": {
            "default_weights": {"price": 0.5, "volume": 0.5},
            "assets": [{"symbol": "BTC", "factors": {"price": 0.8, "volume": 0.9}}],
        },
    }), encoding="utf-8")
    monkeypatch.setattr(ace, "_SEED_PATH", p)
    return p


@pytest.fixture
def protocol_seed(tmp_path, monkeypatch):
    p = tmp_path / "protocol_metrics_layer_seed.json"
    p.write_text(json.dumps({
        "bot_rules": {"rules": ["exclude_bots"]},
        "protocols": {
            "uniswap": {"name": "Uniswap", "dau": 1000, "mau": 5000, "bot_addresses_excluded": 100},
        },
    }), encoding="utf-8")
    monkeypatch.setattr(pml, "_SEED_PATH", p)
    return p


@pytest.fixture
def portfolio_seed(tmp_path, monkeypatch):
    p = tmp_path / "portfolio_intelligence_layer_seed.json"
    p.write_text(json.dumps({
        "portfolios": {
            "demo": {"name": "Demo", "latest_snapshot_timestamp": "2026-08-01T00:00:00Z"},
        },
        "snapshots": {
            "demo:2026-08-01T00:00:00Z": {
                "holdings": [{"asset": "BTC", "amount": 1, "price_usd": 65000, "value_usd": 65000}],
                "no_current_label_leakage": True,
            },
        },
    }), encoding="utf-8")
    monkeypatch.setattr(pil, "_SEED_PATH", p)
    return p


@pytest.fixture
def asset_seed(tmp_path, monkeypatch):
    p = tmp_path / "asset_intelligence_profiles_seed.json"
    p.write_text(json.dumps({
        "duplicates_resolved": [],
        "assets": {
            "asset_btc": {
                "entity_id": "asset_btc", "symbol": "BTC", "name": "Bitcoin",
                "version": "1.0", "lifecycle_status": "active", "duplicate_resolved": True,
                "market_cap_usd": 1e12, "coverage": {"research": True},
                "sources": {"market_data": "binance"}, "freshness_seconds": 120,
            },
        },
    }), encoding="utf-8")
    monkeypatch.setattr(aip, "_SEED_PATH", p)
    return p


def test_510_renamed_integrated_whale_tracker(whale_seed):
    panel = wfdt.build_whale_flow_destination_panel()
    assert panel["title"] == "Whale Flow Destination Tracker"
    assert panel["no_ai_profiling"] is True
    assert panel["standalone_rejected"] is True
    assert panel["not_portfolio_management"] is True
    flow = panel["flows"][0]
    assert "heuristic-based" in flow["display"]
    assert flow["not_ai_prediction"] is True


def test_511_evidence_linked_no_hallucination(ai_seed):
    feed = ace.build_market_evidence_feed(asset="BTC")
    assert feed["every_claim_linked"] is True
    assert feed["no_hallucinated_intent"] is True
    item = feed["evidence_items"][0]
    assert item["transaction_refs"] == ["0xabc"]
    assert item["no_hallucinated_intent"] is True


def test_512_digest_traceable_with_freshness(ai_seed):
    digest = ace.build_market_digest(digest_id="daily")
    assert digest["every_claim_traceable"] is True
    assert "freshness_score" in digest["freshness"]
    assert digest["claims"][0]["no_hallucinated_facts"] is True


def test_513_restructured_screener_not_rating(ai_seed):
    screener = ace.build_multi_factor_screener()
    assert screener["not_rating_engine"] is True
    assert screener["no_investment_score"] is True
    assert screener["no_opportunity_rank"] is True
    assert screener["composite_metric_name"] == "Factor Alignment Indicator"
    assert screener["user_controlled_weights"] is True
    assert screener["learned_scoring_blocked"] is True


def test_514_active_users_bot_filtering(protocol_seed):
    panel = pml.build_protocol_metrics_panel("uniswap")
    assert panel["active_users"]["bot_filtering_applied"] is True
    assert panel["active_users"]["bot_rules_documented"] is True
    assert panel["standalone_rejected"] is True


def test_515_historical_snapshot_reproducible(portfolio_seed):
    panel = pil.build_portfolio_intelligence_panel("demo")
    snapshot = panel["snapshot"]
    assert snapshot["point_in_time_reconstruction"] is True
    assert snapshot["reproducible"] is True
    assert snapshot["no_current_label_leakage"] is True
    assert "snapshot_hash" in snapshot


def test_516_asset_profiles_foundation(asset_seed):
    panel = aip.build_asset_intelligence_panel("asset_btc")
    assert panel["foundation_feature"] is True
    assert panel["priority"] == "highest"
    profile = panel["profile"]
    assert profile["entity"]["stable_id"] is True
    assert profile["duplicate_assets_resolved"] is True
    assert profile["source_freshness"]["source_visible"] is True


def test_api_routes(whale_seed, ai_seed, protocol_seed, portfolio_seed, asset_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/intelligence-ledger/onchain-layer/whale-flow-destination/status").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/intelligence-layer/ai-content/status").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/intelligence-layer/ai-content/evidence?asset=BTC").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/data-layer/protocol-metrics?protocol_id=uniswap").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/portfolio-layer/snapshots?portfolio_id=demo").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/data-layer/asset-profiles?entity_id=asset_btc").status_code == 200


def test_full_seeds_exist():
    assert json.loads(Path("data/whale_flow_destination_tracker_seed.json").read_text())["feature_id"] == 510
    assert 511 in json.loads(Path("data/ai_content_engine_seed.json").read_text())["feature_ids"]
    assert json.loads(Path("data/protocol_metrics_layer_seed.json").read_text())["feature_id"] == 514
    assert json.loads(Path("data/portfolio_intelligence_layer_seed.json").read_text())["feature_id"] == 515
    assert json.loads(Path("data/asset_intelligence_profiles_seed.json").read_text())["priority"] == "highest"
