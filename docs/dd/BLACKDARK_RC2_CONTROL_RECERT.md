# BLACKDARK RC2 — Independent 210-Control Re-Certification

**RC1 SHA (immutable):** `de6537fb29d6bc6203d58b572924db55b9c74d53`  
**RC2 evaluation SHA:** `a597fb7808e5cf79626d24e9bdc1e388abc416fa`  
**Method:** Re-evaluate every RC1 control against RC2 repository evidence. Do not inherit PASS from documentation alone. EXTERNAL never fabricated as PASS.

## Aggregate (RC2)

| Status | Count | Notes |
|--------|------:|-------|
| PASS | 178 | +16 vs RC1 162 — repo remediations + new evidence |
| PASS_WITH_RISK | 18 | −12 vs RC1 30 — residual accepted / partial |
| FAIL | 0 | −5 vs RC1 (Vault contradiction, SBOM, license inventory, thin ops, founder email closed in-repo) |
| NOT_TESTED | 1 | −3 — chaos pack added; remaining = live multi-fault buyer cloud |
| EXTERNAL_EVIDENCE | 12 | PSP, CodeQL UI, DR drill live, branch protection, counsel×2, account ownership, Sonar New Code, WAF/pentest, 60s, HA remeasure optional |
| N/A | 1 | — |
| **Total** | **210** | |

## Kill Gates

| Gate | RC2 | Evidence |
|------|-----|----------|
| KG financial false profit | PASS | Decimal arb path; fee/gas fail-closed tests |
| KG authz bypass | PASS | prior + security suites |
| KG secrets in logs | PASS | telegram private file; mask patterns |
| KG Bandit H/M | PASS | `bandit -c .bandit` HIGH=0 MEDIUM=0 LOW=112 |
| KG CodeQL analyze workflow | PASS (run) | Analyze job historically green; **open alert count EXTERNAL** |
| KG Sonar main QG | EXTERNAL | F-EXT-08 / F-TEST-01 — do not fake coverage |
| KG counsel IP | EXTERNAL | F-EXT-05 |
| KG transferability operate | PASS_WITH_RISK | Handover pack present; ownership schedule unfilled EXTERNAL |
| KG live PSP | EXTERNAL | F-EXT-01 |

## Material control deltas (FAIL → PASS / PASS_WITH_RISK)

| Control | RC1 | RC2 | Evidence |
|---------|-----|-----|----------|
| D2-07 Vault honesty | FAIL | PASS | compose `vault-dev` profile + ARCHITECTURE |
| D10-08 / D14-05 Runbooks | FAIL/PWR | PASS | expanded RUNBOOK + ops/* |
| D12-04 SBOM | FAIL | PASS | CycloneDX + CI job |
| D13-01 License inventory | FAIL | PASS_WITH_RISK | inventory generated; counsel EXTERNAL |
| D16-03 Founder email | FAIL | PASS | YOU@example.com + registry |
| D14-07 / D16-07 Transfer | PWR HIGH | PASS_WITH_RISK | handover pack; bus factor residual EXTERNAL accounts |
| D2-03 / D5-06 Money path | PWR | PASS | arbitrage_engine → money_decimal |
| D5-10 Advisory label | PWR | PASS | ADVISORY_NOT_EXECUTABLE |
| D5-14 Gas truth | PWR | PASS | fail-closed gas; no +$3 bridge invent |
| D6-11 Telegram secrets | PWR | PASS | 0600 secrets file |
| D6-02 CSP attestation | PWR | PASS_WITH_RISK | default ON + attestation form (fill EXTERNAL) |
| D6-23 CORS | INFO | PASS_WITH_RISK | review doc; origin list fill at deploy |
| D8-05 Chaos | NOT_TESTED | PASS_WITH_RISK | unit chaos pack; live multi-fault still limited |
| D12-05 Action pins | PWR | PASS | SHA-pinned workflows |
| D13-06 NOTICE | PWR | PASS | NOTICE added |
| D2-06 Dual oracle | PWR | PASS_WITH_RISK | contract documented; full unify POST_CLOSE |

## Domains still EXTERNAL-heavy

D4 payments live, D6 Code Scanning UI, D7 live DR, D10 branch protection, D11 Sonar main New Code, D13 counsel, D15 regulatory counsel, D16 account ownership / 60s.

## Integrity notes

- Automatic Analysis remains **disabled** by operating model during CI scanner verification.
- No coverage emptying / exclusion gaming performed for Sonar.
- Capacity: MEASURED only per `docs/LOAD_TEST_RUN_LOG.md`; 1k/10k users **UNPROVEN**.
