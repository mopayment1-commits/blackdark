# Protocol Valuation Layer — #570 #571

## Epic Decision

Merged **NVT Fair-Value Model (#570)** and **NVT Intelligence (#571)** into **Protocol Valuation Layer** (Sprint 1 Data Layer).

| Task | Sub-Module | Role |
|------|------------|------|
| #570 | NVT Ratio & Historical Context | Current NVT + historical percentile |
| #571 | NVT Variants | Documented windows, entity-adjusted option |

Depends on: **#542 Entity-Adjusted Metrics**

## #570 — NVT Ratio & Historical Context

| Rule | Implementation |
|------|----------------|
| No fair-value claim | Renamed from "Fair-Value Model" |
| No price guarantee | `no_price_guarantee: true` on all outputs |
| Estimate ≠ value | "Current NVT: X \| Historical percentile: Y%" |
| Entity-adjusted preferred | Uses entity-adjusted transfers when available |

## #571 — NVT Variants

| Rule | Implementation |
|------|----------------|
| Documented windows | 30d standard, 30d entity-adjusted, 90d |
| Entity-adjusted option | Configurable per variant |
| No arbitrary valuation | Descriptive percentile only |

## Acceptance Criteria

| Criterion | Implementation |
|-----------|----------------|
| Methodology versioned | Formula v1.0 |
| Entity-adjusted preferred | #542 dependency |
| No price guarantee | Banned terms enforced |
| Formula documented | `build_formula_documentation()` |

## API

```
GET /api/platform/intelligence-ledger/data-layer/protocol-valuation/status
GET /api/platform/intelligence-ledger/data-layer/protocol-valuation?asset_id=bitcoin
GET /api/platform/intelligence-ledger/data-layer/protocol-valuation/reconciliation-tests
```

## Layer Architecture

```
Foundation Layer (Sprint 0)
└── #542 Entity-Adjusted Metrics

Data Layer (Sprint 1)
└── Protocol Valuation Layer (Epic #570)
    ├── #570 NVT Ratio & Historical Context
    └── #571 NVT Variants
```
