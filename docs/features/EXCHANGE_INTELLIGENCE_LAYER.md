# Exchange Intelligence Layer — #544 #546 #547 #548 #549 #550 #551

## Epic Decision

Seven exchange-related tickets merged into one epic: **Exchange Intelligence Layer**.
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

Depends on: **#541 Entity Resolution Engine** (exchange wallet clusters)

## #551 — Exchange Supply / Balance Intelligence

| Rule | Implementation |
|------|----------------|
| No standalone | Merged into Exchange Intelligence Epic |
| Entity-adjusted | Balances computed from entity-resolved clusters |
| Cluster revisions tracked | Revision log with affected exchanges |
| Historical reproducibility | Snapshot ID + as_of timestamp |

## Acceptance Criteria

| Criterion | Implementation |
|-----------|----------------|
| Internal transfers filtered | #549 classifies same-entity cluster transfers |
| No silent filtering | Raw vs adjusted toggle; internal count visible |
| Labels confidence/source | Mandatory on every exchange entity |
| Netflow formula fixed | `inflow_usd - outflow_usd` (v1.0) |
| Timestamps aligned | Transfer timestamps preserved |
| Freshness visible | Reserve/balance freshness_seconds exposed |
| Historical revisions controlled | Revision log + controlled replay |
| Entity-adjusted (#551) | Supply balances from entity clusters |
| Cluster revisions tracked (#551) | Revision log per exchange |
| Historical reproducibility (#551) | Snapshot + methodology version |
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
    └── #551 Supply / Balance Intelligence (extends #550)
```
