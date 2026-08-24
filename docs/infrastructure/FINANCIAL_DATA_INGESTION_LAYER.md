# Financial Data Ingestion Layer — Feature #137 (Sprint 0)

**Internal infrastructure — NOT a user-facing product feature.**

Integrates with #118 (ETL), #175/#194 (Unified Connector Layer), and #138 (Aggregators).

## Pipeline

```
Collect (#194/#175) → Normalize → Deduplicate → Store (#118) → Query → Export
```

## Policies

| Policy | Implementation |
|--------|----------------|
| Normalization | `canonical_market_v1` schema, symbol normalization |
| Deduplication | SHA-256 checksum index |
| Freshness tracking | Per-asset age + stale threshold (300s) |
| Aggregators (#138) | Backup + cross-reference only — never sole source |
| No venue leakage | Generic "Source temporarily unavailable" |

## API

| Endpoint | Auth | Description |
|----------|------|-------------|
| `GET /api/platform/infra/ingestion/status` | Public | Layer status |
| `POST /api/platform/infra/ingestion/run` | Admin | Run ingestion cycle |
| `GET /api/platform/infra/ingestion/query` | Public | Query ingested data (≤1s) |
| `GET /api/platform/infra/ingestion/freshness` | Public | Freshness tracker |
| `GET /api/platform/infra/ingestion/aggregators` | Public | Aggregator policy (#138) |
| `GET /api/platform/infra/ingestion/export` | Admin | Export reports |

## Acceptance Criteria

| Criterion | Target |
|-----------|--------|
| Accuracy | 99.99% |
| Query SLA | ≤ 1 second |
| Update | Near-real-time |
| Retention | ≥ 2 years |

## Integration

- **#118** Local ETL — structured storage
- **#175** Flexible Connector Microservice — retries, health, failover
- **#194** Unified Connector Layer — canonical schema
- **#138** Aggregators — CoinGecko cross-reference
