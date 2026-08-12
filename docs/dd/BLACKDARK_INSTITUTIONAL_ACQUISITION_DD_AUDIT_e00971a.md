# BLACKDARK — Institutional Acquisition & Launch DD Audit

**Canonical main SHA:** `e00971a034043046f4eefd3df1807c7b59101859`  
**As-of:** 2026-08-12T14:10Z  
**Standard applied:** Hardest reasonable M&A tech DD + institutional launch committee (kill gates, external evidence, no marketing credit)

---

## Executive verdict

| Question | Answer |
|----------|--------|
| Institutionally acquisition-ready as turnkey operated business? | **NO** |
| Commercially launch-ready (paid production, strict path)? | **NO** |
| Software asset transferable under conditions? | **YES — PROCEED WITH CONDITIONS** |
| Fabricated “READY / COMPLETE” claim allowed? | **FORBIDDEN** |

**Committee recommendation:** **PROCEED WITH CONDITIONS** as a *software asset*, not a certified operated franchise. Do not pitch Soft Launch SQLite / demo SSO as institutional production.

---

## Live tip gates (`e00971a`)

| Gate | Result |
|------|--------|
| CI Critical Gate | **PASS** |
| Security Scan (pip-audit + pytest-security) | **PASS** |
| CodeQL Analyze (python / js / actions) | **PASS** |
| Full local pytest | **647 passed / 0 failed / 1 skipped** |
| SonarCloud CI Scanner on main | **FAIL** (QG) |
| Sonar main Quality Gate | **ERROR** — only `new_coverage` 33.8% &lt; 80% |
| New Code period | `previous_version` start **2026-08-08** (~10,765 new lines to cover) |
| Sonar `projectVersion` on tip analysis | **2026.08.12** (VERSION event registered by #69) |
| Bugs / Vulnerabilities / Hotspots (Sonar) | **0 / 0 / 0** |
| Overall coverage (Sonar) | **31.0%** (honest; not gamed) |
| Branch protection API | **403 — unverifiable** |
| Code Scanning open-alert export | **403 — unverifiable** |

**Note on #69:** Version cut registered correctly, but New Code window did **not** collapse on the first analysis of `2026.08.12` (period still 2026-08-08). Under Previous version, a **second intentional version increment** after this baseline analysis is the legitimate next step — not Number of days gaming.

Automatic Analysis: **must remain DISABLED**.

---

## Domain scorecard (14)

| # | Domain | Score | One-line evidence |
|---|--------|-------|-------------------|
| 1 | Financial truth / fail-closed | **PASS** | Fee/withdrawal/net-edge fail-closed; RC2 financial tests in Critical CI |
| 2 | Auth / session / secrets / prod guard | **CONDITIONAL** | Fernet/CSRF/vault/TOTP solid; Soft Launch bypasses Postgres/billing |
| 3 | XSS / CSP / DOM | **CONDITIONAL** | Nonce CSP + XSS suites; residual `style-src 'unsafe-inline'` |
| 4 | CodeQL / Bandit / scanners | **CONDITIONAL** | Tip Analyze + Security green; Bandit H/M=0; open-alert UI EXTERNAL |
| 5 | Sonar main QG | **FAIL** | Tip QG FAILED on `new_coverage` 33.8% |
| 6 | Live PSP / payments | **EXTERNAL** | Hosted checkout design OK; live purchase evidence missing |
| 7 | DR / restore drill | **EXTERNAL** | Scripts/runbooks present; live drill artifact missing |
| 8 | Branch protection / supply chain | **CONDITIONAL** | Hash-locked deps + SHA-pinned Actions; protection unverifiable |
| 9 | Counsel IP / regulatory | **EXTERNAL** | Eng packs exist; no counsel opinion (KG-08) |
| 10 | Scale / viral | **CONDITIONAL** | Limited signed HA; 1k–10k UNPROVEN; surge PR not on main |
| 11 | Enterprise SSO / SCIM claims | **FAIL** | `product_complete`/`scim_ready` True with `demo_sso_ok` / `ENTERPRISE_SSO_DEMO` default true |
| 12 | Test honesty | **CONDITIONAL** | Critical Gate green & scoped honestly; Sonar suite curated; overall cov ~31% |
| 13 | Stale open security PRs | **FAIL** | #40/#41/#50/#51/#54/#65 still open; several CONFLICTING |
| 14 | Commercial launch | **FAIL** | Soft Launch escape + PSP/ownership/Sonar blockers; not paid-prod launch |

---

## Kill-style blockers (acquisition / launch)

1. Sonar **main** Quality Gate red on certified tip  
2. No counsel IP/license opinion  
3. No live PSP test purchase (or signed Soft-Launch non-sale disclosure)  
4. Code Scanning open C/H/M counts unknown  
5. Cloud/DNS/vendor ownership schedule incomplete  
6. Enterprise SSO advertised complete while demo path defaults on  
7. Branch protection unverifiable  
8. No live backup/restore drill artifact  
9. Open conflicting security/integrity PRs (#40/#41/#50/#65)  
10. Strict commercial launch path not closed (`SOFT_LAUNCH` can waive Postgres/billing)

---

## What is defensible today

- Fail-closed financial economics with regression gates  
- Auth/session hardening, production-guard fail-closed (strict path)  
- CSP nonce default + XSS regression coverage  
- Hash-locked installs, pinned Actions, SBOM/license tooling  
- Bandit HIGH/MEDIUM = 0; Critical + Security + CodeQL Analyze green on tip  
- Sonar bugs/vulns/hotspots = 0; reliability/security/maintainability New Code ratings OK  
- DD documentation historically honest about EXTERNAL gaps (do not override with READY claims)

---

## Forbidden claims

- READY / CERTIFIED COMPLETE / turnkey operated acquisition  
- Enterprise SSO / SCIM production-complete  
- Viral 1k–10k proven  
- Sonar main Quality Gate PASS  
- Soft Launch = institutional production  

---

## Required next actions (ordered)

### Repository (engineering)

1. Post-baseline Sonar version increment (after `2026.08.12` analysis exists) so Previous version New Code starts at that baseline — then prove **main** QG PASS.  
2. Remove or hard-gate false-complete SSO flags (`product_complete` / `scim_ready` / demo default) until real IdP path is proven.  
3. Close or explicitly supersede stale conflicting PRs (#40/#41/#50/#51/#54/#65) with main truth.  
4. Keep expanding meaningful coverage for production New Code — without narrowing coverage exclusions to fake %.

### Owner / admin / counsel (non-repo)

1. Sonar UI: keep **Previous version** (do not switch to Number of days).  
2. Export branch protection + required checks.  
3. Code Scanning UI: open Critical/High/Medium = 0 screenshot on tip SHA.  
4. Live PSP test purchase evidence.  
5. Live restore drill artifact.  
6. Counsel IP + regulatory memos.  
7. Account ownership schedule filled.  
8. Pentest/WAF or buyer waiver.

---

## Final institutional stamp

```
INSTITUTIONAL ACQUISITION READINESS: NOT READY
COMMERCIAL LAUNCH READINESS: NOT READY
SOFTWARE ASSET DD POSTURE: PROCEED WITH CONDITIONS
CONFIDENCE IN ENGINEERING GATES (Critical/Security/CodeQL tip): HIGH
CONFIDENCE IN OPERATED / LEGAL / LIVE EVIDENCE: LOW
OVERALL COMMITTEE SCORE (indicative): ~65–70% — MEDIUM
FINAL VERDICT: NOT COMPLETE
```
