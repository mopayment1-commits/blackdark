"""Tests — #603 Supply Distribution Intelligence merged into #577 On-Chain Metrics Library."""

from __future__ import annotations

import json

import pytest

from bd_platform import onchain_metrics_library as oml


@pytest.fixture
def metrics_seed(tmp_path, monkeypatch):
    eth_holders = [
        {"address": "0x0000000000000000000000000000000000000001", "balance": 0.05},
        {"address": "0x0000000000000000000000000000000000000002", "balance": 0.5},
        {"address": "0x0000000000000000000000000000000000000003", "balance": 5.0},
        {"address": "0x0000000000000000000000000000000000000004", "balance": 50.0},
        {"address": "0x0000000000000000000000000000000000000005", "balance": 500.0},
        {"address": "0x0000000000000000000000000000000000000006", "balance": 5000.0},
        {"address": "0x0000000000000000000000000000000000000008", "balance": 11599444.445},
        {"address": "0x0000000000000000000000000000000000000009", "balance": 11599444.445},
        {"address": "0x000000000000000000000000000000000000000a", "balance": 11599444.445},
        {"address": "0x000000000000000000000000000000000000000b", "balance": 11599444.445},
        {"address": "0x000000000000000000000000000000000000000c", "balance": 11599444.445},
        {"address": "0x000000000000000000000000000000000000000d", "balance": 11599444.445},
        {"address": "0x000000000000000000000000000000000000000e", "balance": 11599444.445},
        {"address": "0x000000000000000000000000000000000000000f", "balance": 11599444.445},
        {"address": "0x0000000000000000000000000000000000000010", "balance": 11599444.445},
        {"address": "0x0000000000000000000000000000000000000011", "balance": 11599444.445},
        {"address": "0x28c6c06298d20db268d28021c6c480b4360329e7", "balance": 2500000.0},
        {"address": "0x21a31ee1afc51d94c2e590ca6e02e44ce58f9897", "balance": 1500000.0},
        {"address": "0xdac17f958d2ee523a2206206994597c13d831ec7", "balance": 500000.0},
    ]
    p = tmp_path / "onchain_metrics_library_seed.json"
    p.write_text(
        json.dumps(
            {
                "metric_definitions": {
                    "active_addresses": {
                        "name": "Active Addresses",
                        "formula": "count(distinct addresses)",
                        "formula_version": "1.0",
                        "source": "indexer",
                    }
                },
                "known_entities": {
                    "ETH": {
                        "exchange": [
                            {"address": "0x28c6c06298d20db268d28021c6c480b4360329e7", "name": "binance_hot"},
                            {"address": "0x21a31ee1afc51d94c2e590ca6e02e44ce58f9897", "name": "binance_cold"},
                        ],
                        "contract": [
                            {"address": "0xdac17f958d2ee523a2206206994597c13d831ec7", "name": "usdt_contract"},
                        ],
                        "bridge": [],
                    }
                },
                "assets": {
                    "ETH": {
                        "metrics": {
                            "active_addresses": {"value": 100, "available": True, "as_of": "2026-08-27T00:00:00Z"},
                        },
                        "supply_distribution_603": {
                            "circulating_supply": 120500000,
                            "prior_cohorts": {
                                "cohort_7": {"supply_share_pct": 12.0},
                            },
                            "holders": eth_holders,
                        },
                    }
                },
                "historical_qa": {"periods_tested": 12},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(oml, "_SEED_PATH", p)
    return p


def test_cohort_thresholds_versioned_seven_tiers():
    thresholds = oml.build_cohort_thresholds()
    assert thresholds["versioned"] is True
    assert thresholds["cohort_count"] == 7
    labels = [t["label"] for t in thresholds["thresholds"]]
    assert labels == ["0–0.1", "0.1–1", "1–10", "10–100", "100–1K", "1K–10K", "10K+"]


def test_supply_distribution_known_entities_handled(metrics_seed):
    panel = oml.build_supply_distribution_dashboard("ETH")
    assert panel["ok"] is True
    assert panel["standalone_rejected"] is True
    assert panel["merged_into"] == 577
    known = panel["known_entities"]
    assert known["handled"] is True
    assert known["excluded_from_retail_cohorts"] is True
    assert len(known["entities"]) == 3
    names = {e["entity_name"] for e in known["entities"]}
    assert "binance_hot" in names or any("Binance" in str(n) for n in names)


def test_supply_distribution_totals_reconcile(metrics_seed):
    panel = oml.build_supply_distribution_dashboard("ETH")
    totals = panel["totals"]
    assert totals["reconciled"] is True
    assert abs(totals["cohort_supply_total"] - totals["circulating_supply"]) < totals["reconciliation_tolerance"]


def test_supply_distribution_seven_cohorts_with_change(metrics_seed):
    panel = oml.build_supply_distribution_dashboard("ETH")
    assert len(panel["cohorts"]) == 7
    whale = next(c for c in panel["cohorts"] if c["cohort_id"] == "cohort_7")
    assert whale["label"] == "10K+"
    assert whale["change_share_pp"] is not None


def test_concentration_risk_for_token_scoring(metrics_seed):
    panel = oml.build_supply_distribution_dashboard("ETH")
    risk = panel["concentration_risk"]
    assert risk["concentration_risk_score"] is not None
    assert risk["band"] in {"low", "moderate", "elevated"}
    hook = panel["token_risk_scoring_hook"]
    assert hook["feature_id"] == 604
    assert hook["concentration_risk_score"] == risk["concentration_risk_score"]


def test_reconciliation_tests_all_pass(metrics_seed):
    qa = oml.run_supply_distribution_reconciliation_tests()
    assert qa["all_passed"] is True
    assert qa["test_count"] >= 4


def test_metrics_library_panel_includes_603_submodule(metrics_seed):
    panel = oml.build_metrics_library_panel("ETH")
    assert panel["epic_feature_id"] == 577
    assert panel["cohort_thresholds_versioned"] is True
    assert panel["known_entities_handled"] is True
    assert panel["totals_reconcile"] is True
    assert panel["sub_modules"]["603_supply_distribution"]["ok"] is True


def test_status_lists_603_absorbed():
    status = oml.onchain_metrics_library_status()
    assert status["epic_feature_id"] == 577
    assert "603" in status["sub_modules"]
    assert status["sub_modules"]["603"]["standalone_rejected"] is True


def test_api_routes(metrics_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/intelligence-ledger/onchain-layer/metrics-library/status").status_code == 200
    panel = c.get("/api/platform/intelligence-ledger/onchain-layer/metrics-library?asset=ETH")
    assert panel.status_code == 200
    assert panel.json().get("epic_feature_id") == 577
    dist = c.get("/api/platform/intelligence-ledger/onchain-layer/metrics-library/supply-distribution?asset=ETH")
    assert dist.status_code == 200
    assert dist.json().get("task_id") == "603"
    qa = c.get("/api/platform/intelligence-ledger/onchain-layer/metrics-library/supply-distribution/reconciliation-tests")
    assert qa.status_code == 200
    assert qa.json().get("all_passed") is True


@pytest.mark.asyncio
async def test_cap646_handlers_for_36_and_202(metrics_seed):
    from cap646.handlers.onchain import handle_onchain_capability

    cap36 = await handle_onchain_capability(36, params={"symbol": "ETH"})
    assert cap36.get("success") is True
    assert cap36.get("surface") == "on_chain_metrics_library"

    cap202 = await handle_onchain_capability(202, params={"symbol": "ETH"})
    assert cap202.get("success") is True
    assert cap202.get("merged_into") == 577
    assert cap202.get("standalone_rejected") is True
