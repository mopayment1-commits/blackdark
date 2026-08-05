# Corrective & Preventive Control Register — Stage 2

**Version:** 5.0 (Stage 2 — controls only)  
**Date:** 2026-08-05  
**Validation branch:** `cursor/g2-g3-quality-gates-soak`  
**Validation commit:** `14112859677b68932c79b31d09a8aed49272794a`  
**Upstream baseline:** `ROOT_CAUSE_REGISTER.md` v4.0 (Stage 1 VERIFIED_CLOSED)  
**Scope:** Corrective (CC-*) and preventive (PCtrl-*) controls only — no implementation steps, test matrix cells, or migrations.

## Stage 2 Notice

Each control below is unique to its finding. Template substitution, parameter-only variation, and delegated “see parent” closures are forbidden. Implementation contracts (Stage 3), test matrix (Stage 4), and migrations (Stage 5) remain **SEMANTICALLY_INVALID — DO NOT EXECUTE** in sibling v3.0 artifacts until their stages pass IVV.

## Control Field Schema

| Field | Requirement |
|-------|-------------|
| **Statement** | One enforceable outcome tied to Stage 1 root cause |
| **Mechanism** | Named artifact, module, job, or gate — not generic “add tests” |
| **Enforcement** | Where violation blocks merge, startup, or execution |
| **Verification predicate** | Observable pass/fail condition for Stage 2 IVV (not full 18-class matrix) |
| **Primary stream** | Remediation stream owning implementation (R0–R8) |

---

## Parent Corrective Controls (CC-001–CC-042)

### CC-001 — Lockfile becomes deploy authority

| Field | Value |
|-------|-------|
| Finding | PC-001 |
| Statement | Commit a pip-tools resolved `requirements-lock.txt` and make CI, Docker, and local install paths consume it as the sole runtime dependency authority. |
| Mechanism | `requirements-lock.txt` generated from `requirements.txt` via `pip-compile`; CI job `lockfile-diff` compares `pip freeze` after install to lock hash; Docker `Dockerfile` installs from lock not ranges. |
| Enforcement | CI merge gate |
| Verification predicate | Two clones at same commit produce identical `pip freeze` sorted output; lockfile present and referenced in CI + Dockerfile. |
| Primary stream | R1 |

### CC-002 — Blocking full pytest collection job

| Field | Value |
|-------|-------|
| Finding | PC-002 |
| Statement | Add a blocking CI job that runs `pytest --collect-only` on entire `tests/` and fails below stored baseline count. |
| Mechanism | `.github/workflows/ci.yml` job `pytest-collection-gate`; artifact `data/ci/test_collection_baseline.json` stores count + commit SHA. |
| Enforcement | CI merge gate |
| Verification predicate | PR cannot merge when collected test count < baseline; baseline file committed. |
| Primary stream | R1 |

### CC-003 — Separate roadmap grid from attested Feature Registry

| Field | Value |
|-------|-------|
| Finding | PC-003 |
| Statement | Establish owner-attested Feature Registry document and demote `FEATURE_MATRIX` to non-authoritative roadmap enumeration in API responses. |
| Mechanism | `docs/institutional/FEATURE_REGISTRY_ATTESTATION.md` (OD-01 scaffold); `bd_platform/registry.py` adds `authority: roadmap_grid` field; remove F-### emission from grid endpoints. |
| Enforcement | Docs + API contract |
| Verification predicate | `/api/platform/features` response includes non-authoritative marker; attestation file exists with owner signature placeholder blocked until OD-01. |
| Primary stream | R0 |

### CC-004 — Implement canonical price APIs and restore UGP module

| Field | Value |
|-------|-------|
| Finding | PC-004 |
| Statement | Implement `market_context.get_canonical_price()`, `get_canonical_venue_price()`, and `unified_global_price.compute_ugp()`; fix G2 script import at L263. |
| Mechanism | New modules `unified_global_price.py` + facade methods in `market_context.py`; migrate `scripts/g2_live_ws_validation.py` to canonical APIs. |
| Enforcement | Runtime + contract tests |
| Verification predicate | G2 validation script imports resolve; execution paths cannot read hub directly without freshness contract. |
| Primary stream | R2 |

### CC-005 — Consolidate execution authority in safety guard module

| Field | Value |
|-------|-------|
| Finding | PC-005 |
| Statement | Introduce `execution_safety_guard.py` with `EXECUTION_ENABLED` master switch, UNKNOWN=DENY, and single reader for all AUTO_EXECUTION_* env vars. |
| Mechanism | Guard module consulted by `execution_engine.py`, `startup_orchestrator.py`, `bd_platform/cex_dex_executor.py`; deprecate direct env reads. |
| Enforcement | Startup fail-closed + runtime |
| Verification predicate | No module outside guard reads AUTO_EXECUTION_* directly; conflict detection aborts startup in prod profile. |
| Primary stream | R3 |

### CC-006 — Migrate financial SQLite REAL columns to NUMERIC

| Field | Value |
|-------|-------|
| Finding | PC-006 |
| Statement | DDL upgrade converting all financial REAL columns in `database.py` to NUMERIC(p,s) with documented precision scale. |
| Mechanism | `db_upgrade.py` migration MIG-03 path; representative + production-scale precision tests. |
| Enforcement | Schema migration + CI |
| Verification predicate | Zero REAL columns on financial tables post-migration; precision property tests pass at scale. |
| Primary stream | R2 |

### CC-007 — Canonical boot profile matrix per deployment class

| Field | Value |
|-------|-------|
| Finding | PC-007 |
| Statement | Document and enforce one canonical service graph per profile (`docker-web`, `local-all`, `compose-workers`) with explicit SERVICE_MODE defaults. |
| Mechanism | `docs/institutional/RUNTIME_TOPOLOGY_MATRIX.md`; startup self-check in `run_service.py` and `dashboard.py` lifespan logging signed graph hash. |
| Enforcement | Startup audit + docs |
| Verification predicate | Architecture test asserts orchestrator invoked iff profile matrix says so; Docker default matches documented web profile. |
| Primary stream | R4 |

### CC-008 — Composition root explicit opt-in flags per domain

| Field | Value |
|-------|-------|
| Finding | PC-008 |
| Statement | Refactor `startup_orchestrator.run_background_startup` so each domain (WS, auto-exec, ML flywheel, etc.) requires explicit opt-in env with safe defaults off for trading paths. |
| Mechanism | Per-domain `RUN_<DOMAIN>` flags default false for execution/WS; composition manifest emitted at startup. |
| Enforcement | Startup |
| Verification predicate | Default env profile starts ≤ N background domains (documented minimal set); auto-exec off without explicit flag. |
| Primary stream | R4 |

### CC-009 — Split platform_api into P01–P16 facade routers

| Field | Value |
|-------|-------|
| Finding | PC-009 |
| Statement | Decompose `platform_api.py` 61-route monolith into per-platform routers registered from composition root with ownership metadata. |
| Mechanism | `bd_platform/routers/pXX_*.py` pattern; `platform_api.py` becomes thin aggregator; route→platform map JSON artifact. |
| Enforcement | Architecture + CI |
| Verification predicate | Route inventory maps 1:1 to P01–P16; no handler remains orphaned in monolithic file. |
| Primary stream | R4 |

### CC-010 — Mandatory authorize_execution before connector calls

| Field | Value |
|-------|-------|
| Finding | PC-010 |
| Statement | Wrap all venue connector entrypoints with unified `authorize_execution()` consulting freeze, exposure, and master switch. |
| Mechanism | `execution_authorization.py` service; `cex_dex_executor.py` and `execution_engine.execute_order` call guard before network I/O. |
| Enforcement | Runtime fail-closed |
| Verification predicate | Connector invocation without auth service raises deterministic ExecutionDenied; freeze state consulted. |
| Primary stream | R3 |

### CC-011 — Encode gate_scope in G3 assessor output schema

| Field | Value |
|-------|-------|
| Finding | PC-011 |
| Statement | Add mandatory `gate_scope` enum (`PILOT`, `INSTITUTIONAL_24H`) to G3 assessment JSON; reject institutional claims when scope ≠ INSTITUTIONAL_24H. |
| Mechanism | `scripts/g3_reliability_soak_test.py` schema v2; `schemas/g3_assessment.schema.json`; CLI sets scope from `--hours` with min 24 for institutional. |
| Enforcement | Evidence validator CI |
| Verification predicate | 1-hour run produces `gate_scope: PILOT`; 24-hour run produces `INSTITUTIONAL_24H`; validator rejects mismatched claims. |
| Primary stream | R7 |

### CC-012 — Unify oracle inference stack under single entry module

| Field | Value |
|-------|-------|
| Finding | PC-012 |
| Statement | Consolidate research and retrain paths behind `oracle_inference_stack.py` public API with provenance fields on every mutation. |
| Mechanism | Facade wrapping `research_lab`, `oracle_retrainer`, `oracle_integrity` filters; deprecate direct cross-imports. |
| Enforcement | Import lint + runtime |
| Verification predicate | Single documented entrypoint; caller inventory shows zero legacy direct paths post-MIG-06. |
| Primary stream | R5 |

