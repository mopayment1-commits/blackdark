# ADR — Batch05 #206/#228 REUSED-LINK to Batch02 Canonical #86 (Funding Rate)

**Status:** Accepted  
**Date:** 2026-09-04  
**Context:** Official Batch05 includes two catalog rows (#206, #228) both named "Funding Rate Intelligence" with `canonical_id` resolving to **batch02 #86**. Hero bindings (`ingest_uniswap_subgraph_206`, `simulate_drawdown_hedge_228`) are Type-4 SPLIT-BRAIN (wrong domains).

## Decision

| ID | TIME | closure_status | Canonical |
|----|------|----------------|-----------|
| **206** Funding Rate Intelligence | **Migrate** | **REUSED-LINK** | `cap646/batch02_production.py::cap_086` |
| **228** Funding Rate Intelligence (duplicate) | **Migrate** | **REUSED-LINK** | `cap646/batch02_production.py::cap_086` |

**Eliminate:** Hero-layer production routing for #206 (uniswap subgraph) and #228 (drawdown hedge simulation).

## Alternatives considered

1. **Invest** new batch05 dedicated funding handlers. **Rejected:** batch02 #86 already implements `funding_rate_intelligence` via `derivatives_hub`; duplicates proven spine.
2. **Keep #206 on hero, only migrate #228**. **Rejected:** both rows share catalog name and canonical_id 86; partial migration leaves MECE gap.
3. **Route public GET directly to batch02** (like #214/#245 → batch01). **Rejected:** #206/#228 are not in `BATCH02_IDS`; they are official batch05 IDs. Facade pattern preserves batch05 spine stamp while reusing batch02 backend.

## Consequences

- Batch05 acceptance rows #206/#228 use `REUSED-LINK` with `catalog_link.canonical_spine=batch02`.
- `cap646/batch05_dedicated.py::_cap206/_cap228` delegate to `batch02_production.execute(86)`.
- Hero bindings for 206/228 removed from `batch05_hero_bridge.py`.

## Public routing truth (end-user GET)

| Layer | Path | Spine for #206/#228 |
|-------|------|---------------------|
| **GET** `/api/cap646/{206\|228}` | `execute_unified` → `execute_capability` → batch05 handler | **batch05** (facade → batch02 #86 backend) |
| **POST** gateway | `gateway_execute` → `execute_capability` | **batch05** |
| **Programmatic** `batch05_production.execute` | `batch05_dedicated` facade → batch02 #86 | **batch05** stamp + `REUSED-LINK` |

Unlike #214/#245 (legacy `BATCH01_IDS` wins before `BATCH05_IDS`), #206/#228 have no legacy batch02 membership — runtime always enters batch05, which facades to batch02.

Entitlement gate uses `canonical_id(206)==canonical_id(228)==86` — verified in gateway contract tests.

## Final disposition (residual 7 — 2026-09-04)

| ID | Institutional decision | Domain rules |
|----|------------------------|--------------|
| **206** | **CLOSED_REUSED_LINK** | 7/7 runtime + facade |
| **228** | **CLOSED_REUSED_LINK** | 7/7 runtime + facade |

Evidence: `docs/BATCH05_RESIDUAL_7_INSTITUTIONAL_DISPOSITION.json` · `docs/ADR_BATCH05_RESIDUAL_7_FINAL_DISPOSITION.md`

## Evidence

- `docs/BATCH05_MECE_OVERLAP_205_232_206_228_DECISION.json`
- Type-4 probes on 5 symbols (BTC/ETH/SOL/AVAX/DOGE)
- batch02 evidence: `cap646/batch02_dedicated.py::_cap086`
