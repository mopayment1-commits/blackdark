# Security Rate Limiting Layer (#1046)

**Sprint 0/1 · API Gateway · NOT standalone · Non-Custodial**

Cross-cutting security gate — blocks brute-force, scraping, and application-layer abuse BEFORE billing quota (#908) and authZ (#1022).

## Gate sequence

```
DDoS edge (#1047) → WAF → Security Rate Limit (#1046) → Billing Quota (#908) → AuthZ (#1022) → Service
```

## Policy

| Surface | Limit |
|---------|-------|
| Auth (IP) | 5 attempts / 5 min |
| Auth (account) | 10 attempts / hour |
| API anonymous | 100 req/min |
| API Free tier | 100 req/min per key |
| API Pro | 10,000 req/min |
| Institution | Custom SLA |

## Scraping protection

- Missing User-Agent → block
- Bot signatures (curl, scrapy, etc.) → 429 + Retry-After
- Rapid sequential requests → throttle

## DDoS Layer-7

Burst detection · auto-block IP at >1000 blocked req/min · incident #1017 alert.

## Response

`429 Too Many Requests` + `Retry-After` header — no silent drop.

## API

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/security-rate-limit/status` | Policy status |
| `GET /api/platform/security-rate-limit/gate` | Production gate |
| `GET /api/platform/security-rate-limit/e2e` | E2E self-test |

## Middleware

`security_rate_limit_middleware` in `dashboard.py` — enabled by default (`SECURITY_RATE_LIMITING=true`).

## Audit

`data/security_rate_limit_audit.jsonl` — 90-day retention, append-only (#1038).
