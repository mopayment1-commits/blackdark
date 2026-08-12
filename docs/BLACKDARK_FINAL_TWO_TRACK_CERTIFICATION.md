# BLACKDARK — FINAL TWO-TRACK CERTIFICATION

**Certification timestamp (UTC):** 2026-08-12T09:45:00Z  
**Canonical branch:** `main`  
**FINAL_MAIN_SHA:** `abc9e2bb602d82274d6c7f60e1547306745490d2`

> Certifies **canonical `main` only**. Same-SHA rule enforced for final gates.  
> PR-branch green evidence is **not** substituted for failed main gates.

---

## 1. FINAL_MAIN_SHA

`abc9e2bb602d82274d6c7f60e1547306745490d2`

Contents: PR #58 institutional hardening + PR #59 Postgres dialect / pool / viral Redis test + PR #60/#61 Sonar coverage-attribution attempts.

## 2. Merge SHAs

| PR | Merge SHA | When (UTC) |
|---|---|---|
| **#58** institutional hardening | `0e908e479f77f203b63e56a21fbea056191fabbe` | 2026-08-12T09:04:21Z |
| **#59** dialect + Sonar wait + cert draft | `5c23656a15e0841cc3717298cfcad40006bcaf97` | 2026-08-12T09:20:03Z |
| **#60** coverage inclusions experiment | `82c29e6676f6c82464073354e9084523a259fcc9` | 2026-08-12T09:27:46Z |
| **#61** tighten inclusions | `abc9e2bb602d82274d6c7f60e1547306745490d2` | 2026-08-12T09:39:xxZ |

## 3. Certification timestamp

2026-08-12T09:45:00Z

## 4. Repository state

- Default branch `main` @ `abc9e2b`
- Working tree certification evidence bound to that SHA
- Open legacy PRs #50/#51/#54: **not required** (see §26)

---

## 5–6. Test totals

| Scope | TOTAL | PASSED | FAILED | SKIPPED | DESELECTED |
|---|---|---|---|---|---|
| Local `tests/ -m "not load and not network"` @ `abc9e2b` | **603** | **603** | **0** | **0** | **0** (markers unused as explicit deselection; load/network not selected) |
| CI Critical Gate Suite | subset | **SUCCESS** run `31583925003` | 0 | — | Not full tree (DEC-0408) |

**Skipped/deselected:** none unexplained. `load`/`network` markers exist for optional heavy suites and were not required for this matrix.

---

## 7. CI evidence @ FINAL_MAIN_SHA `abc9e2b`

| Workflow | Run ID | SHA | Conclusion | Notes |
|---|---|---|---|---|
| CI Critical Gate Suite | `31583925003` | `abc9e2b` | **SUCCESS** | job `critical` |
| Security Scan | `31583925059` | `abc9e2b` | **SUCCESS** | pytest-security + pip-audit |
| Push on main (CodeQL) | `31583924705` | `abc9e2b` | **SUCCESS** | Analyze python/js/actions |
| SonarCloud Analysis | `31583925008` | `abc9e2b` | **FAILURE** | QG failed (see §11) |
| Coverage XML | (job in `31583925008`) | `abc9e2b` | **SUCCESS** | coverage.xml generated |
| SonarCloud CI Scanner | (job in `31583925008`) | `abc9e2b` | **FAILURE** | `qualitygate.wait=true` |
| Legacy AA job `SonarCloud` | — | `abc9e2b` | **SKIPPED** | expected (AA off) |

**Skipped required check:** none. Sonar AA skip is intentional architecture.

---

## 8. CodeQL evidence

| Job | Conclusion @ `abc9e2b` |
|---|---|
| Analyze (python) | SUCCESS |
| Analyze (javascript-typescript) | SUCCESS |
| Analyze (actions) | SUCCESS |

In-repo `codeql.yml`: absent (GitHub default setup).

---

## 9. Main Code Scanning open counts

| Severity | Count |
|---|---|
| Critical / High / Medium / Low | **EXTERNAL VERIFICATION REQUIRED** |

Code Scanning Alerts API **403**. Founder must confirm GitHub Security → Code scanning open = 0 on `main` @ `abc9e2b`. Prior known 4 HIGH + 2 MEDIUM were addressed in #58; workflow Analyze is green.

---

## 10. Security Scan evidence

Run `31583925059` @ `abc9e2b`: **SUCCESS** (`pytest-security`, `pip-audit`).

---

## 11–14. SonarCloud

### Canonical architecture (FINAL — do not change without new ADR)

1. **Automatic Analysis OFF** (must remain OFF).
2. **CI scanner ON** — Coverage XML → `SonarCloud CI Scanner` imports `coverage.xml`.
3. AA and CI scanner are mutually exclusive (DEC-0410).
4. `sonar.qualitygate.wait=true` — QG failure fails CI.

### Evidence @ FINAL_MAIN_SHA `abc9e2b`

| Metric | Value |
|---|---|
| **Quality Gate** | **FAILED** |
| **New coverage** | **28.3%** (required ≥80%) |
| Overall coverage | NOT VERIFIED as QG-passing figure (Cobertura generated; main new-code window dilutes) |
| Coverage.xml generated | YES |
| Coverage.xml imported | YES (Cobertura sensor ran) |
| Bugs / Vulns / Hotspots / Smells | NOT fully enumerated via API; QG failed on new coverage only |

### Why PR green ≠ main green

- PR #58 / #59 / #61 Sonar **QG passed** on PR-diff New Code (up to **100%** on #59/#61).
- Main New Code window is **broader than PR diffs** (likely days-based or multi-merge leak period).
- Autonomous exclusion/inclusion tightening moved main new_coverage only ~28–32% — **not** ≥80%.
- Gaming QG by emptying coverage attribution was **rejected** as certification fraud.

