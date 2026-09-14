# 26 — Assumption & Limitation Register

**Generated:** 2026-09-10T23:55:00Z

| ID | Assumption | Domain | Classification |
|---|---|---|---|
| ASM-001 | BATCH07_FINAL_LOCAL_FREEZE=true implies institutional readiness | Governance | INVALID (E6 only) |
| ASM-002 | CI PASS in JSON equals current CI state | SDLC | UNKNOWN |
| ASM-003 | Empty DATABASE_URL → SQLite acceptable for prod | Data | WEAK |
| ASM-004 | LLM oracle fallback to rules is safe | AI/ML | UNKNOWN |
| ASM-005 | 1054 tests provide operational assurance | Test | WEAK (not executed in audit) |
| ASM-006 | Public API routes without auth are intentional | Security | UNKNOWN |
| LIM-001 | Dual schema may cause data divergence | Data | Documented WF-017 |
| LIM-002 | REAL persistence limits sub-satoshi accuracy | Financial | Documented WF-013 |
