"""Tests — Batch 26: #945/#1003/#1010, #986/#1004, #1001, #1005, #1007/#1009."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import data_engine_native_sql_workspace as sql_ws
from bd_platform import data_engine_provenance_layer as prov
from bd_platform import intelligence_ledger_sector_comparables as sector
from bd_platform import intelligence_ledger_tokenomics as tokenomics
from bd_platform import protocol_kpi_intelligence as kpi


@pytest.fixture
def prov_seed() -> dict:
    return json.loads(Path("data/data_engine_provenance_layer_seed.json").read_text(encoding="utf-8"))


@pytest.fixture
def kpi_seed() -> dict:
    return json.loads(Path("data/protocol_kpi_intelligence_seed.json").read_text(encoding="utf-8"))


@pytest.fixture
def sector_seed() -> dict:
    return json.loads(Path("data/intelligence_ledger_sector_comparables_seed.json").read_text(encoding="utf-8"))


@pytest.fixture
def sql_seed() -> dict:
    return json.loads(Path("data/data_engine_native_sql_workspace_seed.json").read_text(encoding="utf-8"))


@pytest.fixture
def tokenomics_seed() -> dict:
    return json.loads(Path("data/intelligence_ledger_tokenomics_seed.json").read_text(encoding="utf-8"))


# --- #945 / #1003 / #1010 ---


def test_945_status(prov_seed):
    status = prov.provenance_layer_status_945(seed=prov_seed)
    assert status["standalone_rejected"] is True
    assert status["every_metric_tagged"] is True
    assert status["end_to_end_traceability"] is True


def test_1003_metric_tagged(prov_seed):
    tagged = prov.tag_metric_provenance_1003(
        "btc_tvl",
        source_type="on_chain",
        transformation="sum_locked_assets",
        transformation_version="1.0.0",
        raw_source={"rpc_node": "eth-mainnet", "block_number": 21000000},
        seed=prov_seed,
    )
    assert tagged["provenance"]["end_to_end_traceable"] is True
    badge = prov.build_provenance_badge_1003(tagged)
    assert badge["badge"]["clickable"] is True


def test_1003_lineage_audit(prov_seed):
    audit = prov.get_lineage_audit_1003("aave_tvl", seed=prov_seed)
    assert audit["raw_to_user_traceable"] is True


def test_1010_data_quality(prov_seed):
    dq = prov.run_data_quality_check_1010("defi_protocol_metrics", seed=prov_seed)
    assert dq["ok"] is True


def test_945_e2e(prov_seed):
    e2e = prov.run_provenance_layer_e2e(seed=prov_seed)
    assert e2e["all_passed"] is True


# --- #986 / #1004 ---


def test_986_status(kpi_seed):
    status = kpi.protocol_kpi_status_986(seed=kpi_seed)
    assert status["standalone_rejected"] is True
    assert status["definitions_public"] is True


def test_1004_definitions(kpi_seed):
    defs = kpi.get_standard_definitions_1004(seed=kpi_seed)
    assert "excluding token incentives" in defs["definitions"]["revenue"]["definition"].lower()


def test_986_morpho_edge_case(kpi_seed):
    mapping = kpi.get_protocol_mapping_audit("morpho", seed=kpi_seed)
    assert mapping["edge_cases_documented"] is True


def test_986_reconciliation(kpi_seed):
    norm = kpi.normalize_protocol_metrics_986("gmx", seed=kpi_seed)
    assert norm["ok"] is True
    assert "variances" in norm["reconciliation"]


def test_986_e2e(kpi_seed):
    e2e = kpi.run_protocol_kpi_e2e(seed=kpi_seed)
    assert e2e["all_passed"] is True


# --- #1001 ---


def test_1001_status(sector_seed):
    status = sector.sector_comparables_status_1001(seed=sector_seed)
    assert status["constituents_transparent"] is True
    assert status["taxonomy_lock"] is True


def test_1001_dashboard(sector_seed):
    dash = sector.build_sector_dashboard_1001("lending", seed=sector_seed)
    assert dash["ok"] is True
    assert dash["constituents_transparent"] is True
    assert len(dash["constituents"]) >= 2
    assert "hhi_index" in dash["concentration"]


def test_1001_scope_lock(sector_seed):
    out = sector.build_sector_dashboard_1001("nft", seed=sector_seed)
    assert out["error"] == "sector_out_of_scope"


def test_1001_e2e(sector_seed):
    e2e = sector.run_sector_comparables_e2e(seed=sector_seed)
    assert e2e["all_passed"] is True


# --- #1005 ---


def test_1005_backtest(sql_seed):
    rules = [{"signal": "buy", "threshold": 35}, {"signal": "sell", "threshold": 65}]
    r1 = sql_ws.run_backtest_sandbox_1005(strategy_rules=rules, seed=42, seed_data=sql_seed)
    r2 = sql_ws.run_backtest_sandbox_1005(strategy_rules=rules, seed=42, seed_data=sql_seed)
    assert r1["ok"] is True
    assert r1["result_hash"] == r2["result_hash"]
    assert r1["no_look_ahead"] is True
    assert r1["no_execution"] is True


def test_1005_e2e(sql_seed):
    e2e = sql_ws.run_backtesting_e2e_1005(seed=sql_seed)
    assert e2e["all_passed"] is True


# --- #1007 / #1009 ---


def test_1007_allocation(tokenomics_seed):
    alloc = tokenomics.build_allocation_analysis_1007("arb", seed=tokenomics_seed)
    assert alloc["ok"] is True
    assert alloc["reconciled"] is True
    assert all(a.get("documented") for a in alloc["allocations"])


def test_1009_vesting(tokenomics_seed):
    vesting = tokenomics.compute_vesting_curve_1009("arb", as_of="2026-08-28T00:00:00Z", seed=tokenomics_seed)
    assert vesting["ok"] is True
    assert vesting["exact_recomputation"] is True
    assert vesting["schedule"]["assumptions_visible"] is True


def test_tokenomics_e2e(tokenomics_seed):
    e2e = tokenomics.run_tokenomics_e2e(seed=tokenomics_seed)
    assert e2e["all_passed"] is True
