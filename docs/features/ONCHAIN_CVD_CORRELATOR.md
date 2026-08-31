# On-Chain CVD, Price-Move Correlator & Cost Basis — #518 #519 #520

## #518 — Bucketed CVD (🟢 Proceed as Layer — Sprint 1)

| Rule | Implementation |
|------|----------------|
| No standalone | On-Chain Metrics Layer |
| Bucket definitions | Versioned thresholds for retail/whale documented |
| Method | Rule-based CVD per size bucket |

API: `/api/platform/intelligence-ledger/onchain-layer/bucketed-cvd/*`

## #519 — Price-Move Event Correlator (🟡 Rename & Proceed — Sprint 2)

| Rule | Implementation |
|------|----------------|
| Rename | "Candle / Price-Move Investigator" → **Price-Move Event Correlator** |
| Framing | "Events in same window" — NOT "cause" or "reason" |
| Causation | Always marked unverified |
| Timestamps | Aligned within correlation window |

Example output:
> Wallet X moved $Y at 14:02. Price moved at 14:00. Correlation: [Z]. **Causation: unverified.**

API: `/api/platform/intelligence-ledger/intelligence-layer/price-move-correlator/*`

## #520 — Cost Basis Distribution (🟢 Proceed as Layer — Sprint 1)

| Rule | Implementation |
|------|----------------|
| No standalone | On-Chain Analytics Layer |
| No future leakage | Point-in-time only, verified per release |
| Cohort rules | Documented and versioned |
| Reproducibility | Distribution hash per snapshot |

API: `/api/platform/intelligence-ledger/onchain-layer/cost-basis/*`

## Layer Architecture

```
On-Chain Layer (Sprint 1)
├── #518 Bucketed CVD (Metrics Layer)
└── #520 Cost Basis Distribution (Analytics Layer)

Intelligence Layer (Sprint 2)
└── #519 Price-Move Event Correlator
```
