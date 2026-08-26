# Protocol Economics Layer — #554 #555

## Epic Decision

Two protocol economics tickets merged into **Protocol Economics Layer** (Sprint 1).
Part of #516 Asset Profiles infrastructure — not standalone.

| Task | Sub-Module | Role |
|------|------------|------|
| #554 | Fees & Revenue | Dashboard with explicit fees vs revenue definitions |
| #555 | Fees Intelligence | Gross fees normalization subset (merged into #554) |

Depends on: **#516 Asset Intelligence Profiles**

## Critical Definition: Fees ≠ Revenue

| Term | Definition |
|------|------------|
| **Fees** | Gross fees paid by users (swap fees, borrow interest, liquidation penalties) |
| **Revenue** | Portion retained by protocol (treasury/DAO/token holders). Revenue ≤ Fees always. |
| **Example** | Uniswap: fees > 0, protocol revenue = 0 (all to LPs). Aave: revenue = treasury share only. |

## Acceptance Criteria

| Criterion | Implementation |
|-----------|----------------|
| Definitions explicit | Mandatory definitions block — fees ≠ revenue |
| #555 merged into #554 | Fees Intelligence as sub-module |
| Contract mapping | Per-protocol contract registry |
| Historical QA | Automated QA tests |
| No standalone | Part of Asset Profiles data layer |

## API

```
GET /api/platform/intelligence-ledger/data-layer/protocol-economics/status
GET /api/platform/intelligence-ledger/data-layer/protocol-economics?protocol_id=uniswap
GET /api/platform/intelligence-ledger/data-layer/protocol-economics/historical-qa
```

## Layer Architecture

```
Data Layer (Sprint 0)
└── #516 Asset Intelligence Profiles (foundation)

Data Layer (Sprint 1)
└── Protocol Economics Layer (Epic #554)
    ├── #554 Fees & Revenue
    └── #555 Fees Intelligence (subset)
```
