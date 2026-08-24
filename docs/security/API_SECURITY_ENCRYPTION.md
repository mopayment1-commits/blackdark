# API Security Encryption — Feature #165

**Non-negotiable** security layer (Sprint 1). Integrates with #192 Security-First Architecture.

## Capabilities

| Capability | Implementation |
|------------|----------------|
| Encrypt at rest | Fernet AES-128-CBC (`secrets_vault`) |
| Per-user isolation | `user_id` scoped key registry |
| Scoped permissions | `scopes` list per key |
| Immediate revocation | `revoke_user_api_secret()` |
| Key rotation | `rotate_user_api_secret()` |
| Audit trail | `data/api_key_security_audit.jsonl` |
| No plaintext logging | `mask_secret` + log redaction |

## API

| Endpoint | Auth | Description |
|----------|------|-------------|
| `GET /api/platform/security/encryption/status` | Admin | Platform posture |
| `GET /api/platform/security/keys/status` | User | Key metadata (no secrets) |
| `POST /api/platform/security/keys/store` | User | Store encrypted secret |
| `POST /api/platform/security/keys/revoke` | User | Immediate revocation |
| `POST /api/platform/security/keys/rotate` | User | Rotation drill |

## Negative tests

- Revoked key → `key_revoked` error
- Cross-user access → `access_denied`
- Plaintext never appears in audit log

## Acceptance criteria

| Criterion | Target |
|-----------|--------|
| No plaintext persistence/logging | Enforced |
| Key rotation | Tested |
| Revocation | Immediate |
| Access audit | Full trail |
| Negative tests | Revoked + isolation |
