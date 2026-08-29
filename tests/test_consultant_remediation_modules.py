"""Tests for consultant-remediation modules."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_reconciliation_shape(monkeypatch):
    async def fake_internal(symbol):
        return 100.0

    async def fake_ref(symbol):
        return 100.5

    import reconciliation_engine as re

    monkeypatch.setattr(re, "_internal_price", fake_internal)
    monkeypatch.setattr(re, "_fetch_binance_spot", fake_ref)
    out = await re.reconcile_symbol("BTC/USDT", threshold_bps=100)
    assert out["reference_exchange"] == "binance"
    assert "deviation_bps" in out


def test_feature_flags_default_and_override(monkeypatch, tmp_path):
    import config
    import feature_flags as ff

    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    monkeypatch.setattr(ff, "_FLAGS_PATH", tmp_path / "feature_flags.json")
    assert ff.is_enabled("arbitrage_scanner") is True
    monkeypatch.setenv("FEATURE_FLAG_ARBITRAGE_SCANNER", "false")
    assert ff.is_enabled("arbitrage_scanner") is False


def test_experiment_registry_register(tmp_path, monkeypatch):
    import config
    import experiment_registry as er

    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    monkeypatch.setattr(er, "_REGISTRY", tmp_path / "experiment_registry.jsonl")
    row = er.register_experiment(
        name="oracle_v2",
        hypothesis="Better calibration",
        model_id="oracle_direction_latest",
        owner="ci",
        status="shadow",
    )
    assert row["experiment_id"].startswith("exp_")
    summary = er.mrm_summary()
    assert summary["total"] >= 1


@pytest.mark.asyncio
async def test_data_lineage_graph():
    from data_lineage_viz import build_lineage_graph

    graph = await build_lineage_graph(symbol="BTC/USDT")
    assert any(n["id"] == "engine" for n in graph["nodes"])
    assert graph["edges"]
