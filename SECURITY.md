# BLACKDARK Security Policy

## Overview

BLACKDARK implements defense-in-depth for crypto trading intelligence platforms handling sensitive user data and exchange API credentials.

## Authentication & Authorization

| Control | Implementation |
|---------|----------------|
| Passwords | PBKDF2-SHA256, 260,000 iterations |
| Sessions | SHA-256 hashed tokens + pepper at rest |
| Execution API | Whale tier + Bearer token required |
| Admin API | `X-Admin-Key` header OR `ADMIN_EMAILS` |
| GraphQL sensitive queries | Pro tier + Bearer token |

## User Exchange API Keys

- Stored in `user_api_keys` table
- Encrypted with **Fernet (AES-128-CBC)** via `secrets_vault.py`
- Production requires `SECRETS_MASTER_KEY` or `SECRETS_VAULT_KEY` env var
- API returns masked keys only — never plaintext secrets

## Environment Variables (Production Required)

```env
SECRETS_MASTER_KEY=<random-64-chars>
SESSION_TOKEN_PEPPER=<random-32-chars>
ADMIN_API_KEY=<random-admin-key>
# Or prefer file-based admin key (mode 0600, never commit):
# ADMIN_API_KEY_FILE=keys/admin_api_key.secret
# python scripts/setup_admin.py you@example.com
ADMIN_EMAILS=admin@yourcompany.com
TELEGRAM_WEBHOOK_SECRET=<telegram-secret>
POSTGRES_PASSWORD=<strong-password>
EXPOSE_B2B_DEMO_KEY=false
```

## Dependency Security

- Pinned versions in `requirements.txt`
- `pip-audit` runs in CI (`.github/workflows/security.yml`)
- Run locally: `python -m pip_audit -r requirements.txt`

## Incident Response

1. Rotate `SECRETS_MASTER_KEY` (requires re-encrypting user keys)
2. Rotate `ADMIN_API_KEY`, `SESSION_TOKEN_PEPPER`
3. Invalidate all sessions: truncate `user_sessions`
4. Review `maintenance_runs` and `execution_logs`

## Reporting

Security issues: contact repository owner privately before public disclosure.

## Due Diligence Endpoint

`GET /api/security/status` — live security posture summary.
