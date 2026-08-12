# Environment / configuration matrix (authoritative excerpt)

| VARIABLE | PURPOSE | REQUIRED IN PROD? | DEFAULT | SECRET? | FAILURE BEHAVIOR |
|---|---|---|---|---|---|
| `ENV` / `APP_ENV` / `ENVIRONMENT` | Environment mode | Yes | unset | No | Production guards inactive if unset |
| `DATABASE_URL` | Postgres DSN | Yes (strict) | SQLite path | Yes | Soft-launch may allow SQLite; strict prod fails guard |
| `SECRETS_MASTER_KEY` / `SECRETS_VAULT_KEY` | Fernet vault | Yes | dev-only key | Yes | Prod startup guard fails; cookie seal fails |
| `SESSION_TOKEN_PEPPER` | Session hashing | Yes | insecure sample | Yes | Prod hygiene fail |
| `ADMIN_API_KEY` / `ADMIN_EMAILS` | Admin auth | Yes | unset | Yes | Admin endpoints 401/403 |
| `ADMIN_TOTP_SECRET` | Admin MFA | Yes (strict) | unset | Yes | Admin MFA assert fails when required |
| `ADMIN_MFA_REQUIRED` | Enforce admin MFA | Recommended | false | No | MFA optional if false |
| `REDIS_URL` | Shared bus / RL | Yes (viral HA) | unset | Yes | Distributed publish fail-closed when required |
| `SERVICE_BUS_LOCAL` | Allow in-process bus | No in HA | true if no Redis | No | Multi-instance divergence if misused |
| `AUTH_TOKEN_IN_BODY` | Return bearer in JSON | No | false in prod | No | Cookie-only session when omitted |
| `ALLOW_LEGACY_SESSION_COOKIE` | Accept unsealed cookies | No | false in prod | No | Unsealed cookies rejected in prod |
| `COOKIE_SECURE` | Force Secure cookie | Recommended | derived | No | Cookies may omit Secure on HTTP |
| `EXPOSE_B2B_DEMO_KEY` | Public demo key page | No | false | No | `/b2b` omits demo key |
| `LIVE_EXECUTION_ALLOW_API` | Live order API | No | false | No | Live orders blocked |
| `SOFT_LAUNCH` | Demo mode | Demo only | false | No | Relaxes Postgres/billing requirements |
| `STRIPE_WEBHOOK_SECRET` / `LEMON_SQUEEZY_WEBHOOK_SECRET` | Webhook verify | Yes if billing | unset | Yes | Webhooks fail closed when configured |

Production must refuse privileged operation when security-critical keys are missing
(`production_guard.enforce_production_guard`).
