# PR #356 — Corrective Report (bandit + orchestrator + Sonar follow-ups)

**Commit under test:** `eecef6b` (pre-fix) → post-fix branch head after this report  
**Generated:** 2026-09-02 UTC

---

## 1) Bandit failure — full inventory

### Re-run command (identical to CI `security.yml`)

```bash
bandit -r . -c .bandit -ll -q
```

### Result on `eecef6b` (before B314 fix)

```
EXIT=1
Total issues by severity: Low=186, Medium=3, High=0
```

| # | Rule | Severity (Bandit) | File | Line | Issue |
|---|------|-------------------|------|------|-------|
| 1 | **B314** | **Medium** (maps to Major in Sonar-style gates) | `scripts/run_closure_mandate_completion.py` | 35 | `xml.etree.ElementTree.parse` on Cobertura XML |
| 2 | **B314** | **Medium** | `scripts/run_closure_mandate_last.py` | 202 | `xml.etree.ElementTree.parse` on Cobertura XML |
| 3 | **B314** | **Medium** | `scripts/run_spine_coverage_snapshot.py` | 47 | `xml.etree.ElementTree.parse` on Cobertura XML |

**No Blocker/Critical/High findings.**  
**186 Low findings** (not failing `-ll` gate alone; exit code driven by the 3 Medium B314).

### Origin classification

| Finding | New in PR #356? | Notes |
|---------|-----------------|-------|
| B314 ×3 in `scripts/run_closure_*` / `run_spine_coverage_snapshot.py` | **No** — pre-existing operator scripts | Unrelated to S2083 fix or `test_sonar_pr356_new_code_coverage.py` |
| cap646 / path_safety / closure_guard changes | **No bandit findings** | `bandit -r cap646/closure_guard.py path_safety.py` → clean |

### ACCEPTED_RISK_REGISTRY.json cross-check

Registry path: `docs/ACCEPTED_RISK_REGISTRY.json`

| Registry entry | Status in registry | Bandit on `eecef6b` | Regression? |
|----------------|-------------------|---------------------|-------------|
| **B110** ×3 (`cap646/entitlements.py` L74,129,143) | ACCEPTED_RISK (LOW) | Not reported at `-ll` failure threshold | **No** — still accepted LOW |
| **B310** (`scripts/complete_pdf_capabilities_826.py` L124) | ACCEPTED_RISK | Suppressed by `.bandit` `skips: B310` | **No** |
| **B310** (`scripts/wave_00_passive_security_scan.py` L17) | ACCEPTED_RISK | Suppressed by `.bandit` `skips: B310` | **No** |
| **B314** (`scripts/run_spine_coverage_snapshot.py` L47) | **FIXED** (2026-09-01) | **Still flagged** — code still used `ET.parse` | **Registry drift** (marked FIXED but implementation incomplete) — **not** a countersignature invalidation of B110/B310 |

**Conclusion:** Bandit CI failure is **old B314 debt in scripts**, not a regression from Sonar/security work. Two additional B314 sites (`run_closure_mandate_completion.py`, `run_closure_mandate_last.py`) were never registered.

### Fix applied (post `eecef6b`)

- Added `scripts/cobertura_spine.py` using **`defusedxml.ElementTree.parse`**
- Migrated all three scripts to shared parser
- Re-run: `bandit -r . -c .bandit -ll -q` → **EXIT=0**

---

## 2) batch-verification-orchestrator failure

### CI evidence (`eecef6b`, run `33589652128`)

```
Orchestrator failed: ['audit_official_batch01_rtm.py']
{"all_verified": false, "failed": ["audit_official_batch01_rtm.py"]}
```

### Failure layer

| Layer | Failed? | Impact on RTM/HTTP/entitlement proofs |
|-------|---------|--------------------------------------|
| **Script 1/8:** `audit_official_batch01_rtm.py` | **Yes** (non-zero exit) | RTM re-generation for batch01 **did not complete** on that CI run |
| Scripts 2–8 | **Not reached** (sequential orchestrator) | HTTP/entitlement proofs **not re-run** on that CI run |
| Committed proof JSONs in repo | Unchanged on CI runner | Prior committed proofs remain; CI run did **not** refresh them |

**Classification:** Failure is in **evidence generation step 1** (RTM audit subprocess), not a cosmetic report-format check.

### Local re-run on `eecef6b` (before orchestrator hardening)

```bash
SERVICE_BUS_LOCAL=true PYTHONPATH=/workspace python scripts/run_batch_verification_orchestrator.py
# EXIT=0, all_verified=true, failed=[]
```

→ **Flaky / environment subprocess issue on CI**, not a deterministic logic failure on current tree.

### Root cause (confirmed via CI job `100259516882`, run `33633460040`)

```
NOT_COMPLETE: [{'id': 25, 'capability': 'Signal → Explanation Workflow', ...
  'notes': 'audit_exception:OperationalError:no such table: order_books'}]
sqlite3.OperationalError: no such table: institutional_flows
```

**Fresh GitHub runner** has no `blackdark.db` schema. Capability **#25** (`footprint_snapshot` → order book tables) throws on empty sqlite. Locally passes because dev DB exists.

