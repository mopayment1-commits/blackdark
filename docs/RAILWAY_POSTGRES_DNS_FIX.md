# Railway PostgreSQL DNS (`gaierror`) — remediation

## Symptom

Production endpoints that query Postgres return errors:

- `/api/telegram/free/status` → `subscribers_error: "gaierror"` (bot still configured)
- `/api/gtm/status` → `metrics_errors` includes `gaierror`
- `/health/ready` → `database_ready: false`, `postgres_pool.last_error: "gaierror"`

Resolver output (2026-09-03):

```json
{
  "candidates": [
    {"env": "DATABASE_URL", "host": "postgres.railway.internal", "resolves": false}
  ],
  "selected_host": "postgres.railway.internal",
  "selection": "first_candidate_unresolved"
}
```

## Root cause

`DATABASE_URL` points at `postgres.railway.internal`, but DNS resolution fails inside the **web** service container. This is **not** a Telegram or hero-binding code defect — the Postgres hostname is unreachable from the running web replica.

Common Railway causes:

1. Postgres plugin detached, paused, or deleted while `DATABASE_URL` reference remains on web.
2. Web service redeployed without a valid linked Postgres variable refresh.
3. Private networking disabled or web/postgres in mismatched environments.

## Fix (owner — Railway dashboard)

1. **Postgres service** → confirm status **Running**.
2. **Web service → Variables** → verify `DATABASE_URL` references the live Postgres plugin (`${{Postgres.DATABASE_URL}}`).
3. If internal host still fails, add **`DATABASE_PUBLIC_URL`** from the Postgres service (Networking → Public URL) — app resolver tries it automatically after `DATABASE_URL`.
4. **Redeploy web** after variable changes.
5. Confirm: `GET /health/ready` → `database_ready: true`, `postgres_pool.active: true`.

## Code mitigations (merged)

- `database_url_resolver.py` — multi-env DSN candidates + host resolution probe.
- `postgres_backend.py` — pool init retries + `last_error` / resolver metadata in `pool_stats()`.
- Graceful degradation: `/api/telegram/free/status` and `/api/gtm/status` return `bot_configured: true` even when subscriber/metrics DB queries fail.
