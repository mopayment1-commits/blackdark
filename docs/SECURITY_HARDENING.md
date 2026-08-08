# Security Hardening — Engineering Posture

**Honest scope:** application-layer controls for auth, sessions, user secrets, abuse routes, and browser headers.  
**Not claimed:** SOC2, ISO 27001, completed third-party penetration test, or edge WAF/CDN.

## Controls shipped

| Layer | Control |
|-------|---------|
| Passwords | PBKDF2-SHA256 (260k) |
| Sessions | SHA-256 + pepper at rest; login revokes prior sessions |
| Cookies | `bd_token` HttpOnly + SameSite=Lax + Secure (prod/HTTPS) |
| Logout | Revokes Bearer **or** cookie token (fixed) |
| MFA | Optional TOTP (`/api/auth/mfa/*`) |
| OAuth | Optional Google/GitHub when configured |
| CSRF | Origin/Referer check for cookie-auth mutations |
| Headers | CSP, nosniff, frame-deny, Referrer-Policy, HSTS (prod) |
| CORS | Explicit allowlist from `APP_BASE_URL` / `CORS_ALLOWED_ORIGINS` |
| Host | TrustedHost when `ALLOWED_HOSTS` or `APP_BASE_URL` set in prod |
| Rate limits | Login IP+email; Redis when available; viral class limits |
| User keys | Fernet vault; withdraw-key reject; prod fails without master key |
| Abuse routes | Telegram/alert tests gated; inbox mark-read ownership |
| Demo keys | Not returned unless `EXPOSE_B2B_DEMO_KEY=true` |
| GraphQL | Legacy `graphql-ws` protocol disabled when supported |
| Soft Launch | Forbids live execution API + public demo key exposure |

## Verify

```bash
curl -sI "$BASE/" | rg -i 'content-security-policy|x-frame|strict-transport|x-content-type'
curl -s "$BASE/api/security/status" | jq '.honesty, .residual_risks'
python -m pytest tests/test_security.py tests/test_security_hardening.py -q
```

## Production env (minimum)

```bash
ENV=production
# SOFT_LAUNCH unset for institutional / viral HA
SECRETS_MASTER_KEY=…          # openssl rand -hex 32
SESSION_TOKEN_PEPPER=…        # openssl rand -hex 16
ADMIN_API_KEY=…
ADMIN_EMAILS=…
REDIS_URL=redis://…
SERVICE_BUS_LOCAL=false
APP_BASE_URL=https://your.domain
ALLOWED_HOSTS=your.domain
EXPOSE_B2B_DEMO_KEY=false
CORS_ALLOWED_ORIGINS=https://your.domain
```

## Residual (operator / external)

1. Activate CDN/WAF — `docs/CDN_WAF_CHECKLIST.md` + `deploy/cloudflare/waf-rules.json`  
2. Schedule Postgres backups — `scripts/backup_postgres.py`  
3. Set `ADMIN_TOTP_SECRET` and send `X-Admin-TOTP` on admin routes  
4. Third-party pentest — `docs/templates/pentest_scope.md`  
5. Soft Launch remains **demo-only** — not the production security bar  

**Max engineering gate:** `python scripts/security_max_audit.py` · Checklist: `docs/SECURITY_MAX_CHECKLIST.md`
