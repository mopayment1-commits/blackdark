"""Encryption Policy — cross-cutting at-rest + in-transit Sprint 0 infrastructure."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture
def enc_env(monkeypatch):
    monkeypatch.setenv("SECRETS_MASTER_KEY", "enc-policy-test-master-key!!!!")
    monkeypatch.setenv("SESSION_TOKEN_PEPPER", "enc-policy-session-pepper!!")
    monkeypatch.setenv("BACKUP_ENCRYPTION_KEY", "enc-policy-backup-key-separate!")
    monkeypatch.delenv("ENV", raising=False)
    monkeypatch.delenv("APP_ENV", raising=False)
    import secrets_vault

    secrets_vault._fernet = None


def test_seed_loads():
    from encryption_policy import _load_seed

    seed = _load_seed()
    assert seed["standalone_rejected"] is True
    assert seed["encryption_policy"]["policy"]["at_rest_algorithm"] == "AES-256-GCM"


def test_at_rest_roundtrip(enc_env):
    from encryption_policy import decrypt_at_rest, encrypt_at_rest

    plain = "wallet-label:user-main"
    enc = encrypt_at_rest(plain, domain="wallet_label")
    assert enc != plain
    assert decrypt_at_rest(enc, domain="wallet_label") == plain


def test_domain_binding_rejects_wrong_aad(enc_env):
    from encryption_policy import decrypt_at_rest, encrypt_at_rest

    enc = encrypt_at_rest("billing-meta", domain="billing")
    with pytest.raises(Exception):
        decrypt_at_rest(enc, domain="session")


def test_audit_payload_roundtrip(enc_env):
    from encryption_policy import decrypt_audit_payload, encrypt_audit_payload

    payload = {"action": "login", "user_id": 42, "result": "ok"}
    blob = encrypt_audit_payload(payload)
    assert isinstance(blob, str)
    restored = decrypt_audit_payload(blob)
    assert restored["action"] == "login"
    assert restored["user_id"] == 42


def test_backup_blob_roundtrip(enc_env):
    from encryption_policy import decrypt_backup_blob, encrypt_backup_blob

    raw = b"pg_dump gzip payload bytes"
    enc = encrypt_backup_blob(raw)
    assert decrypt_backup_blob(enc) == raw


def test_in_transit_non_prod_allows_http(monkeypatch):
    from encryption_policy import verify_in_transit_request
    from starlette.requests import Request

    monkeypatch.delenv("ENV", raising=False)
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/",
        "raw_path": b"/",
        "query_string": b"",
        "headers": [],
        "client": ("127.0.0.1", 80),
        "server": ("test", 80),
    }
    req = Request(scope)
    result = verify_in_transit_request(req)
    assert result["ok"] is True


def test_key_management_status(enc_env):
    from encryption_policy import key_management_status

    km = key_management_status()
    assert km["keys_configured"]["operational"] is True
    assert km["keys_configured"]["backup"] is True
    assert km["keys_configured"]["session_pepper"] is True
    assert km["rotation_days"] == 90


def test_production_gate_passes_in_dev(enc_env):
    from encryption_policy import check_encryption_production_gate

    gate = check_encryption_production_gate()
    assert gate["checks"]["aes_256_gcm"] is True
    assert gate["checks"]["tls_1_3_policy"] is True
    assert gate["ok"] is True


def test_e2e_all_passed(enc_env):
    from encryption_policy import run_encryption_policy_e2e

    result = run_encryption_policy_e2e()
    assert result["ok"] is True
    assert result["all_passed"] is True
    ids = {c["id"] for c in result["checks"]}
    assert "roundtrip" in ids
    assert "domain_binding" in ids
    assert "stripe_pci" in ids
    assert "gdpr_art32" in ids


def test_stripe_pci_scope():
    from encryption_policy import stripe_pci_scope_note

    note = stripe_pci_scope_note()
    assert note["pci_card_data_in_platform_db"] is False
    assert note["stripe_handles_card_data"] is True


def test_security_posture_includes_encryption(enc_env):
    from security_posture import security_posture_report

    report = security_posture_report()
    assert report.get("encryption_policy") is not None
    ids = {c["id"] for c in report["checks"]}
    assert "encryption_policy_aes_gcm" in ids
    assert "encryption_policy_tls_1_3" in ids


@pytest.mark.asyncio
async def test_platform_encryption_routes(enc_env):
    from dashboard import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for path in (
            "/api/platform/encryption/status",
            "/api/platform/encryption/gate",
            "/api/platform/encryption/e2e",
        ):
            r = await client.get(path)
            assert r.status_code == 200, path
            body = r.json()
            assert body.get("ok") is True or body.get("all_passed") is True or "checks" in body


@pytest.mark.asyncio
async def test_security_status_includes_encryption(enc_env):
    from dashboard import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/api/security/status")
        assert r.status_code == 200
        body = r.json()
        assert body["at_rest_encryption"]["algorithm"] == "AES-256-GCM"
        assert "encryption_policy" in body
        assert "in_transit_encryption" in body
        assert "backup_encryption" in body


def test_record_key_rotation(enc_env, tmp_path, monkeypatch):
    from encryption_policy import _ROTATION_STATE_PATH, record_key_rotation_event

    state_file = tmp_path / "rotation.json"
    monkeypatch.setattr("encryption_policy._ROTATION_STATE_PATH", state_file)
    event = record_key_rotation_event(actor="test-admin")
    assert event["actor"] == "test-admin"
    assert state_file.is_file()
    saved = json.loads(state_file.read_text(encoding="utf-8"))
    assert saved["actor"] == "test-admin"
