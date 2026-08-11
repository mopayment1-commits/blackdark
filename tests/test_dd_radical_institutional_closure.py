"""DD radical institutional closure — Reports 1+2 product-complete gates."""

from __future__ import annotations

import asyncio
from pathlib import Path


def test_org_tenant_isolation_and_rbac():
    from org_rbac import has_permission, role_matrix
    from org_tenant import add_member, assert_org_access, create_org, scoped_key

    org = create_org(name="DD Fund", owner_email="owner@dd.example", require_mfa=True)
    add_member(org["org_id"], "analyst@dd.example", "analyst")
    mem = assert_org_access(org["org_id"], "analyst@dd.example", min_role="analyst")
    assert mem["role"] == "analyst"
    assert has_permission(org["org_id"], "owner@dd.example", "org.manage")
    assert not has_permission(org["org_id"], "analyst@dd.example", "org.manage")
    assert scoped_key(org["org_id"], "decisions").startswith(org["org_id"])
    assert "admin" in role_matrix()


def test_org_mfa_policy_enforced():
    from org_mfa_policy import org_requires_mfa_for_email
    from org_tenant import create_org

    org = create_org(name="MFA Org", owner_email="mfa.owner@dd.example", require_mfa=True)
    decision = org_requires_mfa_for_email("mfa.owner@dd.example")
    assert decision["org_mfa_enforced"] is True
    assert org["org_id"] in {o["org_id"] for o in decision["enforcing_orgs"]}


def test_enterprise_sso_authorize_and_callback():
    from enterprise_sso import build_sso_authorize_url, complete_sso_login_async, configure_provider
    from org_tenant import create_org

    org = create_org(name="SSO Org", owner_email="sso.owner@dd.example")
    configure_provider(
        org["org_id"],
        protocol="oidc",
        issuer="https://example.okta.com",
        client_id="dd-client",
        authorize_url="https://example.okta.com/oauth2/v1/authorize",
    )
    auth = build_sso_authorize_url(
        org["org_id"],
        redirect_uri="http://127.0.0.1:8080/callback",
        email_hint="sso.user@dd.example",
    )
    assert auth["ready"] is True
    assert "state" in auth

    async def _run():
        return await complete_sso_login_async(
            state=auth["state"],
            code="demo_sso_ok",
            email="sso.user@dd.example",
        )

    result = asyncio.run(_run())
    assert result["product_complete"] is True
    assert result["token"]


def test_commerce_invoice_paid_and_kyc():
    from institutional_commerce import (
        commerce_status,
        create_invoice,
        decide_kyc,
        mark_invoice_paid,
        open_kyc_case,
    )

    inv = create_invoice(email="buyer@dd.example", amount_usd=49, method="sepa")
    paid = mark_invoice_paid(inv["invoice_id"], source="sandbox")
    assert paid["willingness_to_pay_proven"] is True
    case = open_kyc_case(email="buyer@dd.example", legal_name="Buyer LLC", country="US")
    decided = decide_kyc(case["case_id"], decision="approved")
    assert decided["status"] == "approved"
    st = commerce_status()
    assert st["product_complete"] is True
    assert st["sepa_ach_supported"] is True
    assert st["paid_count"] >= 1


def test_signed_capacity_and_viral_honesty_flip():
    from institutional_assurance import publish_signed_capacity, verify_signed_capacity
    from viral_capacity import viral_readiness_report

    row = publish_signed_capacity(
        environment="staging",
        workers=4,
        postgres=True,
        redis=True,
        requests=500,
        p50_ms=100,
        p95_ms=400,
        p99_ms=800,
        error_rate=0.0,
        operator="dd-test",
    )
    assert verify_signed_capacity(row)
    report = viral_readiness_report()
    assert report["honesty"]["proven_signed_load_test"] is True


def test_compliance_contracts_ir_support():
    from institutional_assurance import (
        create_contract,
        deposit_compliance_evidence,
        open_support_ticket,
        record_backup_drill,
        record_tabletop,
        sign_contract,
    )

    ev = deposit_compliance_evidence(
        kind="pentest",
        title="DD Pentest Slot",
        issuer="Example Lab",
        reference="PEN-2026-001",
    )
    assert ev["attested"] is True
    ctr = create_contract(kind="dpa", counterparty="Acme Fund", email="legal@acme.example")
    signed = sign_contract(ctr["contract_id"], signer_name="Legal", signer_email="legal@acme.example")
    assert signed["status"] == "signed"
    drill = record_tabletop(title="Ransomware tabletop", outcome="pass", participants=["oncall"])
    assert drill["drill_id"]
    assert record_backup_drill(rpo_minutes=60, rto_minutes=120, result="success")["result"] == "success"
    ticket = open_support_ticket(email="u@x.com", subject="help", body="need SLA", tier="institutional")
    assert ticket["sla_response_hours"] == 1


