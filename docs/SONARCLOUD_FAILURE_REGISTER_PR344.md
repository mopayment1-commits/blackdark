# SonarCloud failure register — PR #344 / branch `cursor/batch-06-501-600-e85e`

**Generated:** 2026-08-31 UTC  
**Purpose:** Explicit documentation per governance request — not a generic "pre-existing" hand-wave.

---

## Executive summary

| Question | Answer |
|----------|--------|
| Does SonarCloud fail on this PR? | **Yes** — Quality Gate FAILED |
| Does SonarCloud fail on `main` too? | **Yes** — documented since 2026-08-27 |
| Is failure caused by today's integrity work (311 reclass, generator ban, pytest.ini)? | **No** — root cause is project-level **New Code coverage** gate; today's layer files may add **duplication smell** but are not the primary QG breaker |
| Is failure blocking Critical Gate? | **No** — Critical Gate is a separate workflow and is **green** |

---

## Evidence runs

| Run | Branch | SHA | Workflow | Conclusion | URL |
|-----|--------|-----|----------|------------|-----|
| `33341818920` | `cursor/batch-06-501-600-e85e` | `e98f5e3` | SonarCloud Analysis | **FAILURE** | https://github.com/mopayment1-commits/blackdark/actions/runs/33341818920 |
| `33341818920` dashboard | PR #344 | — | SonarCloud QG | **FAILED** | https://sonarcloud.io/dashboard?id=mopayment1-commits_blackdark&pullRequest=344 |
| `33071878866` | `main` | (2026-08-27) | SonarCloud Analysis | **FAILURE** | https://github.com/mopayment1-commits/blackdark/actions/runs/33071878866 |

Log excerpt (PR run `33341818920`):
```
ERROR QUALITY GATE STATUS: FAILED
View details on https://sonarcloud.io/dashboard?id=mopayment1-commits_blackdark&pullRequest=344
```

---

## Documented quality-gate conditions (project baseline)

Source: `docs/BLACKDARK_FINAL_TWO_TRACK_CERTIFICATION.md` §11–14 (main @ `abc9e2b`, 2026-08-27):

| Condition | Observed on main | Required | Result |
|-----------|------------------|----------|--------|
| **New Code coverage** | **28.3%** | ≥ **80%** | **FAIL** |
| Overall coverage | Imported via Cobertura | — | Not QG-passing |
| Bugs / Vulnerabilities / Hotspots | Not fully enumerated in CI log | — | QG failed on coverage first |

**Root cause class:** `F-EXT-08` / `F-TEST-01` — SonarCloud **New Code period definition** on main is broader than PR diffs; admin action required (`New Code = Previous version` per `sonar.projectVersion=2026.08.12`).

---

## Failure attribution vs today's commits

### Commits in scope (integrity session)

| Commit | Files touched | Sonar relevance |
|--------|---------------|-----------------|
| `f3c6f2b` | 311 reclass JSONL/xlsx, generator `raise RuntimeError`, `pytest.ini` | **pytest.ini** not in `sonar.sources` scope for QG; JSON/xlsx excluded; generators under `scripts/**` **excluded** in `sonar-project.properties` |
| `e98f5e3` | `cap978/external_registry.py`, `institutional_gate.py`, `verify_institutional_closure.py`, `conftest.py` | Small Python delta; **not** the coverage gate breaker |

### Large files from hero batches (present on branch, pre-dating today's integrity commit)

These **are** in `sonar.sources` (not excluded):

- `bd_platform/charting_market_intelligence_layer.py`
- `bd_platform/defi_yield_intelligence_layer.py`
- `bd_platform/derivatives_onchain_intelligence_layer.py`
- `bd_platform/institutional_delivery_intelligence_layer.py`

**Risk:** High structural duplication (`_base`/`_metric` pattern × hundreds of functions) → likely elevates **duplication** and **cognitive complexity** smells on **new code** window.  
**Not the documented primary QG failure** on main (coverage 28.3% < 80%).

### Explicitly excluded from Sonar analysis (today's audit scripts)

Per `sonar-project.properties` lines 38–39: `scripts/**` excluded — includes:

- `scripts/reclassify_template_seed_stubs.py`
- `scripts/audit_production_path_alignment.py`
- `scripts/generate_template_stub_311_remediation_plan.py`
- `scripts/generate_*_intelligence_layer.py` (banned generators)

---

## Per-failure-item register

| ID | Failure | Source | Related to today? | Remediation owner |
|----|---------|--------|-------------------|-------------------|
| SC-01 | Quality Gate FAILED | SonarCloud CI Scanner | **Indirect** — branch carries large generated layers; **primary** gate is coverage | Engineering + SonarCloud admin |
| SC-02 | New Code coverage 28.3% (main baseline) | `BLACKDARK_FINAL_TWO_TRACK_CERTIFICATION.md` | **No** — predates 2026-08-30 integrity work | SonarCloud admin: New Code = Previous version |
| SC-03 | PR #344 QG FAILED | Run `33341818920` | **No** for pytest.ini / reclass / gate fix | Same as SC-02 |
| SC-04 | Potential duplication in 4 template layers | Static structure | **Yes (branch content)** — generator output on branch | Address via 311 remediation Option A/B; do not re-enable generators |
| SC-05 | `scripts/**` excluded — audit tooling not scanned | `sonar-project.properties` | N/A (by design) | Accept or narrow exclusion in future ADR |

---

## Relationship to CI Critical Gate (merge gate)

| Workflow | PR #344 latest green run | Role |
|----------|--------------------------|------|
| **CI Critical Gate Suite** | https://github.com/mopayment1-commits/blackdark/actions/runs/33341818925 — **SUCCESS** | **Authoritative merge gate** |
| SonarCloud Analysis | `33341818920` — FAILURE | Parallel quality signal; **not fixed in this session** |

---

## Recommended next steps (out of current scope)

1. SonarCloud admin: set **New Code = Previous version** aligned to `SONAR_PROJECT_VERSION` (`2026.08.12`).
2. During 311 remediation: **do not expand** the four template layers; Option A builds must land in dedicated modules wired through `cap646/backend_registry.py`.
3. Re-run SonarCloud on PR after admin change; attach dashboard link per `docs/CI_CRITICAL_GATE_EVIDENCE_POLICY.md`.
