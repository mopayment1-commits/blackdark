"""Institutional-quality unpaid closure — OMS lifecycle, time-separated grade, ops honesty."""

from __future__ import annotations

import pytest


def test_historical_self_grade_requires_time_separation(monkeypatch):
    from historical_self_grade import grade_historical_oracle_outcomes, _pair_independent_outcomes

    rows = [
        {
            "event": "prediction_created",
            "prediction_id": "1",
            "timestamp": "2026-08-01T00:00:00+00:00",
            "asset": "BTC",
            "price_at_prediction": 100,
            "resolved": False,
        },
        {
            "event": "prediction_resolved",
            "prediction_id": "1",
            "timestamp": "2026-08-01T00:00:10+00:00",
            "asset": "BTC",
            "label": "correct",
            "resolved": True,
            "price_at_prediction": 100,
            "price_after_24h": 110,
        },
        {
            "event": "prediction_created",
            "prediction_id": "2",
            "timestamp": "2026-08-01T00:00:00+00:00",
            "asset": "ETH",
            "resolved": False,
        },
        {
            "event": "prediction_resolved",
            "prediction_id": "2",
            "timestamp": "2026-08-02T00:00:00+00:00",
            "asset": "ETH",
            "label": "correct",
            "resolved": True,
            "price_after_24h": 12,
        },
    ]
    pairs = _pair_independent_outcomes(rows, min_delta_seconds=60)
    ids = {p["prediction_id"] for p in pairs}
    assert "1" not in ids  # 10s < 60s
    assert "2" in ids

    monkeypatch.setattr(
        "historical_self_grade._read_chain_rows",
        lambda: rows,
    )
    monkeypatch.setattr(
        "oracle_audit_chain.verify_chain",
        lambda: {"valid": True, "records": 4},
    )
    out = grade_historical_oracle_outcomes(min_delta_seconds=60)
    assert out["same_tick_withheld"] is True
    assert out["independent_of_this_tick"] is True
    assert out["independent_pairs"] == 1
    assert out["learning_self_grade"] is True


def test_decision_e2e_same_tick_never_self_grades():
    from decision_e2e import run_decision_e2e

    out = run_decision_e2e(symbol="BTC/USDT", org_id="e2e_hist", notional=10_000.0)
    assert out["ok"] is True
    d = out["decision_object"]
    assert d["same_tick_self_grade"] is False
    assert d["historical_self_grade"]["same_tick_withheld"] is True
    assert d["historical_self_grade"]["independent_of_this_tick"] is True
    assert out["product_complete"] is False


@pytest.mark.asyncio
async def test_options_oms_full_lifecycle_and_reject_unknown():
    from options_oms import paper_cycle, list_orders

    snap = {
        "ok": True,
        "instruments": [
            {
                "instrument": "BTC-29MAR24-100000-C",
                "mark_price": 0.05,
                "bid": 0.04,
                "ask": 0.06,
            }
        ],
    }
    filled = await paper_cycle(
        instrument="BTC-29MAR24-100000-C",
        side="buy",
        quantity=1,
        snapshot=snap,
    )
    assert filled["ok"] is True
    assert filled["live_execution"] is False
    states = [h["state"] for h in filled["order"]["history"]]
    assert states == [
        "INTENT",
        "VALIDATION",
        "RISK_CHECK",
        "ACK",
        "FILL",
        "RECONCILE",
    ]
    assert filled["order"]["state"] == "RECONCILE"

    rejected = await paper_cycle(
        instrument="NOT-A-REAL-OPTION",
        side="buy",
        quantity=1,
        snapshot=snap,
    )
    assert rejected["ok"] is False
    assert rejected["reason"] == "unknown_instrument"
    assert rejected["order"]["state"] == "RECONCILE"
    assert "FILL" not in [h["state"] for h in rejected["order"]["history"]]
    assert list_orders(limit=5)

    bad_qty = await paper_cycle(
        instrument="BTC-29MAR24-100000-C",
        side="buy",
        quantity=0,
        snapshot=snap,
    )
    assert bad_qty["ok"] is False
    assert bad_qty["reason"] == "validation_failed"


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


def test_l2_remainder_never_claims_complete():
    from l2_remainder import catalog_l2_remainder

    out = catalog_l2_remainder()
    assert out["product_complete"] is False
    assert out["full_mesh_l2_complete"] is False
    assert out["remainder_count"] >= 5
    assert all(v["depth_class"] == "synthetic_mid" for v in out["remainder"])
    assert any(v["id"] == "uniswap_v3" for v in out["remainder"])
    assert "synthetic_mid ≠ venue_l2" in out["honesty"] or "synthetic_mid" in out["honesty"]


def test_billing_unpaid_upgrade_and_oauth_503():
    from billing_service import unpaid_upgrade_path
    from fastapi.testclient import TestClient
    from dashboard import app

    path = unpaid_upgrade_path()
    assert path["unpaid_path_complete"] is True
    assert path["product_complete"] is False
    client = TestClient(app, follow_redirects=False)
    unpaid = client.get("/api/billing/unpaid-upgrade")
    assert unpaid.status_code == 200
    assert unpaid.json()["unpaid_path_complete"] is True
    oauth_status = client.get("/api/auth/oauth/status")
    assert oauth_status.status_code == 200
    oauth_body = oauth_status.json()
    assert oauth_body["unpaid_protocol_complete"] is True
    start = client.get("/api/auth/oauth/google/start")
    if oauth_body.get("live_idp"):
        assert start.status_code == 200
    else:
        assert start.status_code == 503
    l2 = client.get("/api/product/l2-remainder")
    assert l2.status_code == 200
    assert l2.json()["full_mesh_l2_complete"] is False
    closure = client.get("/api/product/unpaid-closure")
    assert closure.status_code == 200
    body = closure.json()
    assert body["product_complete"] is False
    assert body["institutional_verdict"] == "NOT_COMPLETE"
    assert body["unpaid_closure_complete"] is True
    assert body["four_blockers"]["live_fill"] is False
    assert body["integrity"]["synthetic_mid_is_not_venue_l2"] is True
