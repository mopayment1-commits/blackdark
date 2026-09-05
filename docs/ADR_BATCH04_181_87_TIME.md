# ADR: Batch04 #181 ↔ Hero #87 — TIME Decision (Catalog Rename)

**Status:** Accepted — Option B implemented  
**Date:** 2026-09-03  
**Scope:** Batch04 ID 181

## Context

Hero function `committee_packets_status_181` declares `duplicate_of: 87` and `merged_into: "ic_report_87"`. Official cap646 **#87** is *Estimated Leverage Ratio* (batch02, PRODUCTION-ALIGNED) — a different domain.

## Type-4 Contract (5 symbols)

Compared `execute_capability(181)` vs `execute_capability(87)` for BTC/ETH/SOL/AVAX/DOGE:

- **5/5 DIFFERENCE** on surface (`ecosystem_development_dashboard` vs `estimated_leverage_ratio`)
- Hero metadata `duplicate_of=87` refers to seed feature `ic_report_87`, not cap646 #87

## TIME Decision

| Option | Verdict |
|--------|---------|
| A — Eliminate (Facade → cap646 #87) | **Rejected** — Type-4 proves semantic non-equivalence |
| B — Catalog rename | **Selected** — rename to **IC Committee Packets Status** |
| C — Invest (build_ic_report_87) | Deferred under BUILD_PHASE_HOLD |

## Implementation

- Catalog only: `CAPABILITIES_826_INVENTORY.json`, `BATCH04_ACCEPTANCE_151_200.json`, `BATCH04_RTM_151_200.json`, `BATCH04_PENTAGONAL_TEMPLATE_151_200.json`, `CAP646_CATALOG.json`
- Runtime surface unchanged: `ecosystem_development_dashboard`
- No handler change (`_cap181` hero bridge retained)
