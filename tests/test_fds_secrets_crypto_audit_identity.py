"""FDS-06/07/08/13/16 + SDG-03/04/05 behavior verification."""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_production_startup_fails_with_default_secret(monkeypatch: pytest.MonkeyPatch):
    from secrets_crypto.production_policy import production_policy_violations

    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("SECRETS_MASTER_KEY", "blackdark-dev-change-me-in-production")
    monkeypatch.setenv("AUDIT_SIGNING_KEY", "audit-prod-key-unique-value")
    monkeypatch.setenv("SECRET_MANAGER_PROVIDER", "hashicorp")
    monkeypatch.setenv("VAULT_ADDR", "http://vault:8200")
    monkeypatch.setenv("KMS_PROVIDER", "managed_env")
    monkeypatch.setenv("KMS_KEY_ID", "key-1")
    violations = production_policy_violations()
    assert any(v["check"] == "production_default_secret" for v in violations)


def test_production_startup_fails_with_dev_audit_key(monkeypatch: pytest.MonkeyPatch):
    from secrets_crypto.audit_integrity import signing_key_material

    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("AUDIT_SIGNING_KEY", "blackdark-audit-dev-sign")
    monkeypatch.setenv("SECRETS_MASTER_KEY", "prod-master-key-material-unique")
    with pytest.raises(RuntimeError):
        signing_key_material()


def test_financial_secret_cannot_persist_plaintext(monkeypatch: pytest.MonkeyPatch):
    import secrets_vault

    monkeypatch.setenv("SECRETS_MASTER_KEY", "fds06-plaintext-check-key!!!")
    secrets_vault._fernet = None
    plain = "whsec_" + "a" * 24
    enc = secrets_vault.encrypt_secret(plain)
    assert plain not in enc
    assert secrets_vault.decrypt_secret(enc) == plain


def test_secret_manager_path_succeeds(monkeypatch: pytest.MonkeyPatch, tmp_path: pytest.TempPathFactory):
    from secrets_crypto.secret_manager import put_secret, secret_manager_status

    monkeypatch.setenv("ENV", "development")
    monkeypatch.delenv("VAULT_ADDR", raising=False)
    status = secret_manager_status()
    assert status["provider"] in {"local_fernet", "hashicorp"}
    result = put_secret("test.financial.credential", "credential-value")
    assert result.get("stored") is True


def test_secret_manager_unavailable_fails_in_production(monkeypatch: pytest.MonkeyPatch):
    from secrets_crypto.secret_manager import get_secret

    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("SECRET_MANAGER_PROVIDER", "hashicorp")
    monkeypatch.delenv("VAULT_ADDR", raising=False)
    monkeypatch.delenv("VAULT_TOKEN", raising=False)
    with pytest.raises(RuntimeError):
        get_secret("missing.financial.secret")


def test_local_dev_fallback_only_non_production(monkeypatch: pytest.MonkeyPatch):
    from secrets_crypto.kms import kms_status, wrap_dek

    monkeypatch.setenv("ENV", "development")
    monkeypatch.delenv("KMS_PROVIDER", raising=False)
    monkeypatch.setenv("SECRETS_MASTER_KEY", "dev-only-master-key-material")
    wrapped = wrap_dek(b"x" * 32)
    assert wrapped["provider"] == "local_dev"

    monkeypatch.setenv("ENV", "production")
    with pytest.raises(RuntimeError):
        wrap_dek(b"x" * 32)


def test_envelope_encryption_roundtrip(monkeypatch: pytest.MonkeyPatch):
    from secrets_crypto.envelope import decrypt_envelope, encrypt_envelope, is_envelope_blob

    monkeypatch.setenv("SECRETS_MASTER_KEY", "envelope-roundtrip-key!!!!")
    enc = encrypt_envelope("sensitive-financial-value")
    assert is_envelope_blob(enc)
    assert decrypt_envelope(enc) == "sensitive-financial-value"


