# 24 — MASTER FINDINGS REGISTER

**Audit ID:** `IDA-2026-BLACKDARK-001`  
**Last Updated:** 2026-09-11T01:02:00Z (Execution Runs 001–002)  
**Total Findings:** 21

| ID | Wave | Sev | Title | Status |
|---|---|---|---|---|
| WF-001 | 0 | P2 | Batch07 freeze/CI PASS claims are E6-only | NOT VERIFIED |
| WF-002 | 0 | OBS | cap646 runtime changes unverified | NOT VERIFIED |
| WF-003 | 0 | P2 | Dual HEAD worktrees (scope ambiguity) | NOT VERIFIED |
| WF-004 | 2 | P2 | Monolithic dashboard.py (~156KB, 225 routes) | NOT VERIFIED |
| WF-005 | 2 | P2 | TODO/FIXME/HACK markers in code | OBSERVED |
| WF-006 | 3 | OBS | 403 model candidates; zero validated | NOT VERIFIED |
| WF-007 | 7 | P1 | Hardcoded secret pattern heuristics (7 hits) | NOT VERIFIED |
| WF-008 | 12 | OBS | 2977 tests executed; 3 failed | EXECUTION VERIFIED |
| WF-009 | 17 | P2 | Freeze JSON claims unrevalidated | NOT VERIFIED |
| WF-011 | 4 | P2 | Split stale/UNKNOWN semantics across layers | PARTIALLY VERIFIED |
| WF-012 | 4 | P1 | Dual precision REAL vs DECIMAL | EXECUTION VERIFIED |
| WF-013 | 5 | P1 | Narrow Decimal adoption; REAL persistence | EXECUTION VERIFIED |
| WF-014 | 5 | P2 | fee_matrix fail-closed pattern | PARTIALLY VERIFIED |
| WF-015 | 7 | P1 | Analytics accepts unauthenticated user_id spoof | **EXECUTION VERIFIED FAIL** |
| WF-016 | 7 | P2 | Dev session pepper default (prod blocked) | NOT VERIFIED |
| WF-017 | 8 | **P1** | Dual-schema architecture (spine vs Wave-01) | **RECLASSIFIED from P0** — EVD-018 |
| WF-018 | 8 | P2 | Duplicate migration 004/010 | NOT VERIFIED |
| WF-019 | 8 | P2 | _REQUIRED_TABLES omits exchange_flow_labels | NOT VERIFIED |
| WF-020 | 8 | P1 | funding_rates REAL vs de_funding_rates DECIMAL | PARTIALLY VERIFIED |
| WF-021 | 9 | P1 | 192/308 endpoints lack Depends decorator | PARTIALLY VERIFIED |
| WF-022 | 10 | P2 | 22 templates: fetch() without error handler | NOT VERIFIED |
| WF-023 | 12 | OBS | Prior zero test execution | **RESOLVED** |
| WF-024 | 15 | P1 | Backup/restore not drill-verified | BLOCKED |
| WF-025 | 18 | OBS | LEGAL VERIFICATION REQUIRED (licenses) | BLOCKED |

**P0 Override removed:** WF-017 downgraded to P1 after schema reconciliation (EVD-018): zero table name overlap, parallel namespaces.

Machine-readable: `24_MASTER_FINDINGS_REGISTER.json`
