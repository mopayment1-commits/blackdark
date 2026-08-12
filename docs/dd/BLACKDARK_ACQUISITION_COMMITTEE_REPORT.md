# BLACKDARK Acquisition Committee Report — RC1

**Independent Technology Due Diligence**  
**RC1 SHA:** `de6537fb29d6bc6203d58b572924db55b9c74d53`  
**Date:** 2026-08-12  
**Mode:** READ-ONLY (no remediation during audit)

---

## 1. Executive conclusion

BLACKDARK is a **real, coherent software product** with material institutional engineering controls already present in code: financial fail-closed fee/withdrawal semantics, CSP nonce defaults, authz hardening, Postgres migration integrity, hash-locked CI installs, and a large green automated test matrix (**603 passed** on RC1).

It is **not** acquisition-ready as a turnkey operated business without conditions. Transferability is founder-centric; several buyer-grade artifacts (SBOM, license inventory, DR evidence, Code Scanning UI confirmation, Sonar main New Code admin, live PSP, counsel) are missing; main Sonar QG is red for a **MIXED tool/baseline** reason, not a proven financial false-profit defect.

**Committee recommendation: PROCEED WITH CONDITIONS.**

No Kill Gate was proven **FAIL**. KG-08 remains **EXTERNAL_EVIDENCE_REQUIRED** (counsel). KG-10 is **PASS_WITH_RISK** (reproducible engineering; founder ops required).

---

## 2. Scope

In-scope: repository at RC1, workflows, tests executable in DD environment, static security/financial review, dependency locks, architecture/docs consistency, decision register sampling.

Out-of-scope: live production cloud, buyer VPC, paid PSP credentials, formal pentest execution, legal opinions, inaccessible Cursor chat history, Code Scanning alert API (403).

---

## 3. RC SHA

`de6537fb29d6bc6203d58b572924db55b9c74d53` — see `docs/dd/BLACKDARK_RC1_MANIFEST.md`.

---

## 4. Methodology

Control matrix first (210 controls) with PASS/FAIL criteria, then evidence binding (E3/E2/E1/E0). Frameworks used as **philosophy only** (NIST SSDF, OWASP SAMM/ASVS, CIS, SLSA principles, SRE, M&A tech DD). **No formal certification claimed.**

---

## 5. Framework mapping

| Theme | Mapping |
|---|---|
| Secure SDLC | CI gates, SAST, dependency audit, hashed installs |
| ASVS-like | Authn/authz/session/CSP/XSS regression tests |
| SLSA-like | Lockfiles + hashes; SBOM gap (F-SC-01) |
| SRE | Health checks; thin runbooks; limited metrics |
| Financial systems | Fail-closed fee authority + independent tests |

---

## 6. Evidence limitations

- Code Scanning alerts API 403  
- Branch protection API not verifiable  
- No live PSP / pentest / WAF  
- Load HA evidence from earlier tip SHA (applicable scenario, not remeasured on RC1)  
- Cursor historical conversations inaccessible  
- No browser E2E in this DD  

Evidence confidence is therefore **not** “near-certain.”

---

## 7. Technical score (100-point model)

| Domain | Weight | Score / Weight | Notes |
|---|---|---|---|
| Product / Asset Reality | 6 | 5.5 | Real product; live PSP external |
| Architecture | 8 | 6.5 | Coherent; Vault doc fail; dual oracle debt |
| Code Quality | 5 | 4.0 | Bandit H/M=0; dashboard debt |
| Functional Correctness | 7 | 5.5 | Strong automated; no E2E/PSP |
| Financial Integrity | 12 | 10.5 | Fail-closed strong; float residual |
| Security | 12 | 9.5 | Hardened; open alerts EXTERNAL |
| Data / Database | 6 | 5.0 | PG integrity good; DR external |
| Reliability | 6 | 4.5 | Fallbacks present; chaos limited |
| Performance / Scalability | 6 | 4.0 | Measured soft HA; scale unproven |
| Infrastructure / DevOps | 5 | 3.5 | CI solid; branch protection unknown |
| Testing / SDLC | 6 | 4.5 | 603 green; Sonar main QG tool issue |
| Supply Chain | 5 | 3.5 | Hashes+audit; no SBOM |
| Observability / Operations | 4 | 2.0 | Thin runbooks; founder ops |
| Compliance Technical | 4 | 2.5 | Hosted payments; counsel needed |
| Transferability / Integration | 5 | 2.5 | Bus factor ~1; MODERATE integration |
| Technical Debt / Remediation | 3 | 2.0 | Register exists; manageable |
| **TOTAL** | **100** | **75.5 ≈ 76/100** | |

