"""SPEC_10 — Financial Data Secret Security adversarial tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from launch57.financial_data_secret_security_spec_common import (
    DOMAIN,
    build_final_status,
    build_requirements_register,
    build_runtime_truth_table,
    independent_verification,
)


def test_requirements_register_nonempty():
    reqs = build_requirements_register()
    assert len(reqs) >= 20
    assert all(r["mandatory"] for r in reqs)


def test_runtime_truth_all_yes():
    truth = build_runtime_truth_table()
    nos = [r for r in truth if r["status"] != "YES"]
    assert not nos, nos


def test_secret_redaction_response_and_log():
    from launch57.financial_security_common import _REDACTED, redact_secrets, sanitize_for_log

    payload = {"api_secret": "unit_test_secret_value_only", "price": 100.0}
    redacted = redact_secrets(payload)
    logged = sanitize_for_log(payload)
    assert redacted["api_secret"] == _REDACTED
    assert logged["api_secret"] == _REDACTED


def test_no_api_keys_in_client_bundle():
    from launch57.financial_security_common import verify_no_api_keys_in_client_bundle

    check = verify_no_api_keys_in_client_bundle()
    assert check["client_bundle_clean"] is True
    assert check["violation_count"] == 0


def test_webhook_bad_signature_fail_closed():
    from launch57.financial_security_common import verify_webhook_bad_signature_fail_closed

    check = verify_webhook_bad_signature_fail_closed()
    assert check["fail_closed"] is True
    assert check["invalid_signature_rejected"] is True
    assert check["unsigned_webhook_blocked"] is True


def test_idor_entitlement_spoof_blocked():
    from launch57.financial_security_common import verify_idor_entitlement_spoof_blocked

    check = verify_idor_entitlement_spoof_blocked()
    assert check["blocked"] is True
    assert check["cross_user_denied"] is True
    assert check["unverified_tier_capped"] is True


def test_file02_file03_security_alignment():
    from launch57.financial_security_common import verify_file02_file03_security_alignment

    alignment = verify_file02_file03_security_alignment()
    assert alignment["aligned"] is True
    assert alignment["anonymous_history_denied"] is True
    assert alignment["client_tier_spoof_capped"] is True


def test_runtime_security_paths_wired():
    from launch57.financial_security_common import verify_runtime_security_path_wiring

    wiring = verify_runtime_security_path_wiring()
    assert wiring["runtime_enforcement_ok"] is True
    assert wiring["wired_paths"]["data_batch1_security_envelope"] is True
    assert wiring["wired_paths"]["explanation_ai_security_envelope"] is True


def test_no_parked_security_scope():
    from launch57.financial_security_common import verify_launch57_security_scope

    parked = verify_launch57_security_scope(999)
    assert parked["parked_contamination"] is True
    assert parked["in_launch57_scope"] is False


def test_machine_readable_security_export():
    from launch57.financial_security_common import build_machine_readable_security_export

    export = build_machine_readable_security_export()
    assert export["artifact"] == "LAUNCH57_FINANCIAL_DATA_SECRET_SECURITY_EXPORT"
    assert export["secret_hygiene_ok"] is True
    assert export["pass_live_not_claimed"] is True


def test_acceptance_criteria_all_pass():
    from launch57.financial_security_common import acceptance_criteria_status

    ac = acceptance_criteria_status()
    required = (
        "ac01_no_raw_card_auth_data",
        "ac05_secrets_not_in_browser",
        "ac06_secrets_not_logged",
        "ac07_secrets_excluded_from_ai",
        "ac11_cross_user_denied",
        "ac13_webhooks_verified",
        "runtime_paths_wired",
        "file02_file03_aligned",
        "webhook_bad_signature_fail_closed",
        "no_api_keys_in_client",
        "idor_entitlement_spoof_blocked",
        "secret_hygiene_ok",
        "ac20_no_false_pass_live",
    )
    missing = [k for k in required if not ac.get(k)]
    assert not missing, missing


def test_anonymous_denied_private_financial_endpoints():
    from starlette.testclient import TestClient

    from dashboard import app

    client = TestClient(app, raise_server_exceptions=False)
    assert client.get("/api/launch57/command-home", params={"symbol": "BTC"}).status_code == 401
    assert client.get("/api/launch57/decision-history", params={"symbol": "BTC"}).status_code == 401
    assert client.get("/api/launch57/guest-trust", params={"symbol": "BTC"}).status_code == 200


def test_independent_verification_passes():
    iv = independent_verification()
    assert iv["INDEPENDENT_VERIFICATION_PASS"] is True
    assert iv["PASS_LIVE_NOT_CLAIMED"] is True


def test_final_status_closed_local():
    status = build_final_status(skip_tests=True)
    assert status["closure_status"] == "CLOSED_LOCAL"
    assert status["PASS_ENGINEERING"] is True
    assert status["LOCAL_ENGINEERING_GAP_COUNT"] == 0
    assert status["secret_hygiene_ok"] is True
    assert status["launch57_only_ok"] is True
    assert status["PASS_LIVE"] is False
    assert status["LIVE_VALIDATION_PENDING"] is True


def test_spec10_artifact_paths_exist():
    gov = Path("governance/launch57/SPEC_10_FINANCIAL_DATA_SECRET_SECURITY")
    for name in (
        "REQUIREMENTS_REGISTER.json",
        "RUNTIME_TRUTH_TABLE.md",
        "LOCAL_CLOSURE_REPORT.md",
        "INDEPENDENT_VERIFICATION.json",
        "FINAL_STATUS.json",
    ):
        path = gov / name
        assert path.exists(), f"missing {path}"
        if name.endswith(".json") and name == "FINAL_STATUS.json":
            payload = json.loads(path.read_text(encoding="utf-8"))
            assert payload.get("domain") == DOMAIN
