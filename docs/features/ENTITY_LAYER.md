# Entity Layer — #542 #543

## Epic Decision

Two entity-related tickets merged into **Entity Layer** (Sprint 1). These are sub-module tasks, not standalone features.

| Task | Sub-Module | Role |
|------|------------|------|
| #542 | Entity-Adjusted Metrics | Raw vs adjusted metrics, internal flow exclusion |
| #543 | Entity-Aware Wallet Intelligence | Presentation layer on #541 |

Depends on: **#541 Entity Resolution Engine**

## #542 — Entity-Adjusted Metrics

| Rule | Implementation |
|------|----------------|
| Raw vs Adjusted toggle | Both views exposed — adjusted-only forbidden |
| Methodology visible | Mandatory methodology block |
| No silent attribution | Internal transfers visible in raw view |
| Confidence/source per cluster | From/to cluster attribution on every transfer |
| Unknown entities preserved | Unknown addresses never attributed |
| Reconciliation tests | Automated — mandatory |

## #543 — Entity-Aware Wallet Intelligence

| Rule | Implementation |
|------|----------------|
| No identity without confidence/source | Identity blocked if confidence or source missing |
| Unknown remains unknown | No "likely Binance" without evidence |
| Presentation layer | Built on #541 resolve_address |

## API

```
GET /api/platform/intelligence-ledger/entity-layer/status
GET /api/platform/intelligence-ledger/entity-layer?address=0x...&view=both
GET /api/platform/intelligence-ledger/entity-layer/wallet-intelligence?address=0x...
GET /api/platform/intelligence-ledger/entity-layer/reconciliation-tests
```

## Layer Architecture

```
Foundation Layer (Sprint 0)
└── #541 Entity Resolution Engine (Critical)

Entity Layer (Sprint 1)
├── #542 Entity-Adjusted Metrics
└── #543 Entity-Aware Wallet Intelligence
```
