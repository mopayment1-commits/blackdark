"""Regression: institutional commerce JSONL stores PII/identifiers encrypted at rest."""

from __future__ import annotations

import json

import pytest


@pytest.fixture
def commerce_paths(tmp_path, monkeypatch):
    root = tmp_path / "commerce"
    monkeypatch.setattr("institutional_commerce._ROOT", root, raising=False)
    monkeypatch.setattr("institutional_commerce._INVOICES", root / "invoices.jsonl", raising=False)
    monkeypatch.setattr("institutional_commerce._KYC", root / "kyc_cases.jsonl", raising=False)
    monkeypatch.setattr("institutional_commerce._PAID", root / "paid.jsonl", raising=False)
    monkeypatch.setattr("institutional_commerce._DATA_BASE", tmp_path, raising=False)
    monkeypatch.setenv("SECRETS_MASTER_KEY", "test-commerce-ledger-master-key")
    import secrets_vault

    secrets_vault._fernet = None
    return {
        "root": root,
        "invoices": root / "invoices.jsonl",
        "kyc": root / "kyc_cases.jsonl",
        "paid": root / "paid.jsonl",
    }


def _raw_jsonl(path) -> str:
    return path.read_text(encoding="utf-8")


def test_persisted_jsonl_does_not_contain_raw_email(commerce_paths):
    from institutional_commerce import create_invoice

    email = "buyer.encryption@example.com"
    create_invoice(email=email, amount_usd=49.0, method="sepa")
    raw = _raw_jsonl(commerce_paths["invoices"])
    assert email not in raw
    assert "sensitive_enc" in raw


def test_persisted_jsonl_does_not_contain_raw_legal_name(commerce_paths):
    from institutional_commerce import open_kyc_case

    legal_name = "Acme Institutional Holdings LLC"
    open_kyc_case(email="kyc@example.com", legal_name=legal_name, country="US")
    raw = _raw_jsonl(commerce_paths["kyc"])
    assert legal_name not in raw
    assert "sensitive_enc" in raw


def test_persisted_jsonl_does_not_contain_raw_session_id(commerce_paths):
    from institutional_commerce import open_kyc_case

    session_id = "didit-session-9f3c2a1b0e8d7c6b"
    open_kyc_case(
        email="didit@example.com",
        legal_name="Didit Buyer",
        country="US",
        provider="didit",
        session_id=session_id,
    )
    raw = _raw_jsonl(commerce_paths["kyc"])
    assert session_id not in raw


def test_persisted_jsonl_does_not_contain_payment_capability_token(commerce_paths):
    from institutional_commerce import create_invoice

    inv = create_invoice(email="token-free@example.com", amount_usd=10.0)
    raw = _raw_jsonl(commerce_paths["invoices"])
    assert "payment_url" not in raw
    assert "token_urlsafe" not in raw
    assert "payment_url" not in inv


def test_business_workflow_reconstructs_required_values(commerce_paths):
    from institutional_commerce import (
        create_invoice,
        find_kyc_case,
        get_invoice,
        mark_invoice_paid,
        open_kyc_case,
    )

    inv = create_invoice(email="workflow@example.com", amount_usd=99.0, method="wire_usd")
    loaded = get_invoice(inv["invoice_id"])
    assert loaded is not None
    assert loaded["email"] == "workflow@example.com"

    paid = mark_invoice_paid(inv["invoice_id"], source="sandbox")
    assert paid["email"] == "workflow@example.com"
    paid_raw = _raw_jsonl(commerce_paths["paid"])
    assert "workflow@example.com" not in paid_raw

    case = open_kyc_case(
        email="workflow@example.com",
        legal_name="Workflow Legal Name",
        country="DE",
        session_id="sess-workflow-001",
    )
    found = find_kyc_case(case["case_id"])
    assert found is not None
    assert found["legal_name"] == "Workflow Legal Name"
    assert found["session_id"] == "sess-workflow-001"


def test_tampered_ciphertext_fails_authentication(commerce_paths):
    from institutional_commerce import _INVOICES, create_invoice

    create_invoice(email="tamper@example.com", amount_usd=1.0)
    lines = _INVOICES.read_text(encoding="utf-8").splitlines()
    row = json.loads(lines[0])
    row["sensitive_enc"] = row["sensitive_enc"][:-4] + "AAAA"
    _INVOICES.write_text(json.dumps(row) + "\n", encoding="utf-8")

    from cryptography.exceptions import InvalidTag

    from institutional_commerce import get_invoice

    with pytest.raises(InvalidTag):
        get_invoice(row["invoice_id"])


def test_production_mode_without_encryption_key_fails_closed(commerce_paths, monkeypatch):
    import secrets_vault

    monkeypatch.setenv("ENV", "production")
    monkeypatch.delenv("SECRETS_MASTER_KEY", raising=False)
    monkeypatch.delenv("SECRETS_VAULT_KEY", raising=False)
    secrets_vault._fernet = None

    from institutional_commerce import create_invoice

    with pytest.raises(RuntimeError, match="SECRETS_MASTER_KEY or SECRETS_VAULT_KEY"):
        create_invoice(email="failclosed@example.com", amount_usd=1.0)
