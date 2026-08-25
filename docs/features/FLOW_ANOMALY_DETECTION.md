# Flow Anomaly Detection Module — #282 (Sprint 2 Intelligence Ledger)

Orderflow anomaly detection via rule-based statistical thresholds. **NOT signals.**

## Institutional Rules

| Rule | Implementation |
|------|----------------|
| Rule-based first | Z-score + IQR (Phase 1) |
| ML deferred | Wave 3 |
| Baseline | 30-day rolling per asset/venue |
| Sample minimum | 1,000 trades/day — below = no detection |
| Evidence schema | trade_ids, addresses, bucket_ids |
| Scope | Spot + perp only; DEX/whale = separate |

## Evidence Schema

```
Alert: [asset, venue, metric, expected_range, actual_value, deviation%,
        evidence: trade_ids/addresses, confidence: low/medium/high]
```

## APIs

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/intelligence-ledger/flow-anomaly/status` | Module status |
| `GET /api/platform/intelligence-ledger/flow-anomaly` | Anomaly panel per asset |
| `GET /api/platform/intelligence-ledger/flow-anomaly/alerts` | Alert list with evidence |

## Disclaimer

"Anomaly alerts describe statistical deviations — not investment advice or trade signals."