Kill Gates prevent hiding failure: **no FAIL kill gate** → score may stand. If counsel finds fatal IP (KG-08), recommendation must escalate to NO-GO.

---

## 8. Evidence confidence

**68% (MEDIUM)** — strong E3 on tests/CI/Bandit/financial unit paths; material EXTERNAL gaps (alerts UI, PSP, counsel, DR, branch protection, Sonar admin).

---

## 9. Kill Gate results

| ID | Result |
|---|---|
| KG-01 Critical remote exploit | **PASS** (no proven Critical; pentest external) |
| KG-02 Systemic authz bypass | **PASS** |
| KG-03 False executable profitability | **PASS** |
| KG-04 Unknown/stale as zero | **PASS** |
| KG-05 Material DB corruption | **PASS** |
| KG-06 Secrets exposed in repo | **PASS** |
| KG-07 Supply-chain compromise | **PASS** |
| KG-08 IP/license fatal | **EXTERNAL_EVIDENCE_REQUIRED** |
| KG-09 Mock-as-production core | **PASS** |
| KG-10 Non-reproducible operation | **PASS_WITH_RISK** (conditions) |
| KG-11 Bypass alternate path | **PASS** |
| KG-12 Fabricated readiness on RC1 | **PASS** (current cert honest NOT COMPLETE) |

Passed: 10 (incl. PASS_WITH_RISK counted as non-fail)  
Failed: 0  
Not tested: 0  
External: 1 (KG-08) + residual confidence limits on KG-01 pentest

---

## 10–13. Findings summary

See `BLACKDARK_FINAL_DD_FINDINGS_REGISTER.md`.

- Critical severity defects: **0**  
- High: **1** (transferability F-XFER-01)  
- Medium/Low: as register  
- Blockers: **0**  
- Critical remediation items: **6** code/doc/process (+ external conditions)

---

## 14. External evidence requirements

F-EXT-01 … F-EXT-10 (PSP, CodeQL UI, DR, branch protection, counsel IP, counsel regulatory, cloud ownership, Sonar New Code admin, WAF/pentest, optional 60s).

---

## 15. Architecture assessment

Coherent Soft Launch vs strict Postgres model; fee_matrix authority; service modes; Redis bus fail-closed. Material honesty defect: Vault documentation vs compose (`F-ARC-02`). Dual oracle paths remain integration debt (`F-ARC-01`).

---

## 16. Financial integrity assessment

**Strong for acquisition technical DD.** Unknown fees/withdrawals fail closed; indicative ≠ executable; stale exec blocked; independent tests exist; CI fee coverage gate ≥85%. Residuals: float vs Decimal dual path; directional advisory soft-pass labeling.

---

## 17. Security assessment

**Strong code posture** (CSP nonce default, CSRF fail-closed, admin MFA, institutional Depends, XSS regressions, Bandit H/M=0, pip-audit green, CodeQL Analyze green). **Incomplete assurance** without Code Scanning UI open counts, pentest, and prod CSP attestation.

---

## 18. Data/database assessment

Single runtime migration authority; Postgres commit/rollback real; dialect-safe subscription SQL; clean PG tests pass. Backup/restore **not evidenced**.

---

## 19. Reliability assessment

Redis negative-cache fallback; distributed bus fail-closed; financial fail-closed under bad quotes. Full chaos **not tested**.

---

## 20. Performance/capacity assessment

