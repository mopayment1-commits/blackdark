"""D-02 — secrets vault encryption and rotation."""

from __future__ import annotations

import secrets_vault


def test_fernet_roundtrip(monkeypatch):
    monkeypatch.setenv("SECRETS_MASTER_KEY", "d02-test-master-key-32chars-min!!")
    secrets_vault._fernet = None
    plain = "api-key-secret-value"
    enc = secrets_vault.encrypt_secret(plain)
    assert enc != plain
    assert secrets_vault.decrypt_secret(enc) == plain


def test_gcm_roundtrip(monkeypatch):
    monkeypatch.setenv("SECRETS_MASTER_KEY", "d02-gcm-test-key-material!!")
    secrets_vault._fernet = None
    plain = "gcm-secret-payload"
    enc = secrets_vault.encrypt_secret_gcm(plain)
    assert enc != plain
    assert secrets_vault.decrypt_secret_gcm(enc) == plain


def test_rotate_reencrypt(monkeypatch):
    monkeypatch.setenv("SECRETS_MASTER_KEY", "d02-rotate-key-material!!!!")
    secrets_vault._fernet = None
    values = ["a", "b", "c"]
    rotated = secrets_vault.rotate_vault_reencrypt(values)
    assert len(rotated) == 3
    for orig, enc in zip(values, rotated):
        assert secrets_vault.decrypt_secret(enc) == orig


def test_no_plaintext_in_ciphertext(monkeypatch):
    monkeypatch.setenv("SECRETS_MASTER_KEY", "d02-plaintext-check-key!!!")
    secrets_vault._fernet = None
    plain = "sk-live-super-secret"
    enc = secrets_vault.encrypt_secret(plain)
    assert plain not in enc