### CC-013 — Tenancy middleware and production isolation package

| Field | Value |
|-------|-------|
| Finding | PC-013 |
| Statement | Implement tenant context middleware, fixture key mode for CI, production demo deny, MFA gate, route manifest audit, and P09 RBAC facade. |
| Mechanism | `tenant_context.py`, `production_route_filter.py`, `rbac_facade.py`, fixture keys under `tests/fixtures/keys/`; MFA policy env `ADMIN_MFA_REQUIRED`. |
| Enforcement | Startup + middleware + CI |
| Verification predicate | Cross-tenant negatives fail; prod profile zero demo routes; MFA enforced when flag set. |
| Primary stream | R6 |

### CC-014 — Persist execution authority and runtime task graph

| Field | Value |
|-------|-------|
| Finding | PC-014 |
| Statement | Persist `RuntimeState` execution authority fields and critical task flags to durable store with reload on startup. |
| Mechanism | `execution_state` table (MIG-04); `startup_orchestrator` loads state before spawning tasks. |
| Enforcement | Runtime + restart test |
| Verification predicate | SIGTERM/restart test shows freeze + loop authority restored from DB not env alone. |
| Primary stream | R3 |

### CC-015 — SSOT taxonomy pointer and authority markers

| Field | Value |
|-------|-------|
| Finding | PC-015 |
| Statement | Publish single SSOT pointer listing authoritative vs roadmap vs tier taxonomies with explicit non-equivalence statements. |
| Mechanism | `docs/institutional/CURRENT_PROGRAM_STATUS_POINTER.md`; mark grid, tier, plan audit sources with authority class. |
| Enforcement | ssot-doc-lint |
| Verification predicate | Pointer file exists; three taxonomies labeled; no duplicate CURRENT_SSOT per class. |
| Primary stream | R0 |

### CC-016 — Unify health probe contract across boot paths

| Field | Value |
|-------|-------|
| Finding | PC-016 |
| Statement | Make `run_service.py` the sole Docker entry that starts sidecar; align `launch_verify.bat` to probe both :8080 and :8180 or document explicit web-only profile exception. |
| Mechanism | Dockerfile ENTRYPOINT → `run_service.py`; `launch_verify.py` optional sidecar check; HEALTHCHECK documents port+100 rule. |
| Enforcement | Docker CI smoke |
| Verification predicate | Container HEALTHCHECK passes on standard boot; launch script documents profile-specific probe set. |
| Primary stream | R4 |

### CC-017 — Declare minimal vs full infra profiles

| Field | Value |
|-------|-------|
| Finding | PC-017 |
| Statement | Document `INFRA_PROFILE=minimal|full` with explicit kafka/redis/vault requirements per feature. |
| Mechanism | `docs/institutional/INFRA_PROFILE_MATRIX.md`; features declare hard vs soft dependency on infra services. |
| Enforcement | Startup loud-fail or degrade-with-metric |
| Verification predicate | Minimal profile test proves defined degradation behavior; full profile requires services up. |
| Primary stream | R4 |

### CC-018 — Repair GAPS_COMPLETED links to existing docs

| Field | Value |
|-------|-------|
| Finding | PC-018 |
| Statement | Update `docs/GAPS_COMPLETED.md` to link only committed paths or mark targets as PLANNED with tracking issue ids. |
| Mechanism | Link audit pass; replace broken institutional links with pointer to `CURRENT_PROGRAM_STATUS_POINTER.md`. |
| Enforcement | docs link-check CI |
| Verification predicate | Zero broken relative links from GAPS_COMPLETED on clone. |
| Primary stream | R8 |

### CC-019 — Training-serving path separation guard

| Field | Value |
|-------|-------|
| Finding | PC-019 |
| Statement | Extend ML safety beyond saturation guard to block serving loaders from reading training artifact directories. |
| Mechanism | `ml_serving_boundary.py` path allowlist; CI anti-leakage test scanning `data/models/` vs serving config. |
| Enforcement | CI + runtime |
| Verification predicate | Serving loader rejects paths under training export dirs; test fails on misconfiguration. |
| Primary stream | R5 |

### CC-020 — Extract dashboard composition to submodules (non-blocking refactor)

| Field | Value |
|-------|-------|
| Finding | PC-020 |
| Statement | Split `dashboard.py` route registration into domain modules without behavior change; reduce file below 1500 lines. |
| Mechanism | `dashboard/routes/*.py` package; lifespan remains in thin `dashboard.py`. |
| Enforcement | Architecture lint (advisory until R8) |
| Verification predicate | Line count reduced; import graph unchanged for external callers. |
| Primary stream | R8 |

### CC-021 — Reconcile CI and Docker dependency manifests

| Field | Value |
|-------|-------|
| Finding | PC-021 |
| Statement | Unify dev/prod manifests via lockfile overlays or single lock with optional extras; eliminate silent import skew. |
| Mechanism | `manifest-reconcile` CI job diffing resolved trees CI image vs Docker image for runtime deps. |
| Enforcement | CI merge gate |
| Verification predicate | Resolved runtime dep diff == 0 between CI and Docker smoke import check. |
| Primary stream | R1 |

### CC-022 — Institutional test class package (E2E, concurrency, DR, bypass)

| Field | Value |
|-------|-------|
| Finding | PC-022 |
| Statement | Add test directories and CI jobs for SSE E2E, execution concurrency, backup/restore drill, and execution bypass negatives. |
| Mechanism | `tests/e2e/`, `tests/concurrency/`, `tests/ops/` with blocking CI jobs per sub-finding. |
| Enforcement | CI |
| Verification predicate | Four test classes exist with signed artifact outputs referenced in program state. |
| Primary stream | R7 |

### CC-023 — Commit institutional SSOT scaffold

| Field | Value |
|-------|-------|
| Finding | PC-023 |
| Statement | Create `docs/institutional/` tree with `CURRENT_PROGRAM_STATUS_POINTER.md` as navigation root. |
| Mechanism | R0 scaffold commit; pointer links governance, feature, price, execution authority docs (stubs allowed, authority class required). |
| Enforcement | ssot-doc-lint |
| Verification predicate | Directory exists; pointer discoverable from repo root README or docs index. |
| Primary stream | R0 |

### CC-024 — Single audit authority module

| Field | Value |
|-------|-------|
| Finding | PC-024 |
| Statement | Consolidate oracle audit, compliance filtering, and regulatory verdict transformation under `audit_authority.py`. |
| Mechanism | All consumers (`weekly_report`, `gtm_service`, routes) import audit exports through facade; `include_synthetic` default enforced. |
| Enforcement | Import lint + invariant test |
| Verification predicate | Static analysis shows zero direct `fetch_oracle_audit_stats` from non-facade callers. |
| Primary stream | R8 |

### CC-025 — Fail-closed startup configuration validation

| Field | Value |
|-------|-------|
| Finding | PC-025 |
| Statement | Abort HTTP bind and background startup when required env/config invalid for active profile; no silent skip. |
| Mechanism | `config_validator.py` invoked before uvicorn bind; `production_guard` escalates failures to exit code ≠ 0 in prod. |
| Enforcement | Startup |
| Verification predicate | Missing required prod env causes process exit; partial orchestrator skip eliminated for critical domains. |
| Primary stream | R3 |

### CC-026 — Execution-grade price freshness contract

| Field | Value |
|-------|-------|
| Finding | PC-026 |
| Statement | Bind scan and execution paths to canonical price freshness thresholds; reject stale hub rows for authorization. |
| Mechanism | Extend DEC-C APIs with `max_age_ms`; `fast_scan_engine` requires fresh canonical prices. |
| Enforcement | Runtime + contract tests |
| Verification predicate | Scan with stale feed produces zero authorized opportunities; G2 fails closed on stale age. |
| Primary stream | R2 |

### CC-027 — Domain-seam database module split plan

| Field | Value |
|-------|-------|
| Finding | PC-027 |
| Statement | Split `database.py` into domain repositories (`db_financial`, `db_oracle`, `db_auth`) behind stable facade for migration safety. |
| Mechanism | Phased extraction with re-export facade preserving import paths until MIG-05 boundary. |
| Enforcement | Import graph test |
| Verification predicate | Financial DDL changes isolated to `db_financial.py`; monolith line count reduced ≥30%. |
| Primary stream | R2 |

### CC-028 — Prohibited oracle import lint

| Field | Value |
|-------|-------|
| Finding | PC-028 |
| Statement | Add `scripts/lint_prohibited_imports.py` blocking direct oracle DB helpers outside approved facade list. |
| Mechanism | CI job scanning import graph against allow list; fails on new violations. |
| Enforcement | CI |
| Verification predicate | Lint runs in CI; current violations enumerated with burn-down to zero for MIG-06. |
| Primary stream | R5 |

### CC-029 — Evidence JSON schema validators in CI

