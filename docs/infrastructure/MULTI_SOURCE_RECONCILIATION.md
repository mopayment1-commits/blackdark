# Multi-Source Ingest & Reconciliation Layer (#1024)

Merged into **Data Engine** — not a standalone module. Cross-validates Price, Volume, and On-chain data from independent sources before user display.

## Minimum sources (2 per type)

| Type | Sources |
|------|---------|
| **Price** | Binance API + CoinGecko |
| **Volume** | CoinMarketCap + TheGraph |
| **On-chain** | Alchemy + QuickNode RPC |

## Cross-validation thresholds (rule-based)

| Type | Tolerance |
|------|-----------|
| Price | ±0.5% |
| Volume | ±2% |
| On-chain | ±0.1% |

## Divergence handling

| Condition | Action |
|-----------|--------|
| variance ≤ threshold | Average values, confidence High/Medium |
| variance > threshold | Suppress output, alert ops, **Data Degraded** badge (#945 fail-closed) |
| source failure | Failover to alternate source + divergence flag |

## Provenance tag (visible in API)

```
[Source A: value X | Source B: value Y | Variance: Z% | Confidence: High/Medium/Low]
```

## API

```
GET  /api/v1/data/reconciliation/status
GET  /api/v1/data/reconciliation/price
GET  /api/v1/data/reconciliation/volume
GET  /api/v1/data/reconciliation/onchain
GET  /api/v1/data/reconciliation/audit-trail
GET  /api/v1/data/reconciliation/sprint1-gate
GET  /api/v1/data/reconciliation/e2e
```

## Caching

- Price/Volume: TTL 5 minutes, divergence recheck every 5 min
- On-chain: TTL ~12s (per block)

## Sprint 1 gate

Blocks Sprint 1 if multi-source reconciliation incomplete.

## Fee DB

Per-source ingest + validation compute + failover overhead logged per data type per query.
