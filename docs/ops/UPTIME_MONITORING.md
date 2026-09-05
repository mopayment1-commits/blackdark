# Uptime Monitoring & Alerting (#1059)

**Merged into:** Sprint-0 Infrastructure — NOT standalone.

## Policy

| Requirement | Target |
|-------------|--------|
| Probe interval | Every 30 seconds |
| Monitoring | Outside-in multi-region (not localhost only) |
| Down alert | >1 minute sustained OR 3 consecutive external fails |
| Notification SLA | ≤2 minutes to on-call |
| Escalation | No ack in 5 min → Incident Commander (#1017) |
| Public status | `/status` — best effort, no guaranteed uptime |

## Critical services (7+)

Oracle API · Market Radar · Portfolio AI · Intelligence Ledger · Stripe Webhook · Admin Panel · Pay-Per-Request (#908)

## API

```
GET  /api/platform/internal/infrastructure/uptime/status
GET  /api/platform/internal/infrastructure/uptime/status-page
POST /api/platform/internal/infrastructure/uptime/probe
GET  /api/platform/internal/infrastructure/uptime/e2e
```

## Integrations

#1017 Incident Response · #1051 Circuit Breakers · #1020 Load Testing · #1047 DDoS · #1030 Badge · #1038 Activity Audit
