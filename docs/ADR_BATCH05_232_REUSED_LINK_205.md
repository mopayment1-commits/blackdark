# ADR — Batch05 #232 REUSED-LINK to Canonical #205 (Open Interest)

**Status:** Accepted  
**Date:** 2026-09-04  
**Context:** Official Batch05 includes duplicate catalog row #232 (Open Interest Intelligence) whose `canonical_id` resolves to **#205**. Hero binding `attach_arbitrage_comparison_230_232` is Type-4 SPLIT-BRAIN (arbitrage domain, not OI).

## Decision

| ID | TIME | closure_status | Canonical |
|----|------|----------------|-----------|
| **205** Open Interest Intelligence | **Invest** | **NOT_COMPLETE** | `cap646/batch05_dedicated.py::_cap205` (hero strangler → glassnode brownfield) |
| **232** Open Interest Intelligence (duplicate) | **Migrate** | **REUSED-LINK** | Facade → `_cap205` (`catalog_link.canonical_capability_id=205`) |

**Eliminate:** Hero-layer production routing for #232 (`attach_arbitrage_comparison_230_232`).

## Alternatives considered

1. **Invest** both #205 and #232 independently. **Rejected:** catalog `REPEAT_CANONICAL` makes #232 a duplicate of #205; parallel implementations violate MECE.
2. **Migrate #205** to batch02 #85 (Futures OI). **Rejected:** catalog canonical for "Open Interest Intelligence" is #205 in batch05; batch02 #85 is "Futures Open Interest Intelligence" (distinct goal).
3. **Tolerate** hero arbitrage binding for #232. **Rejected:** Type-4 SPLIT-BRAIN on 5 symbols; owner mandate requires decisive TIME.

## Consequences

- Batch05 acceptance row #232 uses `REUSED-LINK` with `catalog_link` to batch05 `_cap205`.
- `cap646/batch05_dedicated.py::_cap232` delegates to `_cap205` and stamps REUSED-LINK metadata.
- #205 remains `NOT_COMPLETE` until live probe sign-off (no PA).

## Public routing truth (end-user GET)

| Layer | Path | Spine for #232 |
|-------|------|----------------|
| **GET** `/api/cap646/232` | `execute_unified` → `execute_capability` → batch05 | **batch05** (facade → `_cap205`) |
| **POST** `/api/cap646/232/execute` | `gateway_execute` → `execute_capability` | **batch05** |
| **Programmatic** `batch05_production.execute(232)` | `batch05_dedicated` facade → `_cap205` | **batch05** stamp + `REUSED-LINK` |

Entitlement gate uses `canonical_id(232) == 205` — verified in `test_batch05_gateway_canonical_entitlement_contract.py`.

## Evidence

- `docs/BATCH05_MECE_OVERLAP_205_232_206_228_DECISION.json`
- Type-4 probes on 5 symbols (BTC/ETH/SOL/AVAX/DOGE)