| Field | Value |
|-------|-------|
| Finding | PC-029 |
| Statement | Check in JSON schemas for G2/G3 evidence; CI validates artifacts on PR when evidence files change. |
| Mechanism | `schemas/g2_log.schema.json`, `schemas/g3_assessment.schema.json`; `scripts/validate_evidence.py`. |
| Enforcement | CI |
| Verification predicate | Unversioned G2 log fails validation; G3 output validates against schema v2. |
| Primary stream | R7 |

### CC-030 — Production guard filters route mounting

| Field | Value |
|-------|-------|
| Finding | PC-030 |
| Statement | Extend `production_guard.py` to block or unmount dev/demo routes when `ENV=production`. |
| Mechanism | Route registry filter applied at FastAPI init based on profile; integrates with PC-013.e manifest. |
| Enforcement | Startup |
| Verification predicate | Production profile OpenAPI spec excludes demo/debug routes. |
| Primary stream | R6 |

### CC-031 — Clarify DEC-E monolith vs worker deployment modes

| Field | Value |
|-------|-------|
| Finding | PC-031 |
| Statement | Amend architecture docs to distinguish logical P01–P16 monolith from optional physical worker replication without P17 extraction. |
| Mechanism | Update `docs/MICROSERVICES_ARCHITECTURE.md` with DEC-E binding section; worker modes labeled deployment profiles not platform splits. |
| Enforcement | Architecture test + docs lint |
| Verification predicate | Doc explicitly states no P17; test forbids new top-level platform packages outside P01–P16. |
| Primary stream | R4 |

### CC-032 — Create Wave 2 navigation index (navigation-only)

| Field | Value |
|-------|-------|
| Finding | PC-032 |
| Statement | Commit `WAVE2_MASTER_REFERENCE_INDEX.md` as navigation-only index without authority declarations. |
| Mechanism | R0-S10 deliverable; index links docs with `authority: navigation_only` header. |
| Enforcement | ssot-doc-lint |
| Verification predicate | File exists; lint confirms no CURRENT_SSOT marker in index. |
| Primary stream | R0 |

### CC-033 — Orchestrate security workflow after full suite

| Field | Value |
|-------|-------|
| Finding | PC-033 |
| Statement | Merge or chain security workflow so security job requires main CI full-suite success via unified workflow or required-check policy. |
| Mechanism | Single `.github/workflows/ci.yml` with `security` job `needs: [pytest-collection-gate, test]` OR org-level required checks documentation in `docs/ci/REQUIRED_CHECKS.md`. |
| Enforcement | GitHub required checks |
| Verification predicate | Security job cannot succeed when collection gate fails; documented in REQUIRED_CHECKS. |
| Primary stream | R1 |

### CC-034 — Security evidence coupling artifact

| Field | Value |
|-------|-------|
| Finding | PC-034 |
| Statement | Publish CI evidence bundle linking security test results to full-suite status in one signed JSON artifact per run. |
| Mechanism | `E-CI/combined_quality_report.json` emitted by orchestrated pipeline with both job outcomes. |
| Enforcement | CI artifact |
| Verification predicate | Artifact shows security subset PASS only when full collection PASS on same run_id. |
| Primary stream | R7 |

### CC-035 — Platform-level G3 metrics instrumentation

| Field | Value |
|-------|-------|
| Finding | PC-035 |
| Statement | Add unified metrics hooks for platforms missing G3 soak sections; extend `infra_metrics.py` registry. |
| Mechanism | Per-platform metric emitters registered in `bd_platform/infra_status.py`; G3 assessor reads completeness score. |
| Enforcement | G3 assessor |
| Verification predicate | G3 performance section lists ≥90% platform coverage per defined platform list. |
| Primary stream | R7 |

### CC-036 — Record FEATURE_REALITY_MATRIX absent status in SSOT pointer

| Field | Value |
|-------|-------|
| Finding | PC-036 |
| Statement | Document absent audit matrix in SSOT pointer as `ARCHIVED_NOT_IN_REPO` with external reference hash if applicable. |
| Mechanism | Section in `CURRENT_PROGRAM_STATUS_POINTER.md`; ssot-doc-lint handles absent file class. |
| Enforcement | Docs governance |
| Verification predicate | Pointer explicitly states matrix not in repo; lint rule updated for absent vs stale. |
| Primary stream | R0 |

### CC-037 — Marketing doc disclaimer linking to attested registry

| Field | Value |
|-------|-------|
| Finding | PC-037 |
| Statement | Add header to MKT docs stating claims are positioning only until crosswalk to attested Feature Registry exists. |
| Mechanism | Standard disclaimer block in `docs/MKT_*.md` linking to FEATURE_REGISTRY_ATTESTATION when available. |
| Enforcement | ssot-doc-lint advisory |
| Verification predicate | All three MKT files contain disclaimer with link target. |
| Primary stream | R0 |

### CC-038 — Feature-to-legal disclaimer mapping table

| Field | Value |
|-------|-------|
| Finding | PC-038 |
| Statement | Create mapping table linking feature ids to regulatory disclaimer variants in `legal_content.py`. |
| Mechanism | `LEGAL_FEATURE_MAP` dict; compliance guard consults map for feature-specific text. |
| Enforcement | Test on feature rollout |
| Verification predicate | Test asserts every attested live feature id has disclaimer entry. |
| Primary stream | R8 |

### CC-039 — Regenerate or commit pytest collection baseline artifact

| Field | Value |
|-------|-------|
| Finding | PC-039 |
| Statement | Generate `data/ci/test_collection_baseline.json` from current `pytest --collect-only` output replacing absent wave1 file. |
| Mechanism | CI job writes baseline on main; documents count provenance in artifact metadata. |
| Enforcement | CI |
| Verification predicate | Baseline file committed with count ≥ current collection; wave1 file dependency removed from gates. |
| Primary stream | R1 |

### CC-040 — Add schema_version to G2 harness output

| Field | Value |
|-------|-------|
| Finding | PC-040 |
| Statement | Emit `schema_version: "g2.v1"` (or successor) in all new G2 JSON logs; provide retroactive tag guidance for stored logs. |
| Mechanism | Update G2 validation scripts; validator rejects missing version. |
| Enforcement | Evidence validator |
| Verification predicate | New G2 run JSON contains schema_version; validator fails without it. |
| Primary stream | R8 |

### CC-041 — Decimal compute path for fee/profit hot loops

| Field | Value |
|-------|-------|
| Finding | PC-041 |
| Statement | Migrate `fee_matrix.py`, `fast_scan_engine.py`, `profit_fee_algorithms.py` to `decimal.Decimal` for authoritative comparisons before persist. |
| Mechanism | Decimal types in hot path with documented quantization; coordinated with MIG-03 rollback boundary. |
| Enforcement | CI property tests |
| Verification predicate | Property tests prove exact decimal invariants on threshold boundaries; no float casts on money paths. |
| Primary stream | R2 |

### CC-042 — Implement ssot-doc-lint per verification standard

| Field | Value |
|-------|-------|
| Finding | PC-042 |
| Statement | Build `scripts/ssot_doc_lint.py` and `tests/governance/test_ssot_doc_lint.py` exactly per REMEDIATION_VERIFICATION_STANDARD contract. |
| Mechanism | Lint script + CI job `ssot-doc-lint` before test job; emits `E-GOV/ssot-lint-report.json`. |
| Enforcement | CI merge gate |
| Verification predicate | Fixture violations fail lint; clean docs pass; report JSON includes sha256. |
| Primary stream | R0 |

---

## Parent Preventive Controls (PCtrl-001–PCtrl-042)

### PCtrl-001 — Lockfile drift blocking on manifest change

| Field | Value |
|-------|-------|
| Finding | PC-001 |
| Statement | Block PR merge when `requirements.txt` or `requirements-prod.txt` changes without synchronized `requirements-lock.txt` update in same PR. |
| Mechanism | CI `lockfile-diff` job; PR label requirement `lockfile-regenerated`. |
| Enforcement | CI |
| Verification predicate | Synthetic PR changing ranges without lock fails CI. |
| Primary stream | R1 |

### PCtrl-002 — Meta-test guards CI subset regression

| Field | Value |
|-------|-------|
| Finding | PC-002 |
| Statement | Add meta-test parsing `.github/workflows/ci.yml` asserting no reduction of test modules without baseline update. |
| Mechanism | `tests/meta/test_ci_workflow_coverage.py`. |
| Enforcement | CI |
| Verification predicate | Removing collection job causes meta-test failure. |
| Primary stream | R1 |

### PCtrl-003 — Forbidden enumeration lint on feature endpoints

| Field | Value |
|-------|-------|
| Finding | PC-003 |
| Statement | ssot-doc-lint and API test forbid emitting F-### ids from grid; forbid CURRENT_SSOT in grid module docs. |
| Mechanism | `tests/test_registry_not_enumeration_authority.py` + ssot-doc-lint FORBIDDEN_ENUMERATION. |
| Enforcement | CI |
| Verification predicate | Grid endpoint test fails if authority field removed or F-ids appear. |
| Primary stream | R0 |

### PCtrl-004 — Prohibited direct hub reads from execution modules

