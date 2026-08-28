# Live Feed Statistical Monitor (#1054)

Merged into **#1026 Outlier Detection Gate** — not a standalone module.

Dynamic streaming anomaly detection on live feeds before data reaches users. Complements:

| Ref | Role |
|-----|------|
| #1026 | Static value outlier gate (±5% median, ±3σ volume) |
| #1053 | Deliberate manipulation patterns (wash, spoof, timestamp) |
| **#1054** | Dynamic statistical anomalies in time-series streams |

## Sequence

```
ingest → anomaly detection (#1054) → outlier validation (#1026) → serve/reject
```

## Rules (Sprint 2 — rule-based only, no ML)

| Rule | Threshold |
|------|-----------|
| Rolling Z-score | ±3σ |
| Rate of change | >5% in 30 seconds |
| Cross-source divergence | >1.5% from consensus |
| Variance regime shift | recent/prior std ratio >2.5× |

## Four mandatory patterns

1. **Price regime change** — sudden volatility shift / return spike
2. **Volume burst** — volume spike without accompanying price movement
3. **Cross-metric divergence** — price up + volume down (or inverse)
4. **Source drift** — one source gradually diverging from consensus

## Output

- Badge: **Statistical Anomaly Detected — Under Review**
- Never labels as "confirmed attack" (#1053 handles deliberate manipulation)
- Fail-closed: suppress data + #1025 failover + **Data Degraded** badge (#1030)

## Latency

≤100ms from ingestion tick to detection (streaming scope — not batch-only).

## Integrations

| Ref | Integration |
|-----|-------------|
| #1024 | Cross-source divergence uses same source pool |
| #1025 | Anomaly from source triggers automatic failover |
| #1030 | Anomaly state → Data Degraded badge + timestamp |
| #945 | Every anomaly event logged append-only |
| #1017 | Sustained anomaly (>5 min) or multi-source → incident trigger |

## API

```
GET  /api/v1/data/outlier/anomaly/status
GET  /api/v1/data/outlier/anomaly/events
GET  /api/v1/data/outlier/anomaly/e2e
```

## Fee DB

Every evaluation logs: compute cost + pattern matched + source affected + action taken + user tier.
