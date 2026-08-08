"""Security module tests."""

import json

import pytest

from secrets_vault import (
    check_vault_key_rotation_policy,
    decrypt_secret,
    encrypt_secret,
    mask_secret,
)
from security_auth import (
    admin_emails,
    hash_session_token,
    is_admin_user,
    persist_auth_audit,
    record_login_failure,
    verify_admin_key,
)
from security_models import AuditLogModel


def test_encrypt_decrypt_roundtrip(monkeypatch):
    monkeypatch.setenv("SECRETS_MASTER_KEY", "test-master-key-for-unit-tests-only")
    plain = "sk-live-binance-secret-key-12345"
    enc = encrypt_secret(plain)
    assert enc != plain
    assert decrypt_secret(enc) == plain


def test_mask_secret():
    assert mask_secret("abcdefghijklmnop") == "abcd...mnop"


def test_session_token_hash_deterministic():
    h1 = hash_session_token("abc123")
    h2 = hash_session_token("abc123")
    assert h1 == h2
    assert len(h1) == 64


def test_admin_key_verify(monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "super-secret-admin")
    assert verify_admin_key("super-secret-admin") is True
    assert verify_admin_key("wrong") is False


def test_is_admin_user():
    assert is_admin_user({"email": "x@y.com"}) is False


def test_audit_log_model_defaults():
    row = AuditLogModel(event="login_failure", subject="a@b.com", reason="invalid_credentials")
    assert row.event == "login_failure"
    assert row.created_at


def test_persist_auth_audit_jsonl(tmp_path, monkeypatch):
    path = tmp_path / "auth_audit.jsonl"
    monkeypatch.setattr("security_auth._AUTH_AUDIT_PATH", path)
    persist_auth_audit(event="login_failure", subject="user@example.com", reason="invalid_credentials")
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    payload = json.loads(lines[0])
    assert payload["event"] == "login_failure"
    assert payload["subject"] == "user@example.com"


def test_record_login_failure_writes_audit(tmp_path, monkeypatch):
    from collections import defaultdict

    path = tmp_path / "auth_audit.jsonl"
    monkeypatch.setattr("security_auth._AUTH_AUDIT_PATH", path)
    monkeypatch.setattr("security_auth._login_attempts", defaultdict(list))
    record_login_failure("fail@example.com")
    assert path.exists()
    assert "login_failure" in path.read_text(encoding="utf-8")


def test_vault_key_rotation_overdue(monkeypatch):
    monkeypatch.setattr("config.VAULT_KEY_ROTATION_DAYS", 30, raising=False)
    monkeypatch.setattr("config.VAULT_KEY_LAST_ROTATED_AT", "2020-01-01", raising=False)
    status = check_vault_key_rotation_policy()
    assert status["status"] == "overdue"
    assert status["ok"] is False
