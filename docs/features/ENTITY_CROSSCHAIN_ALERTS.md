# Entity Resolution, Cross-Chain Liquidity & Custom Alerts — #541 #522 #532

## #541 — Entity Resolution Engine (🟢 Critical — Sprint 0)

| Rule | Implementation |
|------|----------------|
| Priority | Critical foundation — build first |
| Source/confidence/version | Mandatory on every attribution |
| Unknown remains unknown | No guessing, no AI attribution without evidence |
| Versioning | Every cluster versioned — auditable historically |

API: `/api/platform/intelligence-ledger/foundation/entity-resolution/*`

Depends on by: #532, #516, #539, #540, #542

## #522 — Cross-Chain Liquidity Flow (🟢 Proceed — Sprint 1)

| Rule | Implementation |
|------|----------------|
| No standalone | Cross-Chain Intelligence Layer |
| Bridge identity | Verified per transfer |
| Double counting | Prevented via dedupe key |
| Reorg handling | Confirmation blocks required |
| Reconciliation tests | Automated — mandatory |

API: `/api/platform/intelligence-ledger/onchain-layer/cross-chain-liquidity/*`

## #532 — Custom Alerts (🟢 Proceed — Sprint 1)

| Rule | Implementation |
|------|----------------|
| No buy/sell alerts | "Address X moved $Y" only |
| Rate limits | Backend enforced per user/hour |
| Direct tx evidence | Every alert requires tx hash |
| Dependencies | #541 Entity Resolution + #516 Asset Profiles |

API: `/api/platform/intelligence-ledger/infrastructure/custom-alerts/*`

## Layer Architecture

```
Foundation Layer (Sprint 0)
└── #541 Entity Resolution Engine (Critical)

On-Chain Layer (Sprint 1)
└── #522 Cross-Chain Liquidity Flow

Infrastructure Layer (Sprint 1)
└── #532 Custom Alerts (depends on #541, #516)
```
