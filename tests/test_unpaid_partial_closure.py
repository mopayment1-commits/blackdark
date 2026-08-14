"""Unpaid partial-closure wave — historical grade, options OMS, SCIM org key, GQL."""

from __future__ import annotations

import pytest


def test_historical_self_grade_independent():
    from historical_self_grade import grade_historical_oracle_outcomes

    out = grade_historical_oracle_outcomes()
    assert out["independent_of_this_tick"] is True
    assert out["same_tick_withheld"] is True
    assert "resolved_count" in out
    assert out["learning_self_grade"] is bool(out.get("ok") and int(out.get("resolved_count") or 0) >= 1)


def test_decision_e2e_same_tick_never_self_grades():
    from decision_e2e import run_decision_e2e

    out = run_decision_e2e(symbol="BTC/USDT", org_id="e2e_hist", notional=10_000.0)
    assert out["ok"] is True
    d = out["decision_object"]
    assert d["same_tick_self_grade"] is False
    assert d["historical_self_grade"]["same_tick_withheld"] is True
    assert d["historical_self_grade"]["independent_of_this_tick"] is True


@pytest.mark.asyncio
async def test_options_paper_oms_no_live_flag():
    from options_oms import chain_snapshot, list_orders, paper_fill

    snap = await chain_snapshot("BTC")
    assert snap["live_execution"] is False
    filled = await paper_fill(instrument="BTC-PERPETUAL", side="buy", quantity=1)
    assert filled["ok"] is True
    assert filled["live_execution"] is False
    assert filled["order"]["state"] == "FILL"
    assert filled["order"]["fill_type"] == "paper_mark"
    assert list_orders(limit=5)


def test_org_scim_key_roundtrip():
    from org_tenant import create_org, issue_org_scim_key, verify_org_scim_key
    from scim_service import require_scim_bearer

    org = create_org(name="SCIM Co", owner_email="scim-owner@example.com")
    issued = issue_org_scim_key(org["org_id"], actor_email="scim-owner@example.com")
    assert issued["api_key"].startswith("bd_scim_")
    hit = verify_org_scim_key(issued["api_key"])
    assert hit and hit["org_id"] == org["org_id"]
    scoped = require_scim_bearer(f"Bearer {issued['api_key']}")
    assert scoped["scope"] == "org"
    assert scoped["org_id"] == org["org_id"]


def test_arb_catalog_promotions_and_arabic():
    from arbitrage_catalog import get_catalog

    cat = get_catalog()
    by_id = {t["id"]: t for t in cat["types"]}
    assert by_id[2]["status"] == "live"
    assert by_id[2]["engine_kind"] == "cex_dex"
    assert by_id[7]["status"] == "proxy"
    assert by_id[20]["status"] == "proxy"
    assert by_id[1]["name_ar"]
    assert cat["counts_by_status"]["planned"] >= 1


@pytest.mark.asyncio
async def test_graphql_capability_inventory():
    from graphql_schema import schema

    result = await schema.execute(
        "{ capabilityInventory { total works partial opsConfig externalBlock institutionalVerdict } }"
    )
    assert result.errors is None
    inv = result.data["capabilityInventory"]
    assert inv["total"] >= 85
    assert inv["institutionalVerdict"] == "NOT_COMPLETE"
    assert inv["partial"] <= 5
    assert inv["externalBlock"] >= 2


def test_inventory_unpaid_closure_mix():
    from product_capability_inventory import capability_catalog, inventory_summary

    rows = capability_catalog()
    by_id = {r["id"]: r for r in rows}
    assert by_id["OR-E2E"]["status"] == "works"
    assert by_id["MKT-OPT"]["status"] == "works"
    assert by_id["B2B-SCIM"]["status"] == "works"
    assert by_id["EX-LIVE"]["status"] == "external_block"
    assert by_id["FUND-HA"]["status"] == "external_block"
    assert by_id["MKT-L2"]["status"] == "partial"
    assert by_id["BIL-CHECKOUT"]["status"] == "ops_config"
    assert by_id["ID-OAUTH"]["status"] == "ops_config"
    s = inventory_summary(rows)
    assert s["works"] >= 75
    assert s["partial"] <= 2
    assert s["external_block"] >= 3
