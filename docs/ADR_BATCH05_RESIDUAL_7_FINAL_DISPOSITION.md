# ADR — Batch05 Residual 7 Final Institutional Disposition

**Status:** Accepted (final — no deferral)  
**Date:** 2026-09-04  
**Scope:** IDs #212, #206, #214, #226, #228, #232, #245

## Decision summary

| ID | TIME | Institutional decision | Canonical | Ceiling |
|----|------|----------------------|-----------|---------|
| **212** | Migrate | CLOSED_DUPLICATE_DELEGATION | #17 batch01 | — |
| **206** | Migrate | CLOSED_REUSED_LINK | #86 batch02 | — |
| **214** | Tolerate | CLOSED_TOLERATE_DUAL_PATH | #214 batch01 | **2026-12-31** |
| **226** | Migrate | CLOSED_REUSED_LINK | #69 batch02 | — |
| **228** | Migrate | CLOSED_REUSED_LINK | #86 batch02 | — |
| **232** | Migrate | CLOSED_REUSED_LINK | #205 batch05 | — |
| **245** | Tolerate | CLOSED_TOLERATE_DUAL_PATH | #245 batch01 | **2026-12-31** |

**Deferred:** 0 · **Silent tolerate:** 0

## Tolerate exit criteria (#214, #245)

1. Gate Zero live probe validates both runtime (batch01) and facade (batch05 REUSED-LINK stamp) paths.
2. Pentagonal probe path aligned to authoritative contract OR dual-path formally re-accepted at ceiling review.
3. Owner sign-off at **2026-12-31** — extension requires new ADR.
4. No hero-layer production routing for these IDs.

## Canonical 25010 gate

All canonical spines (#17, #86, #69, #205, #214, #245) verified locally `success=true` on execute_capability probe. This does **not** claim PRODUCTION-ALIGNED for batch05 manifest rows.

## Evidence

- `docs/BATCH05_RESIDUAL_7_INSTITUTIONAL_DISPOSITION.json`
- Type-4 probes: BTC/ETH/SOL per ID
- Per-ID ADRs listed in decision table

## Phase statement

هذه المرحلة = بناء spine + قبول مسبق + اختبارات محلية فقط. لا إعلان اكتمال حوكمة · لا Batch05 complete · لا جاهزية حية 100%.
