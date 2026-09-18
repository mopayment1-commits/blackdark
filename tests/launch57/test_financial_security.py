"""Launch-57 Financial Data & Secret Security baseline tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from launch57.financial_security_common import (
    INTERNAL_SECURITY_COMPONENTS,
    _REDACTED,
    acceptance_criteria_status,
    attach_financial_security_envelope,
    build_capability_security_findings,
    build_credential_boundary_metadata,
    build_environment_isolation_status,
    build_payment_flow_metadata,
    build_security_component_registry,
    build_sensitive_data_inventory,
    build_webhook_security_requirements,
    record_security_incident_signal,
    redact_secrets,
    sanitize_for_ai_llm,
    sanitize_for_public_surface,
    scan_for_secret_leakage,
    verify_cross_user_access,
)


def test_internal_components_all_have_consumers():
    registry = build_security_component_registry()
    assert len(registry) == len(INTERNAL_SECURITY_COMPONENTS)
    for row in registry:
        assert row["launch_scope"] == "LAUNCH57"
        assert row["launch_surface"] is False
        assert row["standalone_capability"] is False
        assert row["consumer_capability_ids"]


def test_redact_secrets_masks_api_secret():
    payload = {"api_secret": "unit_test_secret_value_only", "price": 100.0}
    redacted = redact_secrets(payload)
    assert redacted["api_secret"] == _REDACTED
    assert redacted["price"] == 100.0


def test_scan_detects_secret_before_redaction():
    payload = {"password": "super_secret_unit_test_value"}
    result = scan_for_secret_leakage(payload)
    assert result["leakage_detected"] is True
    assert result["ok"] is False


def test_scan_clean_after_redaction():
    payload = {"password": "super_secret_unit_test_value"}
    redacted = redact_secrets(payload)
    result = scan_for_secret_leakage(redacted)
    assert result["ok"] is True


def test_sanitize_for_ai_llm_excludes_secrets():
    payload = {
        "api_key": "secret123",
        "user_id": "u-1",
        "symbol": "BTC",
        "explanation": "price moved",
    }
    cleaned = sanitize_for_ai_llm(payload)
    assert cleaned.get("ai_secret_exclusion_applied") is True
    assert "api_key" not in cleaned
    assert "user_id" not in cleaned
    assert cleaned["symbol"] == "BTC"


def test_sanitize_for_public_surface_strips_private_fields():
    payload = {
        "symbol": "BTC",
        "email": "user@example.com",
        "account_id": "acc-1",
        "price": 42000.0,
    }
    cleaned = sanitize_for_public_surface(payload)
    assert cleaned.get("public_safe_projection") is True
    assert "email" not in cleaned
    assert "account_id" not in cleaned
    assert cleaned["symbol"] == "BTC"


def test_cross_user_access_denied():
    result = verify_cross_user_access(subject_id="user-a", resource_owner_id="user-b")
    assert result["allowed"] is False
    assert result["cross_user_denied"] is True


def test_cross_user_access_allowed_for_owner():
    result = verify_cross_user_access(subject_id="user-a", resource_owner_id="user-a")
    assert result["allowed"] is True
    assert result["cross_user_denied"] is False


def test_credential_boundary_for_connector():
    meta = build_credential_boundary_metadata(launch_item_id=42, credential_scope="public_rest")
    assert meta["server_side_only"] is True
    assert meta["ui_exposure"] == "FORBIDDEN"
    assert meta["unrestricted_execution"] is False


def test_webhook_security_requirements():
    req = build_webhook_security_requirements()
    assert req["signature_verification"] is True
    assert req["invalid_signature_rejection"] is True
    assert req["tls_required"] is True


def test_payment_flow_forbids_raw_card_path():
    flow = build_payment_flow_metadata()
    assert flow["raw_pan_cvv_path"] == "FORBIDDEN"
    assert flow["provider_hosted_tokenized"] is True


def test_environment_isolation_status():
    status = build_environment_isolation_status()
    assert status["prod_secrets_in_dev_forbidden"] is True
    assert status["environment_specific_credentials"] is True


def test_attach_financial_security_envelope_internal():
    body = {"launch_item_id": 42, "symbol": "BTC", "api_secret": "unit_test_only"}
    out = attach_financial_security_envelope(body, surface_type="internal", launch_item_id=42)
    assert out["launch57_financial_security"]["internal_support_only"] is True
    assert out["api_secret"] == _REDACTED
    assert out["launch57_financial_security"]["secret_leakage_scan"]["ok"] is True


def test_attach_financial_security_envelope_public():
    body = {"launch_item_id": 44, "symbol": "BTC", "email": "a@b.com"}
    out = attach_financial_security_envelope(body, surface_type="public", launch_item_id=44)
    assert out["launch57_financial_security"]["public_private_boundary_enforced"] is True
    assert "email" not in out


def test_attach_financial_security_envelope_ai():
    body = {"launch_item_id": 36, "api_key": "x", "summary": "move"}
    out = attach_financial_security_envelope(body, surface_type="ai", launch_item_id=36)
    assert out["launch57_financial_security"]["ai_secret_exclusion_enforced"] is True
    assert "api_key" not in out


def test_incident_signal_persisted(tmp_path, monkeypatch):
    store = tmp_path / "launch57_financial_security_incidents.jsonl"
    monkeypatch.setattr("launch57.financial_security_common._FAILURE_STORE", store)
    row = record_security_incident_signal(
        incident_type="credential_leakage_test",
        capability_id=42,
        detail="test signal only",
    )
    assert row["signal_id"].startswith("fds_sig_")
    lines = store.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    parsed = json.loads(lines[0])
    assert parsed["incident_type"] == "credential_leakage_test"


def test_acceptance_criteria_core_checks():
    status = acceptance_criteria_status()
    assert status["ac01_no_raw_card_auth_data"] is True
    assert status["ac07_secrets_excluded_from_ai"] is True
    assert status["ac11_cross_user_denied"] is True
    assert status["ac20_no_false_pass_live"] is True


def test_capability_security_findings_cover_touchpoints():
    findings = build_capability_security_findings()
    cap_ids = {row["launch_item_id"] for row in findings}
    assert 36 in cap_ids
    assert 42 in cap_ids
    assert 44 in cap_ids


def test_sensitive_data_inventory_complete():
    inventory = build_sensitive_data_inventory()
    class_ids = {row["class_id"] for row in inventory}
    assert "FDS-C4_FINANCIAL_CREDENTIALS" in class_ids
    assert "PUBLIC_MARKET" in class_ids
