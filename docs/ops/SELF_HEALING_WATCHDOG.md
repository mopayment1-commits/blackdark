# Self-Healing Watchdog (#1062)

**Merged into:** Sprint-0 Infrastructure — NOT standalone.

## Triggers (rule-based)

1. Process exit/crash
2. Health check fails 3× consecutive
3. Memory leak >threshold
4. Connection pool exhaustion

## Policy

- Max 3 restarts in 5 minutes · exponential backoff
- Graceful restart (zero-downtime pattern)
- Stateful exceptions: database — no auto-restart (failover via #1016 DR)
- Circuit breaker open = watchdog paused

## API

```
GET  /api/platform/internal/infrastructure/watchdog/status
POST /api/platform/internal/infrastructure/watchdog/restart
GET  /api/platform/internal/infrastructure/watchdog/e2e
```

## Integrations

#1059 Uptime · #1061 APM · #1051 Circuit Breakers · #1017 Incident Response · #1016 DR · #1060 Logging
