"""Tests — #42 Cross-Asset Correlation, #43 Cross-Chain Warehouse, #47 Decision Graph."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from bd_platform.cross_asset_correlation import (
    _pearson,
    _significance,
    compute_correlation_matrix,
    correlation_view_for_asset,
    portfolio_correlation_enrichment,
)
from bd_platform.cross_chain_warehouse import (
    CHAIN_SEMANTICS,
    bootstrap_chain_registry,
    ingest_transactions,
    list_chain_semantics,
    query_warehouse_transactions,
    warehouse_status,
)
from bd_platform.decision_graph import build_causal_decision_graph, expand_node


def test_pearson_perfect_negative():
    x = [0.01, -0.02, 0.03, -0.01, 0.02]
    y = [-0.01, 0.02, -0.03, 0.01, -0.02]
    r = _pearson(x, y)
    assert r is not None
    assert r < -0.9


def test_significance_strong_window():
    sig = _significance(-0.72, 30)
    assert sig["strength"] == "strong"
    assert sig["samples"] == 30
    assert sig["significant"] is True


def test_portfolio_correlation_enrichment():
    holdings = [
        {"symbol": "BTC", "value_usd": 6000},
        {"symbol": "ETH", "value_usd": 4000},
    ]
    matrix = {
        "BTC": {"SPX": {"correlation": 0.5}},
        "ETH": {"SPX": {"correlation": 0.8}},
    }
    out = portfolio_correlation_enrichment(holdings, matrix=matrix)
    assert out["correlation_enriched"] is True
    assert out["weighted_spx_correlation"] == pytest.approx(0.62, abs=0.01)


@pytest.mark.asyncio
async def test_correlation_matrix_mocked():
    async def fake_returns(asset_key: str, *, window: int):
        if asset_key == "BTC":
            return [0.01, -0.02, 0.03, -0.01, 0.02] * 6, "mock"
        return [-0.01, 0.02, -0.03, 0.01, -0.02] * 6, "mock"

    with patch(
        "bd_platform.cross_asset_correlation._series_returns",
        side_effect=fake_returns,
    ):
        out = await compute_correlation_matrix(
            crypto_assets=["BTC"],
            tradfi_assets=["SPX"],
            window=30,
        )
    assert out["ok"] is True
    assert out["feature"] == "#42"
    assert out["matrix"]["BTC"]["SPX"]["correlation"] is not None


@pytest.mark.asyncio
async def test_correlation_view_for_asset():
    with patch(
        "bd_platform.cross_asset_correlation.compute_correlation_matrix",
        new=AsyncMock(
            return_value={
                "matrix": {
                    "BTC": {
                        "DXY": {
                            "correlation": -0.65,
                            "significance": {"significant": True, "strength": "strong"},
                        }
                    }
                },
                "latency_ms": 12,
                "window_days": 30,
            }
        ),
    ):
        out = await correlation_view_for_asset("BTC")
    assert out["ok"] is True
    assert out["asset"] == "BTC"
    assert any("DXY" in h for h in out["highlights"])


def test_warehouse_chain_semantics_documented():
    sem = list_chain_semantics()
    assert sem["count"] >= 6
    assert "ethereum" in sem["chains"]
    eth = CHAIN_SEMANTICS["ethereum"]
    assert eth["address_format"] == "evm_hex_0x"
    assert eth["semantics"]


def test_warehouse_ingest_and_query(tmp_path, monkeypatch):
    db = tmp_path / "data" / "warehouse" / "cross_chain_warehouse.db"
    monkeypatch.setattr("bd_platform.cross_chain_warehouse._DB_PATH", db)
    monkeypatch.setattr("bd_platform.cross_chain_warehouse._DATA_BASE", tmp_path / "data")

    bootstrap_chain_registry()
    row = {
        "tx_hash": "0xabc",
        "chain": "ethereum",
        "chain_id": 1,
        "from_address": "0xfrom",
        "to_address": "0xto",
        "value_native": 1.0,
        "value_usd": None,
        "token_symbol": "ETH",
        "timestamp": 1700000000,
        "action_type": "transfer",
        "source": "test",
        "semantics": "point_in_time",
    }
    ing = ingest_transactions([row], mirror_to_index=False)
    assert ing["written_sql"] == 1
    q = query_warehouse_transactions(chain="ethereum", limit=10)
    assert q["ok"] is True
    assert q["count"] == 1
    status = warehouse_status()
    assert status["feature"] == "#43"
    assert status["semantics_documented"] is True


@pytest.mark.asyncio
async def test_decision_graph_causal_mocked():
    fake_inputs = {
        "ok": True,
        "risk_score_delta": 2.0,
        "headlines": ["Test headline"],
        "twelvedata_macro": {
            "ok": True,
            "correlation_narrative": "Bitcoin down 3% while DXY up 0.5%",
            "headline": "Macro stress",
        },
        "exchange_flows": {
            "ok": True,
            "headline": "Large ETH inflow to exchange",
            "risk_score_delta": 1.5,
        },
        "order_flow_intelligence": {"ok": False},
        "news_context": {"ok": False},
        "futures_cvd": {"ok": False},
    }
    with patch(
        "bd_platform.decision_engine_inputs.gather_decision_inputs",
        new=AsyncMock(return_value=fake_inputs),
    ), patch(
        "database.fetch_labeled_oracle_predictions",
        new=AsyncMock(return_value=[]),
    ):
        graph = await build_causal_decision_graph(asset="BTC", limit=20)

    assert graph["ok"] is True
    assert graph["feature"] == "#47"
    assert graph["interactive"] is True
    assert graph["causal"] is True
    assert len(graph["nodes"]) >= 2
    assert any(e.get("relation") in {"because", "then", "influenced"} for e in graph["edges"])
    assert graph["sla_met"] is True

    node_id = graph["nodes"][0]["id"]
    expanded = await expand_node(node_id=node_id, asset="BTC")
    assert expanded["ok"] is True
    assert expanded["node"]["id"] == node_id
