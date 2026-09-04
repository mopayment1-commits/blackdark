# Batch05 SonarCloud Quality Gate Analysis — PR #366

**Date:** 2026-09-04  
**PR:** [#366](https://github.com/mopayment1-commits/blackdark/pull/366)  
**Baseline commit:** `947cc7c`  
**Branch:** `cursor/batch05-201-250-e85e`  
**Scope:** Code-only analysis — findings attributable to **#212 / #226** changes vs repo-wide QG failure

---

## Executive summary

| Layer | Status | Notes |
|-------|--------|-------|
| **Coverage XML** (CI prerequisite) | **PASS** | Run `33892906398` — `test_duplicate_capability_delegates` green after #212 fix |
| **SonarCloud CI Scanner** | **FAIL** | Quality Gate did not pass |
| **Coverage XML success = QG success** | **FALSE** | Prerequisite cleared; QG is a separate gate |

**Batch05 remains OPEN.** No `LOCAL_GOVERNANCE_COMPLETE` · no `PRODUCTION-ALIGNED` for any new ID.

---

## 1) Quality Gate conditions (PR #366)

Source: SonarCloud API `qualitygates/project_status?pullRequest=366` @ 2026-09-04.

| Condition | Threshold | Actual | Status | Batch05 #212/#226 attribution |
|-----------|-----------|--------|--------|-------------------------------|
| `new_reliability_rating` | ≤ A (1) | **D (4)** | **ERROR** | **Not attributable** — driven by `batch04_strangler_spine.py` BUG |
| `new_security_rating` | ≤ A (1) | A (1) | OK | N/A |
| `new_maintainability_rating` | ≤ A (1) | A (1) | OK | N/A |
| `new_coverage` | ≥ 80% | **79.6%** | **ERROR** | **Marginal repo-wide gap** — `batch05_ids.py` at 100% line coverage |
| `new_duplicated_lines_density` | ≤ 3% | 0.8% | OK | N/A |
| `new_security_hotspots_reviewed` | 100% | 100% | OK | N/A |

Dashboard: https://sonarcloud.io/dashboard?id=mopayment1-commits_blackdark&pullRequest=366

---

## 2) New-code issues on PR #366 (37 total)

### 2.1 Files touched by #212 / #226 lock (in scope)

| File | Sonar issues | Coverage (local `coverage.xml`) | #212/#226 verdict |
|------|-------------:|----------------------------------|-------------------|
| `cap646/batch05_ids.py` | **0** | **100%** line-rate | **Clean** — routing exclusion for #212 |
| `cap646/batch05_dedicated.py` (`_cap226`) | 2 (pre-existing pattern) | 62.9% file aggregate | **No new blocking issue** — S1172/S7503 on shared `_cap_hero_bridge` at L180, not `_cap226` |
| `cap646/batch05_hero_bridge.py` | 5× S1192 (literal duplication) | 95.2% | **Pre-existing** — removals for #212/#226 reduced surface; not introduced by lock |
| `cap646/batch05_production.py` | 0 | 78.6% | Unchanged routing contract |

**#212-specific:** No new Python module — exclusion-only via `batch05_ids.py`. Zero Sonar issues.

**#226-specific:** `_cap226` is a 4-line facade delegating to `batch02_production.execute(69)` — follows established `_cap206/_cap228` pattern. No unique Sonar rule violations.

### 2.2 Issues outside #212/#226 scope — minimal QG fix applied (continuation)

| Severity | File | Rule | Action |
|----------|------|------|--------|
| **BUG (CRITICAL)** | `cap646/batch04_strangler_spine.py:227` | `pythonbugs:S6466` | **FIXED** — `_as_dict_list()` + `asset`/`symbol` normalization |
| CRITICAL ×5 | `cap646/batch05_hero_bridge.py` | `python:S1192` | Pre-existing literal duplication — not in scope |
| MAJOR/MINOR | `cap646/batch04_dedicated.py` | S1172, S7503 | batch04 gateway overlap fix (#159) |
| CRITICAL ×6 | `scripts/generate_batch05_*.py` | S1192 | Generator scripts — not runtime |

---

## 3) Prioritized findings — Batch05 #212/#226 code only

| Priority | Finding | Action | Test backing |
|----------|---------|--------|--------------|
| P0 | None — zero blocking Sonar issues in `batch05_ids.py` or `_cap226` | **No code change required** | `test_duplicate_capability_delegates`, `test_cap226_reused_link_facade` |
| P1 | `new_coverage` 79.6% &lt; 80% (repo PR aggregate) | **Addressed** — `test_batch05_ids_contract.py` on batch05 routing manifest | Local PASS; CI pending |
| P2 | `new_reliability_rating` D from `batch04_strangler_spine.py` bug | **FIXED** — `_as_dict_list` + asset key normalization | `test_cap164_unlock_actionability_matches_asset_key` |

### Proposed minimal fixes (Batch05 #212/#226 only)

**None required for institutional lock.** The two closed items introduce no new Sonar violations and no new reliability bugs.

If owner later mandates closing the 0.4% `new_coverage` gap without touching batch04:

- Add a **unit test** importing `BATCH05_IDS`, `BATCH05_DUPLICATE_DELEGATION_IDS`, asserting `len(BATCH05_IDS)==49` and `212 not in BATCH05_IDS` (partially covered by `test_batch05_manifest_count` — already present).

---

## 4) CI cross-reference (commit `947cc7c`)

| Check | Result |
|-------|--------|
| Coverage XML | **pass** (22m8s) |
| SonarCloud CI Scanner | **fail** — QG |
| SonarCloud Code Analysis | **fail** — QG |
| critical (Postgres) | fail — **out of scope** |
| pip-audit / bandit | fail — **out of scope** |
| CAP978 Institutional Gate | pass |

---

## 5) Institutional lock statement

- **Coverage XML PASS** confirms regression #212 is closed on CI.
- **QG FAIL** is a **separate** institutional gate — predominantly driven by batch04 reliability bug and aggregate new-coverage margin, **not** by #212/#226 implementation defects.
- **No QG-related code changes** are proposed within the #212/#226 scope beyond what is already merged at `947cc7c`.

---

**تصريح:** Coverage XML نجاح ≠ Quality Gate نجاح. Batch05 **OPEN** حتى اجتياز QG أو قرار مالك صريح بفصل عتبة batch04 عن batch05.
