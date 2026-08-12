# BLACKDARK EXTERNAL AUDIT READINESS CERTIFICATION

**Date (UTC):** 2026-08-12  
**Branch:** `cursor/external-audit-readiness-120d`  
**RC2 merge SHA (canonical main at mission start):** `9618a761ec3f7f29073e556d1ac003c954ccb6d7`  
**This certification tip:** see latest commit on branch after surge remediations  

---

## CANONICAL MAIN (mission freeze)

| Item | Value |
|------|-------|
| main SHA (RC2 merge) | `9618a761ec3f7f29073e556d1ac003c954ccb6d7` |
| RC2 merge time | 2026-08-12T11:35:28Z (approx) |
| CI @ merge | Critical Gate `31592534252` SUCCESS · Security `31592534167` SUCCESS · CodeQL/Push `31592534598` SUCCESS · Sonar `31592534133` **FAILURE** (new_coverage) |

PR-branch greens are **not** substitutes for post-merge main evidence.

---

## TESTS (clean env: `SERVICE_BUS_LOCAL=true`)

Focused packs on this branch (adversarial + viral + institutional): green during remediation.  
Full-matrix re-count to be recorded on tip after CI; do not invent.

---

## CODEQL MAIN

| | |
|--|--|
| Analyze workflow on main merge | SUCCESS |
| Open alerts API | **403 — EXTERNAL EVIDENCE REQUIRED** |
| Owner action | GitHub → Security → Code scanning → filter `branch:main` → confirm **open = 0**; screenshot |

Until UI/API proves open=0: gate remains **EXTERNAL**, not COMPLETE for CodeQL closure.

---

## SONARCLOUD MAIN

| | |
|--|--|
| Automatic Analysis | Keep **DISABLED** (CI scanner + coverage.xml) |
| Main QG @ RC2 merge | **FAIL** — new_coverage ≈29% vs ≥80% (wide Previous-version window) |
| Remediation in flight | `sonar.projectVersion=rc2-9618a76` + coverage inclusions; second analysis after merge needed |
| Owner/admin | Confirm New Code = Previous version; do not lower 80% gate |

---

## VIRAL SURGE / CONCURRENT SURVIVABILITY

| | |
|--|--|
| Harness | `scripts/viral_surge_staged.py` Stages A–E + 65s recovery |
| Topology | Postgres + Redis + 2 uvicorn workers (lab) |
| SAFE VERIFIED CAPACITY | **100 concurrent HTTP workers** |
| DEGRADED BUT STABLE | **200 concurrent HTTP workers** |
| FAILURE POINT | **Not reached** on this host |
| BOTTLENECK | Viral RL / oracle compute |
| Recovery | **Proven** |
| SPOF register | `docs/dd/VIRAL_SPOF_REGISTER.md` |
| **VIRAL SURGE VERDICT** | **VIRAL SURGE READY** |

Not a 100k-user marketing claim. Buyer/staging multi-replica + CDN re-sign required for larger envelopes.

---

## SECURITY / FINANCIAL (this mission)

Repository-fixable Critical/High closed in branch:

- Enterprise SSO demo fail-closed; live IdP unverified path blocked  
- Org member APIs RBAC-enforced  
- Live book per-symbol freshness; stale unknown legs fail closed  
- Funding/DeFi no longer claim executable profit without depth  
- Cross-engine deposit fee aligned; metrics token gate; clear-text log hygiene  

Bandit LOW triage: `docs/dd/BANDIT_LOW_TRIAGE.md`

---

## 210 CONTROLS

Re-certification against post-merge tip is required (no inherited PASS).  
RC2 baseline: PASS 178 · PASS_WITH_RISK 18 · FAIL 0 · NOT_TESTED 1 · EXTERNAL 12 · N/A 1 — **must be re-evidenced** after this PR merges; interim status inherits EXTERNAL set.

---

## KNOWN LAUNCH BLOCKERS (EXTERNAL)

1. Live PSP proof / Soft-Launch-only disclosure  
2. Code Scanning UI open=0 screenshot on main  
3. Backup/restore drill artifact  
4. Branch protection export  
5. Counsel IP + marketing/regulatory  
6. Account ownership schedule filled  
7. Sonar main QG PASS (admin New Code + post-baseline analysis)  
8. Pentest/WAF or waiver  
9. CSP production attestation  
10. Optional HA remeasure on multi-replica staging / 60s walkthrough  

---

## LAUNCH VERDICT

**NOT READY** — EXTERNAL blockers remain; viral surge lab READY does not alone authorize global launch.

## EXTERNAL AUDIT VERDICT

**NOT READY** — CodeQL open=0 and Sonar main QG not yet evidenced on canonical main; data-room EXTERNAL packs incomplete.

## FINAL VERDICT

**NOT COMPLETE**

Integrity: no fabrication of EXTERNAL green; known repository-fixable Critical/High from this adversarial pass are remediated on the PR branch; viral surge measured and READY within lab envelope.
