# Exchange Intelligence Layer — #544 #546 #547 #548 #549 #550

## Epic Decision

Six exchange-related tickets merged into one epic: **Exchange Intelligence Layer**.
These are sub-module tasks, not standalone features.

| Task | Sub-Module | Role |
|------|------------|------|
| #549 | Internal-Flow Filter | Foundation — raw vs adjusted toggle, no silent filtering |
| #547 | Netflow Formula | Fixed `netflow = inflow_usd - outflow_usd` |
| #548 | Inflow Intelligence | External→exchange inflow aggregation |
| #546 | Flow Intelligence | Net inflow/outflow dashboard |
| #544 | Balance & Netflow | Balances, trends, anomalies |
| #550 | Reserve Intelligence | Exchange-held assets, change, confidence |

Depends on: **#541 Entity Resolution Engine** (exchange wallet clusters)

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
    └── #550 Reserve Intelligence
```