**MEASURED:** Soft-launch-class multi-worker HA (Postgres+Redis, WEB_CONCURRENCY=2) with controlled 429 — prior signed log.  
**UNPROVEN:** 1k–10k / multi-replica global narrative.  
Do not extrapolate.

---

## 21. DevOps/release assessment

Critical CI + Security Scan healthy; Docker/compose/k8s/railway artifacts present; hash-locked installs. Branch protection **unverifiable** here. Sonar CI architecture correct (AA off, coverage import); main QG red for New Code window reasons.

---

## 22. SDLC/testing assessment

603 passed local matrix; critical gate green; security & fee gates real. Sonar diagnosis: **MIXED** (tool/baseline + narrowed inclusions + broader main New Code) — **not** automatic proof of missing financial tests.

---

## 23. Supply-chain assessment

Hashes + require-hashes + pip-audit = solid baseline. Missing SBOM and formal license inventory are buyer DD gaps.

---

## 24. Observability/operations assessment

Health endpoints exist; runbooks too thin for founder-free 03:00 ops. Metrics/tracing immature.

---

## 25. Compliance technical-readiness assessment

Hosted checkout / no PAN storage is good technical boundary. Not a legal compliance certification. Counsel required for advice/marketing and privacy program.

---

## 26. Transferability assessment

**HIGH RISK (founder dependency)** — bus factor ≈ 1 for secrets, Glass Box, PSP, Sonar admin, CodeQL UI. Engineering repo is transferable; **operated production** is not, until handover pack lands.

---

## 27. Integration risk

**MODERATE** — FastAPI routers, Docker portability, dual PSP option; identity OAuth secrets external; dual oracle complicates reasoning integration.

---

## 28. Technical debt

Manageable post-close set (dashboard modularization, Decimal unification, observability). Pre-close is mostly honesty artifacts + handover + external attestations—not a rewrite.

---

## 29. Data-room readiness

**PARTIAL** — strong architecture/tests/CI/security code evidence; missing SBOM, license report, DR, pentest, account ownership, alert UI exports.

| Category | Status |
|---|---|
| Architecture | READY |
| Repo history | READY |
| Dependency locks | READY |
| SBOM | MISSING |
| Security code evidence | READY |
| Code Scanning alert export | EXTERNAL |
| Tests/coverage | PARTIAL (main Sonar QG) |
| CI/CD | READY |
| Infra manifests | READY |
| Performance | PARTIAL |
| Tech debt register | READY (this DD) |
| IP/license | EXTERNAL |
| Runbooks/DR | PARTIAL |
| Decision register | READY (sampled) |

---

## 30. Remediation effort

Pre-close: mostly **S–L process/doc/admin** + counsel (not a multi-quarter rewrite).  
Post-close modernization: **M–L** engineering program items.

---

## 31. Pre-close conditions

All PRE_CLOSE rows in `BLACKDARK_FINAL_REMEDIATION_REGISTER.md` (F-XFER-01/02, F-OPS-01, F-ARC-02, F-SC-01, F-IP-01, F-SEC-01 attestation, F-EXT-01/02/03/04/05/06/07/08/09).

---

## 32. Post-close recommendations

F-ARC-01, F-FIN-01..03, F-CQ-01/02, F-OPS-02/03, observability, chaos, action SHA pinning, privacy roadmap.

---

## 33. Unknowns

Live prod posture; open CodeQL alert counts; counsel outcomes; true multi-region capacity; browser E2E defects; compound outage behavior.

---

## 34. Final acquisition recommendation

# PROCEED WITH CONDITIONS

**Not PROCEED** — material external/transfer gaps remain.  
**Not REMEDIATE BEFORE ACQUISITION** — no proven Kill Gate FAIL requiring code rewrite before term sheet; conditions are largely evidence/handover/admin/counsel.  
**Not NO-GO** — asset is real; financial/security core controls are materially present.

If counsel returns fatal IP (KG-08) or Code Scanning reveals Critical open exploitables (KG-01), escalate immediately.

---

*Committee integrity: recommendation uses only evidence available for frozen RC1. Inaccessible systems were not marked verified. BLACKDARK production code was not modified during this audit.*
