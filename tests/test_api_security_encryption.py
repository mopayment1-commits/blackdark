"""Tests — API Security Encryption (#165)."""

from __future__ import annotations

import json

import pytest

from bd_platform import api_security_encryption as ase


@pytest.fixture
def isolated_security_paths(tmp_path, monkeypatch):
    registry = tmp_path / "registry.json"
    revocations = tmp_path / "revocations.json"
    audit = tmp_path / "audit.jsonl"
    monkeypatch.setattr(ase, "_REGISTRY_PATH", registry)
    monkeypatch.setattr(ase, "_REVOCATIONS_PATH", revocations)
    monkeypatch.setattr(ase, "_AUDIT_PATH", audit)
    return registry, revocations, audit


def test_store_and_access_encrypted_secret(isolated_security_paths):
    stored = ase.store_user_api_secret(
        user_id=42,
        label="binance-read",
        plaintext="super-secret-api-key-12345",
        scopes=["read"],
        exchange="binance",
    )
    assert stored["ok"] is True
    assert "super-secret" not in stored["masked_preview"]
    assert stored["plaintext_logged"] is False

    access = ase.access_user_api_secret(user_id=42, key_id=stored["key_id"], action="read")
    assert access["ok"] is True
    assert access["value"] == "super-secret-api-key-12345"
    assert access["plaintext_logged"] is False


def test_per_user_isolation_denied(isolated_security_paths):
    stored = ase.store_user_api_secret(
        user_id=1,
        label="key-a",
        plaintext="user-one-secret",
        scopes=["read"],
    )
    denied = ase.access_user_api_secret(
        user_id=1,
        key_id=stored["key_id"],
        action="read",
        requester_user_id=2,
    )
    assert denied["ok"] is False
    assert denied["error"] == "access_denied"


def test_revoked_key_immediate_denial(isolated_security_paths):
    stored = ase.store_user_api_secret(
        user_id=7,
        label="revoke-me",
        plaintext="to-be-revoked",
        scopes=["read"],
    )
    revoke = ase.revoke_user_api_secret(user_id=7, key_id=stored["key_id"])
    assert revoke["revoked"] is True

    denied = ase.access_user_api_secret(user_id=7, key_id=stored["key_id"], action="read")
    assert denied["ok"] is False
    assert denied["error"] == "key_revoked"


def test_rotation_reencrypts(isolated_security_paths):
    stored = ase.store_user_api_secret(
        user_id=9,
        label="rotate-me",
        plaintext="old-secret-value",
        scopes=["read"],
    )
    rotated = ase.rotate_user_api_secret(
        user_id=9,
        key_id=stored["key_id"],
        new_plaintext="new-secret-value",
    )
    assert rotated["ok"] is True
    assert rotated["rotation_count"] == 1

    access = ase.access_user_api_secret(user_id=9, key_id=stored["key_id"], action="read")
    assert access["value"] == "new-secret-value"


def test_no_plaintext_in_audit_log(isolated_security_paths):
    _, _, audit_path = isolated_security_paths
    stored = ase.store_user_api_secret(
        user_id=3,
        label="audit-test",
        plaintext="plaintext-should-not-appear",
        scopes=["read"],
    )
    ase.access_user_api_secret(user_id=3, key_id=stored["key_id"], action="read")

    raw = audit_path.read_text(encoding="utf-8")
    assert "plaintext-should-not-appear" not in raw
    rows = [json.loads(line) for line in raw.splitlines() if line.strip()]
    assert rows
    assert all("plaintext-should-not-appear" not in json.dumps(r) for r in rows)


def test_security_encryption_status():
    status = ase.security_encryption_status()
    assert status["feature_id"] == 165
    assert status["plaintext_logging"] is False
    assert status["per_user_isolation"] is True
