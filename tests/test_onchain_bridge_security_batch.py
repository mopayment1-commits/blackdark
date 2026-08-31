"""Tests — #506+#521 Bridge Flow, #507 Dusting Detection, #508 Exchange Flow Velocity."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import (
    cross_chain_bridge_flow_monitor as cbfm,
    dusting_attack_detection_alert as dada,
    exchange_flow_velocity_monitor as efvm,
)


@pytest.fixture
def bridge_seed(tmp_path, monkeypatch):
    p = tmp_path / "cross_chain_bridge_flow_monitor_seed.json"
    p.write_text(json.dumps({
        "indexing": {"no_ml": True, "no_ai": True},
        "bridges": {"wormhole": {"name": "Wormhole"}},
        "flows": [{
            "bridge_id": "wormhole",
            "source_chain": "ethereum",
            "dest_chain": "solana",
            "direction": "inflow",
            "amount_usd": 50000000,
            "transaction_count": 100,
            "entity_tag": "Unknown",
            "freshness_seconds": 120,
        }],
    }), encoding="utf-8")
    monkeypatch.setattr(cbfm, "_SEED_PATH", p)
    return p


@pytest.fixture
def dusting_seed(tmp_path, monkeypatch):
    p = tmp_path / "dusting_attack_detection_alert_seed.json"
    p.write_text(json.dumps({
        "heuristics": {
            "micro_transfer_threshold": 5,
            "dust_max_usd": 1.0,
            "unknown_sender_ratio_threshold": 0.7,
        },
        "wallets": {
            "wallet_alpha": {
                "address": "0xABC",
                "chain": "ethereum",
                "chains_affected": ["ethereum", "arbitrum"],
                "micro_transfer_count": 10,
                "unknown_sender_ratio": 0.8,
                "avg_transfer_usd": 0.5,
                "force_alert": True,
            },
            "wallet_clean": {
                "address": "0xDEF",
                "chain": "ethereum",
                "chains_affected": ["ethereum"],
                "micro_transfer_count": 1,
                "unknown_sender_ratio": 0.2,
                "avg_transfer_usd": 100.0,
            },
        },
    }), encoding="utf-8")
    monkeypatch.setattr(dada, "_SEED_PATH", p)
    return p


@pytest.fixture
def exchange_flow_seed(tmp_path, monkeypatch):
    p = tmp_path / "exchange_flow_velocity_monitor_seed.json"
    p.write_text(json.dumps({
        "velocity_windows": {"baseline_days": 30, "current_hours": 24},
        "exchanges": {
            "binance": {
                "name": "Binance",
                "entity_name": "Binance",
                "current_outflow_usd": 300000000,
                "baseline_outflow_avg_usd": 100000000,
                "current_inflow_usd": 200000000,
                "baseline_inflow_avg_usd": 150000000,
                "chains_tracked": ["ethereum"],
                "assets_tracked": ["BTC"],
            },
        },
    }), encoding="utf-8")
    monkeypatch.setattr(efvm, "_SEED_PATH", p)
    return p


def test_506_521_merged_bridge_flow_monitor(bridge_seed):
    panel = cbfm.build_bridge_flow_panel()
    assert panel["title"] == "Cross-Chain Bridge Flow Monitor"
    assert panel["no_ai_engine"] is True
    assert panel["no_trading_signals"] is True
    assert panel["no_performance_claims"] is True
    assert panel["data_monitoring_only"] is True
    assert "521" in panel["absorbed_tickets"]
    flow = panel["flows"][0]
    assert flow["not_signal"] is True
    assert "Entity:" in flow["display"]
    assert "Confidence: data freshness" in flow["display"]


def test_506_no_performance_claims_in_output(bridge_seed):
    panel = cbfm.build_bridge_flow_panel()
    user_facing = " ".join([
        panel["disclaimer"],
        panel["flows"][0]["display"],
        panel["indexing"]["display"],
    ]).lower()
    assert "sharpe" not in user_facing
    assert "win rate" not in user_facing
    assert panel["acceptance_criteria"]["sharpe_claims_removed"] is True


def test_507_renamed_detection_not_neutralizer(dusting_seed):
    panel = dada.build_dusting_detection_panel()
    assert panel["title"] == "Dusting Attack Detection Alert"
    assert panel["not_neutralizer"] is True
    assert panel["detection_and_alert_only"] is True
    assert panel["not_protection"] is True
    assert len(panel["alerts"]) >= 1
    alert = panel["alerts"][0]
    assert alert["not_blocked"] is True
    assert alert["not_neutralized"] is True
    assert "Potential dusting pattern detected" in alert["display"]
    assert "Detection based on heuristics" in panel["disclaimer"]


def test_507_heuristics_rule_based(dusting_seed):
    wallet = {
        "micro_transfer_count": 10,
        "unknown_sender_ratio": 0.8,
        "avg_transfer_usd": 0.5,
        "chains_affected": ["ethereum", "arbitrum"],
    }
    result = dada.evaluate_dusting_heuristics(wallet)
    assert result["detected"] is True
    assert result["not_blocked"] is True
    assert result["false_positives_possible"] is True


def test_508_renamed_integrated_feed(exchange_flow_seed):
    panel = efvm.build_exchange_flow_velocity_panel()
    assert panel["title"] == "Exchange Flow Velocity Monitor"
    assert panel["standalone_rejected"] is True
    assert panel["not_portfolio_management"] is True
    assert panel["not_acceleration_predictive"] is True
    record = panel["records"][0]
    assert "Entity:" in record["display"]
    assert record["not_signal"] is True
    assert record["outflow"]["not_sell_signal"] is True
    assert "velocity" in record["outflow"]["display"].lower()


def test_508_velocity_computation(exchange_flow_seed):
    velocity = efvm.compute_flow_velocity(300_000_000, 100_000_000, flow_type="outflow")
    assert velocity["velocity_pct"] == 200.0
    assert velocity["not_predictive"] is True
    assert "+200%" in velocity["display"]


def test_api_routes(bridge_seed, dusting_seed, exchange_flow_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/intelligence-ledger/onchain-layer/bridge-flow/status").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/onchain-layer/bridge-flow").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/security-layer/dusting-detection/status").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/security-layer/dusting-detection").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/onchain-layer/exchange-flow-velocity/status").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/onchain-layer/exchange-flow-velocity").status_code == 200


def test_full_seeds_exist():
    bridge = json.loads(Path("data/cross_chain_bridge_flow_monitor_seed.json").read_text())
    assert 506 in bridge["feature_ids"]
    assert bridge["no_ai_engine"] is True

    dusting = json.loads(Path("data/dusting_attack_detection_alert_seed.json").read_text())
    assert dusting["not_neutralizer"] is True

    exchange = json.loads(Path("data/exchange_flow_velocity_monitor_seed.json").read_text())
    assert exchange["standalone_rejected"] is True
