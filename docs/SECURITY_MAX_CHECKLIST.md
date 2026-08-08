# SECURITY MAX — Engineering 100% Checklist

Goal: every **in-repo / operator-activatable** control is present and verified.  
External certifications (SOC2) and paid pentest execution remain outside this list.

## A. Merge & code (agent)

- [x] Security middleware (CSP/HSTS/CORS/CSRF/TrustedHost)
- [x] HttpOnly sessions + logout fix + session revoke on login
- [x] Abuse route gates + inbox IDOR fix + demo key hidden
- [x] MFA (user TOTP) + OAuth scaffolding
- [x] Admin MFA (`ADMIN_TOTP_SECRET` + `X-Admin-TOTP`)
- [x] Security event log (`security_events.py`)
- [x] Viral capacity / Redis rate limits
- [x] Dependency pins (aiohttp / cryptography / strawberry / starlette)
- [x] Postgres backup/restore scripts
- [x] Nginx + Cloudflare + k8s NetworkPolicy templates
- [x] `scripts/security_max_audit.py` gate

## B. Production env (operator — must do)

- [ ] Merge PR security-hardening-closure
- [ ] `ENV=production` · Soft Launch **unset**
- [ ] Postgres `DATABASE_URL` + Redis `REDIS_URL` + `SERVICE_BUS_LOCAL=false`
- [ ] `SECRETS_MASTER_KEY` · `SESSION_TOKEN_PEPPER` · `ADMIN_API_KEY`
- [ ] `ADMIN_MFA_REQUIRED=true` · `ADMIN_TOTP_SECRET=<base32>`
- [ ] `EXPOSE_B2B_DEMO_KEY=false` · `BLACKDARK_B2B_DEMO_KEY=disabled`
- [ ] `APP_BASE_URL` / `ALLOWED_HOSTS` / `CORS_ALLOWED_ORIGINS` HTTPS
- [ ] `WEB_CONCURRENCY≥2` · `WEB_REPLICAS≥2` · `VIRAL_MODE=true`

## C. Edge & ops (operator — must do)

- [ ] Activate CDN/WAF (`docs/CDN_WAF_CHECKLIST.md`)
- [ ] Schedule `python scripts/backup_postgres.py` (daily+) + test restore
- [ ] Sentry DSN + uptime monitor on `/health/live`
- [ ] Rotate secrets after any suspected leak
- [ ] Run `python scripts/security_max_audit.py` → `engineering_complete=true`

## D. External (optional institutional)

- [ ] Third-party pentest using `docs/templates/pentest_scope.md`
- [ ] SOC2 / ISO27001 program (organizational)

## Verify commands

```bash
python scripts/security_max_audit.py
curl -s "$BASE/api/security/status" | jq '.honesty, .residual_risks'
curl -s -H "X-Admin-Key: $ADMIN_API_KEY" -H "X-Admin-TOTP: $(…)" "$BASE/api/security/events"
```
