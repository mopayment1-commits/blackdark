# ADR — Batch05 #214/#245 REUSED-LINK to Batch01 Canonical Spine

**Status:** Accepted  
**Date:** 2026-09-04  
**Context:** Official Batch05 (201–250) overlaps Batch01 legacy extension for #214 and #245. Historical SPLIT-BRAIN caused wrong hero bindings.

## Decision

| ID | TIME | closure_status | Canonical |
|----|------|----------------|-----------|
| **214** Watchlists | **Migrate** (not Invest) | **REUSED-LINK** | `cap646/batch01_dedicated.py::_cap214_watchlists` |
| **245** Market Health & Freshness | **Migrate** (not Invest) | **REUSED-LINK** + OVERLAP-PARTIAL note | `cap646/batch01_production.py::cap_245` → `freshness_assurance_report` |

**Eliminate:** Hero-layer production routing for these IDs (`whale_intelligence_214`, `analyze_triangular_arbitrage_214`, `coinmarketcal_status_245`, `emerging_fund_terminal_245`).

## Alternatives considered

1. **Invest** — New batch05 dedicated handlers for watchlists/freshness. **Rejected:** duplicates proven batch01 spine; violates MECE and historical regression lessons.
2. **Tolerate** hero SPLIT-BRAIN for 48h. **Rejected:** owner mandate requires decisive TIME before acceptance.
3. **Eliminate** capabilities from catalog. **Rejected:** both are user-facing catalog goals with working batch01 paths.

## Consequences

- Batch05 acceptance rows #214/#245 use `REUSED-LINK` with `catalog_link` rules.
- `cap646/batch05_dedicated.py` must dispatch to batch01 — no parallel implementation.
- #245 documents `functional_gap`: catalog name vs runtime surface `real_time_data_freshness_update_assurance` and internal `capability_id` 630 stamp.

## Public routing truth (end-user GET)

| Layer | Path | Spine for #214/#245 |
|-------|------|---------------------|
| **GET** `/api/cap646/{id}` | `execute_unified` → `execute_capability` | **batch01** (`LEGACY_BATCH01_EXTENSION_IDS` wins before `BATCH05_IDS` in runtime) |
| **POST** `/api/cap646/{id}/execute` | `gateway_execute` → `execute_capability` | **batch01** |
| **Programmatic** `batch05_production.execute` | `batch05_dedicated` facade → batch01 backend | **batch05** stamp + `REUSED-LINK` catalog_link (RTM/contract only; not public GET) |

`runtime.py` checks `BATCH01_IDS` before `BATCH05_IDS` — same precedence pattern as batch04 overlap **#175**.

`batch05_production.execute` is **not** on the public GET path. It exists for batch05 spine binding, CI contract tests, and future strangler migration. When `user` is supplied it applies `entitlement_engine.check(canonical_id)` — matching gateway/runtime (see `test_batch05_gateway_canonical_entitlement_contract.py`).

## Evidence

- `docs/BATCH05_MECE_OVERLAP_214_245_DECISION.json`
- Type-4 probes on 5 symbols (BTC/ETH/SOL/AVAX/DOGE)
- Tests: `test_cap214_watchlists_not_market_probe`, `test_batch01_245_freshness_not_lake`