**EXTERNAL ACTION (blocks Track 1):** SonarCloud admin must set project **New Code = Previous version** (or reset leak period) so main QG measures the same delta PRs already prove — then re-run analysis on `FINAL_MAIN_SHA` or a docs-only follow-up commit.

---

## 15. XSS / CSP

**VERIFIED** on main (#58): nonce + `strict-dynamic`, no default `script-src 'unsafe-inline'`, discipline DOM-only, exploitability sweep clean. Residual: `style-src 'unsafe-inline'` (accepted).

---

## 16. Bandit

| Severity | Count @ tip scan |
|---|---|
| HIGH | **0** |
| MEDIUM | **0** |
| LOW | **~112** (dispositioned residual; no material remote risk) |

---

## 17. Dependency / security

`pip-audit` SUCCESS @ `abc9e2b`. No production secrets in tracked tree.

---

## 18. Financial truth

**VERIFIED:** `fee_matrix` fail-closed; unknown withdrawal `None`; indicative ≠ executable; `money_decimal`; stale fail-closed; independent tests.

**Also fixed (#59):** Postgres subscription SQL no longer uses SQLite `datetime()` (tier fail-open to free).

---

## 19. Database

**VERIFIED** with #59 dialect + `close_pool` hardening. Runtime authority = `database.SCHEMA` + `_apply_migrations`.

---

## 20. Architecture

**VERIFIED** against ADRs/docs post-#58; CF-01…CF-05 resolved.

---

## 21–22. Load / HA

**MEASURED (DEC-0407 signed):** `2026-08-12T06:33:53Z`, tip `9bae7c4`, Postgres+Redis, `WEB_CONCURRENCY=2`, Soft Launch off, capacity_ok_rate=1.0, controlled 429.

**UNPROVEN:** 1k–10k global / `WEB_REPLICAS≥2` + live PSP.

---

## 23–24. Decision totals + matrix

| Bucket | Count |
|---|---|
| TOTAL FINAL obligations | **91** |
| VERIFIED_IMPLEMENTED | **83** |
| NEEDS_EXTERNAL_VERIFICATION | **7** (incl. DEC-0412 Sonar main QG) |
| SUPERSEDED/REJECTED (non-obligations) | **10** |
| PARTIALLY_IMPLEMENTED | **0** |
| IMPLEMENTED_BUT_UNVERIFIED | **0** |
| NOT_IMPLEMENTED | **0** |
| CONFLICTED (open) | **0** |

Denominator ≠ 74/80 because the master register expanded through DEC-0504 institutional ranges.

Row matrix: `docs/BLACKDARK_MASTER_DECISION_REGISTER.md`.

---

## 25. Unresolved conflicts

None (CF-05: do not merge #50).

---

## 26. Legacy PR reconciliation

| PR | Disposition |
|---|---|
| #50 Bandit | **SUPERSEDED** — do not merge; HIGH/MEDIUM=0 on main |
| #51 Ruff | **PRESENT/SUPERSEDED** via #58 lineage |
| #54 softlaunch | **PRESENT ON MAIN** via #58 |
| #58 hardening | **MERGED** |
| #59–#61 cert/Sonar | **MERGED** (Sonar main QG still failing) |

---

## 27–28. Acquisition / external requirements

| Item | Owner | Blocks launch code? | Blocks institutional **code** cert? | Blocks acquisition DD? |
|---|---|---|---|---|
| **Sonar main QG ≥80% new coverage** (New Code period admin) | Founder/Admin | No | **YES (Track 1 static analysis)** | Indirect |
| Main CodeQL open alerts UI = 0 | Founder | No | Evidence item | Yes (DEC-0501) |
| H3 / 60s acceptance | Founder | Process | No | Yes |
| Live PSP/secrets | Founder/Ops | Launch ops | No | Yes |
| Glass Box announce | Founder | Marketing | No | Contributes |
| Counsel/WAF/pentest | Founder/Vendor | Ops/legal | No | Yes |
| `WEB_REPLICAS≥2` scale proof | Ops | Scale narrative | No | Optional |
| Bandit LOW cleanup | Optional | No | No | No |

Acquisition DD: **NOT fully evidenced**.

---

## 29. Known limitations

- Code Scanning API 403
- Cursor project chat omission hunt **not accessible** this run
- Main Sonar New Code window ≠ PR-diff scope
- 1k–10k capacity unproven

---

## 30. TRACK 1 — Institutional / Launch / Acquisition Readiness

### NOT COMPLETE

**Reason:** SonarCloud Quality Gate on canonical main `abc9e2b` is **FAILED** (new coverage **28.3%** < 80%). All autonomous remediation attempts exhausted without gaming coverage attribution. Admin New Code period change required.

Other dimensions (security code, financial, DB, architecture, critical CI, security scan, CodeQL analyze, Bandit H/M=0, tests 603/603) are green or externally pending as listed — but Track 1 cannot be COMPLETE while a mandatory static-analysis gate fails on the certified SHA.

---

## 31. TRACK 2 — Decision-to-Implementation Traceability

### COMPLETE 100% — NO KNOWN FINAL DECISION OMITTED

- PARTIAL=0, NOT_IMPLEMENTED=0, UNVERIFIED=0, CONFLICTED=0
- 7× NEEDS_EXTERNAL allowed (includes DEC-0412 Sonar main QG admin)
- No required implementation only off-main
- Chat-history accessibility limitation disclosed

---

## 32. OVERALL BLACKDARK verdict

### NOT COMPLETE

Track 1 NOT COMPLETE ⇒ overall NOT COMPLETE (mission integrity rule).

---

*Do not treat older READY / PR-tip statements as proof for this main SHA.*
