"""Tests — Secrets Management & Key Vault (#189)."""

from __future__ import annotations

import json
import logging
import time

import pytest

from bd_platform import secrets_key_vault as vault


@pytest.fixture
def isolated_vault(tmp_path, monkeypatch):
    reg = tmp_path / "registry.json"
    cipher = tmp_path / "ciphertext.json"
    audit = tmp_path / "audit.jsonl"
    monkeypatch.setattr(vault, "_REGISTRY_PATH", reg)
    monkeypatch.setattr(vault, "_CIPHER_BLOB_PATH", cipher)
    monkeypatch.setattr(vault, "_AUDIT_PATH", audit)
    vault._revoked_ids.clear()
    vault._revoked_loaded = False
    monkeypatch.setenv("SECRETS_MASTER_KEY", "vault-189-test-master-key!!!!!")
    import secrets_vault

    secrets_vault._fernet = None
    return {"registry": reg, "cipher": cipher, "audit": audit}


def test_create_secret_reveal_once_only(isolated_vault):
    plain = "sk-live-test-api-key-abcdef123456"
    out = vault.create_secret(
        tenant_id="default",
        user_id=42,
        name="binance_trading",
        value=plain,
        permission="trading",
        secret_type="exchange_api",
    )
    assert out["ok"] is True
    assert out["reveal_once"] == plain
    assert out["status"] == "active"
    assert "warning" in out

    listed = vault.list_secrets(tenant_id="default", user_id=42)
    assert listed["count"] == 1
    assert listed["secrets"][0]["masked_hint"] != plain
    assert "sk-live" not in json.dumps(listed)


def test_negative_no_plaintext_in_storage(isolated_vault):
    """Mandatory negative test — DB/files must contain ciphertext only."""
    plain = "super-secret-negative-test-value-xyz"
    out = vault.create_secret(
        tenant_id="default",
        user_id=1,
        name="test_key",
        value=plain,
        permission="read_only",
    )
    assert out["ok"]

    neg = vault.negative_test_plaintext_absent(plain)
    assert neg["ok"] is True
    assert neg["plaintext_found_in"] == []
    assert neg["logs_redacted"] is True

    reg_text = isolated_vault["registry"].read_text(encoding="utf-8")
    cipher_text = isolated_vault["cipher"].read_text(encoding="utf-8")
    assert plain not in reg_text
    assert plain not in cipher_text


def test_negative_logs_redacted(isolated_vault, caplog):
    plain = "token-should-never-appear-in-logs"
    with caplog.at_level(logging.INFO):
        vault.create_secret(
            tenant_id="default",
            user_id=2,
            name="oauth_token",
            value=plain,
            permission="read_only",
            secret_type="oauth_token",
        )
    log_blob = caplog.text
    assert plain not in log_blob
    assert vault.redact_for_logs(plain) == "[redacted]"


def test_tenant_isolation(isolated_vault):
    plain = "tenant-isolated-secret"
    created = vault.create_secret(
        tenant_id="tenant_a",
        user_id=10,
        name="key_a",
        value=plain,
    )
    sid = created["secret_id"]

    denied = vault.decrypt_secret_for_use(
        sid, tenant_id="tenant_b", user_id=10, actor="test"
    )
    assert denied["ok"] is False
    assert denied["error"] == "access_denied"

    ok = vault.decrypt_secret_for_use(
        sid, tenant_id="tenant_a", user_id=10, actor="test"
    )
    assert ok["ok"] is True
    assert ok["value"] == plain


def test_revocation_immediate(isolated_vault):
    plain = "revoke-me-fast"
    created = vault.create_secret(
        tenant_id="default",
        user_id=5,
        name="revoke_test",
        value=plain,
    )
    sid = created["secret_id"]

    t0 = time.perf_counter()
    rev = vault.revoke_secret(sid, tenant_id="default", user_id=5)
    elapsed_ms = (time.perf_counter() - t0) * 1000

    assert rev["ok"] is True
    assert rev["status"] == "revoked"
    assert rev["immediate"] is True
    assert elapsed_ms <= 1000

    blocked = vault.decrypt_secret_for_use(
        sid, tenant_id="default", user_id=5, actor="test"
    )
    assert blocked["ok"] is False
    assert blocked["error"] == "revoked"


def test_rotation_reencrypt(isolated_vault):
    old_plain = "rotate-old-value-abc"
    new_plain = "rotate-new-value-xyz"
    created = vault.create_secret(
        tenant_id="default",
        user_id=7,
        name="rotate_key",
        value=old_plain,
    )
    sid = created["secret_id"]

    rot = vault.rotate_secret(
        sid,
        tenant_id="default",
        user_id=7,
        new_value=new_plain,
    )
    assert rot["ok"] is True
    assert rot["reveal_once"] == new_plain
    assert rot["rotation_due_at"]

    dec = vault.decrypt_secret_for_use(
        sid, tenant_id="default", user_id=7, actor="test"
    )
    assert dec["ok"] is True
    assert dec["value"] == new_plain
    assert dec["value"] != old_plain


def test_audit_trail_searchable(isolated_vault):
    vault.create_secret(
        tenant_id="default",
        user_id=99,
        name="audit_key",
        value="audit-secret-value",
    )
    audit = vault.search_audit_log(tenant_id="default", user_id=99, action="create")
    assert audit["ok"] is True
    assert audit["count"] >= 1
    assert audit["exportable"] is True
    for event in audit["events"]:
        assert "audit-secret-value" not in json.dumps(event)


def test_dashboard_metadata_only(isolated_vault):
    vault.create_secret(
        tenant_id="default",
        user_id=1,
        name="dash_key",
        value="dashboard-secret-12345",
        permission="trading",
    )
    dash = vault.key_vault_dashboard()
    assert dash["ok"] is True
    assert dash["feature_id"] == 189
    assert dash["architecture"]["encryption_at_rest"] == "AES-256-GCM-envelope"
    assert dash["compliance"]["no_plaintext_persistence"] is True
    assert "dashboard-secret-12345" not in json.dumps(dash)


def test_scoped_permission_enforcement(isolated_vault):
    created = vault.create_secret(
        tenant_id="default",
        user_id=3,
        name="readonly_key",
        value="perm-test-secret",
        permission="read_only",
    )
    sid = created["secret_id"]

    denied = vault.decrypt_secret_for_use(
        sid,
        tenant_id="default",
        user_id=3,
        required_permission="trading",
        actor="test",
    )
    assert denied["ok"] is False
    assert denied["error"] == "insufficient_permission"


def test_architecture_status():
    status = vault.vault_architecture_status()
    assert status["feature_id"] == 189
    assert status["envelope_encryption"] is True
    assert status["plaintext_persistence"] is False
    assert status["rotation_policy_days"] == 90
