# Entity Intelligence Layer — #539 #540 #561

## Epic Decision

Three entity intelligence tickets merged into **Entity Intelligence Layer** (Sprint 1 Entity Layer).

| Task | Sub-Module | Role |
|------|------------|------|
| #539 | Entity PnL Tracker | Realized/unrealized PnL, cost basis rules, transfers ≠ sales |
| #540 | Entity Profiles | Portfolio, history, PnL, exchange usage, counterparties |
| #561 | Inter-Entity Flow Intelligence | Entity-pair flow matrix (miners/exchanges/funds) |

Depends on: **#541 Entity Resolution**, **#542 Entity-Adjusted**, **#549 Internal Filter**, **#553 Exchange-to-Exchange**

## #561 — Inter-Entity Flow Intelligence

| Rule | Implementation |
|------|----------------|
| Label confidence visible | Confidence/source on every entity label |
| PIT/revision status visible | as_of + revision log per entity |
| Internal transfers controlled | Same-entity internal excluded via #542/#549 |

## Acceptance Criteria

| Criterion | Implementation |
|-----------|----------------|
| Cost basis rules | FIFO v1.0 — versioned, documented |
| Transfers not sales | Internal transfers excluded from PnL |
| Unknown basis flagged | Transfer-in without basis flagged |
| Entity-wallet reconciliation | Wallets matched against #541 |
| Freshness visible | Source, as_of, freshness_seconds |
| Label confidence visible (#561) | Per-entity label metadata |
| PIT/revision status visible (#561) | Point-in-time + revision log |
| Internal transfers controlled (#561) | Same-entity excluded from matrix |

## API

```
GET /api/platform/intelligence-ledger/entity-intelligence/status
GET /api/platform/intelligence-ledger/entity-intelligence?entity_id=entity_whale_alpha
GET /api/platform/intelligence-ledger/entity-intelligence/pnl?entity_id=entity_whale_alpha
GET /api/platform/intelligence-ledger/entity-intelligence/reconciliation-tests
```

## Layer Architecture

```
Foundation Layer (Sprint 0)
└── #541 Entity Resolution Engine

Entity Layer (Sprint 1)
└── Entity Intelligence Layer (Epic #539)
    ├── #539 Entity PnL Tracker
    ├── #540 Entity Profiles
    └── #561 Inter-Entity Flow Intelligence
```
