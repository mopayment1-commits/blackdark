# Environment Variable Registry

**Finding:** `F-XFER-01` transferability  
Canonical matrix also: `docs/ENV_CONFIG_MATRIX.md`

## Critical (production)

| Variable | Required | Default | Notes |
|----------|----------|---------|-------|
| `DATABASE_URL` | strict prod | — | Postgres DSN |
| `SOFT_LAUNCH` | soft only | unset | Must be unset for strict prod |
| `SECRETS_MASTER_KEY` / `SECRETS_VAULT_KEY` | yes | — | Fernet |
| `SESSION_TOKEN_PEPPER` | yes | — | Cookie integrity |
| `ADMIN_API_KEY` or `ADMIN_API_KEY_FILE` | yes | — | Admin boundary |
| `ADMIN_EMAILS` | yes | — | Comma list |
| `APP_BASE_URL` | yes | — | Canonical public URL |
| `CORS_ALLOWED_ORIGINS` | recommended | localhost | Exact origins |
| `CSP_NONCE_MODE` | recommended | `true` | Break-glass `false` only |
| `REDIS_URL` | viral/HA | — | Required when VIRAL_MODE |
| `WEB_CONCURRENCY` / `WEB_REPLICAS` | HA | 1 | Multi-worker evidence separate |
| `TELEGRAM_SECRETS_FILE` | optional | — | Points to 0600 file |
| `STRIPE_*` / `LEMON_SQUEEZY_*` | billing | — | PSP path |

## Financial truth related

| Variable | Effect |
|----------|--------|
| Fee tables | Code authority `fee_matrix` — not env |
| `GAS_ORACLE_REFRESH_SEC` | Cache refresh cadence |
| `GAS_ORACLE_MAX_STALE_SEC` | Fail-closed stale window (default 60) |
| `DEFAULT_QUOTE_AMOUNT` | Scan notional |

## Do not set in production

| Variable | Why |
|----------|-----|
| `CSP_NONCE_MODE=false` | Reopens unsafe-inline scripts |
| Soft Launch flags under viral HA claims | Contradicts institutional mode |
| Vault `-dev` root token as prod secret | Local profile only |