**Fix:** `run_batch_verification_orchestrator.main()` now calls `await database.init_db()` before subprocess audits.

### Post-fix re-run (full orchestrator, commit `462f61d`)

```
EXIT=0
{"all_verified": true, "failed": []}
```

### CI bandit (commit `ecf2e15`, run `33635124256`)

```
bandit -r . -c .bandit -ll -q → job conclusion: pass (22s)
```

### CI batch-verification-orchestrator (commit `462f61d`, run `33635124389`)

```
batch-verification-orchestrator → job conclusion: pass (3m6s)
```

---

## 3) RTM/HTTP/entitlement evidence refresh

Regenerated via orchestrator post-fix. **Substantive proof fields unchanged** — only timestamps/log lines:

| Artifact | Material change |
|----------|-----------------|
| `docs/BATCH01_OFFICIAL_RTM_1_50.json` | `generated_at` only; `production_aligned: 50/50` |
| `docs/BATCH02_OFFICIAL_RTM_51_100.json` | `generated_at` only |
| `docs/BATCH01_HTTP_PROOF_1_50.json` | timestamp in stderr metadata only |
| `docs/BATCH_VERIFICATION_ORCHESTRATOR_RESULT.json` | `verified_at` + log timestamps; `all_verified: true` |

---

## 4) `runtime.py` — Sonar 62.5% (3/8 new lines uncovered) — **RESOLVED**

### Sonar metrics before fix (PR #356, pre-deletion)

- `new_lines_to_cover`: 8  
- `new_uncovered_lines`: 3  
- `new_coverage`: 62.5%

### Reachability analysis (why the blocks were dead)

Catalog scan: every ID where `canonical_id(cid) != cid` and target ∈ batch01/02/03 has `is_duplicate(cid)==True`, handled earlier at lines 128–133 via recursive `execute_capability(target_id, ...)`.

**No production ID reached the former `target_id` batch delegation blocks** with current catalog invariants.

### Applied solution: **(ب) حذف الكتل الثلاث**

Removed the three post-entitlement `target_id in BATCH0x_IDS` delegates (former L147–160). Batch spine routing is already covered by:

1. Direct `capability_id in BATCH0x_IDS` (L112–125)
2. Duplicate recursion `execute_capability(target_id, …)` (L128–133)

Replacement comment in `cap646/runtime.py`:

```147:148:cap646/runtime.py
    # Batch spine is reached only via direct BATCH0x_IDS (L112-125) or duplicate
    # recursion (L128-133). No further target_id batch delegation exists in catalog.
```

### Post-fix verification

| Check | Command | Result |
|-------|---------|--------|
| Runtime spine tests | `pytest tests/cap646/test_runtime_spine_coverage.py -q` | **39 passed** |
| Full spine suite | `pytest` (11 spine modules in `SPINE_PYTEST`) | **passed** |
| `runtime.py` coverage (spine suite) | `--cov=cap646 --cov-report=xml:coverage-runtime-fix.xml` | **88.98%** line-rate (`105/118` stmts); missed: `55,58,61,63,66,76-82,99` only |
| Former L147–160 | cobertura line scan | **0 missed** (lines removed) |
| jscpd (official + hero scope) | `npx jscpd` paths from `run_closure_mandate_last.py` | **15 clones**, 159 duplicated lines (unchanged vs pre-fix baseline) |

**Sonar impact:** Removing 3 unreachable new lines eliminates the 3 uncovered Sonar new-code lines on `runtime.py`; aggregate PR new coverage remains **≥ 80%** (was 93.9% before this deletion).

---

## 5) `batch03_dedicated.py` in PR New Code scope

### Confirmation

| Question | Answer |
|----------|--------|
| Scope | **Prep only** — IDs **101–150** (`BATCH03_DEDICATED_IDS`) |
| Official closure batches 1–100 | **Not in numerator** — batch01 (1–50) + batch02 (51–100) only |
| Callable from 1–100 runtime? | **Only via `BATCH03_IDS` (101–150)** in `runtime.execute_capability` |
| Overlap IDs 103, 129 | Routed to **`batch01_production`**, not `batch03_dedicated` (`BATCH03_OVERLAP_BATCH01_IDS`) |
| Production use in 1–100 | **None** — `batch03_production.execute` raises for IDs outside 101–150 |

`batch03_dedicated.py` appears in Sonar New Code because PR touched shared helpers (`dedicated_common.py` extractions) and prep module lines — **not** because batch03 is in the 1–100 closure spine.

---

## 6) Command transcript summary

```bash
# eecef6b bandit (pre-fix)
bandit -r . -c .bandit -ll -q  → EXIT=1 (3× B314 Medium)

# post-fix bandit
bandit -r . -c .bandit -ll -q  → EXIT=0

# eecef6b orchestrator local
SERVICE_BUS_LOCAL=true PYTHONPATH=/workspace python scripts/run_batch_verification_orchestrator.py → EXIT=0

# CI eecef6b orchestrator (run 33589652128)
→ EXIT=1, failed=['audit_official_batch01_rtm.py']
```
