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
| source failure | Automatic Failover Engine → backup source, **Source Switched** badge, confidence Medium |

## Automatic Failover Engine (inside #1024)

No standalone module — detection, switch, logging, and recovery are part of the Multi-Source Layer.

| Dimension | Rule |
|-----------|------|
| **Detection** | Health check every 30s (price/volume), every block (on-chain); latency >2× baseline = trigger |
| **Switch** | Automatic — backup from source registry, no manual intervention |
| **Speed** | Failover time ≤5 seconds (measured) |
| **Logging** | Every event → #945 Provenance (source_from, source_to, reason, duration, timestamp) + #1017 auto-alert if >3 failovers/hour |
| **User impact** | No service interruption — backup served with confidence Medium + badge **Source Switched** |
| **Recovery** | Primary restored → automatic reversion after 5-minute validation before confidence returns to High |

### Integrations

- **#959 Reference Pricing**: price failover feeds reference price calculation (no stale price)
- **#992 Real Volume**: volume failover feeds real volume (venue quality re-evaluated)
- **#12 On-Chain Extension**: RPC node failover transparent with consensus across remaining nodes

## API

```
GET  /api/v1/data/reconciliation/status
GET  /api/v1/data/reconciliation/price
GET  /api/v1/data/reconciliation/volume
GET  /api/v1/data/reconciliation/onchain
GET  /api/v1/data/reconciliation/failover/status
GET  /api/v1/data/reconciliation/failover/events
GET  /api/v1/data/reconciliation/audit-trail
GET  /api/v1/data/reconciliation/sprint1-gate
GET  /api/v1/data/reconciliation/e2e
```

```
[Source A: value X | Source B: value Y | Variance: Z% | Confidence: High/Medium/Low]
```

Failover provenance tag:

```
[Failover: primary → backup | Value: X | Reason: source_failure | Confidence: Medium]
```

## API (reconciliation)

## Caching

- Price/Volume: TTL 5 minutes, divergence recheck every 5 min
- On-chain: TTL ~12s (per block)

## Sprint 1 gate

Blocks Sprint 1 if multi-source reconciliation incomplete.

## Fee DB

Per-source ingest + validation compute + failover overhead logged per data type per query.
