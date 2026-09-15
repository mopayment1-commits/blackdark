"""FDS-20/21 + SDG-15/16/17 behavior verification."""

from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
async def spine_db(tmp_path, monkeypatch):
    import config
    import database

    db_path = tmp_path / "spine.db"
    monkeypatch.setattr(config, "DB_PATH", str(db_path))
    monkeypatch.delenv("DATABASE_URL", raising=False)
    await database.init_db()
    return database


# --- Retention ---


def test_each_fds_class_resolves_to_retention_policy():
    from financial_data.classification import FDSClass
    from fds_retention_incident.retention_policy import retention_for_class

    for cls in (FDSClass.C3_BANKING, FDSClass.C4_SECRET, FDSClass.C5_SENSITIVE_FINANCIAL, FDSClass.C6_PAYMENT_REFERENCE):
        policy = retention_for_class(cls)
        assert policy["policy_key"] != "unclassified_hold"
        assert policy.get("retention_days") is not None


def test_indefinite_default_rejected():
    from fds_retention_incident.retention_policy import financial_retention_matrix, reject_indefinite_retention

    for policy in financial_retention_matrix():
        assert reject_indefinite_retention(policy) is True
    assert reject_indefinite_retention({"retention_days": -1}) is False
    assert reject_indefinite_retention({"retention_days": None}) is False


@pytest.mark.asyncio
async def test_account_closure_invokes_correct_lifecycle(spine_db, tmp_path, monkeypatch):
    from fds_retention_incident.account_closure import close_account

    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    email = "closure-test@example.com"
    await spine_db.create_user(email, "hash")
    result = await close_account(email, confirmed=True)
    assert result["status"] == "closed"
    assert result["false_deletion_claim"] is False
    assert any(i["status"] == "deleted" for i in result["immediate_deletion"])
    assert any("anonymized" in r["status"] for r in result["retained_legal_security"])


@pytest.mark.asyncio
async def test_legal_retention_does_not_falsely_claim_deletion(spine_db, tmp_path, monkeypatch):
    from fds_retention_incident.account_closure import close_account

    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    email = "legal-hold@example.com"
    await spine_db.create_user(email, "hash")
    result = await close_account(email, confirmed=True)
    retained = result["retained_legal_security"]
    assert retained
    for item in retained:
        assert "immediate" not in item.get("status", "")
    assert result["backup_pending_expiry"][0]["status"] == "pending_backup_expiry"


@pytest.mark.asyncio
async def test_financial_credential_revoked_on_closure(spine_db, tmp_path, monkeypatch):
    from fds_retention_incident.account_closure import close_account, revoke_financial_credentials

    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    email = "cred-revoke@example.com"
    user_id = await spine_db.create_user(email, "hash")
    await spine_db.upsert_user_api_key(user_id, "binance", "enc_key", "enc_secret")
    revoked = await revoke_financial_credentials(user_id)
    assert revoked["credential_revocation_complete"] is True
    assert any(r["type"] == "exchange_credentials" for r in revoked["revoked"])


def test_backup_receives_expiry_state(tmp_path, monkeypatch):
    from fds_retention_incident.backup_lifecycle import record_backup_creation

    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("BACKUP_RETENTION_DAYS", "14")
    rec = record_backup_creation(backup_path="test_backup.sql.gz", sha256="abc")
    assert rec["state"] == "RETENTION_WINDOW"
    assert rec["expiry_at"]
    assert rec["retention_days"] == 14


def test_backup_expiry_deletion_verification_recorded(tmp_path, monkeypatch):
    from fds_retention_incident.backup_lifecycle import process_expired_backups, record_backup_creation, verify_backup_deletion

    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    monkeypatch.setenv("BACKUP_DIR", str(backup_dir))
    monkeypatch.setenv("BACKUP_RETENTION_DAYS", "1")
    gz = backup_dir / "expired.sql.gz"
    gz.write_bytes(b"test")
    rec = record_backup_creation(backup_path=str(gz), sha256="deadbeef")
    rec["expiry_ts"] = time.time() - 10
    evidence = tmp_path / "backup_lifecycle_evidence.jsonl"
    evidence.write_text(json.dumps({"event": "backup_created", **rec}) + "\n")
    results = process_expired_backups(backup_dir)
    assert results
    assert results[0]["state"] in {"VERIFIED", "DELETED"}
    verify = verify_backup_deletion(str(gz))
    assert verify["verified"] is True


