# 26 — POSITIVE ASSURANCE REGISTER

**Updated:** 2026-09-11T01:07:25Z

| ID | Claim | Procedure | Evidence | Strength | Coverage | Limitations |
|---|---|---|---|---|---|---|
| PA-001 | money_decimal fee/net helpers match independent Decimal formulas | W5-FIN-001 | EVD-017, EVD-033 | E2 | 5/5 vectors | Cross-exchange depth-walk not fully independent |
| PA-002 | Spine SQLite init_db creates schema from zero | W8-DB-001 | EVD-018, EVD-047 | E1 | 60 tables | Postgres Wave01 path separate |
| PA-003 | Admin billing inline auth blocks anonymous (403) | W7-SEC-001 | EVD-025, EVD-045 | E1 | 3/3 admin routes | Token-based not session-based |
| PA-004 | Data failure semantics tests pass (UNKNOWN≠ZERO policy) | W4-DATA-001 | EVD-022, EVD-042 | E1 | 14/14 tests | Cross-layer cache not fully traced |
| PA-005 | Targeted critical domains (auth/billing/financial/security/db) pass | W12-TEST-002 | EVD-023, EVD-050 | E1 | 5/5 domains | Subset not full suite |
| PA-006 | HIGH/CRITICAL model pytest suites pass | W3-MODEL-SUM | EVD-034..041 | E1 | 8/8 models | Test pass ≠ independent validation |
| PA-007 | User journey register/login/logout passes | W11-UJ-001 | EVD-027, EVD-049 | E1 | 1/35 journeys | Most journeys not executed |
| PA-008 | Chaos resilience tests pass (where Postgres absent, skip documented) | W15-RES-001 | EVD-053 | E1 | partial | Postgres chaos skipped |

**Note:** No generic "system is secure" or "production ready" statements. Each entry is population-bound.
