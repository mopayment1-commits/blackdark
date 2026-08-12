# BLACKDARK Remediation Ledger

**Baseline HEAD at freeze:** `bf84b5f0ff061331c66cfc37dcb7bb6ad3f14601`  
**Branch:** `cursor/institutional-hardening-120d`  
**Started:** 2026-08-11

| ID | Sev | Status | Notes |
|---|---|---|---|
| P0-SEC-01 | P0 | VERIFIED | Loopback admin bypass removed |
| P0-SEC-02 | P0 | VERIFIED | Institutional API authz |
| P0-SEC-03 | P0 | VERIFIED | Universe activate-full admin-only |
| P0-FIN-01 | P0 | VERIFIED | Execution stale/slip fail-closed |
| P0-FIN-02 | P0 | VERIFIED | ToB/mid indicative-only |
| P0-FIN-03 | P0 | VERIFIED | Rewalk net recompute |
| P0-DATA-01 | P0 | VERIFIED | Single runtime authority + PG dialect |
| P0-DEVOPS-01 | P0 | BLOCKED | Sonar AA + coverage import needs user action |
| P1-SEC-04 | P1 | VERIFIED | Admin MFA wired |
| P1-SEC-05 | P1 | VERIFIED | B2B demo key gated |
| P1-SEC-06 | P1 | FIXED | Cookie-only session; residual XSS sinks elsewhere |
| P1-SEC-07 | P1 | VERIFIED | Production rejects unsealed cookies |
| P1-FIN-04 | P1 | FIXED | fee_matrix authority |
| P1-FIN-05 | P1 | FIXED | Unknown withdrawal = None |
| P1-FIN-06 | P1 | OPEN | Broader stale surfaces |
| P1-FIN-07 | P1 | OPEN | Forecast/hype claims |
| P1-DATA-02 | P1 | VERIFIED | PG commit/rollback real |
| P1-TEST-01 | P1 | PARTIAL | Critical CI expanded; full tree not green |
| P1-COV-01 | P1 | BLOCKED | Coverage not imported under AA |

## Batch commits

1. Authz — `ea1358c`
2. Financial — `79fdb9a`
3. Database — `981b30f`
4. Session — `047b3a0`
5. Decimal / Redis / CI — (this tip)
