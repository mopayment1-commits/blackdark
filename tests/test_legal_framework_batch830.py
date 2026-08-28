"""Tests — Batch: #830 Legal Framework Cross-Cutting Policy (PRV-001 Sprint-0)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import legal_framework_cross_cutting as legal


@pytest.fixture
def legal_seed() -> dict:
    return json.loads(Path("data/legal_framework_cross_cutting_seed.json").read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def reset_state():
    legal.reset_legal_framework_state()
    yield
    legal.reset_legal_framework_state()


def test_830_status_cross_cutting(legal_seed):
    status = legal.legal_framework_status_830(seed=legal_seed)
    assert status["standalone_rejected"] is True
    assert status["cross_cutting"] is True
    assert status["control_ref"] == "PRV-001"
    assert status["policy"]["lawyer_review_required"] is True


def test_830_tos_en_clauses(legal_seed):
    tos = legal.get_tos_summary_830(lang="en", seed=legal_seed)
    for clause in ("analytical_tool", "not_financial_advice", "no_buy_sell_recommendation", "no_return_guarantee"):
        assert clause in tos["clauses"]


def test_830_tos_ar_clauses(legal_seed):
    tos = legal.get_tos_summary_830(lang="ar", seed=legal_seed)
    assert "استشارة استثمارية" in tos["clauses"]["not_financial_advice"]
    assert "لا ضمان عائد" in tos["clauses"]["no_return_guarantee"]


def test_830_privacy_limited_collection(legal_seed):
    privacy = legal.get_privacy_policy_summary_830(seed=legal_seed)
    assert "private_keys" in privacy["data_not_collected"]
    assert privacy["gdpr_ccpa_compliant"] is True
    assert privacy["retention_ref"] == 949


def test_830_forbidden_language_scan(legal_seed):
    clean = legal.scan_forbidden_language_830("Market analysis based on data.")
    assert clean["passed"] is True
    bad = legal.scan_forbidden_language_830("Guaranteed returns every week.")
    assert bad["passed"] is False
    assert "guaranteed returns" in bad["forbidden_matches"]
    ar_bad = legal.scan_forbidden_language_830("ربح مضمون على كل صفقة")
    assert ar_bad["passed"] is False


def test_830_ai_footer_921(legal_seed):
    footer = legal.build_ai_output_footer_830(risk_score=55, source="oracle", seed=legal_seed)
    assert footer["integration_ref"] == 921
    assert footer["footer"]["risk_score"] == 55
    assert footer["footer"]["source"] == "oracle"


def test_830_signal_disclaimer_11(legal_seed):
    sig = legal.build_signal_disclaimer_830(seed=legal_seed)
    assert sig["integration_ref"] == 11
    assert sig["disclaimer"]["opportunity_not_prediction"] is True


def test_830_decision_intel_938(legal_seed):
    layer = legal.build_decision_intel_disclaimer_830(layer="hypothesis", seed=legal_seed)
    assert layer["integration_ref"] == 938


def test_830_billing_note_908(legal_seed):
    note = legal.build_pay_per_request_legal_note_830(seed=legal_seed)
    assert note["billing_ref"] == 908
    assert note["tiered_pricing_documented"] is True


def test_830_multi_account_907(legal_seed):
    note = legal.build_multi_account_sync_legal_note_830(seed=legal_seed)
    assert note["read_only"] is True
    assert note["no_custody"] is True
    assert note["no_execution"] is True


def test_830_user_consent_immutable(legal_seed):
    consent = legal.record_user_consent_830(user_id="user_123", seed=legal_seed)
    assert consent["consent"]["checkbox_explicit"] is True
    assert consent["consent"]["immutable"] is True
    assert consent["consent"]["chain_hash"]


def test_830_document_versions(legal_seed):
    versions = legal.get_document_versions_830(seed=legal_seed)
    assert versions["versioned"] is True
    assert versions["versions"]["terms_of_service"]["version"] == "2.0-sprint0"


def test_830_incident_crossref(legal_seed):
    xref = legal.get_incident_response_legal_crossref_830(seed=legal_seed)
    assert xref["incident_response_ref"] == 829
    assert xref["data_breach_cross_referenced"] is True


def test_830_output_compliance(legal_seed):
    result = legal.validate_output_compliance_830({"signal_type": "opportunity"}, output_type="signal", seed=legal_seed)
    assert result["ok"] is True
    assert result["not_financial_advice"] is True


def test_830_e2e(legal_seed):
    e2e = legal.run_legal_framework_e2e_830(seed=legal_seed)
    assert e2e["all_passed"] is True
    assert len(e2e["checks"]) >= 25


def test_legal_shield_still_binding():
    from legal_content import TERMS_OF_SERVICE

    assert "Four-layer legal shield" in TERMS_OF_SERVICE
