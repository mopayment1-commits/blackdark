# Credential Vault Layer — #907 Multi-Account Sync

**Not a standalone product.** Read-only exchange API key isolation merged into Multi-Account Sync.

## Purpose

- **Isolate** user exchange API keys in Vault/HSM — no plaintext in DB, code, or env
- **Read-only only** — reject trade/withdraw/write permissions at validation
- **Non-custodial** — sync keys for portfolio insight; no wallet private keys; no custody
- **Never exposed** — decryption happens backend-only during sync jobs

## Policy

| Requirement | Implementation |
|-------------|----------------|
| Vault/HSM | HashiCorp Vault (`VAULT_ADDR`) or local Fernet fallback + `SECRETS_MASTER_KEY` |
| Encryption | AES-256-GCM tenant-bound (`user_id` + `exchange` AAD) — extension of #1039 |
| Read-only enforcement | Exchange API probe — `can_trade` or `can_withdraw` → reject + user alert |
| Access control | Only `multi_account_sync` / `sync_connector` callers may decrypt |
| Audit | Append-only `data/credential_vault_audit.jsonl` — 2-year retention |
| Fee tracking | `data/credential_vault_fees.jsonl` per user/key/operation |

## Modules

| Module | Role |
|--------|------|
| `credential_vault_layer.py` | Store/retrieve/rotate/delete + production gate |
| `multi_account_sync.py` | #907 sync connector — vault retrieve → account snapshot |
| `user_keys_service.py` | Thin wrapper — delegates to credential vault |
| `api_key_security_guard.py` | `validate_read_only_sync_key()` |

## APIs

| Endpoint | Purpose |
|----------|---------|
| `POST /api/user/exchange-keys` | Store read-only sync key (whale tier) |
| `GET /api/user/exchange-keys` | List keys (masked only — never plaintext) |
| `DELETE /api/user/exchange-keys/{exchange}` | Revoke key |
| `GET /api/platform/credential-vault/status` | Vault layer status |
| `GET /api/platform/credential-vault/gate` | Production gate |
| `GET /api/platform/credential-vault/e2e` | Self-test |
| `GET /api/platform/multi-account-sync/status` | Sync feature status |
| `POST /api/platform/multi-account-sync/run` | Trigger sync for authenticated user |

## Integrations

| Ref | Integration |
|-----|-------------|
| #907 | Sync connector retrieves from vault — key lifecycle tied to account |
| #1019 | `trigger_compromise_playbook()` — revoke keys on suspected compromise |
| #1017 | Unauthorized vault access → security event + forensics hook |
| #1039 | Tenant AES-256-GCM = at-rest encryption implementation for credentials |
| #1038 | Key operations cross-logged via `record_key_access` |
| #1022 | RBAC — whale tier required to store keys; no human plaintext access |

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `SECRETS_MASTER_KEY` | Master encryption key (required in production) |
| `VAULT_ADDR` / `VAULT_TOKEN` | HashiCorp Vault backend |
| `AWS_KMS_KEY_ID` | AWS KMS integration (status reporting) |
| `KMS_PROVIDER` | Explicit KMS provider selection |

## Production Gate

`check_credential_vault_production_gate()` blocks production if:
- Plaintext storage policy violated
- Master key missing (production)
- Vault backend unavailable (production)
- Read-only / tenant encryption policies disabled

## Non-Custodial Clarification

BLACKDARK is **insight-only**. The platform:
- Accepts **read-only** exchange API keys for Multi-Account Sync
- **Rejects** trade-enabled or withdraw-enabled keys
- **Never** stores wallet private keys
- **Never** returns decrypted credentials in API responses
