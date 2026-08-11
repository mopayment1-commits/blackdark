# BLACKDARK Remediation Ledger

**Baseline HEAD at freeze:** `bf84b5f0ff061331c66cfc37dcb7bb6ad3f14601`  
**Branch:** `cursor/institutional-hardening-120d`  
**Started:** 2026-08-11

| ID | Sev | Status | Notes |
|---|---|---|---|
| P0-SEC-01 | P0 | OPEN | Loopback admin bypass |
| P0-SEC-02 | P0 | OPEN | Institutional API unauthenticated |
| P0-SEC-03 | P0 | OPEN | Universe activate-full unauthenticated |
| P0-FIN-01 | P0 | OPEN | Execution skips stale/slip |
| P0-FIN-02 | P0 | OPEN | ToB/mid false profitable |
| P0-FIN-03 | P0 | OPEN | Rewalk executable without net |
| P0-DATA-01 | P0 | OPEN | Dual migration / PG AUTOINCREMENT |
| P0-DEVOPS-01 | P0 | OPEN | CI/Sonar false-green + coverage AA |
| P1-SEC-04 | P1 | OPEN | Admin MFA not wired |
| P1-SEC-05 | P1 | OPEN | /b2b always exposes demo key |
| P1-SEC-06 | P1 | OPEN | localStorage + XSS sinks |
| P1-SEC-07 | P1 | OPEN | Cookie unseal inconsistency |
| P1-FIN-04..07 | P1 | OPEN | Fee dual-path / withdraw0 / stale / forecast |
| P1-DATA-02 | P1 | OPEN | PG commit/rollback no-ops |
| P1-TEST-01 | P1 | OPEN | CI subset of tests |
| P1-COV-01 | P1 | OPEN | ~14.7% coverage, not in Sonar |
