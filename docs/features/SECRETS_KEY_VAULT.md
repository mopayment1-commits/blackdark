# Secrets Management & Key Vault — Feature #189

Sprint 0 security layer — **before everything else**.

## Architecture

| Layer | Implementation |
|-------|----------------|
| Primary backend | HashiCorp Vault (`VAULT_ADDR` + `VAULT_TOKEN`) via `bd_platform/vault_client.py` |
| Local fallback | AES-256-GCM envelope encryption via `secrets_vault.encrypt_secret_gcm` |
| Master key | `SECRETS_MASTER_KEY` — loaded in memory only at boot |
| Transit | TLS 1.3 (platform ingress) |

## Capabilities

| Capability | Function | API |
|------------|----------|-----|
| Architecture status | `vault_architecture_status()` | `GET /api/platform/secrets-vault/status` |
| Key dashboard | `key_vault_dashboard()` | `GET /api/platform/secrets-vault/dashboard` |
| Create secret | `create_secret()` | `POST /api/platform/secrets-vault/keys` |
| List keys (metadata) | `list_secrets()` | `GET /api/platform/secrets-vault/keys` |
| Revoke | `revoke_secret()` | `POST /api/platform/secrets-vault/keys/{id}/revoke` |
| Rotate (90d) | `rotate_secret()` | `POST /api/platform/secrets-vault/keys/{id}/rotate` |
| Audit trail | `search_audit_log()` | `GET /api/platform/secrets-vault/audit` |
| Suspicious alerts | `suspicious_access_alerts()` | `GET /api/platform/secrets-vault/alerts` |

## Guarantees

1. **No plaintext persistence** — registry + ciphertext blob contain encrypted material only
2. **No plaintext logging** — `log_safety.redact_secret` → `[redacted]`
3. **Per-tenant isolation** — `tenant_id` + `user_id` required for decrypt
4. **Scoped permissions** — `read_only` | `trading` | `withdrawal`
5. **90-day rotation** — `rotation_due_at` on every secret
6. **Immediate revocation** — in-memory `_revoked_ids` + persisted status (≤1s)
7. **Never re-display** — `reveal_once` only at create/rotate

## Mandatory negative tests

`tests/test_secrets_key_vault.py`:

- `test_negative_no_plaintext_in_storage` — extract from registry → ciphertext only
- `test_negative_logs_redacted` — logs must not contain secret values

## Integration

- `user_keys_service.store_user_exchange_keys` registers parallel vault entry (#189)
- Existing `user_api_keys` table continues Fernet encryption (D-02)
- `api_key_security_guard` audit trail complements vault audit

## Rotation documentation

See `docs/ops/SECRET_ROTATION.md` + `rotate_secret()` API for 90-day drill.

## Penetration test

Annual external pentest required (`penetration_test: annual_external_required` in status).