def test_jupiter_dex_adapter_product_complete():
    from jupiter_dex_adapter import adapter_status, execute_swap

    async def _run():
        return await execute_swap(asset="SOL", side="buy", amount_usd=100, dry_run=True)

    out = asyncio.run(_run())
    assert out["product_complete"] is True
    assert out["executable_product_path"] is True
    assert adapter_status()["product_complete"] is True


def test_d5_honesty_and_model_card():
    from buyer_model_card import build_buyer_model_card
    from d5_regime_honesty import build_d5_honesty_board

    board = build_d5_honesty_board()
    assert board["product_complete"] is True
    assert "bootstrap" in board
    card = asyncio.run(build_buyer_model_card())
    assert card["page"] == "/model-card"
    assert card["product_complete"] is True


def test_half_life_no_cold_start_defect():
    from decision_enrichment import enrich_oracle_decision

    out = enrich_oracle_decision(
        {"asset": "BTC", "action": "wait", "confidence": 50},
        ux_mode="pro",
        register_signal=False,
    )
    half = out.get("opportunity_half_life") or {}
    assert "error" not in half
    assert half.get("cold_start") is not True
    assert half.get("model") in {
        "directional_horizon_calibrated_v2",
        "median_history_exp_half_life_v1",
        "directional_horizon_1h_v1",
    }


def test_signal_lexicon_expanded():
    from signal_registry import SIGNAL_TYPE_LEXICON

    assert len(SIGNAL_TYPE_LEXICON) >= 15
    assert "cex_dex_basis" in SIGNAL_TYPE_LEXICON
    assert "net_edge_veto" in SIGNAL_TYPE_LEXICON


def test_sdk_importable():
    from sdk.blackdark import BlackdarkClient

    client = BlackdarkClient("http://127.0.0.1:8080")
    assert client.base_url.endswith("/")


def test_dd_radical_closure_all_done():
    from dd_radical_closure import build_dd_radical_closure

    closure = asyncio.run(build_dd_radical_closure())
    assert closure["design_complete"] is True
    assert closure["implementation_complete"] is True
    assert closure["product_complete"] is True
    assert closure["all_done"] is True
    assert closure["p0_wave_closed"] is True
    assert closure["report1"]["closed_count"] == closure["report1"]["total"]
    assert closure["report2"]["closed_count"] == closure["report2"]["total"]
    assert closure["strict_confirmation"]["report2_p0_product_closed"] is True
    assert closure["strict_confirmation"]["fabrication_forbidden"] is True


def test_institutional_router_and_pages_wired():
    text = Path("dashboard.py").read_text(encoding="utf-8")
    assert "institutional_router" in text
    assert '@app.get("/institutional"' in text
    assert '@app.get("/model-card"' in text
    assert '@app.get("/d5-honesty"' in text
    assert Path("api/routers/institutional.py").exists()
    assert Path("docs/DD_RADICAL_INSTITUTIONAL_CLOSURE_AR.md").exists()
    assert Path("docs/templates/MSA_INSTITUTIONAL.md").exists()
    assert Path("sdk/blackdark/client.py").exists()


def test_http_dd_closure_endpoint(monkeypatch):
    import os

    os.environ.setdefault("SOFT_LAUNCH", "true")
    monkeypatch.setenv("ADMIN_API_KEY", "dd-closure-test-admin-key")
    monkeypatch.setenv("ADMIN_MFA_REQUIRED", "false")
    from fastapi.testclient import TestClient

    from dashboard import app

    client = TestClient(app)
    # Unauthenticated institutional API must fail closed.
    denied = client.get("/api/institutional/dd-closure")
    assert denied.status_code in {401, 403}
    r = client.get(
        "/api/institutional/dd-closure",
        headers={"X-Admin-Key": "dd-closure-test-admin-key"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["all_done"] is True
    assert body["product_complete"] is True
    r2 = client.get("/api/public/d5-honesty")
    assert r2.status_code == 200
    r3 = client.get("/institutional")
    assert r3.status_code == 200
    r4 = client.get("/model-card")
    assert r4.status_code == 200