def test_failed_deletion_remains_observable(tmp_path, monkeypatch):
    from fds_retention_incident.backup_lifecycle import process_expired_backups, record_backup_creation

    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    monkeypatch.setenv("BACKUP_DIR", str(backup_dir))
    stuck = backup_dir / "stuck.sql.gz"
    rec = record_backup_creation(backup_path=str(stuck), sha256="x")
    rec["expiry_ts"] = time.time() - 10
    stuck.write_bytes(b"stuck")
    evidence = tmp_path / "backup_lifecycle_evidence.jsonl"
    evidence.write_text(json.dumps({"event": "backup_created", **rec}) + "\n")

    original_unlink = Path.unlink

    def fail_unlink(self, missing_ok=False):
        if self.name == "stuck.sql.gz":
            raise OSError("permission denied")
        return original_unlink(self, missing_ok=missing_ok)

    monkeypatch.setattr(Path, "unlink", fail_unlink)
    results = process_expired_backups(backup_dir)
    assert any(r.get("state") == "FAILED" for r in results)


# --- Incident Response ---


def test_pan_in_log_synthetic_incident_detected(tmp_path, monkeypatch):
    from fds_retention_incident.incident_drill import run_drill_scenario

    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    result = run_drill_scenario("pan_in_log_fixture")
    assert result["outcome"] == "PASS"
    assert result["incident_type"] == "pan_discovered_in_storage"


def test_leaked_webhook_secret_routed_correctly(tmp_path, monkeypatch):
    from fds_retention_incident.incident_drill import run_drill_scenario

    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    result = run_drill_scenario("webhook_secret_exposed")
    assert result["outcome"] == "PASS"
    assert "rotate_webhook_secret" in result["controls_invoked"]


def test_leaked_exchange_credential_triggers_revoke_rotate(tmp_path, monkeypatch):
    from fds_retention_incident.incident_drill import run_drill_scenario

    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    result = run_drill_scenario("exchange_api_secret_leaked")
    assert result["outcome"] == "PASS"
    assert any(d.get("revoke_rotate_triggered") for d in result["decisions"])


def test_unauthorized_financial_export_incident(tmp_path, monkeypatch):
    from fds_retention_incident.incident_drill import run_drill_scenario

    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    result = run_drill_scenario("unauthorized_bulk_financial_export")
    assert result["outcome"] == "PASS"


def test_ai_boundary_leak_incident(tmp_path, monkeypatch):
    from fds_retention_incident.incident_drill import run_drill_scenario

    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    result = run_drill_scenario("financial_data_ai_boundary")
    assert result["outcome"] == "PASS"


def test_privileged_misuse_incident(tmp_path, monkeypatch):
    from fds_retention_incident.incident_drill import run_drill_scenario

    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    result = run_drill_scenario("privileged_misuse")
    assert result["outcome"] == "PASS"


def test_incident_record_contains_no_secret(tmp_path, monkeypatch):
    from fds_retention_incident.incident_playbook import create_incident

    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    with pytest.raises(ValueError):
        create_incident("leaked_financial_api_secret", detection_source="whsec_live_secret_value")
    incident = create_incident("leaked_financial_api_secret", detection_source="credential_monitor")
    dumped = json.dumps(incident)
    assert "whsec" not in dumped
    assert "sk_live" not in dumped


def test_post_incident_review_required(tmp_path, monkeypatch):
    from fds_retention_incident.incident_playbook import create_incident

    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    incident = create_incident("compromised_payment_integration", detection_source="billing_monitor")
    assert incident["post_incident_review_required"] is True


