"""FDS-05/15/18/24/25 + SDG-01/08/10/12 behavior verification."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SYNTHETIC_PAN = "4242424242424242"
SYNTHETIC_PAN_SPACED = "4242 4242 4242 4242"
BLOCKED_PAN = "5555555555554444"


def test_fds_c1_classification_and_prohibited_sinks():
    from financial_data.classification import FDSClass, class_definition, classify_field
    from financial_data.sink_policy import Sink, is_sink_allowed

    assert classify_field("cvv", "123") == FDSClass.C1_SAD
    policy = class_definition(FDSClass.C1_SAD)
    assert "logs" in policy.prohibited_sinks
    assert is_sink_allowed(FDSClass.C1_SAD, Sink.AI_LLM) is False


def test_fds_c2_pan_handling():
    from financial_data.classification import FDSClass, classify_field
    from financial_data.classification import luhn_valid

    assert luhn_valid(SYNTHETIC_PAN)
    assert classify_field("card_number", SYNTHETIC_PAN) == FDSClass.C2_PAN


def test_fds_c3_banking_sensitive_classification():
    from financial_data.classification import FDSClass, classify_field

    assert classify_field("iban", "GB82WEST12345698765432") == FDSClass.C3_BANKING


def test_fds_c4_secret_handling():
    from financial_data.classification import FDSClass, classify_field

    assert classify_field("webhook_secret", "not-a-real-secret") == FDSClass.C4_SECRET
    assert classify_field("api_key", "whsec_" + "a" * 24) == FDSClass.C4_SECRET


def test_fds_c5_sensitive_financial_policy():
    from financial_data.classification import FDSClass, classify_field
    from financial_data.sink_policy import Sink, is_sink_allowed

    assert classify_field("balance", "12345.67") == FDSClass.C5_SENSITIVE_FINANCIAL
    assert is_sink_allowed(FDSClass.C5_SENSITIVE_FINANCIAL, Sink.AI_LLM) is False


def test_fds_c6_payment_reference_policy():
    from financial_data.classification import FDSClass, classify_field
    from financial_data.sink_policy import Sink, is_sink_allowed

    assert classify_field("stripe_customer_id", "cus_abc") == FDSClass.C6_PAYMENT_REFERENCE
    assert is_sink_allowed(FDSClass.C6_PAYMENT_REFERENCE, Sink.AI_LLM) is False


def test_unknown_financial_input_fails_closed():
    from financial_data.classification import FDSClass, classify_field
    from financial_data.sink_policy import PolicyViolation, Sink, enforce_sink_policy

    assert classify_field("mystery_financial_blob", "opaque") == FDSClass.UNKNOWN
    with pytest.raises(PolicyViolation):
        enforce_sink_policy({"mystery_financial_blob": "opaque"}, Sink.AI_LLM)


def test_pan_scanner_detects_synthetic_pan(tmp_path):
    from financial_data.scanner import scan_text_content, load_allowlist

    text = f"probe {BLOCKED_PAN} end\n"
    rel = "tests/tmp_probe_pan.txt"
    findings = scan_text_content(text, rel_path=rel, allowlist=load_allowlist())
    assert any(f["kind"] == "luhn_pan" for f in findings)


def test_scanner_rejects_prohibited_finding(tmp_path):
    from financial_data.scanner import scan_text_content, load_allowlist

    findings = scan_text_content(
        f"pan={BLOCKED_PAN}",
        rel_path="tests/tmp_forbidden_pan.txt",
        allowlist=load_allowlist(),
    )
    assert findings


def test_allowlisted_synthetic_fixture_passes():
    from financial_data.scanner import scan_text_content, load_allowlist

    fixture = (ROOT / "tests/fixtures/fds_synthetic_pan.txt").read_text(encoding="utf-8")
    findings = scan_text_content(
        fixture,
        rel_path="tests/fixtures/fds_synthetic_pan.txt",
        allowlist=load_allowlist(),
    )
    assert findings == []


def test_false_positive_candidate_allowlisted_clean():
    from financial_data.scanner import scan_repository

    report = scan_repository()
    assert report["clean"] is True
    assert report["pan_finding_count"] == 0


def test_cvv_sad_detection_does_not_echo_value():
    from financial_data.dlp import redact_financial_text, scan_text_for_prohibited_patterns

    raw = "cvv: 987"
    findings = scan_text_for_prohibited_patterns(raw)
    assert findings
    redacted = redact_financial_text(raw)
    assert "987" not in redacted
    assert "[financial_redacted]" in redacted


def test_logger_sanitizes_restricted_classes():
    from financial_data.dlp import sanitize_financial_log_value

    assert "[financial_redacted]" in sanitize_financial_log_value(SYNTHETIC_PAN, field_name="pan")
    assert "[financial_redacted]" in sanitize_financial_log_value("sk_live_" + "y" * 24, field_name="api_key")
    assert "[financial_redacted]" in sanitize_financial_log_value("123", field_name="cvv")


def test_error_path_remains_sanitized():
    from log_safety import sanitize_log_value

    out = sanitize_log_value(SYNTHETIC_PAN, field_name="pan")
    assert SYNTHETIC_PAN not in out
    assert "financial_redacted" in out or "redacted" in out


def test_external_llm_path_rejects_restricted_payload():
    from financial_data.boundary import gate_external_llm_payload
    from financial_data.sink_policy import PolicyViolation

    with pytest.raises(PolicyViolation):
        gate_external_llm_payload({"pan": SYNTHETIC_PAN})
    with pytest.raises(PolicyViolation):
        gate_external_llm_payload({"cvv": "123"})


def test_analytics_support_prohibited_sink_rejects_restricted_payload():
    from financial_data.boundary import gate_analytics_export, gate_support_export
    from financial_data.sink_policy import PolicyViolation

    with pytest.raises(PolicyViolation):
        gate_analytics_export({"card_number": SYNTHETIC_PAN})
    with pytest.raises(PolicyViolation):
        gate_support_export({"cvc": "321"})


def test_allowed_market_context_remains_functional():
    from financial_data.boundary import prepare_llm_context

    ctx = prepare_llm_context(
        {
            "macro": {"macro_regime_proxy": "risk_on"},
            "sentiment": {"fear_greed_index": 55},
            "geo_news": {"geopolitical_headline_count": 1},
            "stripe_customer_id": "cus_hidden",
        }
    )
    assert "macro" in ctx
    assert "stripe_customer_id" not in ctx


def test_fds_evidence_verifier_derives_status_from_checks():
    from governance.fds_data_boundary import verify_fds_data_boundary_scope

    result = verify_fds_data_boundary_scope()
    assert "controls" in result
    assert result["controls"]["FDS-05"]["verified"] is True
    assert result["scope_verified"] is True


def test_hardcoded_catalog_cannot_override_failed_evidence():
    from governance.fds_data_boundary import verify_fds_data_boundary_scope
    from governance.fds_requirements import verify_fds_runtime

    boundary = verify_fds_data_boundary_scope()
    runtime = verify_fds_runtime()
    assert runtime["all_ok"] == boundary["scope_verified"]
    if not boundary["scope_verified"]:
        assert runtime["all_ok"] is False


def test_payment_security_regression_remains_green():
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_payments_usd_security.py", "-q"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_sdg12_test_fixture_policy():
    from financial_data.test_data_policy import is_allowed_synthetic_pan, validate_test_fixture_text

    assert is_allowed_synthetic_pan(SYNTHETIC_PAN)
    violations = validate_test_fixture_text(f"value {BLOCKED_PAN}", rel_path="tests/sample_bad.py")
    assert violations


def test_closure_script_produces_evidence():
    proc = subprocess.run(
        [sys.executable, "scripts/fds_security_governance_data_boundary_closure_verify.py"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    evidence = json.loads((ROOT / "FDS_SECURITY_GOVERNANCE_DATA_BOUNDARY_CLOSURE_EVIDENCE.json").read_text())
    assert evidence["verdict"] == "FDS_SECURITY_GOVERNANCE_DATA_BOUNDARY_CLOSED"
    assert evidence["summary"]["fds_controls_in_scope"] == 5
