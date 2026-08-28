"""Credential Vault Layer — read-only sync key isolation (#907)."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture
def vault_env(monkeypatch, tmp_path):
    monkeypatch.setenv("SECRETS_MASTER_KEY", "cvault-test-master-key-material!")
    monkeypatch.delenv("ENV", raising=False)
    monkeypatch.delenv("APP_ENV", raising=False)
    audit = tmp_path / "credential_vault_audit.jsonl"
    fees = tmp_path / "credential_vault_fees.jsonl"
    monkeypatch.setattr("credential_vault_layer._AUDIT_PATH", audit)
    monkeypatch.setattr("credential_vault_layer._FEE_PATH", fees)
    import secrets_vault

    secrets_vault._fernet = None
    return {"audit": audit, "fees": fees}


def test_seed_loads():
    from credential_vault_layer import _load_seed

    seed = _load_seed()
    assert seed["standalone_rejected"] is True
    assert seed["credential_vault"]["policy"]["read_only_keys_only"] is True


def test_tenant_encryption_roundtrip(vault_env):
    from credential_vault_layer import decrypt_credential, encrypt_credential

    plain = "read-only-api-key-secret"
    enc = encrypt_credential(plain, user_id=42, exchange="binance")
    assert plain not in enc
    assert decrypt_credential(enc, user_id=42, exchange="binance") == plain


def test_tenant_binding_rejects_wrong_user(vault_env):
    from credential_vault_layer import decrypt_credential, encrypt_credential

    enc = encrypt_credential("secret", user_id=1, exchange="binance")
    with pytest.raises(Exception):
        decrypt_credential(enc, user_id=2, exchange="binance")


@pytest.mark.asyncio
async def test_read_only_validation_rejects_trade_keys():
    from api_key_security_guard import validate_read_only_sync_key

    with patch("execution_keys.verify_binance_keys", new_callable=AsyncMock) as mock_verify:
        mock_verify.return_value = {
            "valid": True,
            "can_trade": True,
            "can_withdraw": False,
        }
        result = await validate_read_only_sync_key("binance", "key", "secret")
        assert result.allowed is False
        assert result.reason == "trade_permission_rejected"


@pytest.mark.asyncio
async def test_read_only_validation_rejects_withdraw_keys():
    from api_key_security_guard import validate_read_only_sync_key

    with patch("execution_keys.verify_binance_keys", new_callable=AsyncMock) as mock_verify:
        mock_verify.return_value = {
            "valid": True,
            "can_trade": False,
            "can_withdraw": True,
        }
        result = await validate_read_only_sync_key("binance", "key", "secret")
        assert result.allowed is False
        assert result.reason == "withdraw_enabled_rejected"


@pytest.mark.asyncio
async def test_read_only_validation_accepts_read_only():
    from api_key_security_guard import validate_read_only_sync_key

    with patch("execution_keys.verify_binance_keys", new_callable=AsyncMock) as mock_verify:
        mock_verify.return_value = {
            "valid": True,
            "can_trade": False,
            "can_withdraw": False,
        }
        result = await validate_read_only_sync_key("binance", "key", "secret")
        assert result.allowed is True
        assert result.reason == "read_only_ok"


@pytest.mark.asyncio
async def test_store_sync_credential_encrypts_no_plaintext(vault_env):
    from credential_vault_layer import store_sync_credential
    from database import fetch_user_api_key_secrets

    with patch("execution_keys.verify_binance_keys", new_callable=AsyncMock) as mock_verify:
        mock_verify.return_value = {"valid": True, "can_trade": False, "can_withdraw": False}
        result = await store_sync_credential(7, "binance", "test-api-key-12345", "test-secret-67890")
        assert result["success"] is True
        assert result["never_exposed"] is True
        assert "test-api-key" not in result.get("api_key_masked", "")

    row = await fetch_user_api_key_secrets(7, "binance")
    assert row is not None
    assert "test-api-key-12345" not in str(row["api_key_encrypted"])
    assert "test-secret-67890" not in str(row["api_secret_encrypted"])


@pytest.mark.asyncio
async def test_store_rejects_trade_keys(vault_env):
    from credential_vault_layer import store_sync_credential

    with patch("execution_keys.verify_binance_keys", new_callable=AsyncMock) as mock_verify:
        mock_verify.return_value = {"valid": True, "can_trade": True, "can_withdraw": False}
        result = await store_sync_credential(8, "binance", "trade-key", "trade-secret")
        assert result["success"] is False
        assert result["reason"] == "trade_permission_rejected"


@pytest.mark.asyncio
async def test_retrieve_blocked_for_unauthorized_caller(vault_env):
    from credential_vault_layer import retrieve_for_sync, store_sync_credential

    with patch("execution_keys.verify_binance_keys", new_callable=AsyncMock) as mock_verify:
        mock_verify.return_value = {"valid": True, "can_trade": False, "can_withdraw": False}
        await store_sync_credential(9, "binance", "ro-key-abc", "ro-secret-xyz")

    creds = await retrieve_for_sync(9, "binance", caller="http_api")
    assert creds is None


@pytest.mark.asyncio
async def test_retrieve_allowed_for_sync_caller(vault_env):
    from credential_vault_layer import retrieve_for_sync, store_sync_credential

    with patch("execution_keys.verify_binance_keys", new_callable=AsyncMock) as mock_verify:
        mock_verify.return_value = {"valid": True, "can_trade": False, "can_withdraw": False}
        await store_sync_credential(10, "binance", "sync-key", "sync-secret")

    creds = await retrieve_for_sync(10, "binance", caller="multi_account_sync")
    assert creds == ("sync-key", "sync-secret")


@pytest.mark.asyncio
async def test_user_keys_service_blocks_client_retrieve(vault_env):
    from credential_vault_layer import store_sync_credential
    from user_keys_service import get_user_exchange_credentials

    with patch("execution_keys.verify_binance_keys", new_callable=AsyncMock) as mock_verify:
        mock_verify.return_value = {"valid": True, "can_trade": False, "can_withdraw": False}
        await store_sync_credential(11, "binance", "hidden-key", "hidden-secret")

    assert await get_user_exchange_credentials(11, "binance") is None
    assert await get_user_exchange_credentials(11, "binance", caller="multi_account_sync") == (
        "hidden-key",
        "hidden-secret",
    )


@pytest.mark.asyncio
async def test_compromise_playbook_revokes_keys(vault_env):
    from credential_vault_layer import store_sync_credential, trigger_compromise_playbook
    from database import fetch_user_api_keys

    with patch("execution_keys.verify_binance_keys", new_callable=AsyncMock) as mock_verify:
        mock_verify.return_value = {"valid": True, "can_trade": False, "can_withdraw": False}
        await store_sync_credential(12, "binance", "comp-key", "comp-secret")

    result = await trigger_compromise_playbook(12, reason="test_compromise")
    assert result["ok"] is True
    assert "binance" in result["revoked_exchanges"]
    rows = await fetch_user_api_keys(12)
    assert rows == []


def test_production_gate_passes_in_dev(vault_env):
    from credential_vault_layer import check_credential_vault_production_gate

    gate = check_credential_vault_production_gate()
    assert gate["checks"]["read_only_only"] is True
    assert gate["ok"] is True


def test_e2e_all_passed(vault_env):
    from credential_vault_layer import run_credential_vault_e2e

    result = run_credential_vault_e2e()
    assert result["ok"] is True
    assert result["all_passed"] is True


def test_security_posture_includes_credential_vault(vault_env):
    from security_posture import security_posture_report

    report = security_posture_report()
    assert report.get("credential_vault") is not None
    ids = {c["id"] for c in report["checks"]}
    assert "credential_vault_read_only" in ids


@pytest.mark.asyncio
async def test_platform_credential_vault_routes(vault_env):
    from dashboard import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for path in (
            "/api/platform/credential-vault/status",
            "/api/platform/credential-vault/gate",
            "/api/platform/credential-vault/e2e",
            "/api/platform/multi-account-sync/status",
        ):
            r = await client.get(path)
            assert r.status_code == 200, path
            body = r.json()
            assert body.get("ok") is True or body.get("all_passed") is True or "feature" in body


@pytest.mark.asyncio
async def test_audit_log_written_on_store(vault_env):
    from credential_vault_layer import store_sync_credential

    with patch("execution_keys.verify_binance_keys", new_callable=AsyncMock) as mock_verify:
        mock_verify.return_value = {"valid": True, "can_trade": False, "can_withdraw": False}
        await store_sync_credential(13, "binance", "audit-key", "audit-secret")

    lines = vault_env["audit"].read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) >= 1
    row = json.loads(lines[-1])
    assert row["action"] == "store"
    assert row["allowed"] is True