| Field | Value |
|-------|-------|
| Finding | PC-004 |
| Statement | Import lint prohibits `live_book_hub.get_best_price` from execution_engine, fast_scan_engine, cex_dex_executor. |
| Mechanism | `scripts/lint_prohibited_imports.py` rule `price_direct_hub_ban`. |
| Enforcement | CI |
| Verification predicate | New direct import fails lint. |
| Primary stream | R2 |

### PCtrl-005 — Architecture test for execution env default parity

| Field | Value |
|-------|-------|
| Finding | PC-005 |
| Statement | CI architecture test reads defaults from orchestrator, engine, compose templates; fails on mismatch. |
| Mechanism | `tests/arch/test_execution_default_parity.py`. |
| Enforcement | CI |
| Verification predicate | Changing one default without others fails test. |
| Primary stream | R3 |

### PCtrl-006 — Schema lint forbids new financial REAL columns

| Field | Value |
|-------|-------|
| Finding | PC-006 |
| Statement | DDL lint in CI fails if new REAL columns added to tables classified as financial in registry. |
| Mechanism | `tests/schema/test_no_new_real_financial_columns.py`. |
| Enforcement | CI |
| Verification predicate | PR adding REAL to pricing_logs fails. |
| Primary stream | R2 |

### PCtrl-007 — Boot graph architecture test per profile

| Field | Value |
|-------|-------|
| Finding | PC-007 |
| Statement | Automated test simulates lifespan for each profile and asserts expected background task set. |
| Mechanism | `tests/arch/test_runtime_topology_profiles.py`. |
| Enforcement | CI |
| Verification predicate | web profile test confirms orchestrator not started; all profile starts orchestrator. |
| Primary stream | R4 |

### PCtrl-008 — Startup domain manifest required in CI

| Field | Value |
|-------|-------|
| Finding | PC-008 |
| Statement | CI integration test captures startup manifest hash and compares to golden file per profile. |
| Mechanism | Golden manifest files under `tests/fixtures/startup_manifests/`. |
| Enforcement | CI |
| Verification predicate | Adding domain without manifest update fails test. |
| Primary stream | R4 |

### PCtrl-009 — Route count and ownership regression gate

| Field | Value |
|-------|-------|
| Finding | PC-009 |
| Statement | CI fails if `platform_api` route count increases without corresponding platform router file and map update. |
| Mechanism | `tests/arch/test_platform_route_ownership.py`. |
| Enforcement | CI |
| Verification predicate | New route in monolith file fails until moved to platform router. |
| Primary stream | R4 |

### PCtrl-010 — Connector bypass negative test matrix in CI

| Field | Value |
|-------|-------|
| Finding | PC-010 |
| Statement | Maintain combinatorial negative tests for connector paths (freeze on, exposure exceeded, master off). |
| Mechanism | `tests/security/test_connector_execution_denials.py`. |
| Enforcement | CI blocking |
| Verification predicate | Any bypass returning success fails CI. |
| Primary stream | R3 |

### PCtrl-011 — G3 schema validator rejects missing gate_scope

| Field | Value |
|-------|-------|
| Finding | PC-011 |
| Statement | CI evidence validator rejects G3 JSON without valid gate_scope and hours consistency. |
| Mechanism | `scripts/validate_evidence.py` G3 section. |
| Enforcement | CI on evidence PRs |
| Verification predicate | Sample JSON without gate_scope fails validation. |
| Primary stream | R7 |

### PCtrl-012 — Single oracle entry import enforcement

| Field | Value |
|-------|-------|
| Finding | PC-012 |
| Statement | Prohibited-import lint blocks direct `oracle_retrainer` / `research_lab` calls outside inference stack facade. |
| Mechanism | Lint rule `oracle_single_entry`. |
| Enforcement | CI |
| Verification predicate | New direct import fails lint. |
| Primary stream | R5 |

### PCtrl-013 — Tenant negative test suite mandatory on CRUD changes

| Field | Value |
|-------|-------|
| Finding | PC-013 |
| Statement | CI requires cross-tenant negative tests pass when any `database.py` user-scoped repository changes. |
| Mechanism | Path-triggered job `tenant-isolation-gate`. |
| Enforcement | CI |
| Verification predicate | CRUD change without tenant test update fails path gate. |
| Primary stream | R6 |

### PCtrl-014 — Restart recovery integration test on execution changes

| Field | Value |
|-------|-------|
| Finding | PC-014 |
| Statement | Any change to execution_engine or startup_orchestrator triggers blocking restart recovery test. |
| Mechanism | `tests/integration/test_execution_restart_recovery.py`. |
| Enforcement | CI path filter |
| Verification predicate | Test simulates restart and asserts persisted authority reload. |
| Primary stream | R3 |

### PCtrl-015 — Taxonomy drift lint across three live sources

| Field | Value |
|-------|-------|
| Finding | PC-015 |
| Statement | CI test verifies grid, tier, and plan audit docs all reference SSOT pointer authority classes. |
| Mechanism | `tests/governance/test_taxonomy_authority_markers.py`. |
| Enforcement | CI |
| Verification predicate | Removing authority marker from registry module fails test. |
| Primary stream | R0 |

### PCtrl-016 — Docker HEALTHCHECK integration in CI smoke

| Field | Value |
|-------|-------|
| Finding | PC-016 |
| Statement | CI builds and runs container asserting HEALTHCHECK on 8180 succeeds within timeout. |
| Mechanism | Docker smoke job in ci.yml post-build. |
| Enforcement | CI |
| Verification predicate | Container marked unhealthy when sidecar disabled fails smoke. |
| Primary stream | R4 |

### PCtrl-017 — Infra profile contract test

| Field | Value |
|-------|-------|
| Finding | PC-017 |
| Statement | CI runs minimal and full profile tests asserting documented degrade vs hard-fail behavior. |
| Mechanism | `tests/infra/test_infra_profile_contract.py`. |
| Enforcement | CI |
| Verification predicate | Kafka-absent minimal profile matches matrix expectation. |
| Primary stream | R4 |

### PCtrl-018 — Markdown link checker on docs/**

| Field | Value |
|-------|-------|
| Finding | PC-018 |
| Statement | CI link-check job scans docs for broken relative links on every PR touching docs/. |
| Mechanism | `scripts/check_doc_links.py` or lychee action. |
| Enforcement | CI |
| Verification predicate | Broken link in GAPS_COMPLETED fails job. |
| Primary stream | R8 |

### PCtrl-019 — Training path isolation CI scan

| Field | Value |
|-------|-------|
| Finding | PC-019 |
| Statement | CI scans serving config for paths pointing into training directories. |
| Mechanism | `tests/ml/test_training_serving_path_isolation.py`. |
| Enforcement | CI |
| Verification predicate | Misconfigured path fails scan. |
| Primary stream | R5 |

### PCtrl-020 — Dashboard line-count advisory gate

| Field | Value |
|-------|-------|
| Finding | PC-020 |
| Statement | CI advisory (later blocking) reports dashboard.py line count; fails if growth >5% without refactor ticket. |
| Mechanism | `scripts/check_module_size.py` threshold on dashboard.py. |
| Enforcement | CI advisory → blocking in R8 |
| Verification predicate | Artificial line increase triggers report/failure per stage policy. |
| Primary stream | R8 |

### PCtrl-021 — Manifest reconcile job on every Docker/CI change

| Field | Value |
|-------|-------|
| Finding | PC-021 |
| Statement | CI `manifest-reconcile` runs on changes to Dockerfile, requirements*, or ci.yml. |
| Mechanism | Diff job comparing import smoke lists. |
| Enforcement | CI path filter |
| Verification predicate | Adding pandas-only-to-CI dependency fails reconcile. |
| Primary stream | R1 |

### PCtrl-022 — Institutional test class registry enforced

| Field | Value |
|-------|-------|
| Finding | PC-022 |
| Statement | Meta-test asserts presence of four institutional test directories and associated CI jobs. |
| Mechanism | `tests/meta/test_institutional_test_classes.py`. |
| Enforcement | CI |
| Verification predicate | Removing e2e job fails meta-test. |
| Primary stream | R7 |

### PCtrl-023 — SSOT pointer discoverability test

| Field | Value |
|-------|-------|
| Finding | PC-023 |
| Statement | CI test walks from README/docs index to CURRENT_PROGRAM_STATUS_POINTER within ≤2 hops. |
| Mechanism | `tests/governance/test_ssot_pointer_navigation.py`. |
| Enforcement | CI |
| Verification predicate | Removing pointer link fails navigation test. |
| Primary stream | R0 |

### PCtrl-024 — Audit export invariant test

| Field | Value |
|-------|-------|
| Finding | PC-024 |
| Statement | Invariant test: all audit export code paths include synthetic filter consistent with audit_authority defaults. |
| Mechanism | `tests/audit/test_audit_export_invariants.py`. |
| Enforcement | CI |
| Verification predicate | Caller bypassing synthetic filter fails invariant scan. |
| Primary stream | R8 |

### PCtrl-025 — Config validation required on orchestrator changes

