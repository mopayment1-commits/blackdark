# Block-Level Ingestion — #212

Sprint 0 — Block-Level Ingestion Layer for high-resolution data delivery.

## Institutional Rules

| Rule | Implementation |
|------|----------------|
| Latency SLO measured | `Block-to-API: Xms \| p95: Yms` |
| Reorg handling | `Chain Reorg Detected \| Block N replaced \| Data updated` |
| Gap detection | Automated alerts for missing block heights |
| No false real-time | `Real-Time` only if < 500ms (enterprise); `Near Real-Time` if > 1s |
| Sub-second | Enterprise tier only |
| Basic tier | Block-level with 1–5s latency |

## APIs

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/block-ingestion/status` | Module status |
| `GET /api/platform/block-ingestion/latency-slo` | Measured latency SLO per chain |
| `GET /api/platform/block-ingestion/feeds` | Block streams with freshness labels |
| `GET /api/platform/block-ingestion/blocks/{id}` | Block detail |
| `GET /api/platform/block-ingestion/bars/{chain}` | Minute aggregation bars |
| `GET /api/platform/block-ingestion/gaps` | Gap detection alerts |
| `POST /api/platform/block-ingestion/reorg` | Record chain reorg |

## Related

- `hot_storage.py` — tick/book hot pipeline
- `feed_lag_scanner.py` — cross-venue feed lag
- `stale_price_guard.py` — quote freshness SLO (~300ms)
