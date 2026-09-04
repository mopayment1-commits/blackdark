# ADR — Batch05 #212 DUPLICATE Delegation to Canonical #17 (Smart Alerts)

**Status:** Accepted  
**Date:** 2026-09-04  
**Context:** Official Batch05 range 201–250 includes #212, but gap matrix and `REPEAT_CANONICAL` resolve #212 → **#17** (`DUPLICATE/ALREADY_COVERED`). Batch05 routing accidentally captured #212 before runtime duplicate delegation — regression identical in class to batch04 #200 spine fix.

## Decision

| ID | TIME | Routing | closure_status |
|----|------|---------|----------------|
| **212** Smart Alerts (duplicate) | **Migrate** (preserve pre-batch05 decision) | **DUPLICATE delegation** → canonical **#17** batch01 | `DUPLICATE/ALREADY_COVERED` |
| **17** Smart Alerts (canonical) | **Invest** (unchanged) | batch01 `_cap017_smart_alerts` | existing |

**Reject:** batch05 spine override for #212 — no MECE gate, no new Invest strangler; hero `hedge_effectiveness_analysis_212` is wrong domain for Smart Alerts.

## Alternatives considered (TIME + MECE)

| Alternative | TIME | Why rejected |
|-------------|------|--------------|
| **Invest** — new batch05 Smart Alerts strangler wrapping hero `hedge_effectiveness_analysis_212` | Invest | Hero domain is hedge-effectiveness, not Smart Alerts (Type-4 SPLIT-BRAIN). Duplicates canonical #17 without MECE benefit. |
| **Tolerate** — leave #212 on batch05 spine until later | Tolerate | Causes regression: `test_duplicate_capability_delegates` fails; violates gap matrix `DUPLICATE/ALREADY_COVERED`. Coverage XML prerequisite blocked. |
| **Eliminate** — remove catalog row #212 | Eliminate | Row is official 201–250 manifest entry; elimination requires catalog change outside Batch05 scope. |
| **Migrate (batch05 MECE REUSED-LINK)** — treat as new overlap gate like #226 | Migrate | **Rejected:** #212 is pre-resolved DUPLICATE, not cross-batch facade candidate. No canonical batch05 spine to link; canonical is batch01 #17 via delegation. |
| **Migrate (chosen)** — exclude from `BATCH05_IDS`, preserve duplicate delegation | Migrate | Matches gap matrix, batch04 #200 fix class, and ISO 12207 classification-before-routing. |

## Implementation

- `cap646/batch05_ids.py`: `BATCH05_DUPLICATE_DELEGATION_IDS={212}`; `BATCH05_IDS` = manifest minus duplicates (49 routing IDs).
- `runtime.execute_capability`: #212 no longer matches `BATCH05_IDS` → falls through to `is_duplicate` recursion → #17 batch01.
- `test_duplicate_capability_delegates` contract restored.

## Evidence

- `docs/cap646/CAP646_GAP_MATRIX.json` id 212: `final_classification=DUPLICATE/ALREADY_COVERED`, reason `Duplicate of ID17`
- `cap646/catalog.py` `REPEAT_CANONICAL["Smart Alerts"]=17`
