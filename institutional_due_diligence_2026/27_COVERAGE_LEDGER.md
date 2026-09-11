# 27 — COVERAGE LEDGER

**Audit ID:** `IDA-2026-BLACKDARK-001`  
**Last Updated:** 2026-09-11T01:02:00Z (Post Execution Runs 001–002)

## Coverage Rules
- **DISCOVERED** = enumerated in audit universe
- **AUDITED (L0)** = static examination
- **EXECUTION VERIFIED (E1/E2)** = runtime/test/recompute evidence

| Category | Discovered | L0 Audited | E1/E2 Verified | NOT VERIFIED |
|---|---:|---:|---:|---|
| Source files | 1435 | 1435 | 0 | 1435 |
| Routes/APIs | 657 | 657 | 308 classified + subset behavioral | 349+ |
| UI pages | 68 | 68 | 0 | 68 |
| DB tables | 76 | 76 | 71 reconciled + spine init | partial |
| Model candidates | 403 | 403 | 0 | 403 |
| Test functions | 1054 | 1054 | **2977 executed** (parametrized) | failures=evidence |
| User journeys | 35 | 35 | 2 executed | 33 |
| Financial calcs (HIGH) | 4 vectors | 4 | **4 recomputed** | partial universe |
| API auth classification | 308 | 308 | 308 AST + 4 behavioral | inline auth partial |

## Wave Completion (Corrected)

| Wave | Status | Execution Evidence |
|---|---|---|
| 0–1 | **CLOSED** | Valid discovery |
| 2 | OPEN | No reachability traces |
| 3 | PARTIALLY EXECUTED | Inventory only |
| 4 | PARTIALLY EXECUTED | EVD-022 |
| 5 | PARTIALLY EXECUTED | EVD-017, EVD-024 |
| 6 | OPEN | No AI validation |
| 7 | PARTIALLY EXECUTED | EVD-020, EVD-025 |
| 8 | PARTIALLY EXECUTED | EVD-018, EVD-021 |
| 9 | PARTIALLY EXECUTED | EVD-019, EVD-026 |
| 10 | OPEN | No frontend E2E |
| 11 | PARTIALLY EXECUTED | EVD-027 |
| 12 | PARTIALLY EXECUTED | EVD-016, EVD-023 |
| 13 | PARTIALLY EXECUTED | CI not re-run |
| 14 | BLOCKED | No load test |
| 15 | OPEN | Backup drill blocked |
| 16 | PARTIALLY EXECUTED | DSR not run |
| 17 | PARTIALLY EXECUTED | Static only |
| 18 | BLOCKED | External legal |
| 19 | PARTIALLY EXECUTED | Qualitative |
| 20 | OPEN | Static grep only |
| 21 | PARTIALLY EXECUTED | EVD-028 |
| 22 | OPEN | Reconciliation incomplete |

## Remaining Gaps
1. Production verification (L3) — granular external items documented
2. High-risk model validation (403 candidates)
3. Frontend render/E2E (68 pages)
4. Full user journey matrix (33/35 remaining)
5. Per-endpoint behavioral API audit (304+ material endpoints)
6. Backup/restore drill
7. Performance load tests
8. Legal/license external review

**FULL AUDIT COMPLETE per §124:** **NO**