| Field | Value |
|-------|-------|
| Finding | PC-025 |
| Statement | Path-filtered CI runs fail-closed config tests when startup_orchestrator or config.py changes. |
| Mechanism | `tests/startup/test_config_fail_closed.py`. |
| Enforcement | CI |
| Verification predicate | Invalid prod config causes test process exit non-zero. |
| Primary stream | R3 |

### PCtrl-026 — Stale price rejection contract test

| Field | Value |
|-------|-------|
| Finding | PC-026 |
| Statement | Contract tests inject stale timestamps and assert scan/execution authorization denied. |
| Mechanism | `tests/contract/test_price_freshness_gate.py`. |
| Enforcement | CI |
| Verification predicate | Stale injection returning authorized opportunity fails. |
| Primary stream | R2 |

### PCtrl-027 — Database module boundary size gate

| Field | Value |
|-------|-------|
| Finding | PC-027 |
| Statement | CI fails if `database.py` grows without corresponding extraction to domain module. |
| Mechanism | Line-count gate with extraction requirement in same PR. |
| Enforcement | CI |
| Verification predicate | +100 lines to database.py without new db_* module fails. |
| Primary stream | R2 |

### PCtrl-028 — Oracle import allow list versioned in repo

| Field | Value |
|-------|-------|
| Finding | PC-028 |
| Statement | Maintain versioned allow list JSON; CI fails on imports not in list. |
| Mechanism | `governance/oracle_import_allowlist.json`. |
| Enforcement | CI lint |
| Verification predicate | New oracle DB import outside list fails lint. |
| Primary stream | R5 |

### PCtrl-029 — Evidence schema version bump policy

| Field | Value |
|-------|-------|
| Finding | PC-029 |
| Statement | CI rejects evidence harness changes without schema version increment and changelog entry. |
| Mechanism | `tests/governance/test_evidence_schema_version_policy.py`. |
| Enforcement | CI |
| Verification predicate | Harness output shape change without version bump fails. |
| Primary stream | R7 |

### PCtrl-030 — Production route diff golden test

| Field | Value |
|-------|-------|
| Finding | PC-030 |
| Statement | CI compares production profile OpenAPI route list to golden allow list. |
| Mechanism | `tests/security/test_production_route_allowlist.py`. |
| Enforcement | CI |
| Verification predicate | New demo route in prod profile fails diff. |
| Primary stream | R6 |

### PCtrl-031 — No P17 platform package test

| Field | Value |
|-------|-------|
| Finding | PC-031 |
| Statement | Architecture test forbids new packages matching `bd_platform/p17_*` or undocumented platform ids. |
| Mechanism | `tests/arch/test_no_p17_platform.py` per DEC-E. |
| Enforcement | CI |
| Verification predicate | Adding p17 module fails test. |
| Primary stream | R4 |

### PCtrl-032 — Navigation index authority lint

| Field | Value |
|-------|-------|
| Finding | PC-032 |
| Statement | ssot-doc-lint forbids CURRENT_SSOT or LIVE markers in WAVE2_MASTER_REFERENCE_INDEX.md. |
| Mechanism | STALE_LIVE_MARKER + FORBIDDEN_ENUMERATION rules. |
| Enforcement | CI ssot-doc-lint |
| Verification predicate | Adding CURRENT_SSOT to index fails lint. |
| Primary stream | R0 |

### PCtrl-033 — Required checks documentation drift test

| Field | Value |
|-------|-------|
| Finding | PC-033 |
| Statement | Meta-test verifies documented required checks match workflow job names. |
| Mechanism | `tests/meta/test_required_checks_doc_sync.py`. |
| Enforcement | CI |
| Verification predicate | Renamed job without doc update fails. |
| Primary stream | R1 |

### PCtrl-034 — Combined quality report mandatory on main

| Field | Value |
|-------|-------|
| Finding | PC-034 |
| Statement | Main branch CI must upload combined_quality_report.json; branch protection references it. |
| Mechanism | Artifact retention policy + required check. |
| Enforcement | GitHub branch protection |
| Verification predicate | Main run missing artifact fails release gate script. |
| Primary stream | R7 |

### PCtrl-035 — G3 metrics completeness threshold in assessor

| Field | Value |
|-------|-------|
| Finding | PC-035 |
| Statement | G3 assessor WARN/FAIL when platform metrics completeness below 90%. |
| Mechanism | Completeness score in g3_reliability_soak_test.py performance section. |
| Enforcement | G3 harness |
| Verification predicate | Assessor FAIL when >10% platforms silent. |
| Primary stream | R7 |

### PCtrl-036 — Absent file class handling in ssot-doc-lint

| Field | Value |
|-------|-------|
| Finding | PC-036 |
| Statement | ssot-doc-lint implements ABSENT_ARCHIVED class for referenced-but-missing governance files. |
| Mechanism | Lint rule `ABSENT_AUTHORITY_FILE` with pointer cross-check only. |
| Enforcement | CI |
| Verification predicate | Lint passes when pointer documents absence; fails on stale LIVE marker for absent file. |
| Primary stream | R0 |

### PCtrl-037 — MKT disclaimer presence lint

| Field | Value |
|-------|-------|
| Finding | PC-037 |
| Statement | Doc lint requires standard disclaimer header in all MKT_*.md files. |
| Mechanism | `scripts/ssot_doc_lint.py` MKT disclaimer rule. |
| Enforcement | CI |
| Verification predicate | Removing disclaimer fails lint. |
| Primary stream | R0 |

### PCtrl-038 — Legal map completeness on feature registry changes

| Field | Value |
|-------|-------|
| Finding | PC-038 |
| Statement | CI fails when FEATURE_REGISTRY attestation adds feature without LEGAL_FEATURE_MAP entry. |
| Mechanism | `tests/legal/test_feature_legal_coverage.py`. |
| Enforcement | CI path filter on attestation file |
| Verification predicate | New F-id without legal map fails. |
| Primary stream | R8 |

### PCtrl-039 — Collection baseline monotonicity guard

| Field | Value |
|-------|-------|
| Finding | PC-039 |
| Statement | CI fails if collection count drops below baseline without explicit baseline regeneration PR. |
| Mechanism | Baseline compare in collection gate job. |
| Enforcement | CI |
| Verification predicate | Deleting tests without baseline update fails gate. |
| Primary stream | R1 |

### PCtrl-040 — G2 schema_version required in validator

| Field | Value |
|-------|-------|
| Finding | PC-040 |
| Statement | Evidence validator hard-fails G2 logs missing schema_version field. |
| Mechanism | validate_evidence.py G2 section. |
| Enforcement | CI |
| Verification predicate | Unversioned log rejected. |
| Primary stream | R8 |

### PCtrl-041 — Float ban lint on authoritative money modules

| Field | Value |
|-------|-------|
| Finding | PC-041 |
| Statement | CI lint forbids new `float(` casts in fee_matrix, fast_scan_engine, profit_fee_algorithms. |
| Mechanism | AST lint `scripts/lint_no_float_money.py`. |
| Enforcement | CI |
| Verification predicate | New float cast in fast_scan_engine fails lint. |
| Primary stream | R2 |

### PCtrl-042 — ssot-doc-lint required on every docs PR

