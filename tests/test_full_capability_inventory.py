"""Full product capability inventory — second-pass institutional review."""

from __future__ import annotations

ALLOWED_STATUS = {"works", "partial", "gated", "external_block", "ops_config"}
PERSONAS = {"retail", "pro", "whale", "fund", "b2b", "acquirer"}


def test_inventory_honest_and_complete_ids():
    from product_capability_inventory import (
        build_full_capability_inventory,
        capability_catalog,
        inventory_summary,
    )

    rows = capability_catalog()
    ids = [r["id"] for r in rows]
    assert len(ids) == len(set(ids))
    assert len(rows) >= 85
    for row in rows:
        assert row["status"] in ALLOWED_STATUS
        assert row["domain"]
        assert row["name_ar"]
        assert row["surfaces"]
        assert row["evidence"]
        assert row["efficiency"]
        assert PERSONAS.issuperset(row["personas"])
        assert row["personas"]

    summary = inventory_summary(rows)
    assert summary["total"] == len(rows)
    assert summary["works"] >= 40
    assert summary["external_block"] >= 2  # live_fill + cloud multi-AZ

    out = build_full_capability_inventory()
    assert out["ok"] is True
    assert out["product_complete"] is False
    assert out["institutional_verdict"] == "NOT_COMPLETE"
    assert out["live_money_ready"] is False
    assert out["trial_ready_unpaid"] is True
    assert out["four_blockers"]["live_fill"] is False
    assert out["four_blockers"]["jupiter_vc"] is False
    assert out["four_blockers"]["full_mesh_l2_complete"] is False
    assert out["four_blockers"]["cloud_multi_az"] is False
    assert set(out["entitlements"]) == PERSONAS
    for p, caps in out["entitlements"].items():
        assert caps, p
    review = out["review"]
    assert review["binding_verdict"] == "NOT_COMPLETE"
    assert review["product_complete"] is False
    assert "live_fill" in review["ask_3_efficiency"]["not_claimed"]
    assert review["ask_4_nothing_forgotten_or_broken"]["known_stopped_product_defects"] == []


def test_required_capability_ids_present():
    from product_capability_inventory import capability_catalog

    ids = {r["id"] for r in capability_catalog()}
    for required in (
        "ID-REG",
        "ID-MFA",
        "OR-SENTENCE",
        "OR-LEDGER",
        "MKT-L2",
        "MKT-MESH",
        "EX-LIVE",
        "EX-JUP",
        "EX-OMS",
        "B2B-FEED",
        "B2B-WL",
        "FUND-HA",
        "FUND-PG",
        "DD-PACK",
        "DD-FOUR",
        "WOW-F1F10",
        "INV-FULL",
        "JR-CRUD",
        "AL-INBOX",
    ):
        assert required in ids, required
    live = next(r for r in capability_catalog() if r["id"] == "EX-LIVE")
    assert live["status"] == "external_block"
    ha = next(r for r in capability_catalog() if r["id"] == "FUND-HA")
    assert ha["status"] == "external_block"
    pg = next(r for r in capability_catalog() if r["id"] == "FUND-PG")
    assert pg["status"] == "works"


def test_inventory_api_and_security_alias():
    from fastapi.testclient import TestClient
    from dashboard import app

    client = TestClient(app, follow_redirects=False)
    inv = client.get("/api/product/capability-inventory")
    assert inv.status_code == 200
    body = inv.json()
    assert body["product_complete"] is False
    assert body["institutional_verdict"] == "NOT_COMPLETE"
    assert body["summary"]["total"] >= 85
    assert "EX-LIVE" in {c["id"] for c in body["capabilities"]}

    redir = client.get("/settings/security")
    assert redir.status_code in {307, 302, 301}
    assert "/profile" in (redir.headers.get("location") or "")

    persona = client.get("/api/trial/persona-readiness")
    assert persona.status_code == 200
    assert persona.json()["product_complete"] is False


def test_retail_is_not_promised_live_execution():
    from product_capability_inventory import capability_catalog

    retail_ids = {r["id"] for r in capability_catalog() if "retail" in r["personas"]}
    assert "OR-SENTENCE" in retail_ids
    assert "JR-CRUD" in retail_ids
    live = next(r for r in capability_catalog() if r["id"] == "EX-LIVE")
    assert "retail" not in live["personas"]
