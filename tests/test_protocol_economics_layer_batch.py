"""Tests — Protocol Economics Layer epic #554 #555."""

from __future__ import annotations

import json

import pytest

from bd_platform import protocol_economics_layer as pel


@pytest.fixture
def economics_seed(tmp_path, monkeypatch):
    p = tmp_path / "protocol_economics_layer_seed.json"
    p.write_text(json.dumps({
        "protocols": {
            "uniswap": {
                "name": "Uniswap V3",
                "gross_fees_usd": 1000000.0,
                "protocol_revenue_usd": 0.0,
                "fees_not_equal_revenue": True,
                "fees_24h_usd": 50000.0,
                "fees_7d_usd": 300000.0,
                "fees_30d_usd": 900000.0,
                "revenue_24h_usd": 0.0,
                "revenue_7d_usd": 0.0,
                "revenue_30d_usd": 0.0,
                "source": "onchain_indexer",
                "freshness_seconds": 300,
                "fee_events": [
                    {
                        "tx_hash": "0x001",
                        "contract_address": "0xuni_factory",
                        "event_type": "Swap",
                        "fee_usd": 100.0,
                        "timestamp": "2026-08-26T10:00:00Z",
                    },
                    {
                        "tx_hash": "0x002",
                        "contract_address": "0xuni_factory",
                        "event_type": "Swap",
                        "fee_usd": 200.0,
                        "timestamp": "2026-08-26T10:05:00Z",
                    },
                ],
            },
            "aave": {
                "name": "Aave V3",
                "gross_fees_usd": 500000.0,
                "protocol_revenue_usd": 100000.0,
                "fees_not_equal_revenue": True,
                "fees_24h_usd": 25000.0,
                "fees_7d_usd": 150000.0,
                "fees_30d_usd": 450000.0,
                "revenue_24h_usd": 5000.0,
                "revenue_7d_usd": 30000.0,
                "revenue_30d_usd": 90000.0,
                "source": "onchain_indexer",
                "freshness_seconds": 420,
                "fee_events": [
                    {
                        "tx_hash": "0x003",
                        "contract_address": "0xaave_pool",
                        "event_type": "ReserveDataUpdated",
                        "fee_usd": 500.0,
                        "timestamp": "2026-08-26T10:00:00Z",
                    },
                ],
            },
        },
        "contract_mappings": {
            "uniswap": {
                "version": "1.0",
                "source": "protocol_registry",
                "fee_event_signatures": ["Swap(...)"],
                "contracts": [
                    {
                        "address": "0xuni_factory",
                        "name": "UniswapV3Factory",
                        "chain": "ethereum",
                        "fee_type": "swap_fee",
                    },
                ],
            },
            "aave": {
                "version": "1.0",
                "source": "protocol_registry",
                "fee_event_signatures": ["ReserveDataUpdated(...)"],
                "contracts": [
                    {
                        "address": "0xaave_pool",
                        "name": "Pool",
                        "chain": "ethereum",
                        "fee_type": "borrow_interest",
                    },
                ],
            },
        },
    }), encoding="utf-8")
    monkeypatch.setattr(pel, "_SEED_PATH", p)
    return p


def test_epic_status_merged_not_standalone(economics_seed):
    status = pel.protocol_economics_layer_status()
    assert status["standalone_rejected"] is True
    assert status["tasks_not_tickets"] is True
    assert set(status["feature_ids"]) == {554, 555}
    assert status["dependencies"]["asset_profiles_feature_id"] == 516


def test_definitions_explicit_fees_not_revenue(economics_seed):
    definitions = pel.build_definitions_block()
    assert definitions["definitions_explicit"] is True
    assert definitions["fees_vs_revenue_distinction"] is True
    assert definitions["definitions"]["fees"]["not_equal_to"] == "revenue"
    assert definitions["definitions"]["revenue"]["not_equal_to"] == "fees"
    assert "DeFi" in definitions["definitions"]["fees_vs_revenue"]["definition"]


def test_555_fees_intelligence_contract_mapping(economics_seed):
    seed = json.loads(economics_seed.read_text(encoding="utf-8"))
    fees = pel.build_fees_intelligence("uniswap", seed=seed)

    assert fees["gross_fees_usd"] == 300.0
    assert fees["contract_mapping"]["contract_mapping"] is True
    assert fees["contract_mapping"]["contract_count"] == 1
    assert fees["historical_qa_applied"] is True


def test_555_gross_fees_normalization(economics_seed):
    seed = json.loads(economics_seed.read_text(encoding="utf-8"))
    events = seed["protocols"]["uniswap"]["fee_events"]
    normalized = pel.normalize_gross_fees(events, protocol_id="uniswap", seed=seed)

    assert normalized["total_gross_fees_usd"] == 300.0
    assert normalized["event_count"] == 2
    assert normalized["historical_qa_applied"] is True


def test_554_fees_revenue_dashboard(economics_seed):
    seed = json.loads(economics_seed.read_text(encoding="utf-8"))
    dashboard = pel.build_fees_revenue_dashboard("uniswap", seed=seed)

    assert dashboard["fees"]["gross_fees_usd"] == 1000000.0
    assert dashboard["revenue"]["protocol_revenue_usd"] == 0.0
    assert dashboard["fees_not_equal_revenue"] is True
    assert dashboard["definitions"]["definitions_explicit"] is True
    assert "definition" in dashboard["fees"]
    assert "definition" in dashboard["revenue"]


def test_554_aave_fees_greater_than_revenue(economics_seed):
    seed = json.loads(economics_seed.read_text(encoding="utf-8"))
    dashboard = pel.build_fees_revenue_dashboard("aave", seed=seed)

    assert dashboard["fees"]["gross_fees_usd"] > dashboard["revenue"]["protocol_revenue_usd"]
    assert dashboard["revenue"]["revenue_share_of_fees_pct"] == 20.0


def test_epic_panel_all_sub_modules(economics_seed):
    panel = pel.build_protocol_economics_panel(protocol_id="uniswap")
    assert panel["ok"] is True
    assert "554_fees_and_revenue" in panel["sub_modules"]
    assert "555_fees_intelligence" in panel["sub_modules"]
    assert panel["definitions"]["definitions_explicit"] is True
    assert panel["acceptance_criteria"]["fees_vs_revenue_distinction"] is True


def test_historical_qa_tests(economics_seed):
    tests = pel.run_historical_qa_tests()
    assert tests["all_passed"] is True
    test_names = [t["test"] for t in tests["historical_qa_tests"]]
    assert "definitions_explicit" in test_names
    assert "fees_not_equal_revenue_defined" in test_names
    assert "contract_mapping_uniswap" in test_names
    assert "revenue_lte_fees_uniswap" in test_names


def test_api_routes(economics_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get(
        "/api/platform/intelligence-ledger/data-layer/protocol-economics/status"
    ).status_code == 200
    assert c.get(
        "/api/platform/intelligence-ledger/data-layer/protocol-economics?protocol_id=uniswap"
    ).status_code == 200
    assert c.get(
        "/api/platform/intelligence-ledger/data-layer/protocol-economics/historical-qa"
    ).status_code == 200
