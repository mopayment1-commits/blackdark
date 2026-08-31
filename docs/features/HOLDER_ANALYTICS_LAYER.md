# Holder Analytics Layer — #559 #560

## Epic Decision

Two holder analytics tickets merged into **Holder Analytics Layer** (Sprint 1 On-Chain Layer).

| Task | Sub-Module | Role |
|------|------------|------|
| #559 | Holder Cohort Intelligence | STH/LTH cohorts, cost basis, profitability |
| #560 | Holder Distribution Intelligence | Distribution bands, concentration metrics |

Depends on: **#541 Entity Resolution Engine** (exchange/contract wallet exclusion)

## Acceptance Criteria

| Criterion | Implementation |
|-----------|----------------|
| Cohort thresholds versioned | v1.0 — STH < 155d, LTH >= 155d |
| No reclassification leakage | Point-in-time classification at `as_of` |
| Exchange/contract excluded | Via #541 entity resolution |
| Provenance clear | Source, label source, freshness on #560 |
| Reconciliation tests | Automated — mandatory |

## API

```
GET /api/platform/intelligence-ledger/onchain-layer/holder-analytics/status
GET /api/platform/intelligence-ledger/onchain-layer/holder-analytics?asset=BTC
GET /api/platform/intelligence-ledger/onchain-layer/holder-analytics/reconciliation-tests
```

## Layer Architecture

```
Foundation Layer (Sprint 0)
└── #541 Entity Resolution Engine

On-Chain Layer (Sprint 1)
└── Holder Analytics Layer (Epic #559)
    ├── #559 Holder Cohort Intelligence (STH/LTH)
    └── #560 Holder Distribution Intelligence (bands)
```
