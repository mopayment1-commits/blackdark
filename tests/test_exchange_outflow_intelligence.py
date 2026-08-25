"""Tests — #242 Exchange Outflow Intelligence + Exchange Intelligence Hub."""

from __future__ import annotations

import json

import pytest

from bd_platform import exchange_flow_common as efc
from bd_platform import exchange_outflow_intelligence as eoi
from bd_platform import exchange_intelligence_hub as eih


@pytest.fixture
def isolated_seed(tmp_path, monkeypatch):
    seed = tmp_path / "exchange_intelligence_hub_seed.json"
    seed.write_text(
        json.dumps({
            "feature_id": 734,
            "methodology_version": "1.0",
            "cluster_version": "4.2",
            "cluster_last_updated": "2026-08-25",
            "exchange_clusters": {
                "binance": {"address_count": 1250},
                "coinbase": {"address_count": 890},
                "kraken": {"address_count": 420},
            },
            "assets": {
                "BTC": {
                    "inflow_usd": 850000000,
                    "outflow_usd": 920000000,
                    "netflow_usd": -70000000,
                    "baseline_30d_outflow_usd": 780000000,
                    "exchange_breakdown": {
                        "binance": {"inflow_usd": 340000000, "outflow_usd": 380000000},
                        "coinbase": {"inflow_usd": 220000000, "outflow_usd": 250000000},
                        "kraken": {"inflow_usd": 120000000, "outflow_usd": 130000000},
                    },
                    "chain_breakdown": {
                        "bitcoin": {"btc": 12500.5},
                        "ethereum": {"btc": 820.3},
                    },
                    "address_dedupe": {
                        "unique_addresses": 45230,
                        "internal_transfers_excluded": True,
                    },
                    "outflow_chart": [{"date": "2026-08-25", "outflow_usd": 920000000}],
                },
            },
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(efc, "_SEED_PATH", seed)
    monkeypatch.setattr(eih, "_SEED_PATH", seed)
    return seed


def test_closure_reconciliation(isolated_seed):
    rec = efc.reconcile_flows(850_000_000, 920_000_000, -70_000_000)
    assert rec["reconciled"] is True
    assert "Inflow - Outflow = Netflow" in rec["closure_display"]
    assert "Reconciled: Yes" in rec["closure_display"]
    assert "Netflow = Inflow - Outflow" in rec["netflow_display"]
    assert "Verified: Yes" in rec["netflow_display"]


def test_closure_variance_alert():
    rec = efc.reconcile_flows(100_000_000, 80_000_000, 10_000_000)
    assert rec["reconciled"] is False
    assert rec["internal_alert"] is True
    assert "Reconciled: No" in rec["closure_display"]


def test_cluster_versioned(isolated_seed):
    seed = json.loads(isolated_seed.read_text())
    cluster = efc.build_cluster_metadata(seed)
    assert "Exchange Cluster v4.2" in cluster["display"]
    assert "Binance: 1250" in cluster["display"]
    assert "Last Updated: 2026-08-25" in cluster["display"]


def test_exchange_breakdown_required(isolated_seed):
    seed = json.loads(isolated_seed.read_text())
    breakdown = seed["assets"]["BTC"]["exchange_breakdown"]
    result = efc.build_exchange_breakdown(breakdown, flow_key="outflow_usd")
    assert len(result["entries"]) == 3
    assert "Total:" in result["display"]
    assert "Binance:" in result["display"]


def test_address_dedupe(isolated_seed):
    seed = json.loads(isolated_seed.read_text())
    dedupe = efc.build_address_dedupe(seed["assets"]["BTC"]["address_dedupe"])
    assert dedupe["internal_transfers_excluded"] is True
    assert "Unique addresses analyzed: 45,230" in dedupe["display"]


def test_chain_validation(isolated_seed):
    seed = json.loads(isolated_seed.read_text())
    chain = efc.build_chain_validation(seed["assets"]["BTC"]["chain_breakdown"])
    assert "Bitcoin:" in chain["display"]
    assert "Ethereum:" in chain["display"]


def test_outflow_anomaly_detection(isolated_seed):
    dash = eoi.build_outflow_dashboard("BTC")
    assert dash["ok"] is True
    anomaly = dash["anomaly"]
    assert anomaly is not None
    assert "Outflow Spike:" in anomaly["display"]
    assert anomaly["label"] == "Elevated Outflow Detected"
    assert "collapsing" not in anomaly["display"].lower()
    assert "withdraw now" not in anomaly["display"].lower()


def test_no_sell_language(isolated_seed):
    dash = eoi.build_outflow_dashboard("BTC")
    text = json.dumps(dash)
    assert "Withdraw from" not in text
    assert "sell" not in dash["context_display"].lower()
    assert dash["no_sell_language"] is True
    assert dash["risk_context_only"] is True


def test_disclaimer_non_hideable(isolated_seed):
    dash = eoi.build_outflow_dashboard("BTC")
    assert dash["disclaimer_hideable"] is False
    assert "Not investment advice" in dash["disclaimer"]


def test_not_standalone(isolated_seed):
    dash = eoi.build_outflow_dashboard("BTC")
    assert dash["standalone"] is False
    assert "Exchange Intelligence Hub" in dash["merged_into"]
    status = eoi.exchange_outflow_status()
    assert status["standalone"] is False


def test_hub_integration(isolated_seed):
    hub = eih.build_exchange_intelligence_hub("BTC")
    assert hub["ok"] is True
    assert hub["standalone"] is False
    assert "outflow" in hub["tabs"]
    assert "inflow" in hub["tabs"]
    assert "netflow" in hub["tabs"]
    assert hub["modules"]["outflow"]["feature_id"] == 242
    assert "Reconciled: Yes" in hub["closure"]


def test_outflow_includes_closure(isolated_seed):
    dash = eoi.build_outflow_dashboard("BTC")
    rec = dash["reconciliation"]
    assert rec["inflow_usd"] == 850_000_000
    assert rec["outflow_usd"] == 920_000_000
    assert rec["netflow_usd"] == -70_000_000


def test_hub_status(isolated_seed):
    status = eih.exchange_intelligence_hub_status()
    assert status["feature_id"] == 734
    assert status["standalone"] is False
    assert status["acceptance_criteria"]["closure_inflow_outflow_netflow"] is True


def test_full_seed_reconciliation():
    seed_data = json.loads(efc._SEED_PATH.read_text(encoding="utf-8"))
    for sym, data in seed_data["assets"].items():
        rec = efc.reconcile_flows(data["inflow_usd"], data["outflow_usd"], data["netflow_usd"])
        assert rec["reconciled"] is True, f"{sym} failed reconciliation"


def test_api_routes(isolated_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/market-radar/exchange-hub/status").status_code == 200
    hub = c.get("/api/platform/market-radar/exchange-hub/dashboard?asset=BTC")
    assert hub.status_code == 200
    assert hub.json()["standalone"] is False
    outflow = c.get("/api/platform/market-radar/exchange-hub/outflow?asset=BTC")
    assert outflow.status_code == 200
    assert outflow.json()["feature_id"] == 242
    assert c.get("/api/platform/market-radar/exchange-hub/outflow?asset=FAKE").status_code == 404
