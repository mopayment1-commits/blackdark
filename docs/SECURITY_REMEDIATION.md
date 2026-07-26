# Security remediation complete — 2026-07-25

## Fixed (100% code-level)

| Issue | Fix |
|-------|-----|
| Unauthenticated execution/risk/admin endpoints | `require_whale`, `require_admin`, `require_pro_or_above` |
| No user API key encryption | `secrets_vault.py` + `user_api_keys` table + `/api/user/exchange-keys` |
| Session tokens plaintext | SHA-256 + pepper hashing |
| No login rate limit | 10 attempts / 5 min |
| GraphQL public sensitive data | Auth context + Pro tier for arb/risk |
| Telegram webhook unverified | `TELEGRAM_WEBHOOK_SECRET` header check |
| Demo B2B key exposed | Hidden unless `EXPOSE_B2B_DEMO_KEY=true` |
| Unpinned dependencies | Version ranges in `requirements.txt` |
| No CVE scanning | `.github/workflows/security.yml` + pip-audit |
| Weak Docker password | `POSTGRES_PASSWORD` required from `.env` |
| No SECURITY.md | `SECURITY.md` + `/api/security/status` |

## Production checklist

```env
SECRETS_MASTER_KEY=<64-char-random>
SESSION_TOKEN_PEPPER=<32-char-random>
ADMIN_API_KEY=<admin-key>
ADMIN_EMAILS=you@company.com
POSTGRES_PASSWORD=<strong-password>
TELEGRAM_WEBHOOK_SECRET=<telegram-secret>
```

## Verify

```bash
python -m pytest tests/test_security.py -v
curl http://localhost:8080/api/security/status
```
