# Encryption Policy — Cross-Cutting Sprint 0 Infrastructure

**Not a user-facing product.** Defense-in-depth for all sensitive platform data.

## Policy

| Layer | Requirement |
|-------|-------------|
| **At-Rest** | AES-256-GCM for all sensitive data (DB, object storage, backups, logs, audit) |
| **In-Transit** | TLS 1.3 minimum — API, DB connections, service mesh, external integrations — no downgrade |
| **Key Management** | KMS (AWS KMS / HashiCorp Vault) — rotation every 90 days — no hardcoded keys |
| **Certificates** | Auto-renewal (Let's Encrypt / managed) — expiry alert 30 days before |
| **Non-Custodial** | Platform never stores wallet private keys — encryption applies to platform data only |

## Module

| File | Role |
|------|------|
| `encryption_policy.py` | Policy engine — encrypt/decrypt, gate, KMS status, cert lifecycle |
| `data/encryption_policy_seed.json` | Sprint 0 policy configuration |
| `secrets_vault.py` | Underlying AES-256-GCM + Fernet primitives |

## Encrypted Scopes

- User credentials
- Session tokens (#1019)
- API keys
- Wallet labels (#926)
- User preferences
- Billing metadata (#908 — Stripe handles card data; platform encrypts metadata only)
- Activity logs (#1038)
- Audit trail / immutable audit (#1029)
- Backups (#1016 — separate key from operational DB)

## APIs

| Endpoint | Purpose |
|----------|---------|
| `GET /api/security/status` | Public posture including encryption policy summary |
| `GET /api/platform/encryption/status` | Full encryption policy status |
| `GET /api/platform/encryption/gate` | Production gate (blocks launch if incomplete) |
| `GET /api/platform/encryption/e2e` | Self-test roundtrip + compliance checks |

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `SECRETS_MASTER_KEY` | Operational at-rest encryption key |
| `BACKUP_ENCRYPTION_KEY` | Separate backup encryption key (required in production) |
| `IMMUTABLE_AUDIT_KEY` | Dedicated immutable audit store key |
| `SESSION_TOKEN_PEPPER` | Session token hashing pepper |
| `KMS_PROVIDER` / `AWS_KMS_KEY_ID` / `VAULT_ADDR` | External KMS integration |
| `TLS_CERT_EXPIRES_AT` | Certificate expiry for lifecycle alerts |
| `ENCRYPT_BACKUPS` | Enable AES-256-GCM backup encryption in `scripts/backup_postgres.py` |

## Integrations

| Ref | Integration |
|-----|-------------|
| #1019 | Session tokens encrypted at rest |
| #1022 | RBAC permission data encrypted |
| #1023 | GDPR Article 32 — documented technical measure |
| #1029 | Immutable audit store — dedicated key |
| #1038 | Activity audit logs encrypted |
| #1016 | Backups encrypted with separate key |
| #908 | PCI scope minimized — no card numbers in platform DB |

## Production Gate

`check_encryption_production_gate()` verifies:

- AES-256-GCM policy active
- TLS 1.3 policy active
- Operational + session + backup keys configured (production)
- HTTPS in production
- Non-custodial + no PCI card data in platform DB
- Pentest attestation (production)
- Certificate not expired / not in alert window

**Sprint 0 blocks production if incomplete.**
