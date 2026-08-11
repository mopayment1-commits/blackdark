# BLACKDARK Remediation Ledger

**Baseline HEAD at freeze:** `bf84b5f0ff061331c66cfc37dcb7bb6ad3f14601`  
**Branch:** `cursor/institutional-hardening-120d`  
**Started:** 2026-08-11

| ID | Sev | Status | Notes |
|---|---|---|---|
| P0-SEC-01 | P0 | VERIFIED | Loopback admin bypass removed; admin-key/MFA only (`security_auth`, `platform_api`) |
| P0-SEC-02 | P0 | VERIFIED | Institutional mutators require authz (`require_institutional_principal` / `require_admin`) |
| P0-SEC-03 | P0 | VERIFIED | Universe activate-full requires admin |
| P0-FIN-01 | P0 | VERIFIED | `enforce_execution_quote_truth` before auto-exec; stale/slip fail-closed |
| P0-FIN-02 | P0 | VERIFIED | ToB/mid paths marked indicative via `executable_edge_truth` |
| P0-FIN-03 | P0 | VERIFIED | Rewalk recomputes net via `profit_fee_algorithms.net_cross_exchange_profit` |
| P0-DATA-01 | P0 | OPEN | Dual migration / PG AUTOINCREMENT |
| P0-DEVOPS-01 | P0 | OPEN | CI/Sonar false-green + coverage AA |
| P1-SEC-04 | P1 | VERIFIED | Admin MFA wired into `require_admin` |
| P1-SEC-05 | P1 | VERIFIED | `/b2b` demo key gated by `EXPOSE_B2B_DEMO_KEY` |
| P1-SEC-06 | P1 | OPEN | localStorage + XSS sinks |
| P1-SEC-07 | P1 | OPEN | Cookie unseal inconsistency |
| P1-FIN-04 | P1 | FIXED | Fee dual-path → fee_matrix authority in arb/exec/net paths |
| P1-FIN-05 | P1 | FIXED | Unknown withdrawal returns None (no silent 0) |
| P1-FIN-06 | P1 | OPEN | Stale quote policy broader surface |
| P1-FIN-07 | P1 | OPEN | Forecast/hype claims |
| P1-DATA-02 | P1 | OPEN | PG commit/rollback no-ops |
| P1-TEST-01 | P1 | OPEN | CI subset of tests |
| P1-COV-01 | P1 | OPEN | Coverage not institutional / AA blocks import |

## Batch evidence

### BATCH 1 — Authz (`ea1358c`)
- Tests: `tests/test_p0_authz_hardening.py`

### BATCH 2 — Financial executability
- Modules: `executable_edge_truth.py`, `execution_engine.py`, `slippage_guard.py`, `fast_scan_engine.py`, `fee_matrix.py`, `profit_fee_algorithms.py`, `arbitrage_engine.py`, `bd_platform/cex_dex_arbitrage.py`
- Tests: `tests/test_p0_financial_executability.py` (+ fee/slippage regressions)
