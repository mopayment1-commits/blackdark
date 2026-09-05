# Performance Validation Gate (REL-001 / #832)

Sprint-0 infrastructure practice — **not** a standalone user-facing product module.

## Purpose

Document **real** load-test numbers (k6 on production-like or production off-peak) for critical endpoints. No theoretical estimates. No localhost-only tests.

## Tooling

```bash
k6 run --env BASE_URL=https://staging.example.com scripts/k6_performance_validation_gate.js
```

- **Required:** k6 (or equivalent scripted runner)
- **Forbidden:** manual-only checks, theoretical estimates, localhost-only

## Environment

| Allowed | Forbidden |
|---------|-----------|
| Staging with production data volume | localhost |
| Production off-peak with real traffic patterns | Theoretical capacity planning only |

## Critical systems (minimum 6)

1. Oracle API
2. Market Radar
3. Portfolio AI
4. Intelligence Ledger
5. Stripe Webhook
6. Admin Panel

## Curl proofs 5.1–5.8 under load

Each historical curl proof must be re-validated under concurrent load:

| Proof | Endpoint | SLO |
|-------|----------|-----|
| 5.1 | Data Engine health | stable |
| 5.2 | Oracle price | document degradation |
| 5.3 | Market Radar snapshot | **p95 ≤ 2000ms** |
| 5.4 | Intelligence score | **p95 ≤ 500ms** |
| 5.5 | Portfolio summary | document degradation |
| 5.6 | Stripe webhook | no billing corruption (#908) |
| 5.7 | Session / 2FA | no race conditions (#831) |
| 5.8 | Admin infra status | document degradation |

## Scaling stages

Concurrent users: **10 → 100 → 500 → 1000 → 5000**

Record exact degradation point when:

- Latency > **2× baseline**
- Error rate > **1%**
- Throughput plateau
- Complete failure

Example (required precision): *"Service degrades at 1,847 concurrent users on /api/market-radar/snapshot"* — not "about 2000".

## Metrics (4 dimensions)

1. Response time (p50, p95, p99)
2. Throughput (req/sec)
3. Error rate (%)
4. CPU / memory utilization

## Sprint 1 gate

**Sprint 1 (Core + Monetization) must not start** until load tests pass on:

- Data Engine
- Oracle API

## Regression

Re-run after **every major deployment** (Sprint boundary). One-time tests are insufficient.

## Integrations

| Issue | Integration |
|-------|-------------|
| #829 Incident Response | Load test failure → incident playbook + ops alert |
| #908 Pay-Per-Request | Rate limits under load; no billing corruption |
| #831 Session Security | Session timeout + 2FA under concurrent load |
| #828 Backup & DR | Load spike = incident type requiring DR awareness |

## API (internal)

- `GET /api/platform/internal/infrastructure/performance-validation/status`
- `GET /api/platform/internal/infrastructure/performance-validation/tooling`
- `GET /api/platform/internal/infrastructure/performance-validation/endpoints`
- `GET /api/platform/internal/infrastructure/performance-validation/curl-proofs`
- `GET /api/platform/internal/infrastructure/performance-validation/scaling`
- `GET /api/platform/internal/infrastructure/performance-validation/degradation-report`
- `GET /api/platform/internal/infrastructure/performance-validation/sprint1-gate`
- `GET /api/platform/internal/infrastructure/performance-validation/signed-evidence`
- `POST /api/platform/internal/infrastructure/performance-validation/record-run`
- `POST /api/platform/internal/infrastructure/performance-validation/e2e`

## Fee DB

N/A — operational cost in infrastructure budget.