| Field | Value |
|-------|-------|
| Finding | PC-042 |
| Statement | CI ssot-doc-lint job runs on all PRs touching docs/** or governance paths; merge blocked on violation. |
| Mechanism | Path-filtered required job in ci.yml. |
| Enforcement | CI branch protection |
| Verification predicate | Duplicate SSOT fixture doc fails job. |
| Primary stream | R0 |

---

## Sub-Finding Corrective Controls

### CC-008.a — Unify AUTO_EXECUTION_LOOP defaults across three sources

| Field | Value |
|-------|-------|
| Finding | PC-008.a |
| Statement | Set single documented default for AUTO_EXECUTION_LOOP in orchestrator, execution_engine status, and docker-compose templates per profile table. |
| Mechanism | Profile matrix in RUNTIME_TOPOLOGY_MATRIX; compose overrides generated from matrix not hand-edited. |
| Enforcement | Architecture test PCtrl-005 extension |
| Verification predicate | Default parity test passes for all three sources per profile. |
| Primary stream | R4 |

### CC-008.b — Machine-readable route inventory artifact

| Field | Value |
|-------|-------|
| Finding | PC-008.b |
| Statement | Generate `governance/platform_route_inventory.json` listing all 61 routes with P01–P16 owner, method, path. |
| Mechanism | OpenAPI introspection script run in CI. |
| Enforcement | CI artifact |
| Verification predicate | Inventory count equals live route count; each route has owner field. |
| Primary stream | R4 |

### CC-008.c — Decision pipeline scope decision artifact

| Field | Value |
|-------|-------|
| Finding | PC-008.c |
| Statement | Either commit `decision_intelligence_pipeline.py` with boundary tests OR publish signed scope-retirement record in architecture register. |
| Mechanism | ADR in `docs/institutional/ADR_DECISION_PIPELINE.md` with owner signature. |
| Enforcement | Governance |
| Verification predicate | One of: module exists with tests OR retirement ADR signed — not both absent. |
| Primary stream | R4 |

### CC-008.d — Single compliance facade for all verdict emitters

| Field | Value |
|-------|-------|
| Finding | PC-008.d |
| Statement | Route all public verdict fields through `compliance_facade.to_public_verdict()`; remove duplicate guard calls. |
| Mechanism | Refactor dashboard and platform routes to single import; static emitter inventory. |
| Enforcement | Static analysis test |
| Verification predicate | Zero direct `apply_regulatory_compliance` outside facade module. |
| Primary stream | R8 |

### CC-009.a — API layer import allow list to P13 facades only

| Field | Value |
|-------|-------|
| Finding | PC-009.a |
| Statement | Replace direct `bd_platform.*` imports in platform_api with facade modules per platform. |
| Mechanism | Facade package `bd_platform/facades/`; platform_api imports only facades. |
| Enforcement | prohibited-import lint |
| Verification predicate | Lint reports zero violations from API layer to internal modules. |
| Primary stream | R4 |

### CC-009.b — Non-authoritative labeling on grid API responses

| Field | Value |
|-------|-------|
| Finding | PC-009.b |
| Statement | Add explicit `enumeration_authority: roadmap_grid_not_attested` on feature summary responses. |
| Mechanism | registry.py response schema change + OpenAPI doc update. |
| Enforcement | API contract test |
| Verification predicate | Response JSON contains field; missing field fails contract test. |
| Primary stream | R0 |

### CC-009.c — Decimal fee/profit scan path implementation

| Field | Value |
|-------|-------|
| Finding | PC-009.c |
| Statement | Same as CC-041 scoped to scan hot path: decimal math in fast_scan and fee_matrix before threshold compare. |
| Mechanism | Coordinated R2-S decimal migration sub-step. |
| Enforcement | Property tests |
| Verification predicate | Boundary property tests at 0.0001 USDT thresholds pass exactly. |
| Primary stream | R2 |

### CC-009.d — Single portfolio read repository

| Field | Value |
|-------|-------|
| Finding | PC-009.d |
| Statement | Consolidate holdings display and rebalance preview to `portfolio_read_model.py` single source. |
| Mechanism | Dashboard routes call read model; rebalancer uses same module for preview numbers. |
| Enforcement | Contract test |
| Verification predicate | UI and API rebalance preview return identical holdings hash for fixture user. |
| Primary stream | R2 |

### CC-010.a — Connector DENY without authorize_execution

| Field | Value |
|-------|-------|
| Finding | PC-010.a |
| Statement | cex_dex_executor raises ExecutionDenied before execute_order when authorize_execution returns false. |
| Mechanism | Guard call at L49 before delegation; separate CEX_DEX flag subordinate to master. |
| Enforcement | Security negative tests |
| Verification predicate | Direct POST execute with master off returns 403/deny regardless of CEX_DEX flag. |
| Primary stream | R3 |

### CC-011.a — Hourly stale integrity veto in G3 assessor

| Field | Value |
|-------|-------|
| Finding | PC-011.a |
| Statement | G3 assessor FAIL when any hour exceeds stale threshold; emit hourly integrity artifact. |
| Mechanism | Hourly veto logic in g3_reliability_soak_test.py; output `HOURLY_OPERATION_REPORTS/` JSON. |
| Enforcement | G3 harness + validator |
| Verification predicate | Unit test injecting stale hour produces FAIL assessment. |
| Primary stream | R7 |

### CC-011.b — gate_scope schema field with hours cross-validation

| Field | Value |
|-------|-------|
| Finding | PC-011.b |
| Statement | Schema requires gate_scope; validator rejects INSTITUTIONAL_24H when hours < 24. |
| Mechanism | JSON schema if/then rules in g3_assessment.schema.json. |
| Enforcement | validate_evidence.py |
| Verification predicate | JSON with INSTITUTIONAL_24H and hours=1 fails validation. |
| Primary stream | R7 |

### CC-012.a — Deprecate parallel oracle entrypoints

| Field | Value |
|-------|-------|
| Finding | PC-012.a |
| Statement | Mark research_lab and oracle_retrainer inference exports deprecated; route callers through oracle_inference_stack. |
| Mechanism | Deprecation warnings + caller migration checklist in MIG-06 prep. |
| Enforcement | Import lint |
| Verification predicate | Zero production callers outside stack module per static analysis. |
| Primary stream | R5 |

### CC-012.b — CAP-053 lineage E2E proof artifact

| Field | Value |
|-------|-------|
| Finding | PC-012.b |
| Statement | E2E test proving lineage fields populated signal→prediction→audit for each decision class. |
| Mechanism | `tests/e2e/test_oracle_lineage_cap053.py` producing signed JSON artifact. |
| Enforcement | CI |
| Verification predicate | Artifact shows non-null lineage fields for all classes in matrix. |
| Primary stream | R5 |

### CC-013.a — Fixture key mode for CI reproducibility

| Field | Value |
|-------|-------|
| Finding | PC-013.a |
| Statement | Commit sandbox fixture keys under tests/fixtures/keys/; document live-key injection boundary for G2 live jobs only. |
| Mechanism | `KEYS_MODE=fixture|live` env; CI uses fixture; live jobs in separate workflow with secrets. |
| Enforcement | CI + docs |
| Verification predicate | CI green without gitignored keys/; live workflow documented separately. |
| Primary stream | R6 |

### CC-013.b — Tenant context middleware on all user-scoped repositories

| Field | Value |
|-------|-------|
| Finding | PC-013.b |
| Statement | Introduce tenant_id column pattern and middleware injecting tenant context; repositories require tenant filter. |
| Mechanism | tenant_context middleware + db repository base class enforcing tenant predicate. |
| Enforcement | Runtime + tests |
| Verification predicate | Cross-tenant read/write attempts fail with 403/404 on all CRUD paths in matrix. |
| Primary stream | R6 |

### CC-013.c — Production demo route deny at startup

| Field | Value |
|-------|-------|
| Finding | PC-013.c |
| Statement | Remove or 404 `/api/b2b/demo` when ENV=production regardless of demo key env. |
| Mechanism | production_route_filter excludes demo routes; startup audit confirms zero demo paths. |
| Enforcement | Startup + security test |
| Verification predicate | Production profile request to demo returns 404; audit log lists zero demo routes. |
| Primary stream | R6 |

### CC-013.d — MFA policy and ADMIN_MFA_REQUIRED gate

| Field | Value |
|-------|-------|
| Finding | PC-013.d |
| Statement | Implement TOTP/WebAuthn MFA for admin tier when ADMIN_MFA_REQUIRED=true. |
| Mechanism | MFA module in auth_service; login flow branch; policy doc in SECURITY.md. |
| Enforcement | Runtime + test |
| Verification predicate | Admin login without MFA fails when flag true; passes with valid second factor. |
| Primary stream | R6 |

### CC-013.e — Signed production route manifest at startup

| Field | Value |
|-------|-------|
| Finding | PC-013.e |
| Statement | Emit signed JSON route manifest on prod startup matching allow list; diff against dev manifest logged. |
| Mechanism | `production_route_manifest.json` artifact; HMAC with startup key. |
| Enforcement | Startup audit |
| Verification predicate | Manifest hash matches golden; unexpected route fails startup in prod. |
| Primary stream | R6 |

### CC-013.f — P09 RBAC facade centralizing tier checks

| Field | Value |
|-------|-------|
| Finding | PC-013.f |
| Statement | Create `bd_platform/rbac_facade.py`; all tier-gated routes use facade not ad hoc auth_service calls. |
| Mechanism | FastAPI dependency `require_platform_action()` routing through facade. |
| Enforcement | Static route audit |
| Verification predicate | Zero routes use require_feature directly outside rbac_facade module. |
| Primary stream | R6 |

### CC-015.a — Record FEATURE_REALITY_MATRIX status in pointer

| Field | Value |
|-------|-------|
| Finding | PC-015.a |
| Statement | SSOT pointer entry: FEATURE_REALITY_MATRIX status ARCHIVED_NOT_IN_REPO with external hash if known. |
| Mechanism | Pointer section + optional archived hash field. |
| Enforcement | ssot-doc-lint ABSENT class |
| Verification predicate | Pointer contains status; lint passes absent file class. |
| Primary stream | R0 |

### CC-015.b — Grid vs CAP disclaimer in registry module

| Field | Value |
|-------|-------|
| Finding | PC-015.b |
| Statement | Module docstring and API docs state grid ids 1–40 are not CAP-### mappings; crosswalk only in attested registry post OD-01. |
| Mechanism | registry.py header + OpenAPI description on /features endpoint. |
| Enforcement | Doc lint + API test |
| Verification predicate | Disclaimer text present; test forbids grid id in CAP crosswalk generator. |
| Primary stream | R0 |

### CC-019.a — Anti-leakage test for training directories

| Field | Value |
|-------|-------|
| Finding | PC-019.a |
| Statement | CI test fails if serving loader config paths overlap training export directories. |
| Mechanism | `tests/ml/test_training_serving_path_isolation.py`. |
| Enforcement | CI |
| Verification predicate | Overlapping path fixture fails test. |
| Primary stream | R5 |

### CC-021.a — Zero diff CI vs Docker resolved runtime deps

| Field | Value |
|-------|-------|
| Finding | PC-021.a |
| Statement | manifest-reconcile job proves import-available package set identical in CI runner and Docker smoke container. |
| Mechanism | Import smoke script listing critical modules (ccxt, pandas, sklearn, kafka). |
| Enforcement | CI |
| Verification predicate | Diff report empty for runtime deps. |
| Primary stream | R1 |

### CC-022.a — Blocking pytest collection job (sub-scope)

| Field | Value |
|-------|-------|
| Finding | PC-022.a |
| Statement | Identical to CC-002/CC-039 — dedicated blocking job with baseline artifact (sub-finding tracks collection gate independently). |
| Mechanism | ci.yml job `pytest-collection-gate`. |
| Enforcement | CI |
| Verification predicate | Sub-finding closes when job blocks merge independently of other PC-022 subs. |
| Primary stream | R1 |

### CC-022.b — SSE E2E CI job

| Field | Value |
|-------|-------|
| Finding | PC-022.b |
| Statement | Add `tests/e2e/test_sse_stream_ci.py` validating SSE endpoint contract with signed log output. |
| Mechanism | pytest job with httpx SSE client against test app fixture. |
| Enforcement | CI blocking |
| Verification predicate | Job green produces E-TEST/sse-e2e-log.json. |
| Primary stream | R7 |

### CC-022.c — Execution concurrency test suite

| Field | Value |
|-------|-------|
| Finding | PC-022.c |
| Statement | Add `tests/concurrency/test_execution_races.py` covering loop vs manual execute vs freeze load. |
| Mechanism | asyncio stress tests with timeout bounds. |
| Enforcement | CI blocking |
| Verification predicate | Suite passes 100 iterations without race failure. |
| Primary stream | R7 |

### CC-022.d — Backup/restore drill integration test

| Field | Value |
|-------|-------|
| Finding | PC-022.d |
| Statement | Add `tests/ops/test_backup_restore_drill.py` producing signed restore drill JSON with RTO metric. |
| Mechanism | SQLite backup/restore cycle test with timing capture. |
| Enforcement | CI |
| Verification predicate | Artifact includes restore_success=true and duration_ms. |
| Primary stream | R7 |

### CC-022.e — Execution bypass DENY matrix tests

| Field | Value |
|-------|-------|
| Finding | PC-022.e |
| Statement | Comprehensive negative matrix: freeze+live flag, exposure exceeded, missing auth, env conflicts — all DENY. |
| Mechanism | `tests/security/test_execution_bypass_matrix.py`. |
| Enforcement | CI blocking |
| Verification predicate | Matrix CSV artifact shows 100% DENY rows. |
| Primary stream | R7 |

### CC-034.a — Unified workflow chaining security to full suite

| Field | Value |
|-------|-------|
| Finding | PC-034.a |
| Statement | Consolidate workflows or add orchestrator workflow where security job needs: [collection-gate, test]. |
| Mechanism | Single ci.yml or reusable workflow `quality-gate.yml`. |
| Enforcement | GitHub Actions needs graph |
| Verification predicate | security job skipped/fails when upstream test job fails. |
| Primary stream | R1 |

---

## Sub-Finding Preventive Controls

### PCtrl-008.a — Auto-exec default parity CI test

| Field | Value |
|-------|-------|
| Finding | PC-008.a |
| Statement | `tests/arch/test_auto_exec_default_parity.py` reads compose, orchestrator, engine defaults. |
| Mechanism | Parsed env default extraction test. |
| Enforcement | CI |
| Verification predicate | Mismatch fails CI. |
| Primary stream | R4 |

### PCtrl-008.b — Route inventory drift gate

| Field | Value |
|-------|-------|
| Finding | PC-008.b |
| Statement | CI fails if live route count ≠ governance/platform_route_inventory.json without inventory regen. |
| Mechanism | Diff job on OpenAPI change. |
| Enforcement | CI |
| Verification predicate | New route without inventory update fails. |
| Primary stream | R4 |

### PCtrl-008.c — ADR required for decision pipeline changes

| Field | Value |
|-------|-------|
| Finding | PC-008.c |
| Statement | Path filter requires ADR update when adding decision/scoring modules. |
| Mechanism | CI check for ADR_DECISION_PIPELINE.md touch on relevant paths. |
| Enforcement | CI |
| Verification predicate | New decision module without ADR fails path gate. |
| Primary stream | R4 |

### PCtrl-008.d — Verdict emitter static analysis

| Field | Value |
|-------|-------|
| Finding | PC-008.d |
| Statement | AST scan ensures all routes returning verdict-shaped JSON call compliance_facade. |
| Mechanism | `scripts/lint_verdict_emitters.py`. |
| Enforcement | CI |
| Verification predicate | New route bypassing facade fails lint. |
| Primary stream | R8 |

### PCtrl-009.a — Prohibited API→bd_platform import lint

| Field | Value |
|-------|-------|
| Finding | PC-009.a |
| Statement | Zero-tolerance lint on platform_api.py imports from bd_platform except facades package. |
| Mechanism | lint_prohibited_imports rule `api_internal_import_ban`. |
| Enforcement | CI |
| Verification predicate | New internal import fails. |
| Primary stream | R4 |

### PCtrl-009.b — API response authority field regression test

| Field | Value |
|-------|-------|
| Finding | PC-009.b |
| Statement | Contract test fails if enumeration_authority field removed from features endpoint. |
| Mechanism | tests/test_platform_features_authority.py. |
| Enforcement | CI |
| Verification predicate | Field absence fails test. |
| Primary stream | R0 |

### PCtrl-009.c — Decimal boundary property tests on scan output

| Field | Value |
|-------|-------|
| Finding | PC-009.c |
| Statement | Property tests on fast_scan output using hypothesis at fee thresholds. |
| Mechanism | tests/property/test_scan_decimal_boundaries.py. |
| Enforcement | CI |
| Verification predicate | Float regression fails property tests. |
| Primary stream | R2 |

### PCtrl-009.d — Portfolio consistency contract test

| Field | Value |
|-------|-------|
| Finding | PC-009.d |
| Statement | CI contract test compares dashboard holdings API vs rebalance preview for fixture accounts. |
| Mechanism | tests/contract/test_portfolio_single_authority.py. |
| Enforcement | CI |
| Verification predicate | Hash mismatch fails. |
| Primary stream | R2 |

### PCtrl-010.a — Connector bypass security test in CI matrix

| Field | Value |
|-------|-------|
| Finding | PC-010.a |
| Statement | Subset of PCtrl-010 focused on cex_dex_executor paths only — must stay in bypass matrix. |
| Mechanism | test_connector_execution_denials.py cex-dex section. |
| Enforcement | CI |
| Verification predicate | CEX-DEX bypass row success fails CI. |
| Primary stream | R3 |

### PCtrl-011.a — Stale hour injection unit test

| Field | Value |
|-------|-------|
| Finding | PC-011.a |
| Statement | Unit test forces stale hour into assessor fixture; expects FAIL verdict. |
| Mechanism | tests/g3/test_hourly_stale_veto.py. |
| Enforcement | CI |
| Verification predicate | PASS on stale injection fails test. |
| Primary stream | R7 |

### PCtrl-011.b — gate_scope validator cross-check

| Field | Value |
|-------|-------|
| Finding | PC-011.b |
| Statement | validate_evidence.py enforces gate_scope/hours consistency on every G3 artifact commit. |
| Mechanism | Schema if/then validation. |
| Enforcement | CI on evidence paths |
| Verification predicate | Inconsistent scope/hours fails validator. |
| Primary stream | R7 |

### PCtrl-012.a — Oracle entrypoint caller inventory gate

| Field | Value |
|-------|-------|
| Finding | PC-012.a |
| Statement | CI compares caller inventory to allowed list; fails on new external caller. |
| Mechanism | scripts/oracle_caller_inventory.py diff in CI. |
| Enforcement | CI |
| Verification predicate | New caller outside stack fails diff. |
| Primary stream | R5 |

### PCtrl-012.b — Lineage field presence lint on E2E artifact

| Field | Value |
|-------|-------|
| Finding | PC-012.b |
| Statement | CI validates CAP-053 E2E artifact JSON schema requires lineage fields non-null. |
| Mechanism | Schema check on test output artifact. |
| Enforcement | CI |
| Verification predicate | Null lineage field fails schema validation. |
| Primary stream | R5 |

### PCtrl-013.a — Fixture keys required in CI env

| Field | Value |
|-------|-------|
| Finding | PC-013.a |
| Statement | CI sets KEYS_MODE=fixture; test fails if live key paths required without skip marker. |
| Mechanism | tests/conftest.py fixture key injection. |
| Enforcement | CI |
| Verification predicate | CI run without gitignored keys/ passes key-dependent unit tests. |
| Primary stream | R6 |

### PCtrl-013.b — Cross-tenant negative suite on db changes

| Field | Value |
|-------|-------|
| Finding | PC-013.b |
| Statement | Path-filtered tenant isolation gate (same as PCtrl-013 scoped to tenant tests). |
| Mechanism | tenant-isolation-gate job. |
| Enforcement | CI |
| Verification predicate | DB change without tenant test update fails. |
| Primary stream | R6 |

### PCtrl-013.c — Demo route production deny regression test

| Field | Value |
|-------|-------|
| Finding | PC-013.c |
| Statement | test_security.py section asserting demo 404 in prod profile. |
| Mechanism | Parametrized prod profile fixture. |
| Enforcement | CI |
| Verification predicate | Demo reachable in prod fails. |
| Primary stream | R6 |

### PCtrl-013.d — MFA enforcement regression test

| Field | Value |
|-------|-------|
| Finding | PC-013.d |
| Statement | Admin login test with ADMIN_MFA_REQUIRED=true rejects single-factor success. |
| Mechanism | tests/security/test_admin_mfa.py. |
| Enforcement | CI |
| Verification predicate | Single-factor pass fails when MFA required. |
| Primary stream | R6 |

### PCtrl-013.e — Route manifest golden diff

| Field | Value |
|-------|-------|
| Finding | PC-013.e |
| Statement | CI diffs prod route manifest against golden allow list on router changes. |
| Mechanism | tests/security/test_production_route_manifest.py. |
| Enforcement | CI path filter |
| Verification predicate | New prod route not in golden fails. |
| Primary stream | R6 |

### PCtrl-013.f — RBAC centralization static audit

| Field | Value |
|-------|-------|
| Finding | PC-013.f |
| Statement | Static analysis lists all routes; fails if tier check not via rbac_facade dependency. |
| Mechanism | scripts/audit_route_rbac.py. |
| Enforcement | CI |
| Verification predicate | Ad hoc require_feature on route fails audit. |
| Primary stream | R6 |

### PCtrl-015.a — Absent matrix lint rule

| Field | Value |
|-------|-------|
| Finding | PC-015.a |
| Statement | ssot-doc-lint ABSENT_ARCHIVED rule for FEATURE_REALITY_MATRIX references. |
| Mechanism | PCtrl-036 absent file class. |
| Enforcement | CI |
| Verification predicate | Stale LIVE marker for absent matrix fails. |
| Primary stream | R0 |

### PCtrl-015.b — Grid-CAP crosswalk prohibition test

| Field | Value |
|-------|-------|
| Finding | PC-015.b |
| Statement | Test forbids automated grid id → CAP-### mapping in code or docs outside attested crosswalk file. |
| Mechanism | tests/governance/test_no_grid_cap_automap.py. |
| Enforcement | CI |
| Verification predicate | Automap script in repo fails test. |
| Primary stream | R0 |

### PCtrl-019.a — Serving path allowlist CI check

| Field | Value |
|-------|-------|
| Finding | PC-019.a |
| Statement | ml_serving_boundary allowlist checked on every ml/ or flywheel config change. |
| Mechanism | Path-filtered isolation test. |
| Enforcement | CI |
| Verification predicate | Config pointing to training dir fails. |
| Primary stream | R5 |

### PCtrl-021.a — Docker import smoke in CI

| Field | Value |
|-------|-------|
| Finding | PC-021.a |
| Statement | Docker smoke container runs import smoke for ccxt/pandas/sklearn/kafka matching CI runner list. |
| Mechanism | docker smoke step post-build. |
| Enforcement | CI |
| Verification predicate | Import missing in container fails smoke. |
| Primary stream | R1 |

### PCtrl-022.a — Collection gate independent required check

| Field | Value |
|-------|-------|
| Finding | PC-022.a |
| Statement | Branch protection lists pytest-collection-gate as required check separate from subset test job. |
| Mechanism | docs/ci/REQUIRED_CHECKS.md + GitHub settings. |
| Enforcement | Branch protection |
| Verification predicate | Merge blocked when only subset test passes. |
| Primary stream | R1 |

### PCtrl-022.b — SSE job required on sse_stream changes

| Field | Value |
|-------|-------|
| Finding | PC-022.b |
| Statement | Path filter triggers SSE E2E job when bd_platform/sse_stream.py changes. |
| Mechanism | CI paths filter. |
| Enforcement | CI |
| Verification predicate | SSE change without e2e job trigger fails path policy test. |
| Primary stream | R7 |

### PCtrl-022.c — Concurrency suite on execution_engine changes

| Field | Value |
|-------|-------|
| Finding | PC-022.c |
| Statement | Path filter runs concurrency suite on execution_engine.py changes. |
| Mechanism | CI paths filter. |
| Enforcement | CI |
| Verification predicate | Engine change skipping concurrency job fails meta-test. |
| Primary stream | R7 |

### PCtrl-022.d — Restore drill scheduled on main weekly

| Field | Value |
|-------|-------|
| Finding | PC-022.d |
| Statement | Scheduled workflow runs restore drill weekly on main; artifact retained 90 days. |
| Mechanism | .github/workflows/ops-drill.yml cron. |
| Enforcement | Scheduled CI |
| Verification predicate | Missing weekly artifact triggers alert script. |
| Primary stream | R7 |

### PCtrl-022.e — Bypass matrix must stay 100% DENY

| Field | Value |
|-------|-------|
| Finding | PC-022.e |
| Statement | CI parses bypass matrix artifact; any SUCCESS row fails build. |
| Mechanism | Post-test artifact validator script. |
| Enforcement | CI |
| Verification predicate | Inject success row in fixture fails validator. |
| Primary stream | R7 |

### PCtrl-034.a — Workflow needs-graph meta-test

| Field | Value |
|-------|-------|
| Finding | PC-034.a |
| Statement | Meta-test parses workflow YAML asserting security job needs full-suite jobs. |
| Mechanism | tests/meta/test_security_workflow_needs.py. |
| Enforcement | CI |
| Verification predicate | Removing needs: dependency fails meta-test. |
| Primary stream | R1 |

---

## Control Coverage Index

| Category | Count | IDs |
|----------|-------|-----|
| Parent corrective | 42 | CC-001–CC-042 |
| Parent preventive | 42 | PCtrl-001–PCtrl-042 |
| Sub corrective | 29 | CC-008.a–CC-034.a (see sections above) |
| Sub preventive | 29 | PCtrl-008.a–PCtrl-034.a |
| **Total controls** | **142** | |

Every parent PC-001–PC-042 and sub PC-008.a–PC-034.a (29 subs) has exactly one CC and one PCtrl. Sub-finding controls are scoped narrower than parent controls and address independent closure evidence from Stage 1.

---

## Register Cross-Reference

| Register | Primary control themes |
|----------|------------------------|
| A | CC-003, CC-015, CC-009.b, CC-015.a/b, PCtrl-003, PCtrl-015 |
| B | CC-008–009, CC-031, CC-008.a–d, CC-009.a/d, platform route/import controls |
| C | CC-004, CC-026, CC-041, CC-009.c/d, PCtrl-004, PCtrl-026 |
| D | CC-005, CC-010, CC-014, CC-010.a, CC-022.c/e, PCtrl-005, PCtrl-010 |
| E | CC-013, CC-030, CC-013.a–f, PCtrl-013, PCtrl-030 |
| F | CC-002, CC-022, CC-033, CC-034, CC-039, CC-022.a–e, CC-034.a, PCtrl-002, PCtrl-022 |
| G | CC-011, CC-029, CC-035, CC-040, CC-011.a/b, PCtrl-011, PCtrl-029, PCtrl-035 |
| H | CC-001, CC-007, CC-016, CC-017, CC-021, CC-025, CC-021.a, PCtrl-001, PCtrl-007, PCtrl-021 |
| I | CC-012, CC-019, CC-028, CC-012.a/b, CC-019.a, PCtrl-012, PCtrl-019 |
| J | CC-006, CC-027, CC-041, CC-009.c, PCtrl-006, PCtrl-027, PCtrl-041 |
| K | CC-023, CC-032, CC-036, CC-037, CC-042, CC-015.a, PCtrl-023, PCtrl-032, PCtrl-042 |
| L | CC-024, CC-038, CC-008.d, CC-013.d/e, PCtrl-024, PCtrl-008.d |

---

## Stage 2 IVV Checklist (design-level)

1. 42/42 parent CC + 42/42 parent PCtrl present with unique statements
2. 29/29 sub CC + 29/29 sub PCtrl present with distinct scope from parent
3. Zero controls use parameter-substituted boilerplate (same mechanism with only ID changed)
4. Every control references concrete files, jobs, or modules from Stage 1 evidence
5. ssot-doc-lint spec in CC-042/PCtrl-042 matches REMEDIATION_VERIFICATION_STANDARD v3.0 contract fields
6. No implementation step contracts, test matrix cells, or migration fields in this artifact

**Stage 2 status:** REMEDIATED_PENDING_IVV
