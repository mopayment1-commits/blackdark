# 00 — FORENSIC BASELINE

**Audit ID:** `IDA-2026-BLACKDARK-001`  
**Wave:** 0 — Forensic Baseline & Audit Governance  
**Generated:** 2026-09-10T23:36:00Z  
**Evidence Level:** L0 (Repository evidence only)  
**Spec Reference:** §16

---

## CURRENT OBSERVED BASELINE

### Repository Identity

| Field | Value |
|---|---|
| Repository path | `/workspace` |
| Remote origin | `https://github.com/mopayment1-commits/blackdark` |
| Current branch | `cursor/batch07-301-350-ed16` |
| HEAD SHA | `14bbf492c69b51e2008d6dc9baefe3d578ae0696` |
| HEAD parent | `c6fa559b5c883b20be6d40b4bdacdeefaac3b47f` |
| HEAD date | 2026-09-06 13:29:30 +0000 |
| HEAD subject | `docs(batch07): v5 final local freeze on c6fa559 — CI PASS, Sonar QG PASSED, perf LOCAL_COMPLETE` |
| HEAD author | Cursor Agent \<cursoragent@cursor.com\> |
| `origin/main` SHA | `9af0c38aec6d2a903e949e11ea2d3af98f345f2e` |
| Ahead of main | 43 commits |
| Behind main | 0 commits |

### Worktree State

| Check | Result |
|---|---|
| Staged changes | **NONE** |
| Unstaged changes | **NONE** |
| Untracked files | **0** |
| Worktree clean | **YES** |

### Secondary Worktree (Observed, Not Primary Audit HEAD)

| Path | HEAD | State |
|---|---|---|
| `/home/ubuntu/blackdark-incident-readonly` | `ce05685893455c062489879963491ca65a651292` | detached HEAD |

**Note:** Dual-HEAD observation recorded as OQ-001 in SSOT. Institutional audit primary universe = workspace HEAD unless Wave 1 reconciliation dictates otherwise.

---

## Git History Snapshot

### Tags

| Tag | Notes |
|---|---|
| `batch01-02-pending-closure-v1` | Prior closure marker — CLAIM REQUIRING REVALIDATION |
| `cap978-closure-v1` | Prior closure marker — CLAIM REQUIRING REVALIDATION |

### Recent Commits (last 15)

| SHA | Date | Subject |
|---|---|---|
| `14bbf492` | 2026-09-06 | docs(batch07): v5 final local freeze on c6fa559 — CI PASS, Sonar QG PASSED, perf LOCAL_COMPLETE |
| `c6fa559b` | 2026-09-06 | fix(batch07): scope pdf routing to 301-350; refresh full-path perf evidence |
| `33bb0939` | 2026-09-06 | docs(batch07): v5 evidence — full-path perf LOCAL_COMPLETE, async forensics, regression FULL_PASS |
| `ef44a98b` | 2026-09-06 | fix(batch07): tighten v5 freeze gates for perf conflicts and Sonar QG |
| `4d363dd2` | 2026-09-06 | fix(batch07): v5 micro-reconciliation — pdf routing, perf thresholds, Sonar QG, async forensics |
| `6e59be44` | 2026-09-06 | fix(batch07): refresh Sonar QG evidence on ci-freeze-only |
| `4499699b` | 2026-09-06 | docs(batch07): refresh freeze CI evidence on 1d06a5a |
| `1d06a5a0` | 2026-09-06 | docs(batch07): v3 local freeze — BATCH07_FINAL_LOCAL_FREEZE=true, full-path evidence hardened |
| `c851d388` | 2026-09-06 | feat(batch07): v3 reconciliation — state vocabulary, 15k duplicate coverage, full-path entitlement/perf, hero matrix |
| `f93ee2c2` | 2026-09-06 | docs(batch07): final local freeze — CI PASS on 71cce58, BATCH07_FINAL_LOCAL_FREEZE=true |
| `d63a9373` | 2026-09-06 | fix(batch07): fetch CI evidence by commit; add --ci-freeze-only updater |
| `71cce58a` | 2026-09-06 | docs(batch07): micro-closure artifacts — hardened perf, queue semantics, drift split |
| `7b6f9783` | 2026-09-06 | fix(batch07): class-specific perf profiles for AI-heavy stability (cap 316) |
| `db737adf` | 2026-09-06 | fix(batch07): micro-closure — performance hardening, assurance_tooling drift, queue semantics |
| `67087dac` | 2026-09-06 | docs(batch07): regenerate freeze artifacts at reconciliation HEAD 3ad4437 |

### Recent Merge History (sample)

