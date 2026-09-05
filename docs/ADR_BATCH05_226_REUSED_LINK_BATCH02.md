# ADR — Batch05 #226 REUSED-LINK to Batch02 Canonical #69 (Cross-Domain Decision)

**Status:** Accepted  
**Date:** 2026-09-04  
**Context:** #226 shares catalog name with canonical **#69** (`REPEAT_CANONICAL`). Hero `analyze_launch_event_226` is Type-4 SPLIT-BRAIN (launch-event analysis, not cross-domain synthesis). Batch02 #69 implements `build_cross_domain_decision_payload`.

## Decision

| ID | TIME | closure_status | Canonical |
|----|------|----------------|-----------|
| **69** Cross-Domain Decision Intelligence Layer | **Invest** (batch02 spine) | existing | `cap646/batch02_dedicated.py::_cap069` |
| **226** (duplicate row) | **Migrate** | **REUSED-LINK** | `cap646/batch02_production.py::cap_069` |

**Eliminate:** Hero `analyze_launch_event_226` from batch05 production path.

## Alternatives considered (TIME + MECE)

| Alternative | TIME | Why rejected |
|-------------|------|--------------|
| **Invest** — keep hero `analyze_launch_event_226` as batch05 strangler | Invest | Type-4 SPLIT-BRAIN: launch-event analysis ≠ cross-domain decision synthesis. Surface slug matches catalog but hero domain is wrong (MECE violation). |
| **Tolerate** — `REPEAT_CANONICAL_PENDING_MECE` overlay, no facade | Tolerate | Leaves wrong hero on production path; pentagonal/RTM show unresolved overlap; entitlement probes on canonical #69 remain misaligned with runtime. |
| **Eliminate** — remove #226 from catalog | Eliminate | Official batch05 manifest ID; removal requires catalog amendment outside current scope. |
| **Migrate → batch05 internal canonical** | Migrate | No batch05-native cross-domain spine exists; inventing one duplicates batch02 #69. |
| **Migrate → REUSED-LINK batch02 #69 (chosen)** | Migrate | Canonical `cap_069` implements `build_cross_domain_decision_payload`; facade preserves batch05 public spine + entitlement on `canonical_id(226)==69`. Hero eliminated. |

**Canonical maturity gate:** batch02 #69 is an existing Invest spine with verified cross-domain payload — REUSED-LINK is permitted (not linking to incomplete canonical).

## Public routing

| Layer | Spine for #226 |
|-------|----------------|
| GET `/api/cap646/226` | **batch05** facade → batch02 #69 backend |
| Entitlement | `canonical_id(226)==69` |

## Final disposition (residual 7 — 2026-09-04)

**Institutional decision:** **CLOSED_REUSED_LINK** — 7/7 domain rules; Six Heroes fed **only** via canonical #69 (Oracle + Arbitrage); facade #226 not in hero inputs.

Evidence: `docs/BATCH05_RESIDUAL_7_INSTITUTIONAL_DISPOSITION.json`

## Evidence

- `docs/BATCH05_MECE_OVERLAP_226_69_DECISION.json`
- Type-4 probes on 5 symbols (BTC/ETH/SOL/AVAX/DOGE)
