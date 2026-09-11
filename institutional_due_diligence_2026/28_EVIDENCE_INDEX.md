# 28 — EVIDENCE INDEX

**Audit ID:** `IDA-2026-BLACKDARK-001`  
**Last Updated:** 2026-09-11T01:02:00Z  
**Total Evidence Items:** 28

## L0 Static Evidence (Discovery / Static Review)

| ID | Level | Method | Subject | Result |
|---|---|---|---|---|
| EVD-001 | L0 | git status/rev-parse | Worktree baseline | Clean @ 14bbf492 |
| EVD-002 | L0 | SHA256 | Lock files | Hashes in 00_FORENSIC_BASELINE.md |
| EVD-003 | L0 | git log --name-status | Recent commits | Material change inventory |
| EVD-004 | L0 | git log | Commit messages | batch07 claims (E6) |
| EVD-005 | L0 | git ls-files | test_batch07_full_path_entitlement.py | Exists, not executed |
| EVD-006 | L0 | file read | BATCH07_FINAL_LOCAL_FREEZE.json | freeze=true claim |
| EVD-007 | L0 | git worktree list | Dual HEAD | 14bbf492 vs ce056858 |
| EVD-008 | L0 | git ls-files | Repo composition | 1435 files |
| EVD-009 | L0 | stat | dashboard.py | ~156KB monolith |
| EVD-010 | L0 | rg TODO/FIXME | Debt markers | 4+ hits |
| EVD-011 | L0 | rg secret patterns | Hardcoded secrets | 7 heuristic hits |
| EVD-012 | L0 | rg route decorators | API surface | 657 handlers |
| EVD-013 | L0 | AST/grep | api/routers auth | 196/304 no auth decorator |
| EVD-014 | L0 | template scan | fetch error handling | 22/43 missing catch |
| EVD-015 | L0 | DDL review | database.py vs migrations | Dual schema (prior P0 claim) |

## E1/E2 Execution Evidence (Run 001–002)

| ID | Level | Method | Subject | Result |
|---|---|---|---|---|
| EVD-016 | E1 | pytest full suite | 2977 tests @ 14bbf492 | 2972 pass, 3 fail, 2 skip, 1319s |
| EVD-017 | E2 | Independent Decimal recompute | money_decimal 4 vectors | 4/4 VERIFIED PASS |
| EVD-018 | E1 | DDL parse + SQLite init | WF-017 reconciliation | Zero overlap; P0 falsified |
| EVD-019 | L0+L1 | AST auth classification | 308 api/routers endpoints | 192 NO_DECORATOR |
| EVD-020 | E1 | TestClient POST | WF-015 analytics spoof | 200 + user_id stored |
| EVD-021 | E1 | pytest migration/spine | DB PROC-014 | Postgres subset pass; 1 fail in full suite |
| EVD-022 | E1 | pytest data_state | UNKNOWN/STALE semantics | VERIFIED PASS |
| EVD-023 | E1 | pytest targeted | auth/billing/financial/security/db | 5/5 domains pass |
| EVD-024 | E1 | Independent Decimal + SQLite REAL | WF-013 empirical | REAL drift; 3/4 vectors pass |
| EVD-025 | E1 | TestClient negative auth | 4 cases | Admin blocked; analytics spoof accepted |
| EVD-026 | L0+L1 | AST inline auth | api/routers | 3 inline-auth routes |
| EVD-027 | E1 | pytest E2E | register/login journey | VERIFIED PASS |
| EVD-028 | E1 | Red team falsification | 5 claims challenged | 4 falsified |

**E1/E2 count:** 13 items (EVD-016 through EVD-028, excluding L0+L1 hybrids counted at highest level)

**Reconciliation:** Findings WF-015, WF-017, WF-013, WF-012, WF-008, WF-023 updated with execution evidence.
