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

## Dual-path convergence (2026-09-04 local)

Runtime `execute_capability` now routes #214/#245 through **batch05 facade** before batch01 legacy extension (`cap646/runtime.py`). Public GET, gateway, runtime, and `batch05_production.execute` all stamp `production_spine=batch05` with `catalog_link` → batch01 canonical. **Tolerate ceiling lifted** — institutional decision **CLOSED_REUSED_LINK**.

| Path | Spine | catalog_link |
|------|-------|--------------|
| GET `/api/cap646/{214\|245}` | batch05 | REUSED-LINK → batch01 |
| `gateway_execute` | batch05 | REUSED-LINK → batch01 |
| `batch01_production.execute` (direct) | batch01 | none (legacy direct only) |

## Tolerate ceiling (superseded 2026-09-04)

~~TOLERATE until 2026-12-31~~ — **CLOSED** via dual-path convergence. Evidence: `docs/BATCH05_LOCAL_INSTITUTIONAL_COMPLETION.json`, semantic oracle 50/50.

| ID | Institutional decision | Ceiling |
|----|------------------------|---------|
| **214** | **CLOSED_REUSED_LINK** | — |
| **245** | **CLOSED_REUSED_LINK** | — |

Master record: `docs/BATCH05_RESIDUAL_7_INSTITUTIONAL_DISPOSITION.json` · `docs/ADR_BATCH05_RESIDUAL_7_FINAL_DISPOSITION.md`

## Public routing truth (end-user GET)

| Layer | Path | Spine for #214/#245 |
|-------|------|---------------------|
| **GET** `/api/cap646/{id}` | `execute_unified` → `execute_capability` | **batch05** (facade → batch01 backend + `catalog_link`) |
| **POST** `/api/cap646/{id}/execute` | `gateway_execute` → `execute_capability` | **batch05** |
| **Programmatic** `batch01_production.execute` (direct) | batch01 dedicated | **batch01** (legacy direct API only) |

`runtime.py` checks `BATCH05_IDS` before `BATCH01_IDS` for manifest IDs #214/#245 — dual-path converged 2026-09-04.

## Evidence

- `docs/BATCH05_MECE_OVERLAP_214_245_DECISION.json`
- Type-4 probes on 5 symbols (BTC/ETH/SOL/AVAX/DOGE)
- Tests: `test_cap214_watchlists_not_market_probe`, `test_batch01_245_freshness_not_lake`
