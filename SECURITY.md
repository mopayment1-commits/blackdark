# BLACKDARK Security Policy

## Overview

BLACKDARK implements defense-in-depth for a Decision Intelligence / Trust OS product handling user accounts and (optional) exchange API credentials.

This document describes **engineering controls**. It is **not** a SOC2/ISO 27001 certificate or a completed third-party penetration-test report.

## Authentication & Authorization

| Control | Implementation |
|---------|----------------|
| Passwords | PBKDF2-SHA256, 260,000 iterations |
| Sessions | SHA-256 hashed tokens + pepper at rest; login revokes prior sessions |
| Cookies | `bd_token` HttpOnly + SameSite=Lax + Secure (prod/HTTPS) |
| MFA | TOTP (`/api/auth/mfa/*`); **enrollment required in production** when `USER_MFA_ENROLL_REQUIRED=true` (Launch-57 default) |
| OAuth | Optional Google/GitHub when client IDs configured |
| Execution API | Whale tier + Bearer/cookie required |
| Admin API | `X-Admin-Key` header OR `ADMIN_EMAILS` |
| GraphQL sensitive queries | Pro tier + Bearer/cookie; legacy `graphql-ws` disabled when supported |

## Browser / HTTP hardening

- Security headers: CSP, `X-Content-Type-Options`, `X-Frame-Options`, Referrer-Policy, HSTS (prod)
- CORS allowlist (`APP_BASE_URL` / `CORS_ALLOWED_ORIGINS`) — never `*` with credentials
- CSRF: Origin/Referer check for cookie-authenticated mutating requests
- TrustedHost when `ALLOWED_HOSTS` or `APP_BASE_URL` is set in production

## User Exchange API Keys

- Stored encrypted with **Fernet** via `secrets_vault.py`
- Production requires `SECRETS_MASTER_KEY` or `SECRETS_VAULT_KEY`
- API returns masked keys only — never plaintext secrets
- Withdraw-capable keys rejected by `api_key_security_guard.py`

## Environment Variables (Production Required)

```env
SECRETS_MASTER_KEY=<openssl rand -hex 32>
SESSION_TOKEN_PEPPER=<openssl rand -hex 16>
ADMIN_API_KEY=<random-admin-key>
ADMIN_EMAILS=admin@yourcompany.com
TELEGRAM_WEBHOOK_SECRET=<telegram-secret>
APP_BASE_URL=https://your.domain
ALLOWED_HOSTS=your.domain
CORS_ALLOWED_ORIGINS=https://your.domain
EXPOSE_B2B_DEMO_KEY=false
REDIS_URL=redis://…
SERVICE_BUS_LOCAL=false
```

Soft Launch (`SOFT_LAUNCH=true`) is **demo-only** and must not enable `LIVE_EXECUTION_ALLOW_API` or public demo-key exposure.

## Dependency Security

- Pinned ranges in `requirements.txt` (aiohttp / cryptography / strawberry bumped for known CVEs)
- `pip-audit` runs in CI (`.github/workflows/security.yml`)
- Run locally: `python -m pip_audit -r requirements.txt`

## Incident Response

1. Rotate `SECRETS_MASTER_KEY` (requires re-encrypting user keys)
2. Rotate `ADMIN_API_KEY`, `SESSION_TOKEN_PEPPER`
3. Invalidate all sessions: truncate `user_sessions`
4. Review `maintenance_runs` and `execution_logs`

## Reporting & vulnerability disclosure

- **Public VDP:** [Vulnerability Disclosure Policy](docs/security/VULNERABILITY_DISCLOSURE_POLICY.md)
- **security.txt:** `/.well-known/security.txt` (RFC 9116)
- Product advisories: `docs/security/PRODUCT_SECURITY_ADVISORY_PROCESS.md`

## Customer security logs

- Policy: `docs/security/CUSTOMER_SECURITY_LOG_POLICY.md` (≥180 day retention)
- Export: `GET /api/security/customer-logs/export` (authenticated)
- Commercial: `docs/security/COMMERCIAL_SECURITY_FEATURES.md` (SSO not sold as separate add-on)

## Security updates

- `docs/security/SECURITY_UPDATE_POLICY.md` — severity SLAs, KEV, supported versions

## Open source governance

- `docs/security/OPEN_SOURCE_GOVERNANCE.md`

## Due Diligence Endpoints

- `GET /api/security/status` — **public** minimal attestations (not a certification)
- `GET /api/security/status/detail` — detailed posture (authenticated)
- `GET /api/security/events` — admin security event log (requires admin + MFA when enforced)
- Max engineering gate: `python scripts/security_max_audit.py`
- Playbooks: `docs/SECURITY_HARDENING.md` · `docs/SECURITY_MAX_CHECKLIST.md` · `docs/CDN_WAF_CHECKLIST.md`
