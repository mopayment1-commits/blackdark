"""Tests — #902 No-Code Analytics, #904 Watchlists, #907 Exchange Sync, #918 Tax PnL."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import data_engine_native_sql_workspace as sql_ws
from bd_platform import portfolio_ai_exchange_connectors as exch
from bd_platform import portfolio_ai_tax_pnl as tax
from bd_platform import portfolio_ai_watchlists as wl


@pytest.fixture
def sql_seed() -> dict:
    return json.loads(Path("data/data_engine_native_sql_workspace_seed.json").read_text(encoding="utf-8"))


@pytest.fixture
def wl_seed() -> dict:
    return json.loads(Path("data/portfolio_ai_watchlists_seed.json").read_text(encoding="utf-8"))


@pytest.fixture
def exch_seed() -> dict:
    return json.loads(Path("data/portfolio_ai_exchange_connectors_seed.json").read_text(encoding="utf-8"))


@pytest.fixture
def tax_seed() -> dict:
    return json.loads(Path("data/portfolio_ai_tax_pnl_seed.json").read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def reset_state():
    sql_ws.reset_native_sql_workspace_state()
    wl.reset_watchlists_state_904()
    exch.reset_exchange_connectors_state_907()
    yield
    sql_ws.reset_native_sql_workspace_state()
    wl.reset_watchlists_state_904()
    exch.reset_exchange_connectors_state_907()


# --- #978 + #902 ---


def test_978_status(sql_seed):
    status = sql_ws.native_sql_workspace_status_978(seed=sql_seed)
    assert status["standalone_rejected"] is True
    assert "no_code_builder" in status["tabs"]
    assert status["formulas_translate_to_sql"] is True
    assert status["sandbox_read_only"] is True


def test_902_formula_validation(sql_seed):
    ok = sql_ws.validate_formula_902("price_change_pct > 5 AND volume_usd >= 1000000", seed=sql_seed)
    assert ok["formula_valid"] is True
    assert ok["rule_based_only"] is True

    ml = sql_ws.validate_formula_902("predict(price) > 0.5", seed=sql_seed)
    assert ml["error"] == "ml_formula_rejected"


def test_902_sql_compilation(sql_seed):
    compiled = sql_ws.translate_formula_to_sql_902(
        "price_change_pct > 5", tenant_id="tenant_alpha", seed=sql_seed
    )
    assert "SELECT" in compiled["compiled_sql"]
    assert compiled["read_only"] is True
    assert compiled["rls_enforced"] is True


def test_902_execute_and_export(sql_seed):
    result = sql_ws.execute_workspace_query(
        user_id="user_pro",
        tenant_id="tenant_alpha",
        tier="pro",
        formula="price_change_pct > 5 AND volume_usd >= 1000000",
        seed=sql_seed,
    )
    assert result["read_only"] is True
    assert result["fee_db"]["total_usd"] > 0

    export = sql_ws.export_workspace_results(result["rows"], fmt="csv")
    assert export["export_parity"] is True
    assert export["checksum_sha256"]


def test_902_reproducibility(sql_seed):
    saved = sql_ws.save_workspace_query(
        user_id="user_pro",
        tenant_id="tenant_alpha",
        name="Test query",
        formula="price_change_pct > 5",
        seed=sql_seed,
    )
    assert saved["saved_query"]["dataset_version"] is not None
    assert saved["saved_query"]["reproducible"] is True


def test_902_e2e(sql_seed):
    e2e = sql_ws.run_native_sql_workspace_e2e(seed=sql_seed)
    assert e2e["all_passed"] is True


# --- #904 ---


def test_904_status(wl_seed):
    status = wl.watchlists_status_904(seed=wl_seed)
    assert status["standalone_rejected"] is True
    assert "portfolio_ai" in status["surfaces"]
    assert status["tier_limits"]["free"]["max_watchlists"] == 3


def test_904_crud(wl_seed):
    created = wl.create_watchlist_904(
        user_id="u1",
        tenant_id="t1",
        tier="pro",
        name="Core",
        surface="portfolio_ai",
        asset_ids=["BTC", "ETH"],
        seed=wl_seed,
    )
    assert created["ok"] is True
    wl_id = created["watchlist"]["watchlist_id"]

    updated = wl.update_watchlist_904(
        wl_id, user_id="u1", tenant_id="t1", tier="pro", asset_ids=["BTC", "ETH", "SOL"]
    )
    assert updated["ok"] is True

    listed = wl.list_watchlists_904(user_id="u1", tenant_id="t1")
    assert listed["count"] == 1

    deleted = wl.delete_watchlist_904(wl_id, user_id="u1", tenant_id="t1")
    assert deleted["ok"] is True


def test_904_tenant_isolation(wl_seed):
    created = wl.create_watchlist_904(
        user_id="u1",
        tenant_id="t1",
        tier="pro",
        name="Private",
        surface="portfolio_ai",
        asset_ids=["BTC"],
        seed=wl_seed,
    )
    wl_id = created["watchlist"]["watchlist_id"]
    cross = wl.update_watchlist_904(wl_id, user_id="u2", tenant_id="t2", tier="pro", name="Hack")
    assert cross["error"] == "cross_tenant_access_denied"


def test_904_e2e(wl_seed):
    e2e = wl.run_watchlists_e2e_904(seed=wl_seed)
    assert e2e["all_passed"] is True


# --- #907 ---


def test_907_status(exch_seed):
    status = exch.exchange_connectors_status_907(seed=exch_seed)
    assert status["standalone_rejected"] is True
    assert status["read_only_by_default"] is True
    assert status["non_custodial"] is True


def test_907_trading_rejected(exch_seed):
    result = exch.connect_exchange_account_907(
        user_id="u1",
        tenant_id="t1",
        exchange="binance",
        account_label="main",
        api_key_hint="key",
        permissions=["read", "trade"],
        seed=exch_seed,
    )
    assert result["error"] == "trading_permissions_rejected"


def test_907_sync_and_consolidate(exch_seed):
    acct = exch.connect_exchange_account_907(
        user_id="u1",
        tenant_id="t1",
        exchange="binance",
        account_label="main",
        api_key_hint="key",
        permissions=["read"],
        seed=exch_seed,
    )
    sync = exch.sync_exchange_account_907(
        acct["account"]["account_id"], user_id="u1", tenant_id="t1", seed=exch_seed
    )
    assert sync["checkpoint_updated"] is True

    view = exch.build_consolidated_view_907(user_id="u1", tenant_id="t1", seed=exch_seed)
    assert view["non_custodial"] is True
    assert view["account_count"] == 1


def test_907_e2e(exch_seed):
    e2e = exch.run_exchange_connectors_e2e_907(seed=exch_seed)
    assert e2e["all_passed"] is True


# --- #918 ---


def test_918_status(tax_seed):
    status = tax.tax_pnl_status_918(seed=tax_seed)
    assert status["standalone_rejected"] is True
    assert status["tax_estimate_not_filing"] is True
    assert status["default_method"] == "fifo"


def test_918_fifo_report(tax_seed):
    report = tax.build_tax_pnl_report_918(
        user_id="u1", tenant_id="t1", method="fifo", seed=tax_seed
    )
    assert report["ok"] is True
    assert report["reconciliation"]["passed"] is True
    assert report["fee_attribution"] is True
    assert len(report["edge_cases"]) >= 1


def test_918_export(tax_seed):
    report = tax.build_tax_pnl_report_918(
        user_id="u1", tenant_id="t1", method="fifo", seed=tax_seed
    )
    csv_out = tax.export_tax_pnl_report_918(report, fmt="csv")
    assert csv_out["ok"] is True
    assert csv_out["checksum_sha256"]
    assert "TOTAL" in csv_out["content"]


def test_918_e2e(tax_seed):
    e2e = tax.run_tax_pnl_e2e_918(seed=tax_seed)
    assert e2e["all_passed"] is True
