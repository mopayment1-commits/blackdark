# Investor Intelligence Layer — #562 #563

## Epic Decision

Two investor tickets merged into **Investor Intelligence Layer** (Sprint 1 Entity Layer).

| Task | Sub-Module | Role |
|------|------------|------|
| #562 | Investor Intelligence | Activity/sector/stage aggregation + ranking |
| #563 | Investor Profiles | Investor pages with portfolio breakdown |

Depends on: **#541 Entity Resolution Engine**

## Acceptance Criteria

| Criterion | Implementation |
|-----------|----------------|
| Entity dedupe | Canonical investor IDs with alias resolution |
| Source provenance | Source/confidence on every investor |
| No inferred affiliation | Evidence required — inferred flagged |

## API

```
GET /api/platform/intelligence-ledger/entity-layer/investor-intelligence/status
GET /api/platform/intelligence-ledger/entity-layer/investor-intelligence?investor_id=investor_paradigm
GET /api/platform/intelligence-ledger/entity-layer/investor-intelligence/reconciliation-tests
```
