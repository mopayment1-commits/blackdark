# Centralized Logging Stack (#1060)

**Merged into:** Sprint-0 Infrastructure — NOT standalone.

## Policy

- **Stack:** Loki-compatible centralized logging
- **Search latency:** ≤2 seconds
- **Schema:** JSON with enforced fields (timestamp · service · level · trace_id · user_id · tenant_id · message · metadata)
- **Retention:** operational 30d · audit 2yr · security 5yr

## Sanitization

Strips private keys · wallet seeds · plaintext passwords (#1040 Vault policy).

## API

```
GET  /api/platform/internal/infrastructure/logging/status
POST /api/platform/internal/infrastructure/logging/ingest
GET  /api/platform/internal/infrastructure/logging/search
GET  /api/platform/internal/infrastructure/logging/e2e
```

## Integrations

#1038 Activity Audit · #945 Provenance · #1017 Incident Response · #1059 Uptime · #1051 Circuit Breakers
