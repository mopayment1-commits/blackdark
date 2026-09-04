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

## Public routing

| Layer | Spine for #226 |
|-------|----------------|
| GET `/api/cap646/226` | **batch05** facade → batch02 #69 backend |
| Entitlement | `canonical_id(226)==69` |

## Evidence

- `docs/BATCH05_MECE_OVERLAP_226_69_DECISION.json`
- Type-4 probes on 5 symbols (BTC/ETH/SOL/AVAX/DOGE)
