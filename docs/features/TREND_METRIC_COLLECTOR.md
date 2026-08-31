# Trend Metric Collector — #299 (Sprint 2 Infrastructure)

Unified trend layer from momentum, volume, and liquidity across timeframes.

## Point-in-Time Controls

| Criterion | Implementation |
|-----------|----------------|
| No look-ahead | Unit tests enforce; `lookahead_violation` flag |
| Point-in-time | Data cutoff at `as_of_timestamp_utc` |
| Universe versioning | `universe.version` documented |
| Cross-sectional ranks | Percentile rank, re-ranked daily |

## Output

- Trend score + acceleration
- Timeframe breakdown (1h, 4h, 1d, 7d)
- Cross-sectional percentile rank

## APIs

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/intelligence-ledger/trend-metrics/status` | Collector status |
| `GET /api/platform/intelligence-ledger/trend-metrics` | Asset trend panel |
| `GET /api/platform/intelligence-ledger/trend-metrics/rankings` | Universe rankings |
