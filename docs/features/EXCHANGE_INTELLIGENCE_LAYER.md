# Exchange Intelligence Layer — #544 #546 #547 #548 #549 #550 #551 #552 #553

## Epic Decision

Nine exchange-related tickets merged into one epic: **Exchange Intelligence Layer**.
These are sub-module tasks, not standalone features.

| Task | Sub-Module | Role |
|------|------------|------|
| #549 | Internal-Flow Filter | Foundation — raw vs adjusted toggle, no silent filtering |
| #547 | Netflow Formula | Fixed `netflow = inflow_usd - outflow_usd` |
| #548 | Inflow Intelligence | External→exchange inflow aggregation |
| #546 | Flow Intelligence | Net inflow/outflow dashboard |
| #544 | Balance & Netflow | Balances, trends, anomalies |
| #550 | Reserve Intelligence | Exchange-held assets, change, confidence |
| #551 | Supply / Balance Intelligence | Entity-adjusted balance + share of supply (extends #550) |
| #552 | Large-Inflow Concentration Metric | Top-N inflow share — statistical anomaly only |
| #553 | Exchange-to-Exchange Flow Intelligence | Source→destination flow matrix |

Depends on: **#541 Entity Resolution Engine** (exchange wallet clusters)
#553 also depends on **#549 Internal-Flow Filter**

## #552 — Large-Inflow Concentration Metric (renamed from Exchange Whale Ratio)

| Rule | Implementation |
|------|----------------|
| No standalone | Merged into Exchange Intelligence Epic |
| Renamed | "Large-Inflow Concentration Metric" — no "whale" in UI |
| Top-N documented | Versioned top-N definition (v1.0, N=5) |
| Low-volume edge cases | Flagged when below threshold — metric unreliable |
| Historical Metric Validation | NOT trading backtest |
| Statistical anomaly | Deviation from 90-day average (z-score) — NOT sell signal |

## #553 — Exchange-to-Exchange Flow Intelligence

| Rule | Implementation |
|------|----------------|
| No standalone | Merged into Exchange Intelligence Epic |
| Same-exchange excluded | Internal transfers filtered via #549 |
| Entity confidence | Cluster confidence/source on matrix |
| Historical revision handling | Revision log tracked |

## Acceptance Criteria

| Criterion | Implementation |
|-----------|----------------|
| Internal transfers filtered | #549 classifies same-entity cluster transfers |
| No silent filtering | Raw vs adjusted toggle; internal count visible |
| Labels confidence/source | Mandatory on every exchange entity |
| Netflow formula fixed | `inflow_usd - outflow_usd` (v1.0) |
| Top-N definition documented (#552) | Versioned, rolling window |
| Low-volume edge cases (#552) | Threshold flag when unreliable |
| Historical Metric Validation (#552) | Window replay — not trading backtest |
| No arbitrary interpretation (#552) | Descriptive only |
| Same-exchange excluded (#553) | Internal flows excluded from matrix |
| Entity confidence (#553) | Per-exchange cluster confidence |
| Historical revision handling (#553) | Revision log |
| Reconciliation tests | Automated — mandatory |

## API

```
GET /api/platform/intelligence-ledger/onchain-layer/exchange-intelligence/status
GET /api/platform/intelligence-ledger/onchain-layer/exchange-intelligence?exchange_id=binance&asset=BTC&adjusted=true
GET /api/platform/intelligence-ledger/onchain-layer/exchange-intelligence/reconciliation-tests
```

## Layer Architecture

```
Foundation Layer (Sprint 0)
└── #541 Entity Resolution Engine (exchange clusters)

On-Chain Intelligence Layer (Sprint 1)
└── Exchange Intelligence Layer (Epic #544)
    ├── #549 Internal-Flow Filter
    ├── #547 Netflow Formula
    ├── #548 Inflow Intelligence
    ├── #546 Flow Intelligence
    ├── #544 Balance & Netflow
    ├── #550 Reserve Intelligence
    ├── #551 Supply / Balance Intelligence (extends #550)
    ├── #552 Large-Inflow Concentration Metric
    └── #553 Exchange-to-Exchange Flow Intelligence
```
