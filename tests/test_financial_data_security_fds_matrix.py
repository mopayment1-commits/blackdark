"""FDS-01 → FDS-25 P0 test matrix — Financial Data Security closure."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

import pytest


def test_fds01_no_pan_backend_path():
    from financial_data_security.scanner import reject_forbidden_financial_payload
    from payments_usd import SECURITY_POSTURE

    assert SECURITY_POSTURE["stores_pan"] is False
    with pytest.raises(ValueError, match="Forbidden"):
        reject_forbidden_financial_payload({"pan": "4111111111111111"})


def test_fds02_cvv_never_stored():
    from financial_data_security.classification import FORBIDDEN_STORAGE_FIELDS
    from financial_data_security.scanner import reject_forbidden_financial_payload
    from payments_usd import SECURITY_POSTURE

    assert "cvv" in FORBIDDEN_STORAGE_FIELDS
    assert SECURITY_POSTURE["stores_cvv"] is False
    with pytest.raises(ValueError, match="Forbidden"):
        reject_forbidden_financial_payload({"cvv": "123"})


def test_fds03_hosted_checkout():
    from payments_usd import payments_architecture

    arch = payments_architecture()
    assert arch["security"]["card_data_handler"] in {
        "stripe_hosted",
        "lemon_squeezy_hosted",
        "hosted_psp",
        "psp_hosted_checkout",
    }
    assert arch["security"]["stores_pan"] is False


def test_fds04_bank_tokenized_policy():
    from payments_usd import SECURITY_POSTURE

    assert SECURITY_POSTURE["stores_full_iban_for_retail"] is False


def test_fds05_scanner_blocks_pan():
    from financial_data_security.scanner import scan_repository_paths, scan_text_for_restricted_data

    assert scan_text_for_restricted_data("4111111111111111")["pan_detected"] is True
    repo = scan_repository_paths()
    assert repo["pass"] is True
    assert repo["pan_hits"] == []


def test_fds06_no_secrets_in_code():
    from financial_data_security.secrets import secret_manager_status

    status = secret_manager_status()
    assert status["plaintext_in_source_scan"] == []


def test_fds08_fips_not_falsely_claimed():
    from financial_data_security.fips_policy import fips_path_status

    status = fips_path_status()
    assert status["status"] == "NEEDS_EXTERNAL_VERIFICATION"
    assert status["fips_140_3_validated_in_runtime"] is False


def test_fds10_admin_mfa_wiring():
    from financial_data_security.mfa import mfa_coverage_status

    status = mfa_coverage_status()
    assert "admin_mfa_policy" in status
    assert status["user_mfa_module"]["available"] is True


@pytest.mark.asyncio
async def test_fds11_resource_authorization():
    from financial_data_security.authorization import authorize_billing_action

    user_a = {"id": 1, "email": "a@test.com"}
    user_b = {"id": 2, "email": "b@test.com"}
    await authorize_billing_action(user=user_a, action="billing.portal", resource_owner_id=1)
    with pytest.raises(PermissionError, match="resource_owner_mismatch"):
        await authorize_billing_action(user=user_b, action="billing.portal", resource_owner_id=1)
    with pytest.raises(PermissionError, match="export_not_allowed"):
        await authorize_billing_action(user=user_a, action="billing.export", resource_owner_id=1)


@pytest.mark.asyncio
async def test_fds12_step_up_on_billing():
    from financial_data_security.step_up import enforce_billing_step_up

    user = {"id": 99, "email": "step@test.com", "step_up_at": None}
    with pytest.raises(ValueError, match="Recent authentication"):
        await enforce_billing_step_up(user, action="billing.sensitive")

    user_fresh = {
        "id": 99,
        "email": "step@test.com",
        "step_up_at": datetime.now(UTC).isoformat(),
    }
    await enforce_billing_step_up(user_fresh, action="billing.sensitive")


def test_fds13_service_identities():
    from financial_data_security.service_identities import service_identity_status

    status = service_identity_status()
    assert status["count"] >= 4
    assert status["shared_static_production_credential"] is False


def test_fds14_environment_isolation():
    from financial_data_security.environment import environment_isolation_status

    status = environment_isolation_status()
    assert "environment" in status
    assert status["pass"] is True


def test_fds16_audit_chain(tmp_path, monkeypatch):
    import financial_data_security.audit_trail as audit_mod

    monkeypatch.setattr(audit_mod, "_DATA", tmp_path / "financial_security_audit.jsonl")
    monkeypatch.setattr(audit_mod, "_LAST_HASH", "genesis")
    from financial_data_security.audit_trail import record_financial_audit, verify_audit_chain

    record_financial_audit(
        actor="test:runner",
        action="fds.test",
        resource="control:FDS-16",
        result="pass",
    )
    chain = verify_audit_chain()
    assert chain["chain_valid"] is True


def test_fds17_bulk_export_alert():
    from financial_data_security.alerts import alert_bulk_export

    low = alert_bulk_export(actor="user:1", record_count=5)
    high = alert_bulk_export(actor="user:1", record_count=500)
    assert low["triggered"] is False
    assert high["triggered"] is True


def test_fds18_automated_scanning():
    from financial_data_security.scanner import scan_repository_paths
    from financial_data_security.secrets import scan_repository_secrets_in_code

    assert scan_repository_paths()["pass"] is True
    assert scan_repository_secrets_in_code() == []


def test_fds19_webhook_controls():
    from financial_data_security.webhooks import (
        validate_webhook_timestamp,
        webhook_replay_key,
        webhook_security_status,
    )

    status = webhook_security_status()
    assert status["replay_protection"] is True
    assert validate_webhook_timestamp(timestamp=int(datetime.now(UTC).timestamp())) is True
    assert validate_webhook_timestamp(timestamp=int(datetime.now(UTC).timestamp()) - 9999) is False
    key_a = webhook_replay_key(provider="stripe", event_id="evt_1", payload_hash="abc")
    key_b = webhook_replay_key(provider="stripe", event_id="evt_2", payload_hash="abc")
    assert key_a != key_b


def test_fds20_retention_policy():
    from financial_data_security.retention import retention_for, retention_status

    status = retention_status()
    assert status["indefinite_retention_default"] is False
    assert retention_for("restricted_auth_data")["retention_days"] == 0


def test_fds21_incident_playbook():
    from financial_data_security.incident import run_incident_drill

    drill = run_incident_drill(trigger="pan_in_storage")
    assert drill["playbook_testable"] is True
    assert len(drill["phases_executed"]) >= 8


@pytest.mark.asyncio
async def test_fds22_break_glass(tmp_path, monkeypatch):
    import database
    from financial_data_security.break_glass import break_glass_status, create_break_glass_override

    monkeypatch.setattr(database.config, "DB_PATH", str(tmp_path / "bg.db"))
    await database.init_db()
    email = f"bg-{datetime.now(UTC).timestamp()}@blackdark.test"
    uid = await database.create_user(email, "pbkdf2_sha256$260000$deadbeef$" + "a" * 64, "BG")
    status = break_glass_status()
    assert status["audited"] is True
    assert status["dual_approval_for_paid"] is True
    result = await create_break_glass_override(
        user_id=uid,
        new_tier="pro",
        actor="admin:test",
        actor_role="platform_ops",
        approval_actor="admin:approver",
        ticket="FDS-22",
        reason="test drill",
    )
    assert result.get("ok") or result.get("override_id") or result.get("user_id")


def test_fds23_access_recertification():
    from financial_data_security.access_recertification import run_access_recertification

    result = run_access_recertification(reviewer="security_ops")
    assert result["status"] == "completed_local_drill"
    assert "billing_administration" in result["scope"]


def test_fds24_ai_boundary():
    from financial_data_security.ai_boundary import prepare_llm_context

    scrubbed = prepare_llm_context(
        {
            "email": "secret@example.com",
            "pan": "4111111111111111",
            "cvv": "999",
            "stripe_customer_id": "cus_secret",
            "oracle": {"verdict": "WAIT"},
        }
    )
    assert "pan" not in scrubbed
    assert "cvv" not in scrubbed
    assert "stripe_customer_id" not in scrubbed
    assert scrubbed["oracle"]["verdict"] == "WAIT"


def test_fds25_matrix_machine_verifiable():
    from financial_data_security.controls import evaluate_fds_controls

    result = evaluate_fds_controls()
    assert result["total_controls"] == 25
    assert len(result["matrix"]) == 25
    assert result["PASS_LIVE_NOT_CLAIMED"] is True
    ids = {row["control_id"] for row in result["matrix"]}
    assert ids == {f"FDS-{i:02d}" for i in range(1, 26)}


def test_fds_api_router_exists():
    from api.routers.financial_data_security import router

    assert router.prefix == "/api/financial-data-security"


def test_fds_billing_checkout_rejects_pan():
    from financial_data_security.scanner import reject_forbidden_financial_payload

    with pytest.raises(ValueError):
        reject_forbidden_financial_payload({"tier": "pro", "card_number": "4111111111111111"})


@pytest.mark.asyncio
async def test_fds_webhook_signature_failure_metric(tmp_path, monkeypatch):
    import database
    from financial_data_security.webhooks import record_webhook_signature_failure

    monkeypatch.setattr(database.config, "DB_PATH", str(tmp_path / "wh.db"))
    await database.init_db()
    await record_webhook_signature_failure(provider="stripe", reason="invalid_signature")
    async with database.get_connection() as db:
        row = await db.execute(
            "SELECT event_type, email, detail FROM billing_fraud_events ORDER BY id DESC LIMIT 1"
        )
        fetched = await row.fetchone()
    assert fetched is not None
    assert fetched["event_type"] == "webhook_signature_failure"
    assert fetched["email"] == "system@internal"
    assert "stripe" in fetched["detail"]


def test_fds_tls_policy_local():
    from financial_data_security.tls_policy import tls_policy_status

    tls = tls_policy_status()
    assert tls["minimum_tls"] == "1.2"
    assert tls["production_tls_verification"] == "NEEDS_EXTERNAL_VERIFICATION"


def test_fds_secrets_vault_roundtrip():
    from financial_data_security.secrets import decrypt_financial_secret, encrypt_financial_secret

    plain = "fds-test-secret-value"
    enc = encrypt_financial_secret(plain)
    assert enc != plain
    assert decrypt_financial_secret(enc) == plain


def test_fds07_secret_manager_local_path():
    from financial_data_security.secrets import secret_manager_status

    status = secret_manager_status()
    assert status["local_vault_module"] == "secrets_vault.py"
    assert status["kms_hsm_production_path"] == "NEEDS_EXTERNAL_VERIFICATION"
