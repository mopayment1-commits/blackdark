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
| MFA | Optional TOTP (`/api/auth/mfa/*`) |
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

## Reporting

Security issues: contact repository owner privately before public disclosure.

## Due Diligence Endpoints

- `GET /api/security/status` — live posture summary (includes honesty + residual risks)
- `GET /api/security/events` — admin security event log (requires admin + MFA when enforced)
- Max engineering gate: `python scripts/security_max_audit.py`
- Playbooks: `docs/SECURITY_HARDENING.md` · `docs/SECURITY_MAX_CHECKLIST.md` · `docs/CDN_WAF_CHECKLIST.md`
