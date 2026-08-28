# Outlier Detection Gate (#1026)

Merged into **Data Engine / Oracle API** — not a standalone module. Validates every incoming data point against expected ranges before API response.

## Bounds (rule-based, versioned)

| Type | Method | Threshold |
|------|--------|-----------|
| **Price** | Median deviation | ±5% from median last 5 minutes (90-day baseline) |
| **Volume** | Z-score | ±3σ from rolling 24h average |
| **On-chain** | Consensus deviation | ±0.1% from consensus across nodes |

Methodology: **Z-score + IQR** — explicit, versioned (`1.0.0`). No ML anomaly detection in Sprint 2.

## Fail-closed

Outlier detected → suppress from response + #945 Provenance flag + badge **Outlier Detected / Data Degraded**. Outlier values are never shown as fact.

## Cross-source (#1024)

If one source is outlier and the other is normal:
- Suppress outlier source
- Automatic failover (#1025) to normal source
- Log divergence (append-only)

## Event corroboration

Real price spike exceeding threshold → **Confirmed Event** only if corroborated by #939 Events or #941 News. No manual override without evidence.

## Historical baseline

90-day rolling window, recalculated daily — no static-only thresholds.

## Integrations

| Ref | Integration |
|-----|-------------|
| #945 | Provenance — every outlier event logged (metric, value, expected_range, source, timestamp, action_taken) |
| #1017 | Incident Response — >3 outliers/hour from same source = auto-alert |
| #1024 | Multi-source input for cross-validation |
| #1025 | Outlier triggers failover — source marked unreliable |
| #1054 | Live Feed Statistical Monitor — runs before outlier validation (streaming anomalies) |
| #1020 | Load testing — ≤50ms overhead SLA |
| #959 / #992 | Reference Pricing / Real Volume receive gated output |

## Live Feed Statistical Monitor (#1054)

Merged into this gate. See `docs/infrastructure/LIVE_FEED_STATISTICAL_MONITOR.md`.

Sequence: **ingest → anomaly detection → outlier validation → serve/reject**

## API

```
GET  /api/v1/data/outlier/status
GET  /api/v1/data/outlier/events
GET  /api/v1/data/outlier/production-gate
GET  /api/v1/data/outlier/e2e
GET  /api/v1/data/outlier/anomaly/status
GET  /api/v1/data/outlier/anomaly/events
GET  /api/v1/data/outlier/anomaly/e2e
```

## Production gate

Blocks production if outlier gate incomplete (Sprint 0/1).

## Fee DB

Validation compute + historical baseline storage + outlier event logging — per data point.
