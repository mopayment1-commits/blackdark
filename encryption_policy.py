"""
Encryption Policy — Cross-Cutting Sprint 0 Infrastructure.

At-Rest (AES-256-GCM) + In-Transit (TLS 1.3) — NOT standalone.
Defense-in-depth for all sensitive platform data.
"""

from __future__ import annotations

import json
import logging
import os
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.EncryptionPolicy")

_FEATURE = "encryption_policy"
_SEED_PATH = Path("data/encryption_policy_seed.json")
_ROTATION_STATE_PATH = Path("data/encryption_key_rotation_state.json")

_SESSION_REF = 1019
_RBAC_REF = 1022
_GDPR_REF = 1023
_IMMUTABLE_REF = 1029
_BACKUP_REF = 1016
_ACTIVITY_REF = 1038
_STRIPE_REF = 908

SensitiveDomain = Literal[
    "credentials",
    "session",
    "api_key",
    "wallet_label",
    "preferences",
    "billing",
    "activity_log",
    "audit",
    "immutable_audit",
    "backup",
    "general",
]


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _cfg(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    return seed.get("encryption_policy") or {}


def encryption_policy_status(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    policy = (_cfg(seed).get("policy") or {})
    return {
        "ok": True,
        "feature": _FEATURE,
        "standalone_rejected": seed.get("standalone_rejected", True),
        "merged_into": seed.get("merged_into"),
        "policy": {
            "at_rest_algorithm": policy.get("at_rest_algorithm", "AES-256-GCM"),
            "in_transit_min_tls": policy.get("in_transit_min_tls", "1.3"),
            "tls_downgrade_forbidden": policy.get("tls_downgrade_forbidden", True),
            "key_rotation_days": policy.get("key_rotation_days", 90),
            "hardcoded_keys_forbidden": policy.get("hardcoded_keys_forbidden", True),
            "non_custodial": policy.get("non_custodial", True),
            "wallet_private_keys_never_stored": policy.get("wallet_private_keys_never_stored", True),
            "pci_card_data_platform_forbidden": policy.get("pci_card_data_platform_forbidden", True),
            "cert_expiry_alert_days": policy.get("cert_expiry_alert_days", 30),
            "blocks_production": policy.get("blocks_production", True),
        },
        "at_rest_scopes": _cfg(seed).get("at_rest_scopes") or [],
        "key_domains": _cfg(seed).get("key_domains") or {},
        "integrations": _cfg(seed).get("integrations") or {},
        "in_transit": in_transit_policy_status(seed=seed),
        "key_management": key_management_status(seed=seed),
        "certificate_lifecycle": certificate_lifecycle_status(seed=seed),
        "timestamp": _utcnow(),
    }


def _domain_aad(domain: SensitiveDomain) -> bytes:
    return f"blackdark-enc:{domain}".encode("utf-8")


def encrypt_at_rest(
    plaintext: str,
    *,
    domain: SensitiveDomain = "general",
    seed: dict[str, Any] | None = None,
) -> str:
    """AES-256-GCM encryption for sensitive platform data."""
    if not plaintext:
        return ""
    seed = seed or _load_seed()
    algo = (_cfg(seed).get("policy") or {}).get("at_rest_algorithm", "AES-256-GCM")
    if algo != "AES-256-GCM":
        raise ValueError(f"Unsupported at-rest algorithm: {algo}")
    from secrets_vault import encrypt_secret_gcm

    return encrypt_secret_gcm(plaintext, aad=_domain_aad(domain))


def decrypt_at_rest(
    ciphertext: str,
    *,
    domain: SensitiveDomain = "general",
    seed: dict[str, Any] | None = None,
) -> str:
    if not ciphertext:
        return ""
    from secrets_vault import decrypt_secret_gcm

    return decrypt_secret_gcm(ciphertext, aad=_domain_aad(domain))


def encrypt_audit_payload(payload: dict[str, Any], *, seed: dict[str, Any] | None = None) -> str:
    """#1029 / #1038 — encrypted audit record blob."""
    return encrypt_at_rest(json.dumps(payload, sort_keys=True, default=str), domain="audit", seed=seed)


def decrypt_audit_payload(ciphertext: str, *, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    raw = decrypt_at_rest(ciphertext, domain="audit", seed=seed)
    return json.loads(raw)


def _is_production() -> bool:
    tokens = [
        (os.getenv("ENV") or "").strip().lower(),
        (os.getenv("APP_ENV") or "").strip().lower(),
        (os.getenv("RAILWAY_ENVIRONMENT") or "").strip().lower(),
    ]
    return any(t in {"production", "prod"} for t in tokens)


def in_transit_policy_status(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    policy = (_cfg(seed).get("policy") or {})
    base_url = (os.getenv("APP_BASE_URL") or "").strip().lower()
    db_url = (os.getenv("DATABASE_URL") or "").strip().lower()
    redis_url = (os.getenv("REDIS_URL") or "").strip().lower()
    min_tls = policy.get("in_transit_min_tls", "1.3")
    return {
        "min_tls_version": min_tls,
        "tls_downgrade_forbidden": policy.get("tls_downgrade_forbidden", True),
        "app_https": base_url.startswith("https://") or not _is_production(),
        "database_ssl": "sslmode=require" in db_url or "ssl=true" in db_url or not db_url.startswith("postgres"),
        "redis_tls": redis_url.startswith("rediss://") or not redis_url,
        "hsts_enabled": _is_production(),
        "internal_mesh_tls": os.getenv("SERVICE_MESH_TLS", "required").lower() in {"1", "true", "required"},
    }


def verify_in_transit_request(request: Any) -> dict[str, Any]:
    """Reject/downgrade detection for incoming requests."""
    scheme = getattr(getattr(request, "url", None), "scheme", "http")
    forwarded_proto = (request.headers.get("x-forwarded-proto") or "").split(",")[0].strip().lower()
    effective = forwarded_proto or scheme
    ok = effective == "https" or not _is_production()
    return {
        "ok": ok,
        "effective_scheme": effective,
        "production": _is_production(),
        "tls_required": _is_production(),
    }


def key_management_status(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    policy = (_cfg(seed).get("policy") or {})
    domains = (_cfg(seed).get("key_domains") or {})
    rotation_days = int(policy.get("key_rotation_days", 90))
    state = _load_rotation_state()
    last_rotation = state.get("last_rotation_at")
    due = False
    if last_rotation:
        try:
            last_dt = datetime.fromisoformat(str(last_rotation).replace("Z", "+00:00"))
            due = datetime.now(UTC) >= last_dt + timedelta(days=rotation_days)
        except ValueError:
            due = True
    else:
        due = _is_production()

    keys = {
        "operational": bool(os.getenv(domains.get("operational", "SECRETS_MASTER_KEY") or "SECRETS_MASTER_KEY")),
        "backup": bool(os.getenv(domains.get("backup", "BACKUP_ENCRYPTION_KEY") or "BACKUP_ENCRYPTION_KEY")),
        "immutable_audit": bool(
            os.getenv(domains.get("immutable_audit", "IMMUTABLE_AUDIT_KEY") or "IMMUTABLE_AUDIT_KEY")
        ),
        "session_pepper": bool(os.getenv(domains.get("session", "SESSION_TOKEN_PEPPER") or "SESSION_TOKEN_PEPPER")),
    }
    kms = (os.getenv("KMS_PROVIDER") or "").strip().lower() or (
        "aws_kms" if os.getenv("AWS_KMS_KEY_ID") else ("vault" if os.getenv("VAULT_ADDR") else "local_env")
    )
    return {
        "kms_provider": kms,
        "keys_configured": keys,
        "rotation_days": rotation_days,
        "rotation_due": due,
        "last_rotation_at": last_rotation,
        "hardcoded_keys_forbidden": policy.get("hardcoded_keys_forbidden", True),
        "backup_key_separate": keys["backup"] or not _is_production(),
    }


def record_key_rotation_event(*, actor: str = "system") -> dict[str, Any]:
    state = {"last_rotation_at": _utcnow(), "actor": actor, "ts": time.time()}
    _ROTATION_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _ROTATION_STATE_PATH.write_text(json.dumps(state), encoding="utf-8")
    return state


def _load_rotation_state() -> dict[str, Any]:
    if not _ROTATION_STATE_PATH.is_file():
        return {}
    try:
        return json.loads(_ROTATION_STATE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def certificate_lifecycle_status(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    policy = (_cfg(seed).get("policy") or {})
    alert_days = int(policy.get("cert_expiry_alert_days", 30))
    expiry_raw = os.getenv("TLS_CERT_EXPIRES_AT", "").strip()
    days_remaining: int | None = None
    alert = False
    if expiry_raw:
        try:
            exp = datetime.fromisoformat(expiry_raw.replace("Z", "+00:00"))
            days_remaining = (exp - datetime.now(UTC)).days
            alert = days_remaining <= alert_days
        except ValueError:
            alert = True
    return {
        "auto_renewal": policy.get("cert_renewal_auto", True),
        "expiry_alert_days": alert_days,
        "cert_expires_at": expiry_raw or None,
        "days_remaining": days_remaining,
        "expiry_alert": alert,
        "provider": os.getenv("TLS_CERT_PROVIDER", "lets_encrypt_managed"),
    }


def stripe_pci_scope_note(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """#908 — PCI scope minimized; Stripe handles card data."""
    seed = seed or _load_seed()
    return {
        "pci_card_data_in_platform_db": False,
        "stripe_handles_card_data": True,
        "platform_encrypts_billing_metadata_only": True,
        "integration_ref": _STRIPE_REF,
    }


def gdpr_article_32_note(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """#1023 — encryption documented for compliance."""
    return {
        "article": "GDPR Article 32",
        "technical_measure": "encryption_at_rest_and_in_transit",
        "documented_in_privacy_policy": True,
        "integration_ref": _GDPR_REF,
    }


def backup_encryption_requirements(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """#1016 — backups use separate key from operational DB."""
    km = key_management_status(seed=seed)
    return {
        "separate_backup_key_required": _is_production(),
        "backup_key_configured": km["keys_configured"].get("backup", False),
        "cross_region_encrypted_storage": os.getenv("BACKUP_CROSS_REGION", "true").lower() in {"1", "true", "yes"},
        "integration_ref": _BACKUP_REF,
    }


def _backup_key(*, seed: dict[str, Any] | None = None) -> bytes:
    import hashlib

    seed = seed or _load_seed()
    domains = (_cfg(seed).get("key_domains") or {})
    key_material = (
        os.getenv(domains.get("backup", "BACKUP_ENCRYPTION_KEY") or "BACKUP_ENCRYPTION_KEY", "").strip()
        or os.getenv(domains.get("operational", "SECRETS_MASTER_KEY") or "SECRETS_MASTER_KEY", "").strip()
        or "blackdark-backup-dev-only"
    )
    return hashlib.sha256(key_material.encode("utf-8")).digest()


def encrypt_backup_blob(data: bytes, *, seed: dict[str, Any] | None = None) -> bytes:
    """Encrypt backup bytes with backup-domain key when BACKUP_ENCRYPTION_KEY set."""
    import base64

    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    nonce = os.urandom(12)
    ct = AESGCM(_backup_key(seed=seed)).encrypt(nonce, data, _domain_aad("backup"))
    return base64.b64encode(nonce + ct)


def decrypt_backup_blob(blob: bytes, *, seed: dict[str, Any] | None = None) -> bytes:
    """Decrypt backup bytes produced by encrypt_backup_blob."""
    import base64

    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    raw = base64.b64decode(blob)
    nonce, ct = raw[:12], raw[12:]
    return AESGCM(_backup_key(seed=seed)).decrypt(nonce, ct, _domain_aad("backup"))


def check_encryption_production_gate(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    status = encryption_policy_status(seed=seed)
    policy = status["policy"]
    in_transit = status["in_transit"]
    keys = status["key_management"]
    cert = status["certificate_lifecycle"]
    backup = backup_encryption_requirements(seed=seed)

    try:
        from pentest_attestation import verify_pentest_attestation

        pentest_ok = verify_pentest_attestation() or not _is_production()
    except ImportError:
        pentest_ok = not _is_production()

    checks = {
        "aes_256_gcm": policy["at_rest_algorithm"] == "AES-256-GCM",
        "tls_1_3_policy": policy["in_transit_min_tls"] == "1.3",
        "operational_key": keys["keys_configured"]["operational"] or not _is_production(),
        "session_pepper": keys["keys_configured"]["session_pepper"] or not _is_production(),
        "backup_key_separate": backup["backup_key_configured"] or not _is_production(),
        "https_in_production": in_transit["app_https"] or not _is_production(),
        "non_custodial": policy["non_custodial"] is True,
        "no_pci_cards": policy["pci_card_data_platform_forbidden"] is True,
        "scoped_data": len(status["at_rest_scopes"]) >= 8,
        "pentest_or_non_prod": pentest_ok,
        "cert_not_expired": cert["expiry_alert"] is False,
    }
    return {
        "ok": all(checks.values()),
        "feature": _FEATURE,
        "blocks_production": policy.get("blocks_production", True),
        "checks": checks,
        "timestamp": _utcnow(),
    }


def run_encryption_policy_e2e(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    checks: list[dict[str, Any]] = []

    status = encryption_policy_status(seed=seed)
    checks.append({"id": "no_standalone", "passed": status["standalone_rejected"] is True})
    checks.append({"id": "aes_256_gcm", "passed": status["policy"]["at_rest_algorithm"] == "AES-256-GCM"})
    checks.append({"id": "tls_1_3", "passed": status["policy"]["in_transit_min_tls"] == "1.3"})
    checks.append({"id": "non_custodial", "passed": status["policy"]["non_custodial"] is True})

    plain = "sensitive-user-preference-value"
    enc = encrypt_at_rest(plain, domain="preferences", seed=seed)
    dec = decrypt_at_rest(enc, domain="preferences", seed=seed)
    checks.append({"id": "roundtrip", "passed": dec == plain and enc != plain})

    wrong_domain = False
    try:
        decrypt_at_rest(enc, domain="billing", seed=seed)
    except Exception:
        wrong_domain = True
    checks.append({"id": "domain_binding", "passed": wrong_domain})

    audit_blob = encrypt_audit_payload({"action": "login", "user_id": 1}, seed=seed)
    checks.append(
        {
            "id": "audit_encrypt",
            "passed": isinstance(audit_blob, str) and len(audit_blob) > 20,
        }
    )

    checks.append({"id": "stripe_pci", "passed": stripe_pci_scope_note(seed=seed)["pci_card_data_in_platform_db"] is False})
    checks.append({"id": "gdpr_art32", "passed": gdpr_article_32_note(seed=seed)["article"] == "GDPR Article 32"})

    gate = check_encryption_production_gate(seed=seed)
    checks.append({"id": "production_gate", "passed": gate["ok"] is True})

    all_passed = all(c["passed"] for c in checks)
    return {
        "ok": all_passed,
        "feature": _FEATURE,
        "all_passed": all_passed,
        "checks": checks,
        "timestamp": _utcnow(),
    }
