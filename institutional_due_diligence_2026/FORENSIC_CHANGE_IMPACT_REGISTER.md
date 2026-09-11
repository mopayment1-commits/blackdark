# FORENSIC CHANGE IMPACT REGISTER

**Audit ID:** `IDA-2026-BLACKDARK-001`  
**Wave:** 0  
**Generated:** 2026-09-10T23:36:00Z  
**Spec Reference:** §17  
**Policy:** No regression assumed without evidence. Default classification for unproven impact: **Not Verified**.

---

| Change ID | Commit / File | Area | Previous Behavior | Current Behavior | Potential Regression | Evidence | Confidence | Status |
|---|---|---|---|---|---|---|---|---|
| CHG-001 | `c6fa559b`, `4d363dd2` / `cap646/backend_registry.py` | Runtime routing | NOT VERIFIED | PDF routing scoped to capability IDs 301–350 per commit message | Caps outside 301–350 may lose PDF routing path | EVD-003 (git diff); EVD-004 (commit message) | Low | **Not Verified** |
| CHG-002 | `c6fa559b`, `4d363dd2` / `cap646/runtime.py` | Runtime | NOT VERIFIED | Runtime module modified in batch07 reconciliation | Behavior change in cap646 execution path unknown without runtime test | EVD-003 | Low | **Not Verified** |
| CHG-003 | `4d363dd2` / `cap646/domain_enrichment.py` | Domain logic | NOT VERIFIED | Domain enrichment logic modified | Enrichment output drift possible | EVD-003 | Low | **Not Verified** |
| CHG-004 | `c851d388` / `tests/test_batch07_full_path_entitlement.py` (added) | Tests | Test did not exist | New entitlement full-path test added | May increase test confidence for batch07 only; coverage outside 301–350 NOT VERIFIED | EVD-005 | Medium | **Not Verified** (test not executed in this audit session) |
| CHG-005 | Multiple / `docs/BATCH07_FINAL_LOCAL_FREEZE.json` | Documentation claims | Prior freeze state unknown | Asserts `BATCH07_FINAL_LOCAL_FREEZE=true`, CI PASS, Sonar QG PASSED, perf LOCAL_COMPLETE | False institutional assurance if claims inaccurate | EVD-006 (file content E6) | N/A | **Not Verified** — claim requires E1/E2 revalidation |
| CHG-006 | `14bbf492` / `scripts/generate_batch07_institutional_package.py` | Tooling | NOT VERIFIED | Package generator modified at freeze commit | Generated artifact integrity depends on generator correctness | EVD-003 | Low | **Not Verified** |
| CHG-007 | `7b6f9783` / `scripts/batch07_reconciliation.py` | Tooling | NOT VERIFIED | Class-specific perf profiles for AI-heavy cap 316 | Performance classification drift | EVD-003 | Low | **Not Verified** |
| CHG-008 | Last 30 commits | Dependency locks | Lock files stable in recent commits | No lock file changes observed | Supply-chain drift not introduced in recent window | EVD-002 | High | **Unrelated** (no change detected) |
| CHG-009 | Last 30 commits | Migrations | NOT VERIFIED | No migration file commits in recent window | Schema drift via migrations unlikely in recent window | EVD-001 | Medium | **Unrelated** (no migration commits) |
| CHG-010 | Last 30 commits | CI/Infrastructure | Workflows unchanged in recent commits | CI workflow files not modified in last 15 commits | CI gate regression from infra change unlikely in window | EVD-001 | Medium | **Unrelated** |

---

## Summary

| Status | Count |
|---|---|
| Proven | 0 |
| Suspected | 0 |
| Unrelated | 3 |
| Not Verified | 7 |

**FORENSIC REGRESSION IDENTIFIED:** **NO** (not proven at Wave 0)  
**Material suspected changes requiring Wave 1+ runtime verification:** CHG-001, CHG-002, CHG-003, CHG-005

---

## Linked Findings

| Change ID | Finding ID |
|---|---|
| CHG-005 | WF-001 |
| CHG-001–003 | WF-002 |
| Dual HEAD observation | WF-003 |