def test_drill_cannot_pass_without_required_lifecycle_steps(tmp_path, monkeypatch):
    from fds_retention_incident.incident_drill import _REQUIRED_STEPS, run_drill_scenario

    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    result = run_drill_scenario("pan_in_log_fixture")
    completed = set(result["lifecycle_steps_completed"])
    assert _REQUIRED_STEPS.issubset(completed)
    assert result["outcome"] == "PASS"


# --- Supply Chain ---


def test_sca_runs_successfully():
    from fds_retention_incident.supply_chain import sca_status

    sca = sca_status()
    assert sca.get("tool") == "pip-audit"
    assert "requirements_file" in sca


def test_sbom_generated_machine_readable():
    from fds_retention_incident.supply_chain import sbom_status

    sbom = sbom_status()
    assert sbom.get("machine_readable") is True
    assert sbom.get("format") == "CycloneDX"
    assert sbom.get("component_count", 0) > 0


def test_critical_finding_release_policy(tmp_path, monkeypatch):
    from fds_retention_incident.supply_chain import evaluate_release_policy, register_waiver

    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    findings = [{"package": "testpkg", "vulnerability_id": "CVE-TEST-UNIQUE-1", "severity": "critical"}]
    blocked = evaluate_release_policy(findings)
    assert blocked["release_blocked"] is True
    register_waiver(
        package="testpkg",
        vulnerability_id="CVE-TEST-UNIQUE-1",
        severity="critical",
        owner="security@example.com",
        reason="vendor patch pending",
        expires_at=(datetime.now(UTC) + timedelta(days=7)).isoformat(),
    )
    waived = evaluate_release_policy(findings)
    assert waived["release_blocked"] is False


def test_waiver_requires_owner_reason_expiry(tmp_path, monkeypatch):
    from fds_retention_incident.supply_chain import register_waiver

    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    with pytest.raises(ValueError):
        register_waiver(
            package="pkg",
            vulnerability_id="CVE-1",
            severity="high",
            owner="",
            reason="",
            expires_at="",
        )


def test_payment_path_third_party_script_inventory_enforced():
    from fds_retention_incident.payment_script_inventory import verify_payment_path_minimization

    result = verify_payment_path_minimization()
    assert result["compliant"] is True
    assert result["architecture"] == "hosted_stripe_lemon_checkout_redirect"


# --- Regression ---


def test_previous_fds_closure_verifiers_remain_green():
    from governance.fds_data_boundary import verify_fds_data_boundary_scope
    from governance.fds_privileged_identity import verify_fds_privileged_identity_scope
    from governance.fds_secrets_crypto_audit import verify_fds_secrets_crypto_audit_scope
    from governance.fds_transport_webhook_environment import verify_fds_transport_webhook_environment_scope

    assert verify_fds_data_boundary_scope()["scope_verified"] is True
    assert verify_fds_privileged_identity_scope()["scope_verified"] is True
    assert verify_fds_secrets_crypto_audit_scope()["scope_verified"] is True
    assert verify_fds_transport_webhook_environment_scope()["scope_verified"] is True


def test_scope_verifier_green(tmp_path, monkeypatch):
    from governance.fds_retention_incident_supply_chain import verify_fds_retention_incident_supply_chain_scope

    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    result = verify_fds_retention_incident_supply_chain_scope()
    assert result["scope_verified"] is True
    assert sum(result["gaps"].values()) == 0


def test_closure_script_produces_evidence():
    proc = subprocess.run(
        [sys.executable, "scripts/fds_retention_incident_supply_chain_closure_verify.py"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=900,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    evidence = json.loads((ROOT / "FDS_RETENTION_INCIDENT_SUPPLY_CHAIN_CLOSURE_EVIDENCE.json").read_text())
    assert evidence["verdict"].startswith("FDS_RETENTION_INCIDENT_SUPPLY_CHAIN_CLOSED")
    assert evidence["summary"]["fds_controls_in_scope"] == 2