def test_kek_not_persisted_beside_ciphertext(monkeypatch: pytest.MonkeyPatch):
    from secrets_crypto.envelope import encrypt_envelope, envelope_metadata

    monkeypatch.setenv("SECRETS_MASTER_KEY", "kek-separation-key-material")
    enc = encrypt_envelope("value")
    meta = envelope_metadata(enc)
    assert meta.get("has_wrapped_dek")
    assert meta.get("has_ciphertext")
    assert "SECRETS_MASTER_KEY" not in enc


def test_dek_key_version_metadata_preserved(monkeypatch: pytest.MonkeyPatch):
    from secrets_crypto.envelope import encrypt_envelope, envelope_metadata

    monkeypatch.setenv("SECRETS_MASTER_KEY", "metadata-key-material!!!!")
    monkeypatch.setenv("KMS_KEY_VERSION", "3")
    meta = envelope_metadata(encrypt_envelope("value"))
    assert meta.get("key_version") == 3
    assert meta.get("key_id")


def test_rotation_preserves_decryptability(monkeypatch: pytest.MonkeyPatch):
    from secrets_crypto.lifecycle import activate_secret_version, create_secret_version, get_secret_version, rotate_secret

    create_secret_version(secret_id="rot-test", secret_type="webhook", value="v1", actor="ops@example.com")
    activate_secret_version("rot-test", actor="ops@example.com")
    rotate_secret("rot-test", new_value="v2", actor="ops@example.com")
    current = get_secret_version("rot-test")
    assert current is not None
    assert current["value"] == "v2"


def test_revoked_secret_cannot_be_newly_used():
    from secrets_crypto.lifecycle import create_secret_version, get_secret_version, revoke_secret

    create_secret_version(secret_id="rev-test", secret_type="api", value="v1", actor="ops@example.com")
    revoke_secret("rev-test", actor="ops@example.com", reason="compromise")
    assert get_secret_version("rev-test") is None


def test_rotation_audit_event_exists(tmp_path, monkeypatch: pytest.MonkeyPatch):
    from secrets_crypto.lifecycle import create_secret_version, lifecycle_events, rotate_secret

    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    create_secret_version(secret_id="audit-rot", secret_type="webhook", value="v1", actor="ops@example.com")
    rotate_secret("audit-rot", new_value="v2", actor="ops@example.com")
    events = lifecycle_events()
    assert any(e.get("event") == "secret_rotated" for e in events)


def test_service_identity_scoped_correctly():
    from secrets_crypto.service_identity import issue_service_credential, verify_service_credential

    cred = issue_service_credential(service_mode="web", purpose="verify")
    rec = verify_service_credential(cred["token"], required_scope="api.read")
    assert rec["service_mode"] == "web"


def test_service_a_cannot_use_service_b_privilege():
    from secrets_crypto.service_identity import issue_service_credential, verify_service_credential

    cred = issue_service_credential(service_mode="aggregator", purpose="verify")
    with pytest.raises(PermissionError, match="service_scope_denied"):
        verify_service_credential(cred["token"], required_scope="api.write")


def test_independent_service_revocation():
    from secrets_crypto.service_identity import issue_service_credential, revoke_service_credential, verify_service_credential

    cred = issue_service_credential(service_mode="ingestion", purpose="verify")
    assert revoke_service_credential(cred["token"], actor="ops@example.com", reason="rotate") is True
    with pytest.raises(PermissionError):
        verify_service_credential(cred["token"], required_scope="data.ingest")


def test_static_shared_service_credential_rejected(monkeypatch: pytest.MonkeyPatch):
    from secrets_crypto.service_identity import reject_shared_static_service_secret

    monkeypatch.setenv("ENV", "production")
    with pytest.raises(PermissionError):
        reject_shared_static_service_secret("SHARED_SERVICE_API_KEY")


