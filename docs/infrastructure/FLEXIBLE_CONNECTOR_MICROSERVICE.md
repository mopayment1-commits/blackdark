# Flexible Connector Microservice — Feature #175

Sprint 1 core architecture. Canonical adapter contract for all connectors.

## Adapter Contract (`CanonicalConnectorAdapter`)

Every connector implements:
- `connector_id` / `exchange`
- `fetch_quote(asset, session) → CanonicalPriceQuote | None`
- `health_probe(asset) → ConnectorHealth`

## Policies

| Policy | Implementation |
|--------|----------------|
| Normalization | `CanonicalPriceQuote` schema |
| Retry | 3 attempts with backoff |
| Rate limit | Per-connector token bucket (60/min) |
| Health check | Certification pass + registry display |
| Schema drift | `detect_schema_drift()` — missing fields flagged |
| Failover | `fetch_with_failover()` — preferred chain |
| No synthetic success | `ok=False` on failure — never invent data |

## User-visible registry

```
Binance: ✅ Healthy | Coinbase: ⚠️ Delayed 5min | Kraken: 🔴 Down (no_data)
```

## APIs

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/infra/connectors/registry` | User-visible health dashboard |
| `GET /api/platform/infra/connectors/certification` | Certification pass |
| `GET /api/platform/infra/connectors/failover` | Failover fetch |
| `GET /api/platform/infra/connectors/microservice/status` | Module status |

## Acceptance

- Contract tests per adapter interface
- Schema drift handling
- Failover without synthetic success
- Health certification