Institutional merges include batch closures, CI hardening, and feature waves (PRs #86–#360 range). Full merge log in git. **Merge claims are not accepted as audit evidence.**

---

## Repository Composition (Tracked @ HEAD)

| Metric | Count |
|---|---|
| Total tracked files | **1,435** |
| Python (`.py`) | 834 |
| Markdown (`.md`) | 210 |
| JSON (`.json`) | 209 |
| HTML (`.html`) | 52 |
| SQL (`.sql`) | 19 |
| JavaScript (`.js`) | 15 |

### Top-Level Directory Distribution

| Root | Files |
|---|---|
| `docs/` | 329 |
| `tests/` | 202 |
| `scripts/` | 171 |
| `bd_platform/` | 74 |
| `templates/` | 50 |
| `cap646/` | 48 |
| `blackdark/` | 47 |
| `data/` | 38 |
| `api/` | 26 |
| `locales/` | 25 |
| `ml/` | 16 |
| `static/` | 14 |
| `browser_extension/` | 13 |
| `cap978/` | 12 |
| `billing/` | 11 |

---

## Dependency Lock Baseline (SHA256 @ HEAD)

| File | SHA256 |
|---|---|
| `requirements.txt` | `deea13dc353e44a38a4dace7df572a671b95013b253a55777c4303b150e7d041` |
| `requirements.lock.txt` | `617acfea2052bb9f24dc031ee4645c9c0d49e73c044d174a4b8724b9c290f826` |
| `requirements.hashes.txt` | `1ced880590c41d474ff545ff75f21fa4809e03065b4baec5dc9f678f813cd911` |
| `requirements-prod.txt` | `f86fb93744c5fddac1ceedd3be656c0b1023a05f24a95ea5c0fbf3e2ed2ce074` |
| `requirements-prod.lock.txt` | `39db59a368aa1de9d44636aabd8a141173b7640bd9e5fa64b6c9127c21e91cae` |
| `requirements-prod.hashes.txt` | `c229b9d1d00f203dcc72df3194866ceb7db098c56c86164c5ae461174b845048` |

**Recent lock changes (last 30 commits):** None detected in commit file lists.

---

## Area Change Scan (Last 30 Commits)

| Area | Commits touching | Files touched | Recent activity |
|---|---:|---:|---|
| Dependency lock | 0 | 0 | Stable in recent history |
| Migrations | 0 | 0 | No alembic/migration file commits |
| Security-named paths | 9 | 1 | Mostly `docs/BATCH07_SECURITY_MATERIAL_PATH_AUDIT.json` |
| Config | 0 | 0 | No recent config file commits |
| Infrastructure | 0 | 0 | No recent workflow/docker commits |
| Frontend/templates | 0 | 0 | No recent template commits |
| Tests | 2 | 2 | `tests/test_batch07_full_path_entitlement.py`, hero batch tests |

### Material Code Changes (Non-Docs) in Recent Window

| Commit | Files | Area |
|---|---|---|
| `c6fa559b` | `cap646/backend_registry.py`, `cap646/runtime.py` | Runtime / routing |
| `4d363dd2` | `cap646/backend_registry.py`, `cap646/domain_enrichment.py`, `cap646/runtime.py` | Runtime / routing |
| `c851d388` | `scripts/batch07_v3_reconciliation.py`, `tests/test_batch07_full_path_entitlement.py` | Reconciliation / tests |

---

## CI/CD Baseline (Observed, Not Executed)

| Workflow | Path |
|---|---|
| Main CI | `.github/workflows/ci.yml` |
| Security | `.github/workflows/security.yml` |
| SonarCloud | `.github/workflows/sonarcloud.yml` |
| CAP978 institutional gate | `.github/workflows/cap978-institutional-gate.yml` |

**CI PASS claims in commit messages and JSON artifacts:** E6 (documentation/claim only) until independently re-run under audit evidence protocol.

---

## Prior Audit Artifacts (Historical — Not Truth Input)

| Location | Status |
|---|---|
| `/home/ubuntu/blackdark-forensics/BLACKDARK_DUE_DILIGENCE_20260910T203924Z/` | Partial prior session; Gate 1 failed; Gate 2A not closed; **excluded from SSOT truth** |
| `docs/BATCH07_*` freeze/reconciliation JSON | Present in repo; **claims requiring revalidation** |
| `docs/BATCH05_*` freeze artifacts | Present; **claims requiring revalidation** |

---

## Baseline Integrity Declaration

| Question | Answer | Evidence |
|---|---|---|
| Was baseline captured from live repository state? | YES | EVD-001, EVD-002 |
| Is worktree clean at capture time? | YES | EVD-001 |
| Are prior PASS claims accepted? | **NO** | Zero-trust §1 |
| Is production state verified? | **NOT VERIFIED** | L3 evidence unavailable |
| Is runtime behavior verified? | **NOT VERIFIED** | Wave 1+ |

---

## Wave 0 Baseline Status

**CURRENT OBSERVED BASELINE:** **CAPTURED**  
**FORENSIC REGRESSION IDENTIFIED:** **NOT PROVEN** (see `FORENSIC_CHANGE_IMPACT_REGISTER.md`)  
**Next:** Wave 1 — Complete System Discovery