def test_audit_row_tampering_detected(monkeypatch: pytest.MonkeyPatch):
    from secrets_crypto.audit_integrity import sign_record, verify_record_signature

    monkeypatch.setenv("AUDIT_SIGNING_KEY", "audit-tamper-test-key-unique")
    secrets_crypto_audit_integrity = __import__("secrets_crypto.audit_integrity", fromlist=["_KEYS"])
    secrets_crypto_audit_integrity._KEYS = {}
    row = {
        "timestamp": "2026-01-01T00:00:00+00:00",
        "actor": "a@example.com",
        "action": "test",
        "payload_hash": "h",
        "outcome": "ok",
        "metadata_json": "{}",
    }
    sig, ver = sign_record(row)
    row["signature"] = sig
    row["signing_key_version"] = ver
    assert verify_record_signature(row) is True
    row["outcome"] = "tampered"
    assert verify_record_signature(row) is False


def test_historical_audit_verifiable_after_key_rotation(monkeypatch: pytest.MonkeyPatch):
    from secrets_crypto.audit_integrity import sign_record, verify_record_signature

    mod = __import__("secrets_crypto.audit_integrity", fromlist=["_KEYS"])
    row = {
        "timestamp": "2026-01-01T00:00:00+00:00",
        "actor": "a@example.com",
        "action": "test",
        "payload_hash": "h",
        "outcome": "ok",
        "metadata_json": "{}",
    }
    monkeypatch.setenv("AUDIT_SIGNING_KEY", "audit-previous-key-material")
    monkeypatch.setenv("AUDIT_SIGNING_KEY_VERSION", "1")
    mod._KEYS = {}
    sig, ver = sign_record(row)
    row["signature"] = sig
    row["signing_key_version"] = ver
    monkeypatch.setenv("AUDIT_SIGNING_KEY", "audit-current-key-material")
    monkeypatch.setenv("AUDIT_SIGNING_KEY_VERSION", "2")
    monkeypatch.setenv("AUDIT_SIGNING_KEY_PREVIOUS", "audit-previous-key-material")
    mod._KEYS = {}
    assert verify_record_signature(row) is True


def test_missing_audit_verification_key_handled_safely(monkeypatch: pytest.MonkeyPatch):
    from secrets_crypto.audit_integrity import verify_record_signature

    monkeypatch.delenv("AUDIT_SIGNING_KEY", raising=False)
    mod = __import__("secrets_crypto.audit_integrity", fromlist=["_KEYS"])
    mod._KEYS = {}
    assert verify_record_signature({"signature": "abc", "signing_key_version": 99}) is False


def test_fips_state_cannot_claim_validated_without_evidence(monkeypatch: pytest.MonkeyPatch):
    from secrets_crypto.fips import assert_no_false_fips_claim, fips_state

    monkeypatch.delenv("FIPS_VALIDATION_EVIDENCE_PATH", raising=False)
    state = fips_state()
    assert state["status"] == "FIPS_VALIDATION_NOT_PROVEN"
    assert state["validated"] is False
    monkeypatch.setenv("FIPS_VALIDATED", "true")
    with pytest.raises(RuntimeError):
        assert_no_false_fips_claim()


def test_previous_fds_closure_verifiers_remain_green():
    from governance.fds_data_boundary import verify_fds_data_boundary_scope
    from governance.fds_privileged_identity import verify_fds_privileged_identity_scope

    assert verify_fds_data_boundary_scope()["scope_verified"] is True
    assert verify_fds_privileged_identity_scope()["scope_verified"] is True


def test_scope_verifier_green():
    from governance.fds_secrets_crypto_audit import verify_fds_secrets_crypto_audit_scope

    result = verify_fds_secrets_crypto_audit_scope()
    assert result["scope_verified"] is True
    assert sum(result["gaps"].values()) == 0


def test_closure_script_produces_evidence():
    proc = subprocess.run(
        [sys.executable, "scripts/fds_secrets_crypto_audit_identity_closure_verify.py"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    evidence = json.loads((ROOT / "FDS_SECRETS_CRYPTO_AUDIT_IDENTITY_CLOSURE_EVIDENCE.json").read_text())
    assert evidence["verdict"].startswith("FDS_SECRETS_CRYPTO_AUDIT_IDENTITY_CLOSED")
    assert evidence["summary"]["fds_controls_in_scope"] == 5
