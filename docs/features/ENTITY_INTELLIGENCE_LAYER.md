# Entity Intelligence Layer — #539 #540

## Epic Decision

Two entity intelligence tickets merged into **Entity Intelligence Layer** (Sprint 1 Entity Layer).

| Task | Sub-Module | Role |
|------|------------|------|
| #539 | Entity PnL Tracker | Realized/unrealized PnL, cost basis rules, transfers ≠ sales |
| #540 | Entity Profiles | Portfolio, history, PnL, exchange usage, counterparties |

Depends on: **#541 Entity Resolution Engine** (address clusters, attribution)

## Acceptance Criteria

| Criterion | Implementation |
|-----------|----------------|
| Cost basis rules | FIFO v1.0 — versioned, documented |
| Transfers not sales | Internal transfers excluded from PnL |
| Unknown basis flagged | Transfer-in without basis flagged — PnL suppressed |
| Entity-wallet reconciliation | Seed wallets matched against #541 resolution |
| Freshness visible | Source, as_of, freshness_seconds on all panels |
| Reconciliation tests | Automated — mandatory |

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
├── Entity Layer (#542 #543) — raw vs adjusted metrics
└── Entity Intelligence Layer (Epic #539)
    ├── #539 Entity PnL Tracker (cost basis, PnL)
    └── #540 Entity Profiles (presentation layer)
```

## Institutional Notes

- No "AI" in naming — **Entity PnL Tracker** (not "Entity PnL AI")
- Unknown basis flagged prevents inflated PnL display
- #540 is presentation layer — not standalone, built on #541 + #539
