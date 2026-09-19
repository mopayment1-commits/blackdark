"""SPEC_12 — Identity Auth Profile adversarial tests."""

from __future__ import annotations

import json
from pathlib import Path

from launch57.identity_auth_profile_spec_common import (
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


def test_weak_hashing_forbidden():
    from launch57.identity_auth_common import verify_weak_hashing_forbidden

    check = verify_weak_hashing_forbidden()
    assert check["ok"] is True
    assert check["weak_forbidden"] is True
    assert check["approved_algorithm"] is True


def test_login_rate_limit_configured():
    from launch57.identity_auth_common import verify_login_rate_limit_configured

    check = verify_login_rate_limit_configured()
    assert check["configured"] is True
    assert check["max_attempts"] > 0
    assert check["window_sec"] > 0


def test_session_cookie_flags():
    from launch57.identity_auth_common import verify_session_cookie_flags

    check = verify_session_cookie_flags()
    assert check["ok"] is True
    assert check["httponly"] is True
    assert check["samesite"] in {"lax", "strict"}


def test_password_not_logged():
    from launch57.identity_auth_common import verify_password_not_logged

    check = verify_password_not_logged()
    assert check["ok"] is True
    assert check["password_redacted_in_log"] is True


def test_file10_secret_hygiene_aligned():
    from launch57.identity_auth_common import verify_file10_secret_hygiene_aligned

    check = verify_file10_secret_hygiene_aligned()
    assert check["aligned"] is True


def test_idor_profile_history_blocked():
    from launch57.identity_auth_common import verify_idor_profile_history_blocked

    check = verify_idor_profile_history_blocked()
    assert check["blocked"] is True
    assert check["history_idor_blocked"] is True
    assert check["mirror_idor_blocked"] is True


def test_file02_file03_identity_alignment():
    from launch57.identity_auth_common import verify_file02_file03_identity_alignment

    alignment = verify_file02_file03_identity_alignment()
    assert alignment["aligned"] is True
    assert alignment["anonymous_history_denied"] is True
    assert alignment["verified_session_entitlement_bound"] is True
    assert alignment["watchlist_anonymous_blocked"] is True


def test_runtime_identity_paths_wired():
    from launch57.identity_auth_common import verify_runtime_identity_path_wiring

    wiring = verify_runtime_identity_path_wiring()
    assert wiring["runtime_enforcement_ok"] is True
    assert wiring["wired_paths"]["edge_ui_identity_envelope"] is True
    assert wiring["wired_paths"]["explanation_ai_identity_envelope"] is True


def test_no_parked_identity_scope():
    from launch57.identity_auth_common import verify_launch57_identity_scope

    parked = verify_launch57_identity_scope(999)
    assert parked["parked_contamination"] is True
    assert parked["in_launch57_scope"] is False


def test_machine_readable_identity_export():
    from launch57.identity_auth_common import build_machine_readable_identity_export

    export = build_machine_readable_identity_export()
    assert export["artifact"] == "LAUNCH57_IDENTITY_AUTH_PROFILE_EXPORT"
    assert export["auth_gate_ok"] is True
    assert export["pass_live_not_claimed"] is True


def test_acceptance_criteria_all_pass():
    from launch57.identity_auth_common import acceptance_criteria_status

    ac = acceptance_criteria_status()
    required = (
        "ac01_immutable_user_identity",
        "ac03_passwords_safely_stored",
        "ac09_auth_separate_from_entitlement",
        "ac12_private_state_protected",
        "ac16_logs_no_auth_secrets",
        "runtime_paths_wired",
        "file02_file03_aligned",
        "login_rate_limit_configured",
        "session_cookie_flags_ok",
        "idor_profile_history_blocked",
        "file10_secret_hygiene_aligned",
        "auth_gate_ok",
        "ac20_no_false_pass_live",
    )
    missing = [k for k in required if not ac.get(k)]
    assert not missing, missing


def test_anonymous_denied_private_launch57_endpoints():
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
    assert status["auth_gate_ok"] is True
    assert status["launch57_only_ok"] is True
    assert status["PASS_LIVE"] is False
    assert status["LIVE_VALIDATION_PENDING"] is True


def test_spec12_artifact_paths_exist():
    gov = Path("governance/launch57/SPEC_12_IDENTITY_AUTH_PROFILE")
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
