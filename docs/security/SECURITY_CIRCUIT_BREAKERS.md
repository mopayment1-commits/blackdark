# Security Controls and Circuit Breakers — Feature #190

**Sprint 0 — Non-negotiable foundation.** Integrates with #192 Security-First Architecture and #165 API Security.

## Capabilities

| Capability | Implementation |
|------------|----------------|
| Threat monitoring 24/7 | Pattern scan over security events + exchange health |
| Suspicious login detection | ≥5 failures per IP in 5 minutes |
| Abnormal withdrawal detection | Withdrawal score < 50 on any exchange |
| Circuit breaker | 50% error rate in 60s → auto-shutdown |
| False positive guard | Minimum 20 samples before trip (≤5% target) |
| Audit log | `data/security_circuit_breaker_audit.jsonl` |
| Alerts | `data/security_circuit_breaker_alerts.jsonl` |

## API

| Endpoint | Auth | Description |
|----------|------|-------------|
| `GET /api/platform/security/circuit-breakers/status` | Public | Circuit breaker status |
| `GET /api/platform/security/circuit-breakers/threats` | Public | Run threat pattern scan |
| `GET /api/platform/security/circuit-breakers/audit` | Admin | Audit trail |
| `POST /api/platform/security/circuit-breakers/reset` | Admin | Reset after investigation |
| `POST /api/platform/security/circuit-breakers/evaluate` | Admin | Force evaluation |

## Circuit Breaker Flow

```
Request → record outcome → rolling 60s window
  → error_rate ≥ 50% AND samples ≥ 20?
    → YES: status=open → 503 on non-health endpoints
    → NO: continue
Admin investigates → POST /reset → status=closed
```

## Acceptance Criteria

| Criterion | Target |
|-----------|--------|
| Detection latency | ≤ 1 minute (60s window) |
| False positive rate | ≤ 5% (min sample gate) |
| Protection | 24/7 monitoring |
| Audit trail | Full JSONL log |
| Integration | #165, #192 |
