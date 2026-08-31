# Data Infrastructure Layer — #564 Market + Network Join

## Decision

**#564 Market + Network Join** merged into **Data Infrastructure Layer** (Sprint 0 Foundation). Task not ticket.

## Acceptance Criteria

| Criterion | Implementation |
|-----------|----------------|
| No look-ahead | network_ts <= market_ts enforced; violations rejected |
| Time-aligned joins | as_of boundary with temporal_alignment_seconds |
| Join rules documented | Versioned rules with zero forward tolerance |

## API

```
GET /api/platform/intelligence-ledger/data-layer/infrastructure/status
GET /api/platform/intelligence-ledger/data-layer/infrastructure/market-network-join?asset=BTC
GET /api/platform/intelligence-ledger/data-layer/infrastructure/reconciliation-tests
```

## Layer Architecture

```
Data Layer (Sprint 0)
└── Data Infrastructure Layer (Epic #564)
    └── #564 Market + Network Join
```
