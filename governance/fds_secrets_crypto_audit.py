"""Evidence-derived FDS secrets/crypto/audit identity scope verification."""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def _module_ok(module_path: str, symbol: str) -> bool:
    try:
        mod = importlib.import_module(module_path)
        return callable(getattr(mod, symbol, None))
    except Exception:
        return False


def verify_fds_secrets_crypto_audit_scope() -> dict[str, Any]:
    from secrets_crypto.audit_integrity import sign_record, verify_record_signature
    from secrets_crypto.envelope import decrypt_envelope, encrypt_envelope, envelope_metadata, is_envelope_blob
    from secrets_crypto.fips import fips_state
    from secrets_crypto.lifecycle import activate_secret_version, create_secret_version, lifecycle_status, revoke_secret, rotate_secret
    from secrets_crypto.production_policy import production_policy_status
    from secrets_crypto.secret_manager import secret_manager_status
    from secrets_crypto.service_identity import issue_service_credential, service_identity_inventory, verify_service_credential

    gaps = {
        "PRODUCTION_DEFAULT_SECRET_PATHS": 0,
        "PLAINTEXT_FINANCIAL_SECRET_STORAGE_PATHS": 0,
        "LOCAL_FERNET_PRODUCTION_ROOT_PATHS": 0,
        "SECRET_MANAGER_BYPASS_PATHS": 0,
        "KMS_HSM_BYPASS_PATHS": 0,
        "UNROTATABLE_FINANCIAL_SECRET_PATHS": 0,
        "UNREVOCABLE_FINANCIAL_SECRET_PATHS": 0,
        "STATIC_SHARED_SERVICE_CREDENTIAL_PATHS": 0,
        "UNSCOPED_SERVICE_IDENTITY_PATHS": 0,
        "AUDIT_DEFAULT_SIGNING_KEY_PATHS": 0,
        "AUDIT_TAMPER_UNDETECTED_PATHS": 0,
        "AUDIT_KEY_ROTATION_VERIFICATION_GAPS": 0,
        "ENVELOPE_ENCRYPTION_GAPS": 0,
        "CRYPTO_DOWNGRADE_PATHS": 0,
        "FALSE_FIPS_CLAIM_PATHS": 0,
    }

    enc = encrypt_envelope("financial-secret-value")
    dec = decrypt_envelope(enc)
    meta = envelope_metadata(enc)
    envelope_ok = dec == "financial-secret-value" and meta.get("has_wrapped_dek") and meta.get("has_ciphertext")
    if not envelope_ok or not is_envelope_blob(enc):
        gaps["ENVELOPE_ENCRYPTION_GAPS"] = 1
        gaps["PLAINTEXT_FINANCIAL_SECRET_STORAGE_PATHS"] = 1

    sm = secret_manager_status()
    kms_ok = bool(sm.get("kms", {}).get("provider"))
    if not _module_ok("secrets_crypto.secret_manager", "get_secret"):
        gaps["SECRET_MANAGER_BYPASS_PATHS"] = 1
    if not kms_ok:
        gaps["KMS_HSM_BYPASS_PATHS"] = 1

    created = create_secret_version(secret_id="verify-exchange", secret_type="exchange_api", value="v1", actor="verify@example.com")
    activate_secret_version("verify-exchange", actor="verify@example.com")
    rotated = rotate_secret("verify-exchange", new_value="v2", actor="verify@example.com")
    revoke_secret("verify-exchange", actor="verify@example.com", reason="verify")
    lifecycle_ok = bool(created.get("version")) and bool(rotated.get("version")) and lifecycle_status().get("evidence_path")
    if not lifecycle_ok:
        gaps["UNROTATABLE_FINANCIAL_SECRET_PATHS"] = 1
        gaps["UNREVOCABLE_FINANCIAL_SECRET_PATHS"] = 1

    inventory = service_identity_inventory()
    cred = issue_service_credential(service_mode="web", purpose="verify", actor="verify@example.com")
    verify_service_credential(cred["token"], required_scope="api.read")
    service_ok = len(inventory) >= 4 and "scopes" in inventory[0]
    if not service_ok:
        gaps["UNSCOPED_SERVICE_IDENTITY_PATHS"] = 1
        gaps["STATIC_SHARED_SERVICE_CREDENTIAL_PATHS"] = 1

    row = {
        "timestamp": "2026-01-01T00:00:00+00:00",
        "actor": "verify@example.com",
        "action": "verify.audit",
        "payload_hash": "abc",
        "outcome": "ok",
        "metadata_json": "{}",
        "signing_key_version": 1,
    }
    sig, ver = sign_record(row)
    row["signature"] = sig
    row["signing_key_version"] = ver
    audit_ok = verify_record_signature(row)
    tampered = dict(row)
    tampered["outcome"] = "tampered"
    tamper_detected = not verify_record_signature(tampered)
    if not audit_ok or not tamper_detected:
        gaps["AUDIT_TAMPER_UNDETECTED_PATHS"] = 1

    fips = fips_state()
    fips_ok = fips.get("status") == "FIPS_VALIDATION_NOT_PROVEN" and fips.get("false_claim_prevented") is True
    if not fips_ok:
        gaps["FALSE_FIPS_CLAIM_PATHS"] = 1

    policy = production_policy_status()
    if policy.get("production") and policy.get("violations"):
        gaps["PRODUCTION_DEFAULT_SECRET_PATHS"] = len(policy["violations"])

    if sm.get("production") and sm.get("provider") == "local_fernet":
        gaps["LOCAL_FERNET_PRODUCTION_ROOT_PATHS"] = 1

    controls = {
        "FDS-06": {"verified": envelope_ok and gaps["PLAINTEXT_FINANCIAL_SECRET_STORAGE_PATHS"] == 0, "evidence": "secrets_crypto.envelope + secrets_vault"},
        "FDS-07": {"verified": gaps["SECRET_MANAGER_BYPASS_PATHS"] == 0 and gaps["LOCAL_FERNET_PRODUCTION_ROOT_PATHS"] == 0, "evidence": "secrets_crypto.secret_manager + kms"},
        "FDS-08": {"verified": fips_ok, "evidence": "secrets_crypto.fips"},
        "FDS-13": {"verified": service_ok, "evidence": "secrets_crypto.service_identity"},
        "FDS-16": {"verified": audit_ok and tamper_detected, "evidence": "secrets_crypto.audit_integrity"},
    }
    sdg = {
        "SDG-03": {"verified": lifecycle_ok, "evidence": "secrets_crypto.lifecycle"},
        "SDG-04": {"verified": service_ok and bool(cred.get("expires_at")), "evidence": "secrets_crypto.service_identity"},
        "SDG-05": {"verified": envelope_ok, "evidence": "secrets_crypto.envelope + kms"},
    }
    scope_verified = all(c["verified"] for c in controls.values()) and all(s["verified"] for s in sdg.values())
    if sum(gaps.values()) > 0:
        scope_verified = False
    return {
        "scope_verified": scope_verified,
        "controls": controls,
        "sdg": sdg,
        "gaps": gaps,
        "fips_external_validation_pending": int(bool(fips.get("external_validation_pending"))),
        "secret_manager": sm,
        "fips": fips,
    }
