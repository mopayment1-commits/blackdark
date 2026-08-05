# Corrective & Preventive Control Register — Stage 2

**Version:** 6.0 (Stage 2 — full 23-field control schema)  
**Date:** 2026-08-05  
**Validation branch:** `cursor/g2-g3-quality-gates-soak`  
**Validation commit:** `14112859677b68932c79b31d09a8aed49272794a`  
**Upstream baseline:** `ROOT_CAUSE_REGISTER.md` v4.0 (Stage 1 evidence-anchored)  
**Scope:** 142 unique controls (71 CC + 71 PCtrl) — design contracts only; no implementation steps.

## Stage 2 Notice

Each control below maps one-to-one to a Stage 1 finding (42 parents + 29 sub-findings). Template substitution, delegated closures, advisory-only preventive gates, and cross-control "same as" references are forbidden. Implementation (Stage 3), test matrix (Stage 4), and schema migrations (Stage 5) remain **SEMANTICALLY_INVALID — DO NOT EXECUTE** until independently verified.

## Control Field Schema (23 fields — all mandatory)

| # | Field name |
|---|------------|
| 1 | Control ID |
| 2 | Finding ID |
| 3 | Control type |
| 4 | Verified Stage 1 root cause addressed |
| 5 | Exact repository evidence files |
| 6 | Exact symbols/settings/routes/tables/functions |
| 7 | Current defective behavior |
| 8 | Required target behavior |
| 9 | Control mechanism |
| 10 | Enforcement point |
| 11 | Explicit affected files or bounded file families |
| 12 | Authority/owning bounded context |
| 13 | Positive impact |
| 14 | Potential negative impact |
| 15 | Other findings affected |
| 16 | Required downstream revalidation |
| 17 | Shared ownership or NONE |
| 18 | Objective acceptance criteria |
| 19 | Verification mechanism |
| 20 | Failure condition |
| 21 | Evidence output required |
| 22 | Architectural-decision compatibility |
| 23 | Stage-boundary declaration |

---


## Parent Corrective Controls (CC-001–CC-042)

### CC-001 — Lockfile becomes deploy authority

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | CC-001 |
| 2 | Finding ID | PC-001 |
| 3 | Control type | CORRECTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 validated systemic cause for PC-001: Identical pip install on two dates resolves different transitive versions. |
| 5 | Exact repository evidence files | `requirements.txt`, `requirements-prod.txt` |
| 6 | Exact symbols/settings/routes/tables/functions | pip install targets; no requirements-lock.txt |
| 7 | Current defective behavior | Identical pip install on two dates resolves different transitive versions. |
| 8 | Required target behavior | Single pip-tools resolved lockfile is sole runtime dependency authority for CI, Docker, local install. |
| 9 | Control mechanism | pip-compile generates requirements-lock.txt; CI lockfile-diff compares freeze to lock; Dockerfile installs from lock. |
| 10 | Enforcement point | CI merge gate |
| 11 | Explicit affected files or bounded file families | `requirements.txt`, `requirements-prod.txt`, `requirements-lock.txt`, `Dockerfile`, `.github/workflows/ci.yml` |
| 12 | Authority/owning bounded context | Build authority / Register H |
| 13 | Positive impact | Deterministic dependency replay at any commit. |
| 14 | Potential negative impact | Lock regen friction on bumps. |
| 15 | Other findings affected | PC-021, PC-033 |
| 16 | Required downstream revalidation | IVV dual-clone freeze parity |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register H |
| 18 | Objective acceptance criteria | Two clones produce identical sorted pip freeze; lock referenced in CI+Docker. |
| 19 | Verification mechanism | CI lockfile-diff + IVV clone test |
| 20 | Failure condition | Manifest merges without lock or freeze mismatch |
| 21 | Evidence output required | E-BUILD/lockfile-parity-report.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### CC-002 — Blocking full pytest collection job

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | CC-002 |
| 2 | Finding ID | PC-002 |
| 3 | Control type | CORRECTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 validated systemic cause for PC-002: CI runs only four modules with 90% coverage gate while tests/ has 34 test_*.py files. |
| 5 | Exact repository evidence files | .github/workflows/ci.yml, tests/ |
| 6 | Exact symbols/settings/routes/tables/functions | CI job test; launch_checklist.py::_run_pytest_quick |
| 7 | Current defective behavior | CI runs only four modules with 90% coverage gate while tests/ has 34 test_*.py files. |
| 8 | Required target behavior | Blocking CI job runs pytest --collect-only on entire tests/ and fails below stored baseline count. |
| 9 | Control mechanism | ci.yml job pytest-collection-gate; artifact data/ci/test_collection_baseline.json stores count+SHA. |
| 10 | Enforcement point | CI merge gate |
| 11 | Explicit affected files or bounded file families | .github/workflows/ci.yml, tests/, data/ci/test_collection_baseline.json |
| 12 | Authority/owning bounded context | QA gate / Register F |
| 13 | Positive impact | Regressions in 30+ modules cannot merge while CI green. |
| 14 | Potential negative impact | Slower CI on large test growth. |
| 15 | Other findings affected | PC-022.a, PC-039, PC-033 |
| 16 | Required downstream revalidation | IVV collection count vs baseline file |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register F |
| 18 | Objective acceptance criteria | PR cannot merge when collected count < baseline; baseline committed. |
| 19 | Verification mechanism | pytest --collect-only in CI gate |
| 20 | Failure condition | Collection count drops without baseline regen PR |
| 21 | Evidence output required | E-TEST/collection-gate-report.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### CC-003 — Separate roadmap grid from attested Feature Registry

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | CC-003 |
| 2 | Finding ID | PC-003 |
| 3 | Control type | CORRECTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 validated systemic cause for PC-003: Feature identity inferred from 40-point delivery tracker; no owner-attested FCP master list. |
| 5 | Exact repository evidence files | bd_platform/registry.py; docs/institutional/ (HISTORICAL_REFERENCE_NOT_PRESENT) |
| 6 | Exact symbols/settings/routes/tables/functions | FEATURE_MATRIX, feature_summary() |
| 7 | Current defective behavior | Feature identity inferred from 40-point delivery tracker; no owner-attested FCP master list. |
| 8 | Required target behavior | Owner-attested Feature Registry document; FEATURE_MATRIX demoted to non-authoritative roadmap in API. |
| 9 | Control mechanism | PROPOSED_ARTIFACT — STAGE 3 MUST DECIDE LOCATION: docs/institutional/FEATURE_REGISTRY_ATTESTATION.md; registry.py adds authority:roadmap_grid; remove F-### from grid endpoints. |
| 10 | Enforcement point | Docs + API contract + CI |
| 11 | Explicit affected files or bounded file families | bd_platform/registry.py, docs/institutional/FEATURE_REGISTRY_ATTESTATION.md (PROPOSED_ARTIFACT), dashboard.py /api/platform/features |
| 12 | Authority/owning bounded context | Feature authority / Register A |
| 13 | Positive impact | DEC-A attestation path opened; DD can distinguish roadmap vs live features. |
| 14 | Potential negative impact | Attestation blocked until OD-01 owner sign-off. |
| 15 | Other findings affected | PC-009.b, PC-015, PC-037 |
| 16 | Required downstream revalidation | IVV attestation scaffold review |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register A |
| 18 | Objective acceptance criteria | /api/platform/features includes non-authoritative marker; attestation file exists with owner placeholder. |
| 19 | Verification mechanism | API contract test + doc review |
| 20 | Failure condition | Grid emits F-### or lacks authority marker |
| 21 | Evidence output required | E-GOV/feature-registry-scaffold.json |
| 22 | Architectural-decision compatibility | DEC-A: APPLICABLE — establishes owner-attested enumeration separating grid from authority; DEC-B: APPLICABLE — crosswalk blocked until attestation closes; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### CC-004 — Implement canonical price APIs and restore UGP module

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | CC-004 |
| 2 | Finding ID | PC-004 |
| 3 | Control type | CORRECTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 validated systemic cause for PC-004: Execution and scan paths read hub prices directly; G2 script imports absent unified_global_price.compute_ugp. |
| 5 | Exact repository evidence files | live_book_hub.py, market_context.py, scripts/g2_live_ws_validation.py |
| 6 | Exact symbols/settings/routes/tables/functions | get_best_price; missing get_canonical_price, compute_ugp |
| 7 | Current defective behavior | Execution and scan paths read hub prices directly; G2 script imports absent unified_global_price.compute_ugp. |
| 8 | Required target behavior | Implement market_context.get_canonical_price(), get_canonical_venue_price(), unified_global_price.compute_ugp(); fix G2 import. |
| 9 | Control mechanism | PROPOSED_ARTIFACT — STAGE 3 MUST DECIDE LOCATION: unified_global_price.py + facade methods in market_context.py; migrate g2_live_ws_validation.py L263. |
| 10 | Enforcement point | Runtime + contract tests + CI |
| 11 | Explicit affected files or bounded file families | live_book_hub.py, market_context.py, unified_global_price.py (PROPOSED_ARTIFACT), scripts/g2_live_ws_validation.py, fast_scan_engine.py, execution_engine.py |
| 12 | Authority/owning bounded context | Price authority / Register C |
| 13 | Positive impact | Single price truth for execution and G2 evidence. |
| 14 | Potential negative impact | Migration effort across scan and execution paths. |
| 15 | Other findings affected | PC-026, PC-009.c, PC-041 |
| 16 | Required downstream revalidation | IVV G2 import resolution + contract tests |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register C |
| 18 | Objective acceptance criteria | G2 validation imports resolve; execution cannot read hub without freshness contract. |
| 19 | Verification mechanism | G2 script import test + contract tests |
| 20 | Failure condition | Hub read without canonical API on execution path |
| 21 | Evidence output required | E-PRICE/canonical-api-contract.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: APPLICABLE — implements canonical price APIs and UGP module per DEC-C binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### CC-005 — Consolidate execution authority in safety guard module

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | CC-005 |
| 2 | Finding ID | PC-005 |
| 3 | Control type | CORRECTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 validated systemic cause for PC-005: Three modules disagree on AUTO_EXECUTION_LOOP defaults; no single master switch with UNKNOWN=DENY. |
| 5 | Exact repository evidence files | execution_engine.py, execution_keys.py, startup_orchestrator.py, instant_alert_engine.py |
| 6 | Exact symbols/settings/routes/tables/functions | AUTO_EXECUTION_* env vars; missing EXECUTION_ENABLED, execution_safety_guard |
| 7 | Current defective behavior | Three modules disagree on AUTO_EXECUTION_LOOP defaults; no single master switch with UNKNOWN=DENY. |
| 8 | Required target behavior | Introduce execution_safety_guard.py with EXECUTION_ENABLED master switch; single reader for all AUTO_EXECUTION_* vars. |
| 9 | Control mechanism | PROPOSED_ARTIFACT — STAGE 3 MUST DECIDE LOCATION: execution_safety_guard.py consulted by execution_engine, startup_orchestrator, cex_dex_executor. |
| 10 | Enforcement point | Startup fail-closed + runtime |
| 11 | Explicit affected files or bounded file families | execution_engine.py, startup_orchestrator.py, execution_safety_guard.py (PROPOSED_ARTIFACT), docker-compose.yml |
| 12 | Authority/owning bounded context | Execution safety / Register D |
| 13 | Positive impact | Operator determines live-trading posture from one flag. |
| 14 | Potential negative impact | Refactor touches all execution entrypoints. |
| 15 | Other findings affected | PC-008.a, PC-010, PC-022.e |
| 16 | Required downstream revalidation | IVV startup conflict detection test |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register D |
| 18 | Objective acceptance criteria | No module outside guard reads AUTO_EXECUTION_* directly; prod profile aborts on conflict. |
| 19 | Verification mechanism | Static import scan + startup test |
| 20 | Failure condition | Split env reads persist outside guard |
| 21 | Evidence output required | E-EXEC/safety-guard-consolidation.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: APPLICABLE — implements EXECUTION_ENABLED master switch and UNKNOWN=DENY per DEC-D; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### CC-006 — Migrate financial SQLite REAL columns to NUMERIC

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | CC-006 |
| 2 | Finding ID | PC-006 |
| 3 | Control type | CORRECTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 validated systemic cause for PC-006: Cumulative fee/profit aggregates suffer IEEE-754 representation error at scale. |
| 5 | Exact repository evidence files | database.py |
| 6 | Exact symbols/settings/routes/tables/functions | DDL REAL on pricing_logs, evaluated_opportunities, oracle_predictions financial columns |
| 7 | Current defective behavior | Cumulative fee/profit aggregates suffer IEEE-754 representation error at scale. |
| 8 | Required target behavior | DDL upgrade converting all financial REAL columns to NUMERIC(p,s) with documented precision scale. |
| 9 | Control mechanism | Schema upgrade in database.py converting REAL to NUMERIC; representative precision tests at production scale. |
| 10 | Enforcement point | Schema validation + CI |
| 11 | Explicit affected files or bounded file families | database.py, db_upgrade.py (PROPOSED_ARTIFACT — STAGE 3 MUST DECIDE LOCATION) |
| 12 | Authority/owning bounded context | Financial safety / Register J |
| 13 | Positive impact | Institutional financial precision claims supportable. |
| 14 | Potential negative impact | Migration downtime and rollback complexity. |
| 15 | Other findings affected | PC-009.c, PC-041, PC-027 |
| 16 | Required downstream revalidation | IVV precision property tests at scale |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register J |
| 18 | Objective acceptance criteria | Zero REAL columns on financial tables post-upgrade; precision property tests pass. |
| 19 | Verification mechanism | Schema inspection + property tests |
| 20 | Failure condition | REAL persists on money columns |
| 21 | Evidence output required | E-DATA/decimal-migration-report.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### CC-007 — Canonical deployment-profile contract and boot graph

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | CC-007 |
| 2 | Finding ID | PC-007 |
| 3 | Control type | CORRECTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 validated systemic cause for PC-007: Same commit produces different background-service graphs by entry path; web vs all lifecycle divergence; launch_verify skips canonical runtime. |
| 5 | Exact repository evidence files | run_service.py, config.py, dashboard.py, microservices/lifecycle.py, Dockerfile, docker-compose.yml, launch_verify.bat |
| 6 | Exact symbols/settings/routes/tables/functions | MODES, SERVICE_MODE, lifespan, startup(), current_mode() |
| 7 | Current defective behavior | Same commit produces different background-service graphs by entry path; web vs all lifecycle divergence; launch_verify skips canonical runtime. |
| 8 | Required target behavior | Document and enforce canonical deployment-profile contract: modes, component ownership, startup, forbidden mixed modes, readiness, deployment parity, topology identity. |
| 9 | Control mechanism | PROPOSED_ARTIFACT — STAGE 3 MUST DECIDE LOCATION: docs/institutional/DEPLOYMENT_PROFILE_CONTRACT.md; startup self-check in run_service.py and dashboard.py logs signed graph hash. |
| 10 | Enforcement point | Startup audit + blocking CI topology validation |
| 11 | Explicit affected files or bounded file families | run_service.py, config.py, dashboard.py, microservices/lifecycle.py, Dockerfile, docker-compose.yml, launch_verify.bat, scripts/launch_verify.py |
| 12 | Authority/owning bounded context | Runtime topology / Register H, B |
| 13 | Positive impact | One answer to what runs in production per profile. |
| 14 | Potential negative impact | Profile matrix maintenance overhead. |
| 15 | Other findings affected | PC-031, PC-008.a, PC-016, PC-005 |
| 16 | Required downstream revalidation | IVV Docker+local+compose topology parity |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register H |
| 18 | Objective acceptance criteria | Architecture test asserts orchestrator invoked iff profile matrix says so; launch_verify starts canonical runtime or documents explicit exception. |
| 19 | Verification mechanism | Architecture test per profile + startup hash log |
| 20 | Failure condition | Mixed monolith/worker boot without profile declaration |
| 21 | Evidence output required | E-TOPO/deployment-profile-contract.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: APPLICABLE — defines canonical deployment profiles without P17 extraction |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### CC-008 — Composition root explicit opt-in flags per domain

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | CC-008 |
| 2 | Finding ID | PC-008 |
| 3 | Control type | CORRECTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 validated systemic cause for PC-008: HTTP readiness does not imply minimal safe runtime; heavy trading/ML domains start unless env overrides known. |
| 5 | Exact repository evidence files | startup_orchestrator.py, platform_api.py, dashboard.py |
| 6 | Exact symbols/settings/routes/tables/functions | run_background_startup, RuntimeState, platform_api.router |
| 7 | Current defective behavior | HTTP readiness does not imply minimal safe runtime; heavy trading/ML domains start unless env overrides known. |
| 8 | Required target behavior | Refactor run_background_startup so each domain requires explicit RUN_<DOMAIN> opt-in with safe defaults off for trading paths. |
| 9 | Control mechanism | Per-domain RUN_<DOMAIN> flags default false for execution/WS; composition manifest emitted at startup. |
| 10 | Enforcement point | Startup + CI |
| 11 | Explicit affected files or bounded file families | startup_orchestrator.py, config.py, dashboard.py |
| 12 | Authority/owning bounded context | Composition root / Register B |
| 13 | Positive impact | Minimal production footprint enforceable. |
| 14 | Potential negative impact | Developers must set explicit flags for full stack. |
| 15 | Other findings affected | PC-008.a, PC-008.b, PC-008.c, PC-008.d |
| 16 | Required downstream revalidation | IVV default-env minimal domain count |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register B |
| 18 | Objective acceptance criteria | Default env profile starts documented minimal set; auto-exec off without explicit flag. |
| 19 | Verification mechanism | Startup manifest capture test |
| 20 | Failure condition | Broad domains start on default env |
| 21 | Evidence output required | E-STARTUP/composition-manifest.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: APPLICABLE — governed opt-in aligns with P01-P16 platform activation boundaries |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### CC-009 — Split platform_api into P01-P16 facade routers

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | CC-009 |
| 2 | Finding ID | PC-009 |
| 3 | Control type | CORRECTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 validated systemic cause for PC-009: HTTP surface owned by monolithic router; overlaps P01/P02 registry boundaries. |
| 5 | Exact repository evidence files | platform_api.py, bd_platform/registry.py, dashboard.py |
| 6 | Exact symbols/settings/routes/tables/functions | APIRouter(prefix=/api/platform), FEATURE_MATRIX, 61 @router handlers |
| 7 | Current defective behavior | HTTP surface owned by monolithic router; overlaps P01/P02 registry boundaries. |
| 8 | Required target behavior | Decompose platform_api.py into per-platform routers bd_platform/routers/pXX_*.py with ownership metadata. |
| 9 | Control mechanism | bd_platform/routers/pXX_*.py pattern; platform_api.py thin aggregator; governance/platform_route_inventory.json artifact. |
| 10 | Enforcement point | Architecture + CI |
| 11 | Explicit affected files or bounded file families | platform_api.py, bd_platform/routers/ (PROPOSED_ARTIFACT family), dashboard.py |
| 12 | Authority/owning bounded context | Platform boundary / Register B |
| 13 | Positive impact | Platform map matches code ownership for DD. |
| 14 | Potential negative impact | Large refactor with merge conflict risk. |
| 15 | Other findings affected | PC-009.a, PC-009.b, PC-009.c, PC-009.d |
| 16 | Required downstream revalidation | IVV route inventory 1:1 P01-P16 |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register B |
| 18 | Objective acceptance criteria | Route inventory maps 1:1 to P01-P16; no orphaned handlers in monolith. |
| 19 | Verification mechanism | OpenAPI introspection + ownership map |
| 20 | Failure condition | Monolith route added without owner |
| 21 | Evidence output required | E-PLATFORM/route-ownership-map.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: APPLICABLE — enforces P01-P16 modular monolith router ownership |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### CC-010 — Mandatory authorize_execution before connector calls

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | CC-010 |
| 2 | Finding ID | PC-010 |
| 3 | Control type | CORRECTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 validated systemic cause for PC-010: Venue execution proceeds through connectors without unified risk/exposure/freeze gate. |
| 5 | Exact repository evidence files | bd_platform/cex_dex_executor.py, execution_engine.py, platform_api.py |
| 6 | Exact symbols/settings/routes/tables/functions | execute_cex_dex_opportunity, execute_order, _live_enabled |
| 7 | Current defective behavior | Venue execution proceeds through connectors without unified risk/exposure/freeze gate. |
| 8 | Required target behavior | Wrap all venue connector entrypoints with authorize_execution() consulting freeze, exposure, master switch. |
| 9 | Control mechanism | PROPOSED_ARTIFACT — STAGE 3 MUST DECIDE LOCATION: execution_authorization.py; cex_dex_executor and execute_order call guard before network I/O. |
| 10 | Enforcement point | Runtime fail-closed + CI |
| 11 | Explicit affected files or bounded file families | bd_platform/cex_dex_executor.py, execution_engine.py, execution_authorization.py (PROPOSED_ARTIFACT), platform_api.py |
| 12 | Authority/owning bounded context | Execution authorization / Register D |
| 13 | Positive impact | Institutional execution safety at connector boundary. |
| 14 | Potential negative impact | Latency from auth consult on every order. |
| 15 | Other findings affected | PC-005, PC-010.a, PC-022.e |
| 16 | Required downstream revalidation | IVV negative matrix 100% DENY |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register D |
| 18 | Objective acceptance criteria | Connector without auth raises ExecutionDenied; freeze state consulted. |
| 19 | Verification mechanism | Security negative tests + runtime guard |
| 20 | Failure condition | Live order without auth consult |
| 21 | Evidence output required | E-EXEC/connector-auth-wrap.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: APPLICABLE — mandatory authorize_execution before connectors per DEC-D; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### CC-011 — Encode gate_scope in G3 assessor output schema

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | CC-011 |
| 2 | Finding ID | PC-011 |
| 3 | Control type | CORRECTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 validated systemic cause for PC-011: 1-hour smoke and 24-hour institutional soak share assessor without gate_scope field; artifacts misread as institutional PASS. |
| 5 | Exact repository evidence files | scripts/g3_reliability_soak_test.py, FEATURE_001_G3_SOAK_TEST_REPORT.md |
| 6 | Exact symbols/settings/routes/tables/functions | TREND_MILESTONE_HOURS, hours_required, --hours |
| 7 | Current defective behavior | 1-hour smoke and 24-hour institutional soak share assessor without gate_scope field; artifacts misread as institutional PASS. |
| 8 | Required target behavior | Add mandatory gate_scope enum (PILOT or INSTITUTIONAL_24H) to G3 assessment JSON; reject institutional claims when scope is not INSTITUTIONAL_24H. |
| 9 | Control mechanism | scripts/g3_reliability_soak_test.py schema v2; schemas/g3_assessment.schema.json; CLI sets scope from --hours with min 24 for institutional. |
| 10 | Enforcement point | Evidence validator CI |
| 11 | Explicit affected files or bounded file families | scripts/g3_reliability_soak_test.py, schemas/g3_assessment.schema.json (PROPOSED_ARTIFACT), scripts/validate_evidence.py (PROPOSED_ARTIFACT) |
| 12 | Authority/owning bounded context | G3 evidence / Register G |
| 13 | Positive impact | Pilot vs institutional soak machine-distinguishable. |
| 14 | Potential negative impact | Short smoke runs cannot claim institutional gate. |
| 15 | Other findings affected | PC-011.a, PC-011.b, PC-029 |
| 16 | Required downstream revalidation | IVV schema validation on sample artifacts |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register G |
| 18 | Objective acceptance criteria | 1-hour run produces gate_scope:PILOT; 24-hour produces INSTITUTIONAL_24H; validator rejects mismatched claims. |
| 19 | Verification mechanism | Schema validator + assessor output inspection |
| 20 | Failure condition | Institutional claim without INSTITUTIONAL_24H scope |
| 21 | Evidence output required | E-G3/gate-scope-schema.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### CC-012 — Unify oracle inference stack under single entry module

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | CC-012 |
| 2 | Finding ID | PC-012 |
| 3 | Control type | CORRECTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 validated systemic cause for PC-012: Research, retrain, and integrity filtering are separate entrypoints without one inference/provenance stack. |
| 5 | Exact repository evidence files | research_lab.py, oracle_retrainer.py, oracle_integrity.py, api/routers/oracle.py |
| 6 | Exact symbols/settings/routes/tables/functions | build_research_lab_report, run_oracle_retrain_step, filter_live_predictions |
| 7 | Current defective behavior | Research, retrain, and integrity filtering are separate entrypoints without one inference/provenance stack. |
| 8 | Required target behavior | Consolidate behind oracle_inference_stack.py public API with provenance fields on every mutation. |
| 9 | Control mechanism | PROPOSED_ARTIFACT — STAGE 3 MUST DECIDE LOCATION: oracle_inference_stack.py facade wrapping research_lab, oracle_retrainer, oracle_integrity. |
| 10 | Enforcement point | Import lint + runtime + CI |
| 11 | Explicit affected files or bounded file families | research_lab.py, oracle_retrainer.py, oracle_integrity.py, oracle_inference_stack.py (PROPOSED_ARTIFACT), api/routers/oracle.py |
| 12 | Authority/owning bounded context | Oracle architecture / Register I |
| 13 | Positive impact | CAP-053 lineage contract enforceable. |
| 14 | Potential negative impact | Caller migration across research and oracle routes. |
| 15 | Other findings affected | PC-012.a, PC-012.b, PC-028 |
| 16 | Required downstream revalidation | IVV caller inventory zero legacy paths |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register I |
| 18 | Objective acceptance criteria | Single documented entrypoint; zero production callers outside stack module. |
| 19 | Verification mechanism | Static caller inventory + import lint |
| 20 | Failure condition | Parallel entrypoint reintroduced |
| 21 | Evidence output required | E-ORACLE/inference-stack-facade.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### CC-013 — Tenancy middleware and production isolation package

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | CC-013 |
| 2 | Finding ID | PC-013 |
| 3 | Control type | CORRECTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 validated systemic cause for PC-013: Multi-tenant isolation, MFA, production demo isolation not enforced as unified P11 contract. |
| 5 | Exact repository evidence files | .gitignore, auth_service.py, dashboard.py, production_guard.py, execution_keys.py |
| 6 | Exact symbols/settings/routes/tables/functions | keys/, TIER_FEATURES, evaluate_production_guard, B2B_DEMO_API_KEY |
| 7 | Current defective behavior | Multi-tenant isolation, MFA, production demo isolation not enforced as unified P11 contract. |
| 8 | Required target behavior | Implement tenant context middleware, fixture key mode, production demo deny, MFA gate, route manifest audit, P09 RBAC facade. |
| 9 | Control mechanism | PROPOSED_ARTIFACT family: tenant_context.py, production_route_filter.py, rbac_facade.py; fixture keys tests/fixtures/keys/; ADMIN_MFA_REQUIRED. |
| 10 | Enforcement point | Startup + middleware + CI |
| 11 | Explicit affected files or bounded file families | auth_service.py, dashboard.py, production_guard.py, tenant_context.py (PROPOSED_ARTIFACT), database.py |
| 12 | Authority/owning bounded context | Tenancy security / Register E |
| 13 | Positive impact | Enterprise-grade tenancy and production isolation. |
| 14 | Potential negative impact | Broad middleware refactor across routes. |
| 15 | Other findings affected | PC-013.a-f, PC-030 |
| 16 | Required downstream revalidation | IVV cross-tenant negative matrix |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register E |
| 18 | Objective acceptance criteria | Cross-tenant negatives fail; prod profile zero demo routes; MFA enforced when flag set. |
| 19 | Verification mechanism | Cross-tenant negative suite + startup audit |
| 20 | Failure condition | Cross-tenant read succeeds |
| 21 | Evidence output required | E-SEC/tenancy-isolation-report.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: APPLICABLE — P11 tenancy facade aligns with modular monolith boundaries |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### CC-014 — Persist execution authority and runtime task graph

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | CC-014 |
| 2 | Finding ID | PC-014 |
| 3 | Control type | CORRECTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 validated systemic cause for PC-014: Restart drops orchestrator task graph and execution loop state; recovery depends on implicit env reread. |
| 5 | Exact repository evidence files | startup_orchestrator.py, dashboard.py, execution_engine.py |
| 6 | Exact symbols/settings/routes/tables/functions | RuntimeState, app.state.runtime, module-level loop tasks |
| 7 | Current defective behavior | Restart drops orchestrator task graph and execution loop state; recovery depends on implicit env reread. |
| 8 | Required target behavior | Persist RuntimeState execution authority fields and critical task flags to durable store with reload on startup. |
| 9 | Control mechanism | execution_state table (PROPOSED_ARTIFACT schema); startup_orchestrator loads state before spawning tasks. |
| 10 | Enforcement point | Runtime + restart test + CI |
| 11 | Explicit affected files or bounded file families | startup_orchestrator.py, execution_engine.py, dashboard.py, execution_state schema (PROPOSED_ARTIFACT) |
| 12 | Authority/owning bounded context | Execution state / Register D |
| 13 | Positive impact | Execution authority survives process restart. |
| 14 | Potential negative impact | DB write latency on state transitions. |
| 15 | Other findings affected | PC-005, PC-022.c |
| 16 | Required downstream revalidation | IVV SIGTERM restart test |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register D |
| 18 | Objective acceptance criteria | Restart test shows freeze + loop authority restored from DB not env alone. |
| 19 | Verification mechanism | Integration restart test |
| 20 | Failure condition | In-memory-only authority after restart |
| 21 | Evidence output required | E-EXEC/persisted-state-report.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### CC-015 — SSOT taxonomy pointer and authority markers

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | CC-015 |
| 2 | Finding ID | PC-015 |
| 3 | Control type | CORRECTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 validated systemic cause for PC-015: Grid ids 1-40, tier flags, and plan audit strings coexist without authority marker; FEATURE_REALITY_MATRIX absent. |
| 5 | Exact repository evidence files | bd_platform/registry.py, auth_service.py, plan_audit.py |
| 6 | Exact symbols/settings/routes/tables/functions | FEATURE_MATRIX, TIER_FEATURES, plan audit feature list |
| 7 | Current defective behavior | Grid ids 1-40, tier flags, and plan audit strings coexist without authority marker; FEATURE_REALITY_MATRIX absent. |
| 8 | Required target behavior | Publish single SSOT pointer listing authoritative vs roadmap vs tier taxonomies with explicit non-equivalence. |
| 9 | Control mechanism | PROPOSED_ARTIFACT — STAGE 3 MUST DECIDE LOCATION: docs/institutional/CURRENT_PROGRAM_STATUS_POINTER.md with authority class per taxonomy source. |
| 10 | Enforcement point | ssot-doc-lint + CI |
| 11 | Explicit affected files or bounded file families | bd_platform/registry.py, auth_service.py, plan_audit.py, docs/institutional/CURRENT_PROGRAM_STATUS_POINTER.md (PROPOSED_ARTIFACT) |
| 12 | Authority/owning bounded context | Feature taxonomy / Register A, K |
| 13 | Positive impact | DD cites one taxonomy authority per layer. |
| 14 | Potential negative impact | Pointer maintenance on every taxonomy touch. |
| 15 | Other findings affected | PC-015.a, PC-015.b, PC-036, PC-023 |
| 16 | Required downstream revalidation | IVV three-taxonomy marker audit |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register A |
| 18 | Objective acceptance criteria | Pointer exists; three taxonomies labeled; no duplicate CURRENT_SSOT per class. |
| 19 | Verification mechanism | ssot-doc-lint + taxonomy marker test |
| 20 | Failure condition | Duplicate CURRENT_SSOT declarations |
| 21 | Evidence output required | E-GOV/taxonomy-pointer.json |
| 22 | Architectural-decision compatibility | DEC-A: APPLICABLE — separates attested enumeration from roadmap grid and tier views; DEC-B: APPLICABLE — crosswalk requires settled taxonomy authority; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### CC-016 — Unify health probe contract across boot paths

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | CC-016 |
| 2 | Finding ID | PC-016 |
| 3 | Control type | CORRECTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 validated systemic cause for PC-016: Container health and operator launch scripts validate different endpoints; non-run_service starts produce false unhealthy. |
| 5 | Exact repository evidence files | Dockerfile, health_sidecar.py, run_service.py, launch_verify.bat |
| 6 | Exact symbols/settings/routes/tables/functions | HEALTHCHECK, start_health_sidecar, HEALTH_PORT |
| 7 | Current defective behavior | Container health and operator launch scripts validate different endpoints; non-run_service starts produce false unhealthy. |
| 8 | Required target behavior | Make run_service.py sole Docker entry starting sidecar; align launch_verify to probe :8080 and :8180 or document web-only exception. |
| 9 | Control mechanism | Dockerfile ENTRYPOINT to run_service.py; launch_verify.py optional sidecar check; HEALTHCHECK documents port+100 rule. |
| 10 | Enforcement point | Docker CI smoke + operator docs |
| 11 | Explicit affected files or bounded file families | Dockerfile, health_sidecar.py, run_service.py, launch_verify.bat, scripts/launch_verify.py |
| 12 | Authority/owning bounded context | Deploy operations / Register H |
| 13 | Positive impact | Consistent health signal across Docker and operator paths. |
| 14 | Potential negative impact | launch_verify complexity for dual-port probe. |
| 15 | Other findings affected | PC-007, PC-031 |
| 16 | Required downstream revalidation | IVV container HEALTHCHECK pass |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register H |
| 18 | Objective acceptance criteria | Container HEALTHCHECK passes on standard boot; launch script documents profile-specific probe set. |
| 19 | Verification mechanism | Docker build smoke + HEALTHCHECK probe |
| 20 | Failure condition | HEALTHCHECK fails on canonical boot |
| 21 | Evidence output required | E-DEPLOY/health-probe-contract.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### CC-017 — Declare minimal vs full infra profiles

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | CC-017 |
| 2 | Finding ID | PC-017 |
| 3 | Control type | CORRECTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 validated systemic cause for PC-017: Staging compose includes Kafka/Vault while web-only deploy omits them; feature paths differ silently. |
| 5 | Exact repository evidence files | docker-compose.yml, bd_platform/kafka_bridge.py, production_guard.py |
| 6 | Exact symbols/settings/routes/tables/functions | kafka, redis, vault services; Kafka bridge module |
| 7 | Current defective behavior | Staging compose includes Kafka/Vault while web-only deploy omits them; feature paths differ silently. |
| 8 | Required target behavior | Document INFRA_PROFILE as minimal or full with explicit kafka/redis/vault requirements per feature. |
| 9 | Control mechanism | PROPOSED_ARTIFACT — STAGE 3 MUST DECIDE LOCATION: docs/institutional/INFRA_PROFILE_MATRIX.md; features declare hard vs soft infra dependency. |
| 10 | Enforcement point | Startup loud-fail or degrade-with-metric + CI |
| 11 | Explicit affected files or bounded file families | docker-compose.yml, production_guard.py, bd_platform/kafka_bridge.py, docs/institutional/INFRA_PROFILE_MATRIX.md (PROPOSED_ARTIFACT) |
| 12 | Authority/owning bounded context | Infrastructure / Register H |
| 13 | Positive impact | Explicit infra assumptions per deploy profile. |
| 14 | Potential negative impact | Feature code must declare infra deps. |
| 15 | Other findings affected | PC-007, PC-025 |
| 16 | Required downstream revalidation | IVV minimal vs full profile boot |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register H |
| 18 | Objective acceptance criteria | Minimal profile test proves defined degradation; full profile requires services up. |
| 19 | Verification mechanism | Profile boot tests |
| 20 | Failure condition | Silent no-op when kafka required |
| 21 | Evidence output required | E-INFRA/profile-matrix.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### CC-018 — Repair GAPS_COMPLETED links to existing docs

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | CC-018 |
| 2 | Finding ID | PC-018 |
| 3 | Control type | CORRECTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 validated systemic cause for PC-018: Navigation from gaps completed to authoritative program docs fails on clone; institutional tree absent. |
| 5 | Exact repository evidence files | docs/GAPS_COMPLETED.md; docs/institutional/ (HISTORICAL_REFERENCE_NOT_PRESENT) |
| 6 | Exact symbols/settings/routes/tables/functions | markdown links to institutional paths |
| 7 | Current defective behavior | Navigation from gaps completed to authoritative program docs fails on clone; institutional tree absent. |
| 8 | Required target behavior | Update docs/GAPS_COMPLETED.md to link only committed paths or mark targets PLANNED with tracking ids. |
| 9 | Control mechanism | Link audit pass; replace broken institutional links with pointer to CURRENT_PROGRAM_STATUS_POINTER.md. |
| 10 | Enforcement point | docs link-check CI |
| 11 | Explicit affected files or bounded file families | docs/GAPS_COMPLETED.md, docs/institutional/CURRENT_PROGRAM_STATUS_POINTER.md (PROPOSED_ARTIFACT) |
| 12 | Authority/owning bounded context | Documentation navigation / Register K |
| 13 | Positive impact | Governance navigation works on fresh clone. |
| 14 | Potential negative impact | Link maintenance on doc moves. |
| 15 | Other findings affected | PC-023, PC-042 |
| 16 | Required downstream revalidation | IVV full docs link scan |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register K |
| 18 | Objective acceptance criteria | Zero broken relative links from GAPS_COMPLETED on clone. |
| 19 | Verification mechanism | Automated link crawler |
| 20 | Failure condition | Broken institutional link remains |
| 21 | Evidence output required | E-DOC/link-audit-report.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### CC-019 — Training-serving path separation guard

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | CC-019 |
| 2 | Finding ID | PC-019 |
| 3 | Control type | CORRECTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 validated systemic cause for PC-019: Saturation guard protects alert economics but not training-data leakage into live-serving paths. |
| 5 | Exact repository evidence files | flywheel_saturation_guard.py, startup_orchestrator.py, ml/ |
| 6 | Exact symbols/settings/routes/tables/functions | _enabled, ML flywheel startup block |
| 7 | Current defective behavior | Saturation guard protects alert economics but not training-data leakage into live-serving paths. |
| 8 | Required target behavior | Extend ML safety to block serving loaders from reading training artifact directories. |
| 9 | Control mechanism | PROPOSED_ARTIFACT — STAGE 3 MUST DECIDE LOCATION: ml_serving_boundary.py path allowlist; anti-leakage test scanning data/models/ vs serving config. |
| 10 | Enforcement point | CI + runtime |
| 11 | Explicit affected files or bounded file families | flywheel_saturation_guard.py, ml/, ml_serving_boundary.py (PROPOSED_ARTIFACT), data/models/ |
| 12 | Authority/owning bounded context | ML governance / Register I |
| 13 | Positive impact | Training artifacts cannot reach serving paths. |
| 14 | Potential negative impact | Stricter serving path configuration. |
| 15 | Other findings affected | PC-019.a, PC-012 |
| 16 | Required downstream revalidation | IVV serving loader rejection test |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register I |
| 18 | Objective acceptance criteria | Serving loader rejects paths under training export dirs; misconfiguration fails test. |
| 19 | Verification mechanism | Path overlap scan + runtime loader test |
| 20 | Failure condition | Serving reads training export dir |
| 21 | Evidence output required | E-ML/serving-boundary-report.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### CC-020 — Extract dashboard composition to submodules

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | CC-020 |
| 2 | Finding ID | PC-020 |
| 3 | Control type | CORRECTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 validated systemic cause for PC-020: dashboard.py ~2398 lines concentrates composition; single-file blast radius for unrelated features. |
| 5 | Exact repository evidence files | dashboard.py |
| 6 | Exact symbols/settings/routes/tables/functions | lifespan, route registrations, FastAPI app |
| 7 | Current defective behavior | dashboard.py ~2398 lines concentrates composition; single-file blast radius for unrelated features. |
| 8 | Required target behavior | Split route registration into dashboard/routes/*.py package; lifespan remains thin dashboard.py; reduce below 1500 lines. |
| 9 | Control mechanism | dashboard/routes/*.py package (PROPOSED_ARTIFACT family); thin dashboard.py lifespan and router aggregation only. |
| 10 | Enforcement point | Blocking CI architecture lint |
| 11 | Explicit affected files or bounded file families | dashboard.py, dashboard/routes/ (PROPOSED_ARTIFACT family) |
| 12 | Authority/owning bounded context | Application composition / Register B |
| 13 | Positive impact | Parallel platform work with reduced merge conflicts. |
| 14 | Potential negative impact | Initial extraction effort without behavior change. |
| 15 | Other findings affected | PC-008, PC-030 |
| 16 | Required downstream revalidation | IVV import graph unchanged for external callers |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register B |
| 18 | Objective acceptance criteria | Line count below 1500; zero new inline route handlers in dashboard.py; all routes registered via dashboard/routes/. |
| 19 | Verification mechanism | Line count + AST route registration scan |
| 20 | Failure condition | dashboard.py grows with inline routes undetected |
| 21 | Evidence output required | E-ARCH/dashboard-extraction-report.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: APPLICABLE — physical module split reflects P01-P16 composition boundaries |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### CC-021 — Reconcile CI and Docker dependency manifests

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | CC-021 |
| 2 | Finding ID | PC-021 |
| 3 | Control type | CORRECTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 validated systemic cause for PC-021: CI installs dev requirements.txt; Docker copies prod manifest; import sets diverge. |
| 5 | Exact repository evidence files | requirements.txt, requirements-prod.txt, Dockerfile, .github/workflows/ci.yml |
| 6 | Exact symbols/settings/routes/tables/functions | pip install lines; COPY requirements-prod |
| 7 | Current defective behavior | CI installs dev requirements.txt; Docker copies prod manifest; import sets diverge. |
| 8 | Required target behavior | Unify dev/prod manifests via lockfile overlays; eliminate silent import skew between CI and Docker. |
| 9 | Control mechanism | manifest-reconcile CI job diffs resolved trees CI image vs Docker image for runtime deps. |
| 10 | Enforcement point | CI merge gate |
| 11 | Explicit affected files or bounded file families | requirements.txt, requirements-prod.txt, Dockerfile, .github/workflows/ci.yml |
| 12 | Authority/owning bounded context | Deploy reproducibility / Register H |
| 13 | Positive impact | Green CI implies deployable image import parity. |
| 14 | Potential negative impact | Reconcile job runtime on Docker builds. |
| 15 | Other findings affected | PC-001, PC-021.a |
| 16 | Required downstream revalidation | IVV import smoke both environments |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register H |
| 18 | Objective acceptance criteria | Resolved runtime dep diff == 0 between CI and Docker smoke import check. |
| 19 | Verification mechanism | Import smoke in CI and Docker |
| 20 | Failure condition | Non-zero import diff between CI and Docker |
| 21 | Evidence output required | E-BUILD/manifest-reconcile-report.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### CC-022 — Institutional test class package E2E concurrency DR bypass

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | CC-022 |
| 2 | Finding ID | PC-022 |
| 3 | Control type | CORRECTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 validated systemic cause for PC-022: Institutional quality claims SSE UI, concurrent execution, DR not continuously evidenced in CI. |
| 5 | Exact repository evidence files | .github/workflows/ci.yml, tests/, bd_platform/sse_stream.py |
| 6 | Exact symbols/settings/routes/tables/functions | CI jobs; absence of SSE E2E, concurrency, restore drill |
| 7 | Current defective behavior | Institutional quality claims SSE UI, concurrent execution, DR not continuously evidenced in CI. |
| 8 | Required target behavior | Add tests/e2e/, tests/concurrency/, tests/ops/ with blocking CI jobs per institutional test class. |
| 9 | Control mechanism | tests/e2e/, tests/concurrency/, tests/ops/ directories with blocking CI jobs and signed artifact outputs. |
| 10 | Enforcement point | CI blocking |
| 11 | Explicit affected files or bounded file families | tests/e2e/, tests/concurrency/, tests/ops/, .github/workflows/ci.yml |
| 12 | Authority/owning bounded context | Test architecture / Register F |
| 13 | Positive impact | Institutional test maturity continuously evidenced. |
| 14 | Potential negative impact | CI time increase from new test classes. |
| 15 | Other findings affected | PC-022.a-e, PC-002, PC-034 |
| 16 | Required downstream revalidation | IVV four test class artifact review |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register F |
| 18 | Objective acceptance criteria | Four test classes exist with signed artifact outputs referenced in program state. |
| 19 | Verification mechanism | Directory + CI job inventory |
| 20 | Failure condition | Institutional test class absent from CI |
| 21 | Evidence output required | E-TEST/institutional-test-package.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### CC-023 — Commit institutional SSOT scaffold

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | CC-023 |
| 2 | Finding ID | PC-023 |
| 3 | Control type | CORRECTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 validated systemic cause for PC-023: Authority documents cannot be discovered from single pointer; institutional tree absent. |
| 5 | Exact repository evidence files | docs/; docs/institutional/ (HISTORICAL_REFERENCE_NOT_PRESENT); CURRENT_PROGRAM_STATUS_POINTER.md (HISTORICAL_REFERENCE_NOT_PRESENT) |
| 6 | Exact symbols/settings/routes/tables/functions | CURRENT_PROGRAM_STATUS_POINTER.md (absent) |
| 7 | Current defective behavior | Authority documents cannot be discovered from single pointer; institutional tree absent. |
| 8 | Required target behavior | Create docs/institutional/ tree with CURRENT_PROGRAM_STATUS_POINTER.md as navigation root. |
| 9 | Control mechanism | docs/institutional/ scaffold commit; pointer links governance stubs with authority class required. |
| 10 | Enforcement point | ssot-doc-lint + CI |
| 11 | Explicit affected files or bounded file families | docs/institutional/ (PROPOSED_ARTIFACT tree), docs/institutional/CURRENT_PROGRAM_STATUS_POINTER.md (PROPOSED_ARTIFACT) |
| 12 | Authority/owning bounded context | SSOT navigation / Register K |
| 13 | Positive impact | Governance pack discoverable on clone. |
| 14 | Potential negative impact | Scaffold stubs require later attestation fill. |
| 15 | Other findings affected | PC-015, PC-036, PC-037, PC-042 |
| 16 | Required downstream revalidation | IVV pointer navigation walk |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register K |
| 18 | Objective acceptance criteria | Directory exists; pointer discoverable from repo root README or docs index. |
| 19 | Verification mechanism | Navigation hop count test |
| 20 | Failure condition | Pointer unreachable from README |
| 21 | Evidence output required | E-GOV/ssot-scaffold-commit.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### CC-024 — Single audit authority module

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | CC-024 |
| 2 | Finding ID | PC-024 |
| 3 | Control type | CORRECTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 validated systemic cause for PC-024: Audit and compliance consumers receive differently filtered views depending on import path. |
| 5 | Exact repository evidence files | oracle_integrity.py, database.py, weekly_report.py, regulatory_compliance_guard.py |
| 6 | Exact symbols/settings/routes/tables/functions | fetch_oracle_audit_stats, filter_live_predictions, apply_regulatory_compliance |
| 7 | Current defective behavior | Audit and compliance consumers receive differently filtered views depending on import path. |
| 8 | Required target behavior | Consolidate oracle audit, compliance filtering, regulatory verdict under audit_authority.py facade. |
| 9 | Control mechanism | PROPOSED_ARTIFACT — STAGE 3 MUST DECIDE LOCATION: audit_authority.py; consumers import through facade; include_synthetic default enforced. |
| 10 | Enforcement point | Import lint + invariant test + CI |
| 11 | Explicit affected files or bounded file families | oracle_integrity.py, database.py, weekly_report.py, audit_authority.py (PROPOSED_ARTIFACT) |
| 12 | Authority/owning bounded context | Audit authority / Register L |
| 13 | Positive impact | Single audit filter semantics for DD exports. |
| 14 | Potential negative impact | Facade migration across report generators. |
| 15 | Other findings affected | PC-008.d, PC-028 |
| 16 | Required downstream revalidation | IVV zero direct fetch_oracle_audit_stats outside facade |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register L |
| 18 | Objective acceptance criteria | Static analysis shows zero direct fetch_oracle_audit_stats from non-facade callers. |
| 19 | Verification mechanism | Static import scan + invariant test |
| 20 | Failure condition | Synthetic predictions in DD export |
| 21 | Evidence output required | E-AUDIT/audit-authority-facade.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### CC-025 — Fail-closed startup configuration validation

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | CC-025 |
| 2 | Finding ID | PC-025 |
| 3 | Control type | CORRECTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 validated systemic cause for PC-025: Misconfiguration reaches live HTTP and background tasks; orchestrator logs and skips on exceptions. |
| 5 | Exact repository evidence files | config.py, startup_orchestrator.py, production_guard.py |
| 6 | Exact symbols/settings/routes/tables/functions | env reads; evaluate_production_guard |
| 7 | Current defective behavior | Misconfiguration reaches live HTTP and background tasks; orchestrator logs and skips on exceptions. |
| 8 | Required target behavior | Abort HTTP bind and background startup when required env/config invalid for active profile. |
| 9 | Control mechanism | PROPOSED_ARTIFACT — STAGE 3 MUST DECIDE LOCATION: config_validator.py before uvicorn bind; production_guard escalates to exit ≠0 in prod. |
| 10 | Enforcement point | Startup hard abort |
| 11 | Explicit affected files or bounded file families | config.py, startup_orchestrator.py, production_guard.py, config_validator.py (PROPOSED_ARTIFACT) |
| 12 | Authority/owning bounded context | Configuration startup / Register H, D |
| 13 | Positive impact | Unsafe partial configs cannot serve traffic. |
| 14 | Potential negative impact | Stricter prod env requirements. |
| 15 | Other findings affected | PC-017, PC-007 |
| 16 | Required downstream revalidation | IVV missing prod env exit test |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register H |
| 18 | Objective acceptance criteria | Missing required prod env causes process exit; partial orchestrator skip eliminated for critical domains. |
| 19 | Verification mechanism | Startup abort integration test |
| 20 | Failure condition | HTTP binds with invalid prod config |
| 21 | Evidence output required | E-CONFIG/fail-closed-startup.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### CC-026 — Execution-grade price freshness contract

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | CC-026 |
| 2 | Finding ID | PC-026 |
| 3 | Control type | CORRECTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 validated systemic cause for PC-026: Scan engines use stale hub rows; REST fallback lacks execution-authority freshness gate. |
| 5 | Exact repository evidence files | market_context.py, fast_scan_engine.py, live_book_hub.py |
| 6 | Exact symbols/settings/routes/tables/functions | probe_price_sources, get_best_price, require_fresh |
| 7 | Current defective behavior | Scan engines use stale hub rows; REST fallback lacks execution-authority freshness gate. |
| 8 | Required target behavior | Bind scan and execution to canonical price freshness thresholds; reject stale hub rows for authorization. |
| 9 | Control mechanism | Extend DEC-C APIs with max_age_ms; fast_scan_engine requires fresh canonical prices only. |
| 10 | Enforcement point | Runtime + contract tests + CI |
| 11 | Explicit affected files or bounded file families | market_context.py, fast_scan_engine.py, live_book_hub.py, unified_global_price.py (PROPOSED_ARTIFACT) |
| 12 | Authority/owning bounded context | Price freshness / Register C |
| 13 | Positive impact | False arbitrage signals during feed lag eliminated. |
| 14 | Potential negative impact | Stricter scan may reduce opportunity count. |
| 15 | Other findings affected | PC-004, PC-009.c |
| 16 | Required downstream revalidation | IVV stale injection test |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register C |
| 18 | Objective acceptance criteria | Scan with stale feed produces zero authorized opportunities; G2 fails closed on stale age. |
| 19 | Verification mechanism | Contract test with injected stale timestamps |
| 20 | Failure condition | Stale price authorizes execution |
| 21 | Evidence output required | E-PRICE/freshness-contract.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: APPLICABLE — freshness contract binds to canonical price authority; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### CC-027 — Domain-seam database module split plan

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | CC-027 |
| 2 | Finding ID | PC-027 |
| 3 | Control type | CORRECTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 validated systemic cause for PC-027: Single database.py hosts all DDL and CRUD; financial migration requires high-churn monolith edits. |
| 5 | Exact repository evidence files | database.py |
| 6 | Exact symbols/settings/routes/tables/functions | module-level CRUD functions (~3700+ lines) |
| 7 | Current defective behavior | Single database.py hosts all DDL and CRUD; financial migration requires high-churn monolith edits. |
| 8 | Required target behavior | Split into db_financial, db_oracle, db_auth behind stable facade preserving import paths. |
| 9 | Control mechanism | Phased extraction with re-export facade; financial DDL isolated to db_financial.py. |
| 10 | Enforcement point | Import graph test + CI |
| 11 | Explicit affected files or bounded file families | database.py, db_financial.py (PROPOSED_ARTIFACT), db_oracle.py (PROPOSED_ARTIFACT), db_auth.py (PROPOSED_ARTIFACT) |
| 12 | Authority/owning bounded context | Database architecture / Register J |
| 13 | Positive impact | Bounded migrations per domain seam. |
| 14 | Potential negative impact | Transitional facade maintenance. |
| 15 | Other findings affected | PC-006, PC-013.b |
| 16 | Required downstream revalidation | IVV financial DDL isolation proof |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register J |
| 18 | Objective acceptance criteria | Financial DDL changes isolated to db_financial.py; monolith line count reduced ≥30%. |
| 19 | Verification mechanism | Import graph + line count analysis |
| 20 | Failure condition | Monolith grows unbounded |
| 21 | Evidence output required | E-DATA/db-seam-split-plan.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### CC-028 — Prohibited oracle import lint

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | CC-028 |
| 2 | Finding ID | PC-028 |
| 3 | Control type | CORRECTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 validated systemic cause for PC-028: New oracle callers added without review; cap047_oracle.py facade absent; no lint tooling. |
| 5 | Exact repository evidence files | market_context.py, voice_service.py, research_lab.py, api/routers/oracle.py |
| 6 | Exact symbols/settings/routes/tables/functions | various oracle/research imports |
| 7 | Current defective behavior | New oracle callers added without review; cap047_oracle.py facade absent; no lint tooling. |
| 8 | Required target behavior | Add scripts/lint_prohibited_imports.py blocking direct oracle DB helpers outside approved facade list. |
| 9 | Control mechanism | scripts/lint_prohibited_imports.py (PROPOSED_ARTIFACT) CI job scanning import graph against allow list. |
| 10 | Enforcement point | CI merge gate |
| 11 | Explicit affected files or bounded file families | market_context.py, research_lab.py, api/routers/oracle.py, scripts/lint_prohibited_imports.py (PROPOSED_ARTIFACT) |
| 12 | Authority/owning bounded context | Oracle import governance / Register I |
| 13 | Positive impact | Oracle caller additions require architectural review. |
| 14 | Potential negative impact | Allow list maintenance overhead. |
| 15 | Other findings affected | PC-012, PC-024 |
| 16 | Required downstream revalidation | IVV burn-down to zero violations |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register I |
| 18 | Objective acceptance criteria | Lint runs in CI; violations enumerated with burn-down to zero. |
| 19 | Verification mechanism | Import graph scan |
| 20 | Failure condition | Unlisted oracle import merges |
| 21 | Evidence output required | E-ORACLE/import-lint-report.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### CC-029 — Evidence JSON schema validators in CI

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | CC-029 |
| 2 | Finding ID | PC-029 |
| 3 | Control type | CORRECTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 validated systemic cause for PC-029: G3/G2 evidence lacks checked-in JSON schema or CI validator; validate_evidence.py absent. |
| 5 | Exact repository evidence files | scripts/g3_reliability_soak_test.py, data/g2_validation_logs/ |
| 6 | Exact symbols/settings/routes/tables/functions | assessment output structure; JSON log files |
| 7 | Current defective behavior | G3/G2 evidence lacks checked-in JSON schema or CI validator; validate_evidence.py absent. |
| 8 | Required target behavior | Check in JSON schemas for G2/G3; CI validates artifacts on PR when evidence files change. |
| 9 | Control mechanism | schemas/g2_log.schema.json, schemas/g3_assessment.schema.json (PROPOSED_ARTIFACT); scripts/validate_evidence.py (PROPOSED_ARTIFACT). |
| 10 | Enforcement point | CI merge gate |
| 11 | Explicit affected files or bounded file families | schemas/, scripts/validate_evidence.py (PROPOSED_ARTIFACT), data/g2_validation_logs/, scripts/g3_reliability_soak_test.py |
| 12 | Authority/owning bounded context | Evidence schema / Register G |
| 13 | Positive impact | Evidence artifacts machine-validatable on commit. |
| 14 | Potential negative impact | Schema churn on harness evolution. |
| 15 | Other findings affected | PC-011, PC-040 |
| 16 | Required downstream revalidation | IVV validator on sample artifacts |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register G |
| 18 | Objective acceptance criteria | Unversioned G2 log fails validation; G3 output validates against schema v2. |
| 19 | Verification mechanism | JSON schema validation |
| 20 | Failure condition | Unschema'd evidence merges |
| 21 | Evidence output required | E-EVIDENCE/schema-validator-report.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### CC-030 — Production guard filters route mounting

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | CC-030 |
| 2 | Finding ID | PC-030 |
| 3 | Control type | CORRECTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 validated systemic cause for PC-030: Production guard checks infra only; demo/dev routes mount unconditionally at import. |
| 5 | Exact repository evidence files | production_guard.py, dashboard.py, platform_api.py |
| 6 | Exact symbols/settings/routes/tables/functions | evaluate_production_guard, route includes |
| 7 | Current defective behavior | Production guard checks infra only; demo/dev routes mount unconditionally at import. |
| 8 | Required target behavior | Extend production_guard.py to block or unmount dev/demo routes when ENV=production. |
| 9 | Control mechanism | Route registry filter at FastAPI init based on profile; integrates production route manifest. |
| 10 | Enforcement point | Startup route filter + CI |
| 11 | Explicit affected files or bounded file families | production_guard.py, dashboard.py, platform_api.py, production_route_filter.py (PROPOSED_ARTIFACT) |
| 12 | Authority/owning bounded context | Production isolation / Register E |
| 13 | Positive impact | Demo routes absent in production profile. |
| 14 | Potential negative impact | Route filter complexity at init. |
| 15 | Other findings affected | PC-013.c, PC-013.e |
| 16 | Required downstream revalidation | IVV prod OpenAPI diff |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register E |
| 18 | Objective acceptance criteria | Production profile OpenAPI spec excludes demo/debug routes. |
| 19 | Verification mechanism | OpenAPI route inventory diff |
| 20 | Failure condition | Demo route reachable in ENV=production |
| 21 | Evidence output required | E-SEC/production-route-filter.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### CC-031 — Canonical deployment-profile contract eliminating competing boot modes

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | CC-031 |
| 2 | Finding ID | PC-031 |
| 3 | Control type | CORRECTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 validated systemic cause for PC-031: Competing monolith/worker boot paths; SERVICE_MODE defaults diverge; web/all lifecycle split; launch_verify does not start canonical runtime. |
| 5 | Exact repository evidence files | microservices/, docker-compose.yml, docs/MICROSERVICES_ARCHITECTURE.md, run_service.py, config.py, dashboard.py, launch_verify.bat |
| 6 | Exact symbols/settings/routes/tables/functions | worker_app.py, lifecycle.startup, SERVICE_MODE, MODES, compose scale directives |
| 7 | Current defective behavior | Competing monolith/worker boot paths; SERVICE_MODE defaults diverge; web/all lifecycle split; launch_verify does not start canonical runtime. |
| 8 | Required target behavior | Define canonical deployment-profile contract: modes, component ownership, startup sequence, forbidden mixed modes, readiness probes, deployment parity, runtime topology identity. |
| 9 | Control mechanism | PROPOSED_ARTIFACT — STAGE 3 MUST DECIDE LOCATION: docs/institutional/DEPLOYMENT_PROFILE_CONTRACT.md binding DEC-E worker modes as deployment profiles not P17 splits; amend MICROSERVICES_ARCHITECTURE.md; launch_verify invokes run_service.py canonical path. |
| 10 | Enforcement point | Blocking CI topology validation + startup audit |
| 11 | Explicit affected files or bounded file families | microservices/, docker-compose.yml, run_service.py, config.py, dashboard.py, microservices/lifecycle.py, Dockerfile, launch_verify.bat, scripts/launch_verify.py, docs/MICROSERVICES_ARCHITECTURE.md |
| 12 | Authority/owning bounded context | Deployment topology / Register B |
| 13 | Positive impact | Architecture story unified: logical P01-P16 monolith with optional physical worker replication. |
| 14 | Potential negative impact | Compose scale-out docs require contract maintenance. |
| 15 | Other findings affected | PC-007, PC-016, PC-008.a |
| 16 | Required downstream revalidation | IVV five-target topology matrix all green |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register B |
| 18 | Objective acceptance criteria | Doc states no P17; test forbids undocumented platform packages; launch_verify starts canonical runtime or documents explicit web-only exception with topology hash. |
| 19 | Verification mechanism | Five-target topology test matrix + startup hash log |
| 20 | Failure condition | Dual-mode boot undetected |
| 21 | Evidence output required | E-TOPO/deployment-profile-contract-v2.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: APPLICABLE — clarifies worker modes as deployment profiles within P01-P16 monolith not P17 extraction |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### CC-032 — Create Wave 2 navigation index navigation-only

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | CC-032 |
| 2 | Finding ID | PC-032 |
| 3 | Control type | CORRECTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 validated systemic cause for PC-032: Wave 2 reference material has no mandated navigation index in repo. |
| 5 | Exact repository evidence files | WAVE2_MASTER_REFERENCE_INDEX.md (HISTORICAL_REFERENCE_NOT_PRESENT) |
| 6 | Exact symbols/settings/routes/tables/functions | (file absent) |
| 7 | Current defective behavior | Wave 2 reference material has no mandated navigation index in repo. |
| 8 | Required target behavior | Commit WAVE2_MASTER_REFERENCE_INDEX.md as navigation-only index without authority declarations. |
| 9 | Control mechanism | PROPOSED_ARTIFACT — STAGE 3 MUST DECIDE LOCATION: WAVE2_MASTER_REFERENCE_INDEX.md with authority:navigation_only header. |
| 10 | Enforcement point | ssot-doc-lint CI |
| 11 | Explicit affected files or bounded file families | WAVE2_MASTER_REFERENCE_INDEX.md (PROPOSED_ARTIFACT) |
| 12 | Authority/owning bounded context | Documentation navigation / Register K |
| 13 | Positive impact | Wave 2 docs navigable without false authority. |
| 14 | Potential negative impact | Index curation overhead. |
| 15 | Other findings affected | PC-023, PC-042 |
| 16 | Required downstream revalidation | IVV lint confirms no CURRENT_SSOT in index |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register K |
| 18 | Objective acceptance criteria | File exists; lint confirms no CURRENT_SSOT marker in index. |
| 19 | Verification mechanism | ssot-doc-lint rule scan |
| 20 | Failure condition | Index declares live authority |
| 21 | Evidence output required | E-DOC/wave2-index-scaffold.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### CC-033 — Orchestrate security workflow after full suite

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | CC-033 |
| 2 | Finding ID | PC-033 |
| 3 | Control type | CORRECTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 validated systemic cause for PC-033: Security workflow passes independently of main CI full-suite success. |
| 5 | Exact repository evidence files | .github/workflows/security.yml, .github/workflows/ci.yml |
| 6 | Exact symbols/settings/routes/tables/functions | separate workflow jobs |
| 7 | Current defective behavior | Security workflow passes independently of main CI full-suite success. |
| 8 | Required target behavior | Merge or chain security workflow so security job requires main CI full-suite success. |
| 9 | Control mechanism | Single ci.yml with security job needs: [pytest-collection-gate, test] OR docs/ci/REQUIRED_CHECKS.md with org policy. |
| 10 | Enforcement point | GitHub required checks |
| 11 | Explicit affected files or bounded file families | .github/workflows/security.yml, .github/workflows/ci.yml, docs/ci/REQUIRED_CHECKS.md (PROPOSED_ARTIFACT) |
| 12 | Authority/owning bounded context | CI orchestration / Register F |
| 13 | Positive impact | Combined green status implies full regression health. |
| 14 | Potential negative impact | Workflow consolidation effort. |
| 15 | Other findings affected | PC-002, PC-034, PC-034.a |
| 16 | Required downstream revalidation | IVV security job dependency graph |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register F |
| 18 | Objective acceptance criteria | Security job cannot succeed when collection gate fails; documented in REQUIRED_CHECKS. |
| 19 | Verification mechanism | Workflow needs graph inspection |
| 20 | Failure condition | Security passes with failing collection gate |
| 21 | Evidence output required | E-CI/workflow-orchestration.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### CC-034 — Security evidence coupling artifact

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | CC-034 |
| 2 | Finding ID | PC-034 |
| 3 | Control type | CORRECTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 validated systemic cause for PC-034: Security subset pass claims decoupled from full regression health. |
| 5 | Exact repository evidence files | tests/test_security.py, .github/workflows/ci.yml, .github/workflows/security.yml |
| 6 | Exact symbols/settings/routes/tables/functions | pytest selections |
| 7 | Current defective behavior | Security subset pass claims decoupled from full regression health. |
| 8 | Required target behavior | Publish CI evidence bundle linking security test results to full-suite status in one signed JSON per run. |
| 9 | Control mechanism | E-CI/combined_quality_report.json (PROPOSED_ARTIFACT path) emitted by orchestrated pipeline with both job outcomes. |
| 10 | Enforcement point | CI artifact + branch protection |
| 11 | Explicit affected files or bounded file families | .github/workflows/ci.yml, .github/workflows/security.yml, E-CI/combined_quality_report.json (PROPOSED_ARTIFACT) |
| 12 | Authority/owning bounded context | CI evidence / Register F, L |
| 13 | Positive impact | DD interprets security pass only with full-suite context. |
| 14 | Potential negative impact | Artifact storage and signing overhead. |
| 15 | Other findings affected | PC-033, PC-034.a |
| 16 | Required downstream revalidation | IVV main run artifact inspection |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register F |
| 18 | Objective acceptance criteria | Artifact shows security subset PASS only when full collection PASS on same run_id. |
| 19 | Verification mechanism | Artifact content validation on main runs |
| 20 | Failure condition | Security green with failing full suite |
| 21 | Evidence output required | E-CI/combined_quality_report.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### CC-035 — Platform-level G3 metrics instrumentation

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | CC-035 |
| 2 | Finding ID | PC-035 |
| 3 | Control type | CORRECTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 validated systemic cause for PC-035: G3 soak may lack platform-level metric completeness for institutional trends. |
| 5 | Exact repository evidence files | infra_metrics.py, bd_platform/infra_status.py |
| 6 | Exact symbols/settings/routes/tables/functions | service_mode reporting; platform infra endpoints |
| 7 | Current defective behavior | G3 soak may lack platform-level metric completeness for institutional trends. |
| 8 | Required target behavior | Add unified metrics hooks for platforms missing G3 soak sections; extend infra_metrics registry. |
| 9 | Control mechanism | Per-platform metric emitters in bd_platform/infra_status.py; G3 assessor reads completeness score. |
| 10 | Enforcement point | G3 harness blocking threshold |
| 11 | Explicit affected files or bounded file families | infra_metrics.py, bd_platform/infra_status.py, scripts/g3_reliability_soak_test.py |
| 12 | Authority/owning bounded context | Observability / Register G |
| 13 | Positive impact | Institutional soak dashboards complete across platforms. |
| 14 | Potential negative impact | Instrumentation work per platform module. |
| 15 | Other findings affected | PC-029, PC-011 |
| 16 | Required downstream revalidation | IVV G3 performance section review |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register G |
| 18 | Objective acceptance criteria | G3 performance section lists ≥90% platform coverage per defined platform list. |
| 19 | Verification mechanism | G3 assessor completeness score |
| 20 | Failure condition | Silent platforms in soak PASS |
| 21 | Evidence output required | E-G3/platform-metrics-registry.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### CC-036 — Taxonomy authority registry per layer with machine-readable metadata

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | CC-036 |
| 2 | Finding ID | PC-036 |
| 3 | Control type | CORRECTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 validated systemic cause for PC-036: Third taxonomy referenced in governance cannot be inspected; no single authority per layer; missing refs treated as live; navigation may redefine authority. |
| 5 | Exact repository evidence files | FEATURE_REALITY_MATRIX.md (HISTORICAL_REFERENCE_NOT_PRESENT), bd_platform/registry.py, auth_service.py, plan_audit.py |
| 6 | Exact symbols/settings/routes/tables/functions | FEATURE_MATRIX, TIER_FEATURES, plan audit list; absent audit matrix |
| 7 | Current defective behavior | Third taxonomy referenced in governance cannot be inspected; no single authority per layer; missing refs treated as live; navigation may redefine authority. |
| 8 | Required target behavior | Establish one taxonomy authority per layer with machine-readable metadata, historical resolution rules, renamed/removed handling; navigation cannot redefine authority. |
| 9 | Control mechanism | PROPOSED_ARTIFACT — STAGE 3 MUST DECIDE LOCATION: governance/taxonomy_authority_registry.json defining layer, authority_class, source_uri, historical_status per taxonomy; SSOT pointer cross-links only. |
| 10 | Enforcement point | Blocking CI ssot-doc-lint + schema validation |
| 11 | Explicit affected files or bounded file families | governance/taxonomy_authority_registry.json (PROPOSED_ARTIFACT), docs/institutional/CURRENT_PROGRAM_STATUS_POINTER.md (PROPOSED_ARTIFACT), bd_platform/registry.py, auth_service.py, plan_audit.py |
| 12 | Authority/owning bounded context | Feature taxonomy governance / Register A, K |
| 13 | Positive impact | Each taxonomy layer has exactly one authority; absent files marked HISTORICAL_NON_CURRENT not LIVE. |
| 14 | Potential negative impact | Registry maintenance on taxonomy changes. |
| 15 | Other findings affected | PC-015, PC-015.a, PC-036, PC-023 |
| 16 | Required downstream revalidation | IVV taxonomy integrity fixture violations |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register A |
| 18 | Objective acceptance criteria | Registry lists authority per layer; lint passes when pointer documents absence; fails on stale LIVE marker for absent FEATURE_REALITY_MATRIX. |
| 19 | Verification mechanism | Taxonomy registry schema + ssot-doc-lint blocking rules |
| 20 | Failure condition | Navigation doc declares CURRENT_SSOT for feature enumeration |
| 21 | Evidence output required | E-GOV/taxonomy-authority-registry.json |
| 22 | Architectural-decision compatibility | DEC-A: APPLICABLE — one enumeration authority per layer; DEC-B: APPLICABLE — crosswalk separated from roadmap and tier taxonomies; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### CC-037 — Attestation-bound owner enumeration capability platform registry publication

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | CC-037 |
| 2 | Finding ID | PC-037 |
| 3 | Control type | CORRECTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 validated systemic cause for PC-037: Marketing docs exceed attested scope; unattested/generated/capability-derived/navigation lists can become canonical enumeration. |
| 5 | Exact repository evidence files | docs/MKT_COMPETITIVE_MATRIX.md, docs/MKT_ICP.md, docs/MKT_MARKET_BARRIERS.md, bd_platform/registry.py |
| 6 | Exact symbols/settings/routes/tables/functions | marketing claims; FEATURE_MATRIX; docs/institutional/ (HISTORICAL_REFERENCE_NOT_PRESENT) |
| 7 | Current defective behavior | Marketing docs exceed attested scope; unattested/generated/capability-derived/navigation lists can become canonical enumeration. |
| 8 | Required target behavior | Bind attestation owner enumeration ↔ capability ↔ platform placement ↔ registry publication; block unattested lists becoming canonical. |
| 9 | Control mechanism | PROPOSED_ARTIFACT — STAGE 3 MUST DECIDE LOCATION: docs/institutional/FEATURE_REGISTRY_ATTESTATION.md with signed owner enumeration; governance/feature_publication_registry.json maps F-id to CAP primary and P-platform; MKT disclaimers link to attestation. |
| 10 | Enforcement point | Blocking CI attestation validator + ssot-doc-lint |
| 11 | Explicit affected files or bounded file families | docs/MKT_*.md, docs/institutional/FEATURE_REGISTRY_ATTESTATION.md (PROPOSED_ARTIFACT), governance/feature_publication_registry.json (PROPOSED_ARTIFACT), bd_platform/registry.py |
| 12 | Authority/owning bounded context | Feature attestation / Register A, K |
| 13 | Positive impact | External narrative bound to signed owner enumeration; capability-derived lists cannot become canonical. |
| 14 | Potential negative impact | Attestation workflow blocked until OD-01. |
| 15 | Other findings affected | PC-003, PC-015.b, PC-038 |
| 16 | Required downstream revalidation | IVV attestation signature and crosswalk separation test |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register A |
| 18 | Objective acceptance criteria | MKT docs contain disclaimer linking attestation; validator rejects grid-derived enumeration as canonical; publication registry matches attested F-ids only. |
| 19 | Verification mechanism | Attestation signature verify + publication registry diff |
| 20 | Failure condition | Grid ids published as attested F-ids |
| 21 | Evidence output required | E-GOV/attestation-binding-report.json |
| 22 | Architectural-decision compatibility | DEC-A: APPLICABLE — owner-attested enumeration is sole canonical source; DEC-B: APPLICABLE — crosswalk publication separated from marketing and navigation; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### CC-038 — Feature-to-legal disclaimer mapping table

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | CC-038 |
| 2 | Finding ID | PC-038 |
| 3 | Control type | CORRECTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 validated systemic cause for PC-038: Legal/compliance text drifts from feature capability claims; no feature-id linkage. |
| 5 | Exact repository evidence files | legal_content.py, regulatory_compliance_guard.py |
| 6 | Exact symbols/settings/routes/tables/functions | REGULATORY_DISCLAIMER, compliance verdict constants |
| 7 | Current defective behavior | Legal/compliance text drifts from feature capability claims; no feature-id linkage. |
| 8 | Required target behavior | Create LEGAL_FEATURE_MAP dict linking feature ids to regulatory disclaimer variants. |
| 9 | Control mechanism | LEGAL_FEATURE_MAP in legal_content.py; compliance guard consults map for feature-specific text. |
| 10 | Enforcement point | Test on feature rollout + CI |
| 11 | Explicit affected files or bounded file families | legal_content.py, regulatory_compliance_guard.py, docs/institutional/FEATURE_REGISTRY_ATTESTATION.md (PROPOSED_ARTIFACT) |
| 12 | Authority/owning bounded context | Legal compliance / Register L |
| 13 | Positive impact | Every live feature has matching disclaimer. |
| 14 | Potential negative impact | Legal review on each new feature id. |
| 15 | Other findings affected | PC-037, PC-003 |
| 16 | Required downstream revalidation | IVV legal map completeness scan |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register L |
| 18 | Objective acceptance criteria | Test asserts every attested live feature id has disclaimer entry. |
| 19 | Verification mechanism | Legal coverage unit test |
| 20 | Failure condition | Feature ships without disclaimer entry |
| 21 | Evidence output required | E-LEGAL/feature-legal-map.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### CC-039 — Regenerate pytest collection baseline artifact

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | CC-039 |
| 2 | Finding ID | PC-039 |
| 3 | Control type | CORRECTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 validated systemic cause for PC-039: Documented Wave 1 full regression count cannot be verified; wave1 file absent. |
| 5 | Exact repository evidence files | data/wave1_full_regression.txt (HISTORICAL_REFERENCE_NOT_PRESENT), tests/, .github/workflows/ci.yml |
| 6 | Exact symbols/settings/routes/tables/functions | (absent baseline file) |
| 7 | Current defective behavior | Documented Wave 1 full regression count cannot be verified; wave1 file absent. |
| 8 | Required target behavior | Generate data/ci/test_collection_baseline.json from current pytest --collect-only replacing absent wave1 file. |
| 9 | Control mechanism | CI job writes baseline on main; documents count provenance in artifact metadata. |
| 10 | Enforcement point | CI merge gate |
| 11 | Explicit affected files or bounded file families | data/ci/test_collection_baseline.json (PROPOSED_ARTIFACT), tests/, .github/workflows/ci.yml |
| 12 | Authority/owning bounded context | Test baseline / Register F |
| 13 | Positive impact | Automated regression drift detection restored. |
| 14 | Potential negative impact | Baseline regen PRs on intentional test removal. |
| 15 | Other findings affected | PC-002, PC-022.a |
| 16 | Required downstream revalidation | IVV baseline count ≥ current collection |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register F |
| 18 | Objective acceptance criteria | Baseline file committed with count ≥ current collection; wave1 dependency removed. |
| 19 | Verification mechanism | pytest --collect-only count compare |
| 20 | Failure condition | Test count drops silently |
| 21 | Evidence output required | E-TEST/collection-baseline.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### CC-040 — Add schema_version to G2 harness output

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | CC-040 |
| 2 | Finding ID | PC-040 |
| 3 | Control type | CORRECTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 validated systemic cause for PC-040: G2 JSON logs lack schema_version; cross-run comparison breaks silently on shape change. |
| 5 | Exact repository evidence files | data/g2_validation_logs/, scripts/g2_live_ws_validation.py |
| 6 | Exact symbols/settings/routes/tables/functions | JSON log structure |
| 7 | Current defective behavior | G2 JSON logs lack schema_version; cross-run comparison breaks silently on shape change. |
| 8 | Required target behavior | Emit schema_version g2.v1 in all new G2 JSON logs; validator rejects missing version. |
| 9 | Control mechanism | Update G2 validation scripts; schemas/g2_log.schema.json requires schema_version. |
| 10 | Enforcement point | Evidence validator CI |
| 11 | Explicit affected files or bounded file families | scripts/g2_live_ws_validation.py, data/g2_validation_logs/, schemas/g2_log.schema.json (PROPOSED_ARTIFACT) |
| 12 | Authority/owning bounded context | G2 evidence / Register G |
| 13 | Positive impact | G2 evidence cross-run comparable. |
| 14 | Potential negative impact | Retroactive tagging needed for stored logs. |
| 15 | Other findings affected | PC-029 |
| 16 | Required downstream revalidation | IVV validator on historical logs guidance |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register G |
| 18 | Objective acceptance criteria | New G2 run JSON contains schema_version; validator fails without it. |
| 19 | Verification mechanism | JSON schema validation |
| 20 | Failure condition | New G2 log without schema_version merges |
| 21 | Evidence output required | E-G2/schema-version-adoption.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### CC-041 — Decimal compute path for fee/profit hot loops

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | CC-041 |
| 2 | Finding ID | PC-041 |
| 3 | Control type | CORRECTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 validated systemic cause for PC-041: Authoritative profit/fee paths compute in float before persist; threshold comparisons subject to IEEE-754 error. |
| 5 | Exact repository evidence files | fee_matrix.py, fast_scan_engine.py, profit_fee_algorithms.py |
| 6 | Exact symbols/settings/routes/tables/functions | float arithmetic on bids/asks/fees/net profit |
| 7 | Current defective behavior | Authoritative profit/fee paths compute in float before persist; threshold comparisons subject to IEEE-754 error. |
| 8 | Required target behavior | Migrate fee_matrix.py, fast_scan_engine.py, profit_fee_algorithms.py to decimal.Decimal for authoritative comparisons before persist. |
| 9 | Control mechanism | Decimal types in hot path with documented quantization coordinated with database NUMERIC schema. |
| 10 | Enforcement point | CI property tests + lint |
| 11 | Explicit affected files or bounded file families | fee_matrix.py, fast_scan_engine.py, profit_fee_algorithms.py, database.py |
| 12 | Authority/owning bounded context | Financial compute / Register J |
| 13 | Positive impact | Exact decimal invariants on threshold boundaries provable. |
| 14 | Potential negative impact | Performance impact on scan hot loop. |
| 15 | Other findings affected | PC-006, PC-009.c |
| 16 | Required downstream revalidation | IVV property tests at 0.0001 USDT boundaries |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register J |
| 18 | Objective acceptance criteria | Property tests prove exact decimal invariants; no float casts on money paths. |
| 19 | Verification mechanism | Hypothesis property tests + AST lint |
| 20 | Failure condition | Float regression in money module |
| 21 | Evidence output required | E-DATA/decimal-compute-report.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### CC-042 — Implement ssot-doc-lint per verification standard

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | CC-042 |
| 2 | Finding ID | PC-042 |
| 3 | Control type | CORRECTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 validated systemic cause for PC-042: ssot-doc-lint specified but scripts/ssot_doc_lint.py not implemented; governance docs unvalidated. |
| 5 | Exact repository evidence files | docs/**/*.md, FEATURE_REALITY_MATRIX.md (HISTORICAL_REFERENCE_NOT_PRESENT), WAVE2_MASTER_REFERENCE_INDEX.md (HISTORICAL_REFERENCE_NOT_PRESENT) |
| 6 | Exact symbols/settings/routes/tables/functions | ssot-doc-lint contract in REMEDIATION_VERIFICATION_STANDARD v3.0 |
| 7 | Current defective behavior | ssot-doc-lint specified but scripts/ssot_doc_lint.py not implemented; governance docs unvalidated. |
| 8 | Required target behavior | Build scripts/ssot_doc_lint.py and tests/governance/test_ssot_doc_lint.py per REMEDIATION_VERIFICATION_STANDARD contract. |
| 9 | Control mechanism | scripts/ssot_doc_lint.py (PROPOSED_ARTIFACT) emitting E-GOV/ssot-lint-report.json with sha256; ci.yml job ssot-doc-lint before test. |
| 10 | Enforcement point | CI merge gate |
| 11 | Explicit affected files or bounded file families | scripts/ssot_doc_lint.py (PROPOSED_ARTIFACT), tests/governance/test_ssot_doc_lint.py (PROPOSED_ARTIFACT), docs/**/*.md |
| 12 | Authority/owning bounded context | SSOT governance / Register K |
| 13 | Positive impact | Governance doc violations blocked at merge. |
| 14 | Potential negative impact | Lint rule tuning as docs evolve. |
| 15 | Other findings affected | PC-015, PC-036, PC-037, PC-032, PC-018 |
| 16 | Required downstream revalidation | IVV fixture violation fail + clean pass |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register K |
| 18 | Objective acceptance criteria | Fixture violations fail lint; clean docs pass; report JSON includes sha256. |
| 19 | Verification mechanism | ssot-doc-lint fixture tests |
| 20 | Failure condition | Governance violation merges |
| 21 | Evidence output required | E-GOV/ssot-lint-report.json |
| 22 | Architectural-decision compatibility | DEC-A: APPLICABLE — lint enforces single enumeration authority declarations; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

---

## Parent Preventive Controls (PCtrl-001–PCtrl-042)

### PCtrl-001 — Lockfile drift blocking on manifest change

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | PCtrl-001 |
| 2 | Finding ID | PC-001 |
| 3 | Control type | PREVENTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 enabling condition for PC-001 recurrence: existing controls did not block reintroduction of Identical pip install on two dates resolves different transitive versions.. |
| 5 | Exact repository evidence files | `requirements.txt`, `requirements-prod.txt` |
| 6 | Exact symbols/settings/routes/tables/functions | pip install targets; no requirements-lock.txt |
| 7 | Current defective behavior | Without blocking gate, PC-001 defect pattern can return via refactor or config drift undetected in CI. |
| 8 | Required target behavior | PR changing semver ranges without synchronized lock update is blocked at merge. |
| 9 | Control mechanism | Blocking CI lockfile-diff job fails when requirements*.txt hash changes without lock update. |
| 10 | Enforcement point | GitHub required check on requirements paths |
| 11 | Explicit affected files or bounded file families | `requirements.txt`, `requirements-prod.txt`, `requirements-lock.txt`, `.github/workflows/ci.yml` |
| 12 | Authority/owning bounded context | Build authority / Register H preventive gate |
| 13 | Positive impact | Automated regression block for PC-001 closure criteria. |
| 14 | Potential negative impact | CI friction on related file changes. |
| 15 | Other findings affected | PC-021, PC-033 |
| 16 | Required downstream revalidation | IVV synthetic regression injection for PC-001 |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register H |
| 18 | Objective acceptance criteria | Synthetic PR with manifest-only change fails required check. |
| 19 | Verification mechanism | CI synthetic manifest PR test |
| 20 | Failure condition | Manifest-only PR merges green |
| 21 | Evidence output required | E-BUILD/lockfile-drift-block-log.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### PCtrl-002 — Meta-test guards CI subset regression

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | PCtrl-002 |
| 2 | Finding ID | PC-002 |
| 3 | Control type | PREVENTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 enabling condition for PC-002 recurrence: existing controls did not block reintroduction of CI runs only four modules with 90% coverage gate while tests/ has 34 test_*.py f. |
| 5 | Exact repository evidence files | .github/workflows/ci.yml, tests/ |
| 6 | Exact symbols/settings/routes/tables/functions | CI job test; launch_checklist.py::_run_pytest_quick |
| 7 | Current defective behavior | Without blocking gate, PC-002 defect pattern can return via refactor or config drift undetected in CI. |
| 8 | Required target behavior | Meta-test parses ci.yml and fails if collection gate removed or test module list shrinks without baseline update. |
| 9 | Control mechanism | tests/meta/test_ci_workflow_coverage.py asserts collection job presence and module list monotonicity. |
| 10 | Enforcement point | CI on workflow changes |
| 11 | Explicit affected files or bounded file families | .github/workflows/ci.yml, tests/meta/test_ci_workflow_coverage.py |
| 12 | Authority/owning bounded context | QA gate / Register F preventive gate |
| 13 | Positive impact | Automated regression block for PC-002 closure criteria. |
| 14 | Potential negative impact | CI friction on related file changes. |
| 15 | Other findings affected | PC-022.a, PC-039, PC-033 |
| 16 | Required downstream revalidation | IVV synthetic regression injection for PC-002 |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register F |
| 18 | Objective acceptance criteria | Removing collection job causes meta-test failure. |
| 19 | Verification mechanism | Meta-test workflow parse |
| 20 | Failure condition | Subset-only green merge allowed |
| 21 | Evidence output required | E-TEST/ci-meta-coverage-log.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### PCtrl-003 — Forbidden enumeration lint on feature endpoints

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | PCtrl-003 |
| 2 | Finding ID | PC-003 |
| 3 | Control type | PREVENTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 enabling condition for PC-003 recurrence: existing controls did not block reintroduction of Feature identity inferred from 40-point delivery tracker; no owner-attested FCP . |
| 5 | Exact repository evidence files | bd_platform/registry.py; docs/institutional/ (HISTORICAL_REFERENCE_NOT_PRESENT) |
| 6 | Exact symbols/settings/routes/tables/functions | FEATURE_MATRIX, feature_summary() |
| 7 | Current defective behavior | Without blocking gate, PC-003 defect pattern can return via refactor or config drift undetected in CI. |
| 8 | Required target behavior | ssot-doc-lint and API contract test forbid emitting F-### ids from grid; forbid CURRENT_SSOT in grid docs. |
| 9 | Control mechanism | tests/test_registry_not_enumeration_authority.py + ssot-doc-lint FORBIDDEN_ENUMERATION rule block grid authority claims. |
| 10 | Enforcement point | CI ssot-doc-lint merge gate |
| 11 | Explicit affected files or bounded file families | bd_platform/registry.py, tests/test_registry_not_enumeration_authority.py, scripts/ssot_doc_lint.py (PROPOSED_ARTIFACT) |
| 12 | Authority/owning bounded context | Feature authority / Register A preventive gate |
| 13 | Positive impact | Automated regression block for PC-003 closure criteria. |
| 14 | Potential negative impact | CI friction on related file changes. |
| 15 | Other findings affected | PC-009.b, PC-015, PC-037 |
| 16 | Required downstream revalidation | IVV synthetic regression injection for PC-003 |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register A |
| 18 | Objective acceptance criteria | Grid endpoint test fails if authority field removed or F-ids emitted. |
| 19 | Verification mechanism | CI lint + contract test |
| 20 | Failure condition | Grid treated as attested enumeration |
| 21 | Evidence output required | E-GOV/forbidden-enumeration-lint.json |
| 22 | Architectural-decision compatibility | DEC-A: APPLICABLE — establishes owner-attested enumeration separating grid from authority; DEC-B: APPLICABLE — crosswalk blocked until attestation closes; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### PCtrl-004 — Prohibited direct hub reads from execution modules

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | PCtrl-004 |
| 2 | Finding ID | PC-004 |
| 3 | Control type | PREVENTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 enabling condition for PC-004 recurrence: existing controls did not block reintroduction of Execution and scan paths read hub prices directly; G2 script imports absent unif. |
| 5 | Exact repository evidence files | live_book_hub.py, market_context.py, scripts/g2_live_ws_validation.py |
| 6 | Exact symbols/settings/routes/tables/functions | get_best_price; missing get_canonical_price, compute_ugp |
| 7 | Current defective behavior | Without blocking gate, PC-004 defect pattern can return via refactor or config drift undetected in CI. |
| 8 | Required target behavior | Import lint prohibits live_book_hub.get_best_price from execution_engine, fast_scan_engine, cex_dex_executor. |
| 9 | Control mechanism | scripts/lint_prohibited_imports.py rule price_direct_hub_ban fails new direct hub imports in execution modules. |
| 10 | Enforcement point | CI import lint merge gate |
| 11 | Explicit affected files or bounded file families | execution_engine.py, fast_scan_engine.py, bd_platform/cex_dex_executor.py, scripts/lint_prohibited_imports.py (PROPOSED_ARTIFACT) |
| 12 | Authority/owning bounded context | Price authority / Register C preventive gate |
| 13 | Positive impact | Automated regression block for PC-004 closure criteria. |
| 14 | Potential negative impact | CI friction on related file changes. |
| 15 | Other findings affected | PC-026, PC-009.c, PC-041 |
| 16 | Required downstream revalidation | IVV synthetic regression injection for PC-004 |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register C |
| 18 | Objective acceptance criteria | New direct get_best_price import in fast_scan_engine fails lint. |
| 19 | Verification mechanism | CI prohibited-import lint |
| 20 | Failure condition | Direct hub import added to execution module |
| 21 | Evidence output required | E-PRICE/hub-import-lint-report.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: APPLICABLE — implements canonical price APIs and UGP module per DEC-C binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### PCtrl-005 — Architecture test for execution env default parity

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | PCtrl-005 |
| 2 | Finding ID | PC-005 |
| 3 | Control type | PREVENTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 enabling condition for PC-005 recurrence: existing controls did not block reintroduction of Three modules disagree on AUTO_EXECUTION_LOOP defaults; no single master switch . |
| 5 | Exact repository evidence files | execution_engine.py, execution_keys.py, startup_orchestrator.py, instant_alert_engine.py |
| 6 | Exact symbols/settings/routes/tables/functions | AUTO_EXECUTION_* env vars; missing EXECUTION_ENABLED, execution_safety_guard |
| 7 | Current defective behavior | Without blocking gate, PC-005 defect pattern can return via refactor or config drift undetected in CI. |
| 8 | Required target behavior | CI architecture test reads defaults from orchestrator, engine, compose; fails on mismatch. |
| 9 | Control mechanism | tests/arch/test_execution_default_parity.py parses default values across orchestrator, engine, docker-compose templates. |
| 10 | Enforcement point | CI architecture test merge gate |
| 11 | Explicit affected files or bounded file families | execution_engine.py, startup_orchestrator.py, docker-compose.yml, tests/arch/test_execution_default_parity.py |
| 12 | Authority/owning bounded context | Execution safety / Register D preventive gate |
| 13 | Positive impact | Automated regression block for PC-005 closure criteria. |
| 14 | Potential negative impact | CI friction on related file changes. |
| 15 | Other findings affected | PC-008.a, PC-010, PC-022.e |
| 16 | Required downstream revalidation | IVV synthetic regression injection for PC-005 |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register D |
| 18 | Objective acceptance criteria | Changing one execution default without updating others fails CI test. |
| 19 | Verification mechanism | CI default parity test |
| 20 | Failure condition | Default mismatch between modules undetected |
| 21 | Evidence output required | E-EXEC/default-parity-test.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: APPLICABLE — implements EXECUTION_ENABLED master switch and UNKNOWN=DENY per DEC-D; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### PCtrl-006 — Schema lint forbids new financial REAL columns

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | PCtrl-006 |
| 2 | Finding ID | PC-006 |
| 3 | Control type | PREVENTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 enabling condition for PC-006 recurrence: existing controls did not block reintroduction of Cumulative fee/profit aggregates suffer IEEE-754 representation error at scale.. |
| 5 | Exact repository evidence files | database.py |
| 6 | Exact symbols/settings/routes/tables/functions | DDL REAL on pricing_logs, evaluated_opportunities, oracle_predictions financial columns |
| 7 | Current defective behavior | Without blocking gate, PC-006 defect pattern can return via refactor or config drift undetected in CI. |
| 8 | Required target behavior | DDL lint in CI fails if new REAL columns added to tables classified as financial. |
| 9 | Control mechanism | tests/schema/test_no_new_real_financial_columns.py blocks new REAL on financial table registry. |
| 10 | Enforcement point | CI schema lint merge gate |
| 11 | Explicit affected files or bounded file families | database.py, tests/schema/test_no_new_real_financial_columns.py |
| 12 | Authority/owning bounded context | Financial safety / Register J preventive gate |
| 13 | Positive impact | Automated regression block for PC-006 closure criteria. |
| 14 | Potential negative impact | CI friction on related file changes. |
| 15 | Other findings affected | PC-009.c, PC-041, PC-027 |
| 16 | Required downstream revalidation | IVV synthetic regression injection for PC-006 |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register J |
| 18 | Objective acceptance criteria | PR adding REAL to pricing_logs fails schema lint. |
| 19 | Verification mechanism | CI schema lint on DDL changes |
| 20 | Failure condition | New REAL column on financial table merges |
| 21 | Evidence output required | E-DATA/real-column-lint.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### PCtrl-007 — Boot graph architecture test per profile

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | PCtrl-007 |
| 2 | Finding ID | PC-007 |
| 3 | Control type | PREVENTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 enabling condition for PC-007 recurrence: existing controls did not block reintroduction of Same commit produces different background-service graphs by entry path; web vs a. |
| 5 | Exact repository evidence files | run_service.py, config.py, dashboard.py, microservices/lifecycle.py, Dockerfile, docker-compose.yml, launch_verify.bat |
| 6 | Exact symbols/settings/routes/tables/functions | MODES, SERVICE_MODE, lifespan, startup(), current_mode() |
| 7 | Current defective behavior | Without blocking gate, PC-007 defect pattern can return via refactor or config drift undetected in CI. |
| 8 | Required target behavior | Automated test simulates lifespan per profile and asserts expected background task set including sidecar and orchestrator rules. |
| 9 | Control mechanism | tests/arch/test_runtime_topology_profiles.py validates orchestrator vs lifecycle path per docker-web, local-all, compose-workers, Railway, CI smoke profiles. |
| 10 | Enforcement point | CI merge gate on boot-path changes |
| 11 | Explicit affected files or bounded file families | run_service.py, dashboard.py, microservices/lifecycle.py, tests/arch/test_runtime_topology_profiles.py, .github/workflows/ci.yml |
| 12 | Authority/owning bounded context | Runtime topology / Register H, B preventive gate |
| 13 | Positive impact | Automated regression block for PC-007 closure criteria. |
| 14 | Potential negative impact | CI friction on related file changes. |
| 15 | Other findings affected | PC-031, PC-008.a, PC-016, PC-005 |
| 16 | Required downstream revalidation | IVV synthetic regression injection for PC-007 |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register H |
| 18 | Objective acceptance criteria | web profile test confirms lifecycle-only path; all profile confirms orchestrator when matrix requires. |
| 19 | Verification mechanism | CI topology test matrix |
| 20 | Failure condition | Topology test passes with divergent boot graphs |
| 21 | Evidence output required | E-TOPO/topology-validation-report.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: APPLICABLE — defines canonical deployment profiles without P17 extraction |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### PCtrl-008 — Startup domain manifest required in CI

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | PCtrl-008 |
| 2 | Finding ID | PC-008 |
| 3 | Control type | PREVENTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 enabling condition for PC-008 recurrence: existing controls did not block reintroduction of HTTP readiness does not imply minimal safe runtime; heavy trading/ML domains sta. |
| 5 | Exact repository evidence files | startup_orchestrator.py, platform_api.py, dashboard.py |
| 6 | Exact symbols/settings/routes/tables/functions | run_background_startup, RuntimeState, platform_api.router |
| 7 | Current defective behavior | Without blocking gate, PC-008 defect pattern can return via refactor or config drift undetected in CI. |
| 8 | Required target behavior | CI integration test captures startup manifest hash and compares to golden file per profile. |
| 9 | Control mechanism | Golden manifest files under tests/fixtures/startup_manifests/ compared on CI integration boot. |
| 10 | Enforcement point | CI merge gate |
| 11 | Explicit affected files or bounded file families | startup_orchestrator.py, tests/fixtures/startup_manifests/, tests/integration/test_startup_manifest.py (PROPOSED_ARTIFACT) |
| 12 | Authority/owning bounded context | Composition root / Register B preventive gate |
| 13 | Positive impact | Automated regression block for PC-008 closure criteria. |
| 14 | Potential negative impact | CI friction on related file changes. |
| 15 | Other findings affected | PC-008.a, PC-008.b, PC-008.c, PC-008.d |
| 16 | Required downstream revalidation | IVV synthetic regression injection for PC-008 |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register B |
| 18 | Objective acceptance criteria | Adding domain without manifest golden update fails CI. |
| 19 | Verification mechanism | CI golden manifest diff |
| 20 | Failure condition | Manifest hash drift undetected |
| 21 | Evidence output required | E-STARTUP/manifest-golden-diff.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: APPLICABLE — governed opt-in aligns with P01-P16 platform activation boundaries |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### PCtrl-009 — Route count and ownership regression gate

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | PCtrl-009 |
| 2 | Finding ID | PC-009 |
| 3 | Control type | PREVENTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 enabling condition for PC-009 recurrence: existing controls did not block reintroduction of HTTP surface owned by monolithic router; overlaps P01/P02 registry boundaries.. |
| 5 | Exact repository evidence files | platform_api.py, bd_platform/registry.py, dashboard.py |
| 6 | Exact symbols/settings/routes/tables/functions | APIRouter(prefix=/api/platform), FEATURE_MATRIX, 61 @router handlers |
| 7 | Current defective behavior | Without blocking gate, PC-009 defect pattern can return via refactor or config drift undetected in CI. |
| 8 | Required target behavior | CI fails if platform_api route count increases without platform router file and map update. |
| 9 | Control mechanism | tests/arch/test_platform_route_ownership.py counts routes and validates owner assignment. |
| 10 | Enforcement point | CI merge gate |
| 11 | Explicit affected files or bounded file families | platform_api.py, bd_platform/routers/, governance/platform_route_inventory.json (PROPOSED_ARTIFACT) |
| 12 | Authority/owning bounded context | Platform boundary / Register B preventive gate |
| 13 | Positive impact | Automated regression block for PC-009 closure criteria. |
| 14 | Potential negative impact | CI friction on related file changes. |
| 15 | Other findings affected | PC-009.a, PC-009.b, PC-009.c, PC-009.d |
| 16 | Required downstream revalidation | IVV synthetic regression injection for PC-009 |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register B |
| 18 | Objective acceptance criteria | New route in monolith file fails until moved to platform router. |
| 19 | Verification mechanism | CI route ownership test |
| 20 | Failure condition | Route count grows in platform_api.py undetected |
| 21 | Evidence output required | E-PLATFORM/route-regression-gate.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: APPLICABLE — enforces P01-P16 modular monolith router ownership |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### PCtrl-010 — Connector bypass negative test matrix in CI

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | PCtrl-010 |
| 2 | Finding ID | PC-010 |
| 3 | Control type | PREVENTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 enabling condition for PC-010 recurrence: existing controls did not block reintroduction of Venue execution proceeds through connectors without unified risk/exposure/freeze. |
| 5 | Exact repository evidence files | bd_platform/cex_dex_executor.py, execution_engine.py, platform_api.py |
| 6 | Exact symbols/settings/routes/tables/functions | execute_cex_dex_opportunity, execute_order, _live_enabled |
| 7 | Current defective behavior | Without blocking gate, PC-010 defect pattern can return via refactor or config drift undetected in CI. |
| 8 | Required target behavior | Maintain combinatorial negative tests for connector paths: freeze on, exposure exceeded, master off. |
| 9 | Control mechanism | tests/security/test_connector_execution_denials.py matrix blocks bypass success rows. |
| 10 | Enforcement point | CI blocking security tests |
| 11 | Explicit affected files or bounded file families | bd_platform/cex_dex_executor.py, tests/security/test_connector_execution_denials.py |
| 12 | Authority/owning bounded context | Execution authorization / Register D preventive gate |
| 13 | Positive impact | Automated regression block for PC-010 closure criteria. |
| 14 | Potential negative impact | CI friction on related file changes. |
| 15 | Other findings affected | PC-005, PC-010.a, PC-022.e |
| 16 | Required downstream revalidation | IVV synthetic regression injection for PC-010 |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register D |
| 18 | Objective acceptance criteria | Any bypass returning success fails CI. |
| 19 | Verification mechanism | CI bypass matrix parser |
| 20 | Failure condition | Bypass test row returns SUCCESS |
| 21 | Evidence output required | E-EXEC/connector-denial-matrix.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: APPLICABLE — mandatory authorize_execution before connectors per DEC-D; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### PCtrl-011 — G3 schema validator rejects missing gate_scope

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | PCtrl-011 |
| 2 | Finding ID | PC-011 |
| 3 | Control type | PREVENTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 enabling condition for PC-011 recurrence: existing controls did not block reintroduction of 1-hour smoke and 24-hour institutional soak share assessor without gate_scope fi. |
| 5 | Exact repository evidence files | scripts/g3_reliability_soak_test.py, FEATURE_001_G3_SOAK_TEST_REPORT.md |
| 6 | Exact symbols/settings/routes/tables/functions | TREND_MILESTONE_HOURS, hours_required, --hours |
| 7 | Current defective behavior | Without blocking gate, PC-011 defect pattern can return via refactor or config drift undetected in CI. |
| 8 | Required target behavior | CI evidence validator rejects G3 JSON without valid gate_scope and hours consistency. |
| 9 | Control mechanism | scripts/validate_evidence.py G3 section hard-fails missing gate_scope. |
| 10 | Enforcement point | CI on evidence PRs |
| 11 | Explicit affected files or bounded file families | scripts/validate_evidence.py, schemas/g3_assessment.schema.json, .github/workflows/ci.yml |
| 12 | Authority/owning bounded context | G3 evidence / Register G preventive gate |
| 13 | Positive impact | Automated regression block for PC-011 closure criteria. |
| 14 | Potential negative impact | CI friction on related file changes. |
| 15 | Other findings affected | PC-011.a, PC-011.b, PC-029 |
| 16 | Required downstream revalidation | IVV synthetic regression injection for PC-011 |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register G |
| 18 | Objective acceptance criteria | Sample JSON without gate_scope fails validation. |
| 19 | Verification mechanism | CI validate_evidence on G3 JSON |
| 20 | Failure condition | Unversioned G3 JSON merges without gate_scope |
| 21 | Evidence output required | E-G3/gate-scope-validator-log.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### PCtrl-012 — Single oracle entry import enforcement

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | PCtrl-012 |
| 2 | Finding ID | PC-012 |
| 3 | Control type | PREVENTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 enabling condition for PC-012 recurrence: existing controls did not block reintroduction of Research, retrain, and integrity filtering are separate entrypoints without one . |
| 5 | Exact repository evidence files | research_lab.py, oracle_retrainer.py, oracle_integrity.py, api/routers/oracle.py |
| 6 | Exact symbols/settings/routes/tables/functions | build_research_lab_report, run_oracle_retrain_step, filter_live_predictions |
| 7 | Current defective behavior | Without blocking gate, PC-012 defect pattern can return via refactor or config drift undetected in CI. |
| 8 | Required target behavior | Prohibited-import lint blocks direct oracle_retrainer/research_lab calls outside inference stack facade. |
| 9 | Control mechanism | scripts/lint_prohibited_imports.py rule oracle_single_entry fails external direct imports. |
| 10 | Enforcement point | CI import lint merge gate |
| 11 | Explicit affected files or bounded file families | research_lab.py, oracle_retrainer.py, scripts/lint_prohibited_imports.py, tests/oracle/ (PROPOSED_ARTIFACT) |
| 12 | Authority/owning bounded context | Oracle architecture / Register I preventive gate |
| 13 | Positive impact | Automated regression block for PC-012 closure criteria. |
| 14 | Potential negative impact | CI friction on related file changes. |
| 15 | Other findings affected | PC-012.a, PC-012.b, PC-028 |
| 16 | Required downstream revalidation | IVV synthetic regression injection for PC-012 |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register I |
| 18 | Objective acceptance criteria | New direct oracle_retrainer import outside stack fails lint. |
| 19 | Verification mechanism | CI prohibited-import scan |
| 20 | Failure condition | Direct research_lab import from production route |
| 21 | Evidence output required | E-ORACLE/oracle-entry-lint.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### PCtrl-013 — Tenant negative test suite mandatory on CRUD changes

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | PCtrl-013 |
| 2 | Finding ID | PC-013 |
| 3 | Control type | PREVENTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 enabling condition for PC-013 recurrence: existing controls did not block reintroduction of Multi-tenant isolation, MFA, production demo isolation not enforced as unified P. |
| 5 | Exact repository evidence files | .gitignore, auth_service.py, dashboard.py, production_guard.py, execution_keys.py |
| 6 | Exact symbols/settings/routes/tables/functions | keys/, TIER_FEATURES, evaluate_production_guard, B2B_DEMO_API_KEY |
| 7 | Current defective behavior | Without blocking gate, PC-013 defect pattern can return via refactor or config drift undetected in CI. |
| 8 | Required target behavior | CI requires cross-tenant negative tests pass when any database.py user-scoped repository changes. |
| 9 | Control mechanism | Path-triggered CI job tenant-isolation-gate blocks database.py CRUD changes without tenant negative test updates. |
| 10 | Enforcement point | CI path-filter merge gate |
| 11 | Explicit affected files or bounded file families | database.py, tests/security/test_tenant_isolation.py (PROPOSED_ARTIFACT), .github/workflows/ci.yml |
| 12 | Authority/owning bounded context | Tenancy security / Register E preventive gate |
| 13 | Positive impact | Automated regression block for PC-013 closure criteria. |
| 14 | Potential negative impact | CI friction on related file changes. |
| 15 | Other findings affected | PC-013.a-f, PC-030 |
| 16 | Required downstream revalidation | IVV synthetic regression injection for PC-013 |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register E |
| 18 | Objective acceptance criteria | CRUD change without tenant test update fails path gate. |
| 19 | Verification mechanism | CI path-triggered tenant gate |
| 20 | Failure condition | DB change merges without tenant tests |
| 21 | Evidence output required | E-SEC/tenant-gate-log.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: APPLICABLE — P11 tenancy facade aligns with modular monolith boundaries |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### PCtrl-014 — Restart recovery integration test on execution changes

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | PCtrl-014 |
| 2 | Finding ID | PC-014 |
| 3 | Control type | PREVENTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 enabling condition for PC-014 recurrence: existing controls did not block reintroduction of Restart drops orchestrator task graph and execution loop state; recovery depends. |
| 5 | Exact repository evidence files | startup_orchestrator.py, dashboard.py, execution_engine.py |
| 6 | Exact symbols/settings/routes/tables/functions | RuntimeState, app.state.runtime, module-level loop tasks |
| 7 | Current defective behavior | Without blocking gate, PC-014 defect pattern can return via refactor or config drift undetected in CI. |
| 8 | Required target behavior | Any change to execution_engine or startup_orchestrator triggers blocking restart recovery test. |
| 9 | Control mechanism | tests/integration/test_execution_restart_recovery.py simulates SIGTERM and asserts persisted authority reload. |
| 10 | Enforcement point | CI path filter on execution modules |
| 11 | Explicit affected files or bounded file families | execution_engine.py, startup_orchestrator.py, tests/integration/test_execution_restart_recovery.py |
| 12 | Authority/owning bounded context | Execution state / Register D preventive gate |
| 13 | Positive impact | Automated regression block for PC-014 closure criteria. |
| 14 | Potential negative impact | CI friction on related file changes. |
| 15 | Other findings affected | PC-005, PC-022.c |
| 16 | Required downstream revalidation | IVV synthetic regression injection for PC-014 |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register D |
| 18 | Objective acceptance criteria | Test simulates restart and asserts persisted authority reload. |
| 19 | Verification mechanism | CI path-filtered recovery test |
| 20 | Failure condition | Restart test skipped on engine change |
| 21 | Evidence output required | E-EXEC/restart-recovery-test.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### PCtrl-015 — Taxonomy drift lint across three live sources

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | PCtrl-015 |
| 2 | Finding ID | PC-015 |
| 3 | Control type | PREVENTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 enabling condition for PC-015 recurrence: existing controls did not block reintroduction of Grid ids 1-40, tier flags, and plan audit strings coexist without authority mark. |
| 5 | Exact repository evidence files | bd_platform/registry.py, auth_service.py, plan_audit.py |
| 6 | Exact symbols/settings/routes/tables/functions | FEATURE_MATRIX, TIER_FEATURES, plan audit feature list |
| 7 | Current defective behavior | Without blocking gate, PC-015 defect pattern can return via refactor or config drift undetected in CI. |
| 8 | Required target behavior | CI test verifies grid, tier, and plan audit docs all reference SSOT pointer authority classes. |
| 9 | Control mechanism | tests/governance/test_taxonomy_authority_markers.py fails when authority marker removed from registry module. |
| 10 | Enforcement point | CI ssot-doc-lint merge gate |
| 11 | Explicit affected files or bounded file families | bd_platform/registry.py, auth_service.py, plan_audit.py, tests/governance/test_taxonomy_authority_markers.py |
| 12 | Authority/owning bounded context | Feature taxonomy / Register A, K preventive gate |
| 13 | Positive impact | Automated regression block for PC-015 closure criteria. |
| 14 | Potential negative impact | CI friction on related file changes. |
| 15 | Other findings affected | PC-015.a, PC-015.b, PC-036, PC-023 |
| 16 | Required downstream revalidation | IVV synthetic regression injection for PC-015 |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register A |
| 18 | Objective acceptance criteria | Removing authority marker from registry fails governance test. |
| 19 | Verification mechanism | CI governance test |
| 20 | Failure condition | Taxonomy source lacks authority class label |
| 21 | Evidence output required | E-GOV/taxonomy-drift-lint.json |
| 22 | Architectural-decision compatibility | DEC-A: APPLICABLE — separates attested enumeration from roadmap grid and tier views; DEC-B: APPLICABLE — crosswalk requires settled taxonomy authority; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### PCtrl-016 — Docker HEALTHCHECK integration in CI smoke

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | PCtrl-016 |
| 2 | Finding ID | PC-016 |
| 3 | Control type | PREVENTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 enabling condition for PC-016 recurrence: existing controls did not block reintroduction of Container health and operator launch scripts validate different endpoints; non-r. |
| 5 | Exact repository evidence files | Dockerfile, health_sidecar.py, run_service.py, launch_verify.bat |
| 6 | Exact symbols/settings/routes/tables/functions | HEALTHCHECK, start_health_sidecar, HEALTH_PORT |
| 7 | Current defective behavior | Without blocking gate, PC-016 defect pattern can return via refactor or config drift undetected in CI. |
| 8 | Required target behavior | CI builds and runs container asserting HEALTHCHECK on 8180 succeeds within timeout. |
| 9 | Control mechanism | Docker smoke job in ci.yml post-build validates HEALTHCHECK success. |
| 10 | Enforcement point | CI Docker smoke merge gate |
| 11 | Explicit affected files or bounded file families | Dockerfile, .github/workflows/ci.yml, tests/docker/test_healthcheck_smoke.py (PROPOSED_ARTIFACT) |
| 12 | Authority/owning bounded context | Deploy operations / Register H preventive gate |
| 13 | Positive impact | Automated regression block for PC-016 closure criteria. |
| 14 | Potential negative impact | CI friction on related file changes. |
| 15 | Other findings affected | PC-007, PC-031 |
| 16 | Required downstream revalidation | IVV synthetic regression injection for PC-016 |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register H |
| 18 | Objective acceptance criteria | Container marked unhealthy when sidecar disabled fails smoke. |
| 19 | Verification mechanism | CI Docker smoke job |
| 20 | Failure condition | Sidecar disabled container passes smoke |
| 21 | Evidence output required | E-DEPLOY/healthcheck-smoke-log.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### PCtrl-017 — Infra profile contract test

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | PCtrl-017 |
| 2 | Finding ID | PC-017 |
| 3 | Control type | PREVENTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 enabling condition for PC-017 recurrence: existing controls did not block reintroduction of Staging compose includes Kafka/Vault while web-only deploy omits them; feature p. |
| 5 | Exact repository evidence files | docker-compose.yml, bd_platform/kafka_bridge.py, production_guard.py |
| 6 | Exact symbols/settings/routes/tables/functions | kafka, redis, vault services; Kafka bridge module |
| 7 | Current defective behavior | Without blocking gate, PC-017 defect pattern can return via refactor or config drift undetected in CI. |
| 8 | Required target behavior | CI runs minimal and full profile tests asserting documented degrade vs hard-fail behavior. |
| 9 | Control mechanism | tests/infra/test_infra_profile_contract.py validates kafka-absent minimal profile behavior. |
| 10 | Enforcement point | CI infra contract merge gate |
| 11 | Explicit affected files or bounded file families | docker-compose.yml, tests/infra/test_infra_profile_contract.py, config.py |
| 12 | Authority/owning bounded context | Infrastructure / Register H preventive gate |
| 13 | Positive impact | Automated regression block for PC-017 closure criteria. |
| 14 | Potential negative impact | CI friction on related file changes. |
| 15 | Other findings affected | PC-007, PC-025 |
| 16 | Required downstream revalidation | IVV synthetic regression injection for PC-017 |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register H |
| 18 | Objective acceptance criteria | Kafka-absent minimal profile matches matrix expectation. |
| 19 | Verification mechanism | CI infra contract test |
| 20 | Failure condition | Minimal profile hard-fails without documented degrade |
| 21 | Evidence output required | E-INFRA/profile-contract-test.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### PCtrl-018 — Markdown link checker on docs/**

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | PCtrl-018 |
| 2 | Finding ID | PC-018 |
| 3 | Control type | PREVENTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 enabling condition for PC-018 recurrence: existing controls did not block reintroduction of Navigation from gaps completed to authoritative program docs fails on clone; ins. |
| 5 | Exact repository evidence files | docs/GAPS_COMPLETED.md; docs/institutional/ (HISTORICAL_REFERENCE_NOT_PRESENT) |
| 6 | Exact symbols/settings/routes/tables/functions | markdown links to institutional paths |
| 7 | Current defective behavior | Without blocking gate, PC-018 defect pattern can return via refactor or config drift undetected in CI. |
| 8 | Required target behavior | CI link-check job scans docs for broken relative links on every PR touching docs/. |
| 9 | Control mechanism | scripts/check_doc_links.py or lychee action blocks broken relative links. |
| 10 | Enforcement point | CI merge gate on docs/** changes |
| 11 | Explicit affected files or bounded file families | docs/**/*.md, scripts/check_doc_links.py (PROPOSED_ARTIFACT), .github/workflows/ci.yml |
| 12 | Authority/owning bounded context | Documentation navigation / Register K preventive gate |
| 13 | Positive impact | Automated regression block for PC-018 closure criteria. |
| 14 | Potential negative impact | CI friction on related file changes. |
| 15 | Other findings affected | PC-023, PC-042 |
| 16 | Required downstream revalidation | IVV synthetic regression injection for PC-018 |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register K |
| 18 | Objective acceptance criteria | Broken link in GAPS_COMPLETED fails job. |
| 19 | Verification mechanism | CI link-check job |
| 20 | Failure condition | Link check not triggered on docs PR |
| 21 | Evidence output required | E-DOC/link-check-ci-log.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### PCtrl-019 — Training path isolation CI scan

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | PCtrl-019 |
| 2 | Finding ID | PC-019 |
| 3 | Control type | PREVENTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 enabling condition for PC-019 recurrence: existing controls did not block reintroduction of Saturation guard protects alert economics but not training-data leakage into liv. |
| 5 | Exact repository evidence files | flywheel_saturation_guard.py, startup_orchestrator.py, ml/ |
| 6 | Exact symbols/settings/routes/tables/functions | _enabled, ML flywheel startup block |
| 7 | Current defective behavior | Without blocking gate, PC-019 defect pattern can return via refactor or config drift undetected in CI. |
| 8 | Required target behavior | CI scans serving config for paths pointing into training directories on ml/ or flywheel config changes. |
| 9 | Control mechanism | tests/ml/test_training_serving_path_isolation.py path-filtered on ml config changes. |
| 10 | Enforcement point | CI path-filter merge gate |
| 11 | Explicit affected files or bounded file families | ml/, tests/ml/test_training_serving_path_isolation.py, startup_orchestrator.py |
| 12 | Authority/owning bounded context | ML governance / Register I preventive gate |
| 13 | Positive impact | Automated regression block for PC-019 closure criteria. |
| 14 | Potential negative impact | CI friction on related file changes. |
| 15 | Other findings affected | PC-019.a, PC-012 |
| 16 | Required downstream revalidation | IVV synthetic regression injection for PC-019 |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register I |
| 18 | Objective acceptance criteria | Misconfigured training path in serving config fails scan. |
| 19 | Verification mechanism | CI ML path isolation test |
| 20 | Failure condition | Isolation test skipped on ml change |
| 21 | Evidence output required | E-ML/training-path-isolation-log.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### PCtrl-020 — Blocking dashboard.py composition invariant gate

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | PCtrl-020 |
| 2 | Finding ID | PC-020 |
| 3 | Control type | PREVENTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 enabling condition for PC-020 recurrence: existing controls did not block reintroduction of dashboard.py ~2398 lines concentrates composition; single-file blast radius for . |
| 5 | Exact repository evidence files | dashboard.py |
| 6 | Exact symbols/settings/routes/tables/functions | lifespan, route registrations, FastAPI app |
| 7 | Current defective behavior | Without blocking gate, PC-020 defect pattern can return via refactor or config drift undetected in CI. |
| 8 | Required target behavior | Blocking CI gate enforces dashboard.py composition invariants: max line count, route registration only via submodules, no new inline handlers. |
| 9 | Control mechanism | scripts/check_dashboard_composition.py (PROPOSED_ARTIFACT) blocking CI: line count ceiling, AST scan forbids new @app routes outside routes/ package. |
| 10 | Enforcement point | CI merge gate — blocking not advisory |
| 11 | Explicit affected files or bounded file families | dashboard.py, scripts/check_dashboard_composition.py (PROPOSED_ARTIFACT), tests/arch/test_dashboard_composition_invariant.py (PROPOSED_ARTIFACT) |
| 12 | Authority/owning bounded context | Application composition / Register B preventive gate |
| 13 | Positive impact | Automated regression block for PC-020 closure criteria. |
| 14 | Potential negative impact | CI friction on related file changes. |
| 15 | Other findings affected | PC-008, PC-030 |
| 16 | Required downstream revalidation | IVV synthetic regression injection for PC-020 |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register B |
| 18 | Objective acceptance criteria | Artificial line increase or inline route addition fails blocking CI gate. |
| 19 | Verification mechanism | CI blocking composition check |
| 20 | Failure condition | Advisory-only report without merge block |
| 21 | Evidence output required | E-ARCH/dashboard-composition-gate-log.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: APPLICABLE — physical module split reflects P01-P16 composition boundaries |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### PCtrl-021 — Manifest reconcile job on every Docker/CI change

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | PCtrl-021 |
| 2 | Finding ID | PC-021 |
| 3 | Control type | PREVENTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 enabling condition for PC-021 recurrence: existing controls did not block reintroduction of CI installs dev requirements.txt; Docker copies prod manifest; import sets diver. |
| 5 | Exact repository evidence files | requirements.txt, requirements-prod.txt, Dockerfile, .github/workflows/ci.yml |
| 6 | Exact symbols/settings/routes/tables/functions | pip install lines; COPY requirements-prod |
| 7 | Current defective behavior | Without blocking gate, PC-021 defect pattern can return via refactor or config drift undetected in CI. |
| 8 | Required target behavior | CI manifest-reconcile runs on Dockerfile, requirements*, or ci.yml changes. |
| 9 | Control mechanism | Diff job comparing import smoke lists ccxt, pandas, sklearn, kafka between CI runner and Docker container. |
| 10 | Enforcement point | CI path filter merge gate |
| 11 | Explicit affected files or bounded file families | Dockerfile, requirements*.txt, .github/workflows/ci.yml, scripts/manifest_reconcile.py (PROPOSED_ARTIFACT) |
| 12 | Authority/owning bounded context | Deploy reproducibility / Register H preventive gate |
| 13 | Positive impact | Automated regression block for PC-021 closure criteria. |
| 14 | Potential negative impact | CI friction on related file changes. |
| 15 | Other findings affected | PC-001, PC-021.a |
| 16 | Required downstream revalidation | IVV synthetic regression injection for PC-021 |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register H |
| 18 | Objective acceptance criteria | Adding pandas-only-to-CI dependency fails reconcile. |
| 19 | Verification mechanism | CI manifest-reconcile diff |
| 20 | Failure condition | Reconcile skipped on Dockerfile change |
| 21 | Evidence output required | E-BUILD/manifest-reconcile-gate.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### PCtrl-022 — Institutional test class registry enforced

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | PCtrl-022 |
| 2 | Finding ID | PC-022 |
| 3 | Control type | PREVENTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 enabling condition for PC-022 recurrence: existing controls did not block reintroduction of Institutional quality claims SSE UI, concurrent execution, DR not continuously e. |
| 5 | Exact repository evidence files | .github/workflows/ci.yml, tests/, bd_platform/sse_stream.py |
| 6 | Exact symbols/settings/routes/tables/functions | CI jobs; absence of SSE E2E, concurrency, restore drill |
| 7 | Current defective behavior | Without blocking gate, PC-022 defect pattern can return via refactor or config drift undetected in CI. |
| 8 | Required target behavior | Meta-test asserts presence of four institutional test directories and associated blocking CI jobs. |
| 9 | Control mechanism | tests/meta/test_institutional_test_classes.py fails if e2e/concurrency/ops job removed. |
| 10 | Enforcement point | CI merge gate |
| 11 | Explicit affected files or bounded file families | tests/meta/test_institutional_test_classes.py, .github/workflows/ci.yml |
| 12 | Authority/owning bounded context | Test architecture / Register F preventive gate |
| 13 | Positive impact | Automated regression block for PC-022 closure criteria. |
| 14 | Potential negative impact | CI friction on related file changes. |
| 15 | Other findings affected | PC-022.a-e, PC-002, PC-034 |
| 16 | Required downstream revalidation | IVV synthetic regression injection for PC-022 |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register F |
| 18 | Objective acceptance criteria | Removing e2e job fails meta-test. |
| 19 | Verification mechanism | Meta-test institutional registry |
| 20 | Failure condition | Meta-test passes with missing e2e job |
| 21 | Evidence output required | E-TEST/institutional-meta-test-log.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### PCtrl-023 — SSOT pointer discoverability test

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | PCtrl-023 |
| 2 | Finding ID | PC-023 |
| 3 | Control type | PREVENTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 enabling condition for PC-023 recurrence: existing controls did not block reintroduction of Authority documents cannot be discovered from single pointer; institutional tree. |
| 5 | Exact repository evidence files | docs/; docs/institutional/ (HISTORICAL_REFERENCE_NOT_PRESENT); CURRENT_PROGRAM_STATUS_POINTER.md (HISTORICAL_REFERENCE_NOT_PRESENT) |
| 6 | Exact symbols/settings/routes/tables/functions | CURRENT_PROGRAM_STATUS_POINTER.md (absent) |
| 7 | Current defective behavior | Without blocking gate, PC-023 defect pattern can return via refactor or config drift undetected in CI. |
| 8 | Required target behavior | CI test walks from README/docs index to pointer within ≤2 hops. |
| 9 | Control mechanism | tests/governance/test_ssot_pointer_navigation.py validates discoverability within two hops. |
| 10 | Enforcement point | CI governance test merge gate |
| 11 | Explicit affected files or bounded file families | README.md, docs/index paths, tests/governance/test_ssot_pointer_navigation.py |
| 12 | Authority/owning bounded context | SSOT navigation / Register K preventive gate |
| 13 | Positive impact | Automated regression block for PC-023 closure criteria. |
| 14 | Potential negative impact | CI friction on related file changes. |
| 15 | Other findings affected | PC-015, PC-036, PC-037, PC-042 |
| 16 | Required downstream revalidation | IVV synthetic regression injection for PC-023 |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register K |
| 18 | Objective acceptance criteria | Removing pointer link fails navigation test. |
| 19 | Verification mechanism | CI discoverability test |
| 20 | Failure condition | Institutional tree still absent |
| 21 | Evidence output required | E-GOV/pointer-navigation-test.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### PCtrl-024 — Audit export invariant test

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | PCtrl-024 |
| 2 | Finding ID | PC-024 |
| 3 | Control type | PREVENTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 enabling condition for PC-024 recurrence: existing controls did not block reintroduction of Audit and compliance consumers receive differently filtered views depending on i. |
| 5 | Exact repository evidence files | oracle_integrity.py, database.py, weekly_report.py, regulatory_compliance_guard.py |
| 6 | Exact symbols/settings/routes/tables/functions | fetch_oracle_audit_stats, filter_live_predictions, apply_regulatory_compliance |
| 7 | Current defective behavior | Without blocking gate, PC-024 defect pattern can return via refactor or config drift undetected in CI. |
| 8 | Required target behavior | Invariant test: all audit export code paths include synthetic filter consistent with audit_authority defaults. |
| 9 | Control mechanism | tests/audit/test_audit_export_invariants.py fails caller bypassing synthetic filter. |
| 10 | Enforcement point | CI audit invariant merge gate |
| 11 | Explicit affected files or bounded file families | weekly_report.py, gtm_service.py, tests/audit/test_audit_export_invariants.py |
| 12 | Authority/owning bounded context | Audit authority / Register L preventive gate |
| 13 | Positive impact | Automated regression block for PC-024 closure criteria. |
| 14 | Potential negative impact | CI friction on related file changes. |
| 15 | Other findings affected | PC-008.d, PC-028 |
| 16 | Required downstream revalidation | IVV synthetic regression injection for PC-024 |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register L |
| 18 | Objective acceptance criteria | Caller bypassing synthetic filter fails invariant scan. |
| 19 | Verification mechanism | CI audit invariant test |
| 20 | Failure condition | Direct oracle audit SQL from report module |
| 21 | Evidence output required | E-AUDIT/audit-invariant-test.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### PCtrl-025 — Config validation required on orchestrator changes

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | PCtrl-025 |
| 2 | Finding ID | PC-025 |
| 3 | Control type | PREVENTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 enabling condition for PC-025 recurrence: existing controls did not block reintroduction of Misconfiguration reaches live HTTP and background tasks; orchestrator logs and s. |
| 5 | Exact repository evidence files | config.py, startup_orchestrator.py, production_guard.py |
| 6 | Exact symbols/settings/routes/tables/functions | env reads; evaluate_production_guard |
| 7 | Current defective behavior | Without blocking gate, PC-025 defect pattern can return via refactor or config drift undetected in CI. |
| 8 | Required target behavior | Path-filtered CI runs fail-closed config tests when startup_orchestrator or config.py changes. |
| 9 | Control mechanism | tests/startup/test_config_fail_closed.py causes process exit on invalid prod config. |
| 10 | Enforcement point | CI path-filter merge gate |
| 11 | Explicit affected files or bounded file families | startup_orchestrator.py, config.py, tests/startup/test_config_fail_closed.py |
| 12 | Authority/owning bounded context | Configuration startup / Register H, D preventive gate |
| 13 | Positive impact | Automated regression block for PC-025 closure criteria. |
| 14 | Potential negative impact | CI friction on related file changes. |
| 15 | Other findings affected | PC-017, PC-007 |
| 16 | Required downstream revalidation | IVV synthetic regression injection for PC-025 |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register H |
| 18 | Objective acceptance criteria | Invalid prod config causes test process exit non-zero. |
| 19 | Verification mechanism | CI config fail-closed test |
| 20 | Failure condition | Orchestrator skip-on-exception persists |
| 21 | Evidence output required | E-CONFIG/config-gate-test.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### PCtrl-026 — Stale price rejection contract test

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | PCtrl-026 |
| 2 | Finding ID | PC-026 |
| 3 | Control type | PREVENTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 enabling condition for PC-026 recurrence: existing controls did not block reintroduction of Scan engines use stale hub rows; REST fallback lacks execution-authority freshne. |
| 5 | Exact repository evidence files | market_context.py, fast_scan_engine.py, live_book_hub.py |
| 6 | Exact symbols/settings/routes/tables/functions | probe_price_sources, get_best_price, require_fresh |
| 7 | Current defective behavior | Without blocking gate, PC-026 defect pattern can return via refactor or config drift undetected in CI. |
| 8 | Required target behavior | Contract tests inject stale timestamps and assert scan/execution authorization denied. |
| 9 | Control mechanism | tests/contract/test_price_freshness_gate.py injects stale timestamps expecting DENY. |
| 10 | Enforcement point | CI contract test merge gate |
| 11 | Explicit affected files or bounded file families | fast_scan_engine.py, tests/contract/test_price_freshness_gate.py |
| 12 | Authority/owning bounded context | Price freshness / Register C preventive gate |
| 13 | Positive impact | Automated regression block for PC-026 closure criteria. |
| 14 | Potential negative impact | CI friction on related file changes. |
| 15 | Other findings affected | PC-004, PC-009.c |
| 16 | Required downstream revalidation | IVV synthetic regression injection for PC-026 |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register C |
| 18 | Objective acceptance criteria | Stale injection returning authorized opportunity fails CI. |
| 19 | Verification mechanism | CI price freshness gate |
| 20 | Failure condition | Freshness contract test skipped |
| 21 | Evidence output required | E-PRICE/stale-rejection-test.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: APPLICABLE — freshness contract binds to canonical price authority; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### PCtrl-027 — Database module boundary size gate

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | PCtrl-027 |
| 2 | Finding ID | PC-027 |
| 3 | Control type | PREVENTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 enabling condition for PC-027 recurrence: existing controls did not block reintroduction of Single database.py hosts all DDL and CRUD; financial migration requires high-chu. |
| 5 | Exact repository evidence files | database.py |
| 6 | Exact symbols/settings/routes/tables/functions | module-level CRUD functions (~3700+ lines) |
| 7 | Current defective behavior | Without blocking gate, PC-027 defect pattern can return via refactor or config drift undetected in CI. |
| 8 | Required target behavior | CI fails if database.py grows without corresponding extraction to domain module. |
| 9 | Control mechanism | Line-count gate requiring new db_* module when database.py grows +100 lines. |
| 10 | Enforcement point | CI merge gate on database.py |
| 11 | Explicit affected files or bounded file families | database.py, tests/arch/test_database_module_boundary.py (PROPOSED_ARTIFACT) |
| 12 | Authority/owning bounded context | Database architecture / Register J preventive gate |
| 13 | Positive impact | Automated regression block for PC-027 closure criteria. |
| 14 | Potential negative impact | CI friction on related file changes. |
| 15 | Other findings affected | PC-006, PC-013.b |
| 16 | Required downstream revalidation | IVV synthetic regression injection for PC-027 |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register J |
| 18 | Objective acceptance criteria | +100 lines to database.py without new db_* module fails gate. |
| 19 | Verification mechanism | CI database boundary gate |
| 20 | Failure condition | Extraction PR bypasses line gate |
| 21 | Evidence output required | E-DATA/db-boundary-gate.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### PCtrl-028 — Oracle import allow list versioned in repo

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | PCtrl-028 |
| 2 | Finding ID | PC-028 |
| 3 | Control type | PREVENTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 enabling condition for PC-028 recurrence: existing controls did not block reintroduction of New oracle callers added without review; cap047_oracle.py facade absent; no lint. |
| 5 | Exact repository evidence files | market_context.py, voice_service.py, research_lab.py, api/routers/oracle.py |
| 6 | Exact symbols/settings/routes/tables/functions | various oracle/research imports |
| 7 | Current defective behavior | Without blocking gate, PC-028 defect pattern can return via refactor or config drift undetected in CI. |
| 8 | Required target behavior | Maintain versioned allow list JSON; CI fails on imports not in list. |
| 9 | Control mechanism | governance/oracle_import_allowlist.json (PROPOSED_ARTIFACT) versioned; CI fails imports outside list. |
| 10 | Enforcement point | CI import lint merge gate |
| 11 | Explicit affected files or bounded file families | governance/oracle_import_allowlist.json (PROPOSED_ARTIFACT), scripts/lint_prohibited_imports.py |
| 12 | Authority/owning bounded context | Oracle import governance / Register I preventive gate |
| 13 | Positive impact | Automated regression block for PC-028 closure criteria. |
| 14 | Potential negative impact | CI friction on related file changes. |
| 15 | Other findings affected | PC-012, PC-024 |
| 16 | Required downstream revalidation | IVV synthetic regression injection for PC-028 |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register I |
| 18 | Objective acceptance criteria | New oracle DB import outside list fails lint. |
| 19 | Verification mechanism | CI allow list diff |
| 20 | Failure condition | Allow list not updated with new caller |
| 21 | Evidence output required | E-ORACLE/oracle-allowlist-gate.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### PCtrl-029 — Evidence schema version bump policy

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | PCtrl-029 |
| 2 | Finding ID | PC-029 |
| 3 | Control type | PREVENTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 enabling condition for PC-029 recurrence: existing controls did not block reintroduction of G3/G2 evidence lacks checked-in JSON schema or CI validator; validate_evidence.p. |
| 5 | Exact repository evidence files | scripts/g3_reliability_soak_test.py, data/g2_validation_logs/ |
| 6 | Exact symbols/settings/routes/tables/functions | assessment output structure; JSON log files |
| 7 | Current defective behavior | Without blocking gate, PC-029 defect pattern can return via refactor or config drift undetected in CI. |
| 8 | Required target behavior | CI rejects evidence harness changes without schema version increment and changelog entry. |
| 9 | Control mechanism | tests/governance/test_evidence_schema_version_policy.py enforces version bump on output shape change. |
| 10 | Enforcement point | CI evidence path merge gate |
| 11 | Explicit affected files or bounded file families | schemas/, scripts/g3_reliability_soak_test.py, tests/governance/test_evidence_schema_version_policy.py |
| 12 | Authority/owning bounded context | Evidence schema / Register G preventive gate |
| 13 | Positive impact | Automated regression block for PC-029 closure criteria. |
| 14 | Potential negative impact | CI friction on related file changes. |
| 15 | Other findings affected | PC-011, PC-040 |
| 16 | Required downstream revalidation | IVV synthetic regression injection for PC-029 |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register G |
| 18 | Objective acceptance criteria | Harness output shape change without version bump fails policy test. |
| 19 | Verification mechanism | CI schema version policy test |
| 20 | Failure condition | Schema version stale after harness change |
| 21 | Evidence output required | E-EVIDENCE/schema-version-policy-log.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### PCtrl-030 — Production route diff golden test

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | PCtrl-030 |
| 2 | Finding ID | PC-030 |
| 3 | Control type | PREVENTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 enabling condition for PC-030 recurrence: existing controls did not block reintroduction of Production guard checks infra only; demo/dev routes mount unconditionally at imp. |
| 5 | Exact repository evidence files | production_guard.py, dashboard.py, platform_api.py |
| 6 | Exact symbols/settings/routes/tables/functions | evaluate_production_guard, route includes |
| 7 | Current defective behavior | Without blocking gate, PC-030 defect pattern can return via refactor or config drift undetected in CI. |
| 8 | Required target behavior | CI compares production profile OpenAPI route list to golden allow list. |
| 9 | Control mechanism | tests/security/test_production_route_allowlist.py diffs prod OpenAPI against golden. |
| 10 | Enforcement point | CI security test merge gate |
| 11 | Explicit affected files or bounded file families | production_guard.py, tests/security/test_production_route_allowlist.py |
| 12 | Authority/owning bounded context | Production isolation / Register E preventive gate |
| 13 | Positive impact | Automated regression block for PC-030 closure criteria. |
| 14 | Potential negative impact | CI friction on related file changes. |
| 15 | Other findings affected | PC-013.c, PC-013.e |
| 16 | Required downstream revalidation | IVV synthetic regression injection for PC-030 |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register E |
| 18 | Objective acceptance criteria | New demo route in prod profile fails diff. |
| 19 | Verification mechanism | CI production route golden test |
| 20 | Failure condition | Golden allow list not updated |
| 21 | Evidence output required | E-SEC/prod-route-golden-diff.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### PCtrl-031 — Blocking topology validation all deployment targets

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | PCtrl-031 |
| 2 | Finding ID | PC-031 |
| 3 | Control type | PREVENTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 enabling condition for PC-031 recurrence: existing controls did not block reintroduction of Competing monolith/worker boot paths; SERVICE_MODE defaults diverge; web/all lif. |
| 5 | Exact repository evidence files | microservices/, docker-compose.yml, docs/MICROSERVICES_ARCHITECTURE.md, run_service.py, config.py, dashboard.py, launch_verify.bat |
| 6 | Exact symbols/settings/routes/tables/functions | worker_app.py, lifecycle.startup, SERVICE_MODE, MODES, compose scale directives |
| 7 | Current defective behavior | Without blocking gate, PC-031 defect pattern can return via refactor or config drift undetected in CI. |
| 8 | Required target behavior | Blocking CI topology validation simulates local, Docker, compose, Railway profile, and CI smoke asserting single canonical graph per profile. |
| 9 | Control mechanism | tests/arch/test_deployment_topology_validation.py (PROPOSED_ARTIFACT) blocking matrix: local-all, docker-web, compose-workers, railway-web, ci-smoke; forbids mixed monolith+worker boot without declared profile. |
| 10 | Enforcement point | CI merge gate — blocks all PRs touching boot paths |
| 11 | Explicit affected files or bounded file families | tests/arch/test_deployment_topology_validation.py (PROPOSED_ARTIFACT), .github/workflows/ci.yml, docker-compose.yml |
| 12 | Authority/owning bounded context | Deployment topology / Register B preventive gate |
| 13 | Positive impact | Automated regression block for PC-031 closure criteria. |
| 14 | Potential negative impact | CI friction on related file changes. |
| 15 | Other findings affected | PC-007, PC-016, PC-008.a |
| 16 | Required downstream revalidation | IVV synthetic regression injection for PC-031 |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register B |
| 18 | Objective acceptance criteria | Mixed-mode boot without profile declaration fails blocking CI; topology hash mismatch across Docker/local/compose. |
| 19 | Verification mechanism | Blocking CI topology validation |
| 20 | Failure condition | Topology validation advisory-only |
| 21 | Evidence output required | E-TOPO/topology-blocking-validation.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: APPLICABLE — clarifies worker modes as deployment profiles within P01-P16 monolith not P17 extraction |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### PCtrl-032 — Navigation index authority lint

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | PCtrl-032 |
| 2 | Finding ID | PC-032 |
| 3 | Control type | PREVENTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 enabling condition for PC-032 recurrence: existing controls did not block reintroduction of Wave 2 reference material has no mandated navigation index in repo.. |
| 5 | Exact repository evidence files | WAVE2_MASTER_REFERENCE_INDEX.md (HISTORICAL_REFERENCE_NOT_PRESENT) |
| 6 | Exact symbols/settings/routes/tables/functions | (file absent) |
| 7 | Current defective behavior | Without blocking gate, PC-032 defect pattern can return via refactor or config drift undetected in CI. |
| 8 | Required target behavior | ssot-doc-lint forbids CURRENT_SSOT or LIVE markers in WAVE2_MASTER_REFERENCE_INDEX.md. |
| 9 | Control mechanism | ssot-doc-lint STALE_LIVE_MARKER + FORBIDDEN_ENUMERATION rules block authority claims in index. |
| 10 | Enforcement point | CI ssot-doc-lint merge gate |
| 11 | Explicit affected files or bounded file families | WAVE2_MASTER_REFERENCE_INDEX.md (PROPOSED_ARTIFACT), scripts/ssot_doc_lint.py (PROPOSED_ARTIFACT) |
| 12 | Authority/owning bounded context | Documentation navigation / Register K preventive gate |
| 13 | Positive impact | Automated regression block for PC-032 closure criteria. |
| 14 | Potential negative impact | CI friction on related file changes. |
| 15 | Other findings affected | PC-023, PC-042 |
| 16 | Required downstream revalidation | IVV synthetic regression injection for PC-032 |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register K |
| 18 | Objective acceptance criteria | Adding CURRENT_SSOT to index fails lint. |
| 19 | Verification mechanism | CI ssot-doc-lint |
| 20 | Failure condition | Index file still absent |
| 21 | Evidence output required | E-DOC/navigation-authority-lint.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### PCtrl-033 — Required checks documentation drift test

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | PCtrl-033 |
| 2 | Finding ID | PC-033 |
| 3 | Control type | PREVENTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 enabling condition for PC-033 recurrence: existing controls did not block reintroduction of Security workflow passes independently of main CI full-suite success.. |
| 5 | Exact repository evidence files | .github/workflows/security.yml, .github/workflows/ci.yml |
| 6 | Exact symbols/settings/routes/tables/functions | separate workflow jobs |
| 7 | Current defective behavior | Without blocking gate, PC-033 defect pattern can return via refactor or config drift undetected in CI. |
| 8 | Required target behavior | Meta-test verifies documented required checks match workflow job names. |
| 9 | Control mechanism | tests/meta/test_required_checks_doc_sync.py fails on job rename without doc update. |
| 10 | Enforcement point | CI meta-test merge gate |
| 11 | Explicit affected files or bounded file families | .github/workflows/ci.yml, docs/ci/REQUIRED_CHECKS.md, tests/meta/test_required_checks_doc_sync.py |
| 12 | Authority/owning bounded context | CI orchestration / Register F preventive gate |
| 13 | Positive impact | Automated regression block for PC-033 closure criteria. |
| 14 | Potential negative impact | CI friction on related file changes. |
| 15 | Other findings affected | PC-002, PC-034, PC-034.a |
| 16 | Required downstream revalidation | IVV synthetic regression injection for PC-033 |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register F |
| 18 | Objective acceptance criteria | Renamed job without doc update fails meta-test. |
| 19 | Verification mechanism | CI meta-test doc sync |
| 20 | Failure condition | Required checks doc drift |
| 21 | Evidence output required | E-CI/required-checks-sync-test.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### PCtrl-034 — Combined quality report mandatory on main

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | PCtrl-034 |
| 2 | Finding ID | PC-034 |
| 3 | Control type | PREVENTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 enabling condition for PC-034 recurrence: existing controls did not block reintroduction of Security subset pass claims decoupled from full regression health.. |
| 5 | Exact repository evidence files | tests/test_security.py, .github/workflows/ci.yml, .github/workflows/security.yml |
| 6 | Exact symbols/settings/routes/tables/functions | pytest selections |
| 7 | Current defective behavior | Without blocking gate, PC-034 defect pattern can return via refactor or config drift undetected in CI. |
| 8 | Required target behavior | Main branch CI must upload combined_quality_report.json; branch protection references it. |
| 9 | Control mechanism | Artifact retention policy + required check referencing combined report on main. |
| 10 | Enforcement point | GitHub branch protection |
| 11 | Explicit affected files or bounded file families | .github/workflows/ci.yml, docs/ci/REQUIRED_CHECKS.md, tests/meta/test_combined_quality_artifact.py (PROPOSED_ARTIFACT) |
| 12 | Authority/owning bounded context | CI evidence / Register F, L preventive gate |
| 13 | Positive impact | Automated regression block for PC-034 closure criteria. |
| 14 | Potential negative impact | CI friction on related file changes. |
| 15 | Other findings affected | PC-033, PC-034.a |
| 16 | Required downstream revalidation | IVV synthetic regression injection for PC-034 |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register F |
| 18 | Objective acceptance criteria | Main run missing combined artifact fails release gate script. |
| 19 | Verification mechanism | Branch protection artifact check |
| 20 | Failure condition | Combined artifact missing on main |
| 21 | Evidence output required | E-CI/combined-quality-gate-log.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### PCtrl-035 — G3 metrics completeness threshold in assessor

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | PCtrl-035 |
| 2 | Finding ID | PC-035 |
| 3 | Control type | PREVENTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 enabling condition for PC-035 recurrence: existing controls did not block reintroduction of G3 soak may lack platform-level metric completeness for institutional trends.. |
| 5 | Exact repository evidence files | infra_metrics.py, bd_platform/infra_status.py |
| 6 | Exact symbols/settings/routes/tables/functions | service_mode reporting; platform infra endpoints |
| 7 | Current defective behavior | Without blocking gate, PC-035 defect pattern can return via refactor or config drift undetected in CI. |
| 8 | Required target behavior | G3 assessor WARN/FAIL when platform metrics completeness below 90%. |
| 9 | Control mechanism | Completeness score in g3_reliability_soak_test.py performance section blocks institutional PASS below 90%. |
| 10 | Enforcement point | G3 harness execution gate |
| 11 | Explicit affected files or bounded file families | scripts/g3_reliability_soak_test.py, bd_platform/infra_status.py |
| 12 | Authority/owning bounded context | Observability / Register G preventive gate |
| 13 | Positive impact | Automated regression block for PC-035 closure criteria. |
| 14 | Potential negative impact | CI friction on related file changes. |
| 15 | Other findings affected | PC-029, PC-011 |
| 16 | Required downstream revalidation | IVV synthetic regression injection for PC-035 |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register G |
| 18 | Objective acceptance criteria | Assessor FAIL when >10% platforms silent. |
| 19 | Verification mechanism | G3 harness FAIL on low completeness |
| 20 | Failure condition | Completeness threshold advisory only |
| 21 | Evidence output required | E-G3/metrics-completeness-gate.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### PCtrl-036 — Blocking taxonomy integrity validation

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | PCtrl-036 |
| 2 | Finding ID | PC-036 |
| 3 | Control type | PREVENTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 enabling condition for PC-036 recurrence: existing controls did not block reintroduction of Third taxonomy referenced in governance cannot be inspected; no single authority. |
| 5 | Exact repository evidence files | FEATURE_REALITY_MATRIX.md (HISTORICAL_REFERENCE_NOT_PRESENT), bd_platform/registry.py, auth_service.py, plan_audit.py |
| 6 | Exact symbols/settings/routes/tables/functions | FEATURE_MATRIX, TIER_FEATURES, plan audit list; absent audit matrix |
| 7 | Current defective behavior | Without blocking gate, PC-036 defect pattern can return via refactor or config drift undetected in CI. |
| 8 | Required target behavior | Blocking preventive validation: duplicate authority detection, dangling ref detection, historical-as-live rejection, taxonomy inversion detection via ssot-doc-lint and CI. |
| 9 | Control mechanism | scripts/ssot_doc_lint.py (PROPOSED_ARTIFACT) blocking rules: DUPLICATE_TAXONOMY_AUTHORITY, DANGLING_TAXONOMY_REF, HISTORICAL_AS_LIVE, TAXONOMY_INVERSION; tests/governance/test_taxonomy_integrity.py (PROPOSED_ARTIFACT). |
| 10 | Enforcement point | CI merge gate — blocks taxonomy drift |
| 11 | Explicit affected files or bounded file families | scripts/ssot_doc_lint.py (PROPOSED_ARTIFACT), governance/taxonomy_authority_registry.json (PROPOSED_ARTIFACT), tests/governance/test_taxonomy_integrity.py (PROPOSED_ARTIFACT) |
| 12 | Authority/owning bounded context | Feature taxonomy governance / Register A, K preventive gate |
| 13 | Positive impact | Automated regression block for PC-036 closure criteria. |
| 14 | Potential negative impact | CI friction on related file changes. |
| 15 | Other findings affected | PC-015, PC-015.a, PC-036, PC-023 |
| 16 | Required downstream revalidation | IVV synthetic regression injection for PC-036 |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register A |
| 18 | Objective acceptance criteria | Duplicate authority or dangling ref or historical-as-live marker fails blocking lint. |
| 19 | Verification mechanism | CI taxonomy integrity test suite |
| 20 | Failure condition | Missing matrix referenced as live authority |
| 21 | Evidence output required | E-GOV/taxonomy-integrity-block-log.json |
| 22 | Architectural-decision compatibility | DEC-A: APPLICABLE — one enumeration authority per layer; DEC-B: APPLICABLE — crosswalk separated from roadmap and tier taxonomies; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### PCtrl-037 — Blocking attestation integrity validation

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | PCtrl-037 |
| 2 | Finding ID | PC-037 |
| 3 | Control type | PREVENTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 enabling condition for PC-037 recurrence: existing controls did not block reintroduction of Marketing docs exceed attested scope; unattested/generated/capability-derived/na. |
| 5 | Exact repository evidence files | docs/MKT_COMPETITIVE_MATRIX.md, docs/MKT_ICP.md, docs/MKT_MARKET_BARRIERS.md, bd_platform/registry.py |
| 6 | Exact symbols/settings/routes/tables/functions | marketing claims; FEATURE_MATRIX; docs/institutional/ (HISTORICAL_REFERENCE_NOT_PRESENT) |
| 7 | Current defective behavior | Without blocking gate, PC-037 defect pattern can return via refactor or config drift undetected in CI. |
| 8 | Required target behavior | Blocking validation of signature, source integrity, immutable identity, amendment lineage, crosswalk separation. |
| 9 | Control mechanism | scripts/validate_attestation_integrity.py (PROPOSED_ARTIFACT) blocking CI: signature verify, source hash, immutable F-id check, amendment lineage, crosswalk file separation from navigation index. |
| 10 | Enforcement point | CI merge gate on attestation and MKT paths |
| 11 | Explicit affected files or bounded file families | scripts/validate_attestation_integrity.py (PROPOSED_ARTIFACT), docs/MKT_*.md, governance/feature_publication_registry.json (PROPOSED_ARTIFACT) |
| 12 | Authority/owning bounded context | Feature attestation / Register A, K preventive gate |
| 13 | Positive impact | Automated regression block for PC-037 closure criteria. |
| 14 | Potential negative impact | CI friction on related file changes. |
| 15 | Other findings affected | PC-003, PC-015.b, PC-038 |
| 16 | Required downstream revalidation | IVV synthetic regression injection for PC-037 |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register A |
| 18 | Objective acceptance criteria | Unattested feature list in publication registry or missing MKT disclaimer fails blocking validator. |
| 19 | Verification mechanism | CI blocking attestation integrity job |
| 20 | Failure condition | Marketing claims without disclaimer merge |
| 21 | Evidence output required | E-GOV/attestation-integrity-block-log.json |
| 22 | Architectural-decision compatibility | DEC-A: APPLICABLE — owner-attested enumeration is sole canonical source; DEC-B: APPLICABLE — crosswalk publication separated from marketing and navigation; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### PCtrl-038 — Legal map completeness on feature registry changes

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | PCtrl-038 |
| 2 | Finding ID | PC-038 |
| 3 | Control type | PREVENTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 enabling condition for PC-038 recurrence: existing controls did not block reintroduction of Legal/compliance text drifts from feature capability claims; no feature-id linka. |
| 5 | Exact repository evidence files | legal_content.py, regulatory_compliance_guard.py |
| 6 | Exact symbols/settings/routes/tables/functions | REGULATORY_DISCLAIMER, compliance verdict constants |
| 7 | Current defective behavior | Without blocking gate, PC-038 defect pattern can return via refactor or config drift undetected in CI. |
| 8 | Required target behavior | CI fails when FEATURE_REGISTRY attestation adds feature without LEGAL_FEATURE_MAP entry. |
| 9 | Control mechanism | tests/legal/test_feature_legal_coverage.py path-filtered on attestation file changes. |
| 10 | Enforcement point | CI path-filter merge gate |
| 11 | Explicit affected files or bounded file families | legal_content.py, tests/legal/test_feature_legal_coverage.py |
| 12 | Authority/owning bounded context | Legal compliance / Register L preventive gate |
| 13 | Positive impact | Automated regression block for PC-038 closure criteria. |
| 14 | Potential negative impact | CI friction on related file changes. |
| 15 | Other findings affected | PC-037, PC-003 |
| 16 | Required downstream revalidation | IVV synthetic regression injection for PC-038 |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register L |
| 18 | Objective acceptance criteria | New F-id without legal map fails CI. |
| 19 | Verification mechanism | CI path-filter legal test |
| 20 | Failure condition | Legal map not consulted by guard |
| 21 | Evidence output required | E-LEGAL/legal-coverage-gate.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### PCtrl-039 — Collection baseline monotonicity guard

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | PCtrl-039 |
| 2 | Finding ID | PC-039 |
| 3 | Control type | PREVENTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 enabling condition for PC-039 recurrence: existing controls did not block reintroduction of Documented Wave 1 full regression count cannot be verified; wave1 file absent.. |
| 5 | Exact repository evidence files | data/wave1_full_regression.txt (HISTORICAL_REFERENCE_NOT_PRESENT), tests/, .github/workflows/ci.yml |
| 6 | Exact symbols/settings/routes/tables/functions | (absent baseline file) |
| 7 | Current defective behavior | Without blocking gate, PC-039 defect pattern can return via refactor or config drift undetected in CI. |
| 8 | Required target behavior | CI fails if collection count drops below baseline without explicit baseline regeneration PR. |
| 9 | Control mechanism | Baseline compare in collection gate job blocks count decrease without labeled regen PR. |
| 10 | Enforcement point | CI collection gate |
| 11 | Explicit affected files or bounded file families | data/ci/test_collection_baseline.json, .github/workflows/ci.yml |
| 12 | Authority/owning bounded context | Test baseline / Register F preventive gate |
| 13 | Positive impact | Automated regression block for PC-039 closure criteria. |
| 14 | Potential negative impact | CI friction on related file changes. |
| 15 | Other findings affected | PC-002, PC-022.a |
| 16 | Required downstream revalidation | IVV synthetic regression injection for PC-039 |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register F |
| 18 | Objective acceptance criteria | Deleting tests without baseline update fails gate. |
| 19 | Verification mechanism | CI baseline monotonicity check |
| 20 | Failure condition | Baseline file absent |
| 21 | Evidence output required | E-TEST/baseline-monotonicity-log.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### PCtrl-040 — G2 schema_version required in validator

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | PCtrl-040 |
| 2 | Finding ID | PC-040 |
| 3 | Control type | PREVENTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 enabling condition for PC-040 recurrence: existing controls did not block reintroduction of G2 JSON logs lack schema_version; cross-run comparison breaks silently on shape . |
| 5 | Exact repository evidence files | data/g2_validation_logs/, scripts/g2_live_ws_validation.py |
| 6 | Exact symbols/settings/routes/tables/functions | JSON log structure |
| 7 | Current defective behavior | Without blocking gate, PC-040 defect pattern can return via refactor or config drift undetected in CI. |
| 8 | Required target behavior | Evidence validator hard-fails G2 logs missing schema_version field. |
| 9 | Control mechanism | validate_evidence.py G2 section hard-fails unversioned logs. |
| 10 | Enforcement point | CI evidence validation merge gate |
| 11 | Explicit affected files or bounded file families | scripts/validate_evidence.py (PROPOSED_ARTIFACT), schemas/g2_log.schema.json |
| 12 | Authority/owning bounded context | G2 evidence / Register G preventive gate |
| 13 | Positive impact | Automated regression block for PC-040 closure criteria. |
| 14 | Potential negative impact | CI friction on related file changes. |
| 15 | Other findings affected | PC-029 |
| 16 | Required downstream revalidation | IVV synthetic regression injection for PC-040 |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register G |
| 18 | Objective acceptance criteria | Unversioned log rejected by validator. |
| 19 | Verification mechanism | CI G2 schema_version check |
| 20 | Failure condition | Validator accepts unversioned log |
| 21 | Evidence output required | E-G2/g2-version-validator-log.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### PCtrl-041 — Float ban lint on authoritative money modules

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | PCtrl-041 |
| 2 | Finding ID | PC-041 |
| 3 | Control type | PREVENTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 enabling condition for PC-041 recurrence: existing controls did not block reintroduction of Authoritative profit/fee paths compute in float before persist; threshold compar. |
| 5 | Exact repository evidence files | fee_matrix.py, fast_scan_engine.py, profit_fee_algorithms.py |
| 6 | Exact symbols/settings/routes/tables/functions | float arithmetic on bids/asks/fees/net profit |
| 7 | Current defective behavior | Without blocking gate, PC-041 defect pattern can return via refactor or config drift undetected in CI. |
| 8 | Required target behavior | CI AST lint forbids new float( casts in fee_matrix, fast_scan_engine, profit_fee_algorithms. |
| 9 | Control mechanism | scripts/lint_no_float_money.py (PROPOSED_ARTIFACT) AST scan blocking new float casts in money modules. |
| 10 | Enforcement point | CI merge gate on money modules |
| 11 | Explicit affected files or bounded file families | fee_matrix.py, fast_scan_engine.py, profit_fee_algorithms.py, scripts/lint_no_float_money.py (PROPOSED_ARTIFACT) |
| 12 | Authority/owning bounded context | Financial compute / Register J preventive gate |
| 13 | Positive impact | Automated regression block for PC-041 closure criteria. |
| 14 | Potential negative impact | CI friction on related file changes. |
| 15 | Other findings affected | PC-006, PC-009.c |
| 16 | Required downstream revalidation | IVV synthetic regression injection for PC-041 |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register J |
| 18 | Objective acceptance criteria | New float cast in fast_scan_engine fails lint. |
| 19 | Verification mechanism | CI float-ban lint |
| 20 | Failure condition | Float cast merges undetected |
| 21 | Evidence output required | E-DATA/float-ban-lint.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### PCtrl-042 — ssot-doc-lint required on every docs PR

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | PCtrl-042 |
| 2 | Finding ID | PC-042 |
| 3 | Control type | PREVENTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 enabling condition for PC-042 recurrence: existing controls did not block reintroduction of ssot-doc-lint specified but scripts/ssot_doc_lint.py not implemented; governance. |
| 5 | Exact repository evidence files | docs/**/*.md, FEATURE_REALITY_MATRIX.md (HISTORICAL_REFERENCE_NOT_PRESENT), WAVE2_MASTER_REFERENCE_INDEX.md (HISTORICAL_REFERENCE_NOT_PRESENT) |
| 6 | Exact symbols/settings/routes/tables/functions | ssot-doc-lint contract in REMEDIATION_VERIFICATION_STANDARD v3.0 |
| 7 | Current defective behavior | Without blocking gate, PC-042 defect pattern can return via refactor or config drift undetected in CI. |
| 8 | Required target behavior | CI ssot-doc-lint job runs on all PRs touching docs/** or governance paths; merge blocked on violation. |
| 9 | Control mechanism | Path-filtered required job in ci.yml; branch protection enforces ssot-doc-lint. |
| 10 | Enforcement point | CI branch protection required check |
| 11 | Explicit affected files or bounded file families | scripts/ssot_doc_lint.py, .github/workflows/ci.yml, tests/governance/test_ssot_doc_lint.py |
| 12 | Authority/owning bounded context | SSOT governance / Register K preventive gate |
| 13 | Positive impact | Automated regression block for PC-042 closure criteria. |
| 14 | Potential negative impact | CI friction on related file changes. |
| 15 | Other findings affected | PC-015, PC-036, PC-037, PC-032, PC-018 |
| 16 | Required downstream revalidation | IVV synthetic regression injection for PC-042 |
| 17 | Shared ownership or NONE with justification | NONE — single bounded-context owner per Register K |
| 18 | Objective acceptance criteria | Duplicate SSOT fixture doc fails required job. |
| 19 | Verification mechanism | CI required ssot-doc-lint job |
| 20 | Failure condition | ssot-doc-lint skipped on docs PR |
| 21 | Evidence output required | E-GOV/ssot-doc-lint-gate-log.json |
| 22 | Architectural-decision compatibility | DEC-A: APPLICABLE — lint enforces single enumeration authority declarations; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

---

## Sub-Finding Corrective Controls

### CC-008.a — Unify AUTO_EXECUTION_LOOP defaults across three sources

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | CC-008.a |
| 2 | Finding ID | PC-008.a |
| 3 | Control type | CORRECTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 sub-finding PC-008.a (parent PC-008): Orchestrator default false, engine status default true, compose sets true — three sources disagree. |
| 5 | Exact repository evidence files | startup_orchestrator.py, execution_engine.py, docker-compose.yml |
| 6 | Exact symbols/settings/routes/tables/functions | AUTO_EXECUTION_LOOP defaults |
| 7 | Current defective behavior | Orchestrator default false, engine status default true, compose sets true — three sources disagree. |
| 8 | Required target behavior | Single documented AUTO_EXECUTION_LOOP default per deployment profile in DEPLOYMENT_PROFILE_CONTRACT. |
| 9 | Control mechanism | Profile matrix in DEPLOYMENT_PROFILE_CONTRACT; compose overrides generated from matrix not hand-edited. |
| 10 | Enforcement point | Startup + CI |
| 11 | Explicit affected files or bounded file families | startup_orchestrator.py, execution_engine.py, docker-compose.yml, docs/institutional/DEPLOYMENT_PROFILE_CONTRACT.md (PROPOSED_ARTIFACT) |
| 12 | Authority/owning bounded context | Composition root / Register B |
| 13 | Positive impact | Operators know auto-exec posture from one default table. |
| 14 | Potential negative impact | Compose regen required on default change. |
| 15 | Other findings affected | PC-005, PC-007, PC-031 |
| 16 | Required downstream revalidation | IVV three-source default table per profile |
| 17 | Shared ownership or NONE with justification | NONE — sub-finding PC-008.a owned under Register B independently of parent closure |
| 18 | Objective acceptance criteria | Default parity test passes for orchestrator, engine, compose per profile. |
| 19 | Verification mechanism | Default extraction test |
| 20 | Failure condition | Unintended auto-exec loop starts |
| 21 | Evidence output required | E-STARTUP/auto-exec-default-unify.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### CC-008.b — Machine-readable route inventory artifact

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | CC-008.b |
| 2 | Finding ID | PC-008.b |
| 3 | Control type | CORRECTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 sub-finding PC-008.b (parent PC-008): 61 handlers in monolith; route ownership not machine-attributed to P01-P16. |
| 5 | Exact repository evidence files | platform_api.py |
| 6 | Exact symbols/settings/routes/tables/functions | 61 @router decorators, /api/platform prefix |
| 7 | Current defective behavior | 61 handlers in monolith; route ownership not machine-attributed to P01-P16. |
| 8 | Required target behavior | Generate governance/platform_route_inventory.json listing all routes with P01-P16 owner, method, path. |
| 9 | Control mechanism | OpenAPI introspection script run in CI producing signed route inventory artifact. |
| 10 | Enforcement point | CI artifact + merge gate |
| 11 | Explicit affected files or bounded file families | platform_api.py, governance/platform_route_inventory.json (PROPOSED_ARTIFACT) |
| 12 | Authority/owning bounded context | Platform API / Register B |
| 13 | Positive impact | Route ownership auditable for change control. |
| 14 | Potential negative impact | Inventory regen on every route add. |
| 15 | Other findings affected | PC-009, PC-008.b |
| 16 | Required downstream revalidation | IVV inventory count equals live routes |
| 17 | Shared ownership or NONE with justification | NONE — sub-finding PC-008.b owned under Register B independently of parent closure |
| 18 | Objective acceptance criteria | Inventory count equals live route count; each route has owner field. |
| 19 | Verification mechanism | OpenAPI introspection diff |
| 20 | Failure condition | Orphan route without owner |
| 21 | Evidence output required | E-PLATFORM/route-inventory.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### CC-008.c — Decision pipeline scope decision artifact

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | CC-008.c |
| 2 | Finding ID | PC-008.c |
| 3 | Control type | CORRECTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 sub-finding PC-008.c (parent PC-008): Decision scoring module absent; P06/P10 boundary unimplemented. |
| 5 | Exact repository evidence files | decision_intelligence_pipeline.py (HISTORICAL_REFERENCE_NOT_PRESENT), research_lab.py, api/routers/oracle.py |
| 6 | Exact symbols/settings/routes/tables/functions | missing decision_intelligence_pipeline.py; oracle scoring ad hoc |
| 7 | Current defective behavior | Decision scoring module absent; P06/P10 boundary unimplemented. |
| 8 | Required target behavior | Either commit decision_intelligence_pipeline.py with boundary tests OR publish signed scope-retirement record. |
| 9 | Control mechanism | PROPOSED_ARTIFACT — STAGE 3 MUST DECIDE LOCATION: decision_intelligence_pipeline.py OR docs/institutional/ADR_DECISION_PIPELINE.md signed retirement. |
| 10 | Enforcement point | Governance + CI |
| 11 | Explicit affected files or bounded file families | decision_intelligence_pipeline.py (PROPOSED_ARTIFACT) OR docs/institutional/ADR_DECISION_PIPELINE.md (PROPOSED_ARTIFACT) |
| 12 | Authority/owning bounded context | Decision intelligence / Register B, I |
| 13 | Positive impact | P06/P10 boundary explicitly committed or retired. |
| 14 | Potential negative impact | Scope retirement requires owner sign-off. |
| 15 | Other findings affected | PC-012, PC-008 |
| 16 | Required downstream revalidation | IVV module-exists XOR retirement-signed |
| 17 | Shared ownership or NONE with justification | NONE — sub-finding PC-008.c owned under Register B independently of parent closure |
| 18 | Objective acceptance criteria | One of: module exists with tests OR retirement ADR signed — not both absent. |
| 19 | Verification mechanism | ADR presence check + module test |
| 20 | Failure condition | Both module and ADR absent |
| 21 | Evidence output required | E-ARCH/decision-pipeline-scope.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### CC-008.d — Single compliance facade for all verdict emitters

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | CC-008.d |
| 2 | Finding ID | PC-008.d |
| 3 | Control type | CORRECTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 sub-finding PC-008.d (parent PC-008): Compliance transformation imported from multiple route call sites without mandatory facade. |
| 5 | Exact repository evidence files | regulatory_compliance_guard.py, dashboard.py, platform routes |
| 6 | Exact symbols/settings/routes/tables/functions | apply_regulatory_compliance, to_public_verdict |
| 7 | Current defective behavior | Compliance transformation imported from multiple route call sites without mandatory facade. |
| 8 | Required target behavior | Route all public verdict fields through compliance_facade.to_public_verdict(); remove duplicate guard calls. |
| 9 | Control mechanism | PROPOSED_ARTIFACT — STAGE 3 MUST DECIDE LOCATION: compliance_facade.py; refactor dashboard and platform routes to single import. |
| 10 | Enforcement point | Static analysis + CI |
| 11 | Explicit affected files or bounded file families | regulatory_compliance_guard.py, dashboard.py, compliance_facade.py (PROPOSED_ARTIFACT), platform_api.py |
| 12 | Authority/owning bounded context | Regulatory compliance / Register L |
| 13 | Positive impact | Consistent regulatory wording on all verdict endpoints. |
| 14 | Potential negative impact | Route refactor to single facade import. |
| 15 | Other findings affected | PC-024, PC-008.d |
| 16 | Required downstream revalidation | IVV zero direct apply_regulatory_compliance outside facade |
| 17 | Shared ownership or NONE with justification | NONE — sub-finding PC-008.d owned under Register L independently of parent closure |
| 18 | Objective acceptance criteria | Zero direct apply_regulatory_compliance outside facade module. |
| 19 | Verification mechanism | AST verdict emitter scan |
| 20 | Failure condition | Route returns verdict without facade |
| 21 | Evidence output required | E-LEGAL/compliance-facade-wrap.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### CC-009.a — API layer import allow list to P13 facades only

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | CC-009.a |
| 2 | Finding ID | PC-009.a |
| 3 | Control type | CORRECTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 sub-finding PC-009.a (parent PC-009): API layer reaches platform internals bypassing P13 facades. |
| 5 | Exact repository evidence files | platform_api.py |
| 6 | Exact symbols/settings/routes/tables/functions | direct bd_platform.* imports throughout file |
| 7 | Current defective behavior | API layer reaches platform internals bypassing P13 facades. |
| 8 | Required target behavior | Replace direct bd_platform imports with facade modules per platform. |
| 9 | Control mechanism | PROPOSED_ARTIFACT — STAGE 3 MUST DECIDE LOCATION: bd_platform/facades/ package; platform_api imports only facades. |
| 10 | Enforcement point | prohibited-import lint + CI |
| 11 | Explicit affected files or bounded file families | platform_api.py, bd_platform/facades/ (PROPOSED_ARTIFACT family) |
| 12 | Authority/owning bounded context | Platform facade / Register B |
| 13 | Positive impact | DEC-E import boundaries measurable from API layer. |
| 14 | Potential negative impact | Facade creation per platform touchpoint. |
| 15 | Other findings affected | PC-009, PC-009.a |
| 16 | Required downstream revalidation | IVV lint zero violations API to internal |
| 17 | Shared ownership or NONE with justification | NONE — sub-finding PC-009.a owned under Register B independently of parent closure |
| 18 | Objective acceptance criteria | Lint reports zero violations from API layer to internal modules. |
| 19 | Verification mechanism | Import graph lint |
| 20 | Failure condition | Direct bd_platform import in API layer |
| 21 | Evidence output required | E-PLATFORM/api-facade-imports.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### CC-009.b — Non-authoritative labeling on grid API responses

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | CC-009.b |
| 2 | Finding ID | PC-009.b |
| 3 | Control type | CORRECTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 sub-finding PC-009.b (parent PC-009): Import success equals live feature in API summaries. |
| 5 | Exact repository evidence files | bd_platform/registry.py |
| 6 | Exact symbols/settings/routes/tables/functions | FEATURE_MATRIX, feature_summary() |
| 7 | Current defective behavior | Import success equals live feature in API summaries. |
| 8 | Required target behavior | Add enumeration_authority:roadmap_grid_not_attested on feature summary responses. |
| 9 | Control mechanism | registry.py response schema change + OpenAPI doc update on /api/platform/features. |
| 10 | Enforcement point | API contract test + CI |
| 11 | Explicit affected files or bounded file families | bd_platform/registry.py, dashboard.py /api/platform/features route |
| 12 | Authority/owning bounded context | Feature enumeration / Register A |
| 13 | Positive impact | API consumers cannot treat grid as attested enumeration. |
| 14 | Potential negative impact | Response schema change for clients. |
| 15 | Other findings affected | PC-003, PC-015.b |
| 16 | Required downstream revalidation | IVV response JSON field presence |
| 17 | Shared ownership or NONE with justification | NONE — sub-finding PC-009.b owned under Register A independently of parent closure |
| 18 | Objective acceptance criteria | Response JSON contains enumeration_authority field; missing field fails contract test. |
| 19 | Verification mechanism | API response assertion |
| 20 | Failure condition | Grid response lacks authority marker |
| 21 | Evidence output required | E-GOV/grid-authority-label.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### CC-009.c — Decimal float elimination in fee_matrix and fast_scan_engine scan path

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | CC-009.c |
| 2 | Finding ID | PC-009.c |
| 3 | Control type | CORRECTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 sub-finding PC-009.c (parent PC-009): Fee and profit scan paths compute in float before threshold compare; marginal opportunities flip near boundaries. |
| 5 | Exact repository evidence files | fee_matrix.py, fast_scan_engine.py |
| 6 | Exact symbols/settings/routes/tables/functions | float tables; L19-24 float conversion on bids/asks/fees |
| 7 | Current defective behavior | Fee and profit scan paths compute in float before threshold compare; marginal opportunities flip near boundaries. |
| 8 | Required target behavior | Migrate fee_matrix.py and fast_scan_engine.py only to decimal.Decimal for authoritative scan-path comparisons before persist or authorization. |
| 9 | Control mechanism | Decimal math in fee_matrix.py and fast_scan_engine.py hot paths with documented quantization; independent of database.py and profit_fee_algorithms.py migration schedule. |
| 10 | Enforcement point | Property tests + CI |
| 11 | Explicit affected files or bounded file families | fee_matrix.py, fast_scan_engine.py |
| 12 | Authority/owning bounded context | Financial scan compute / Register J, C |
| 13 | Positive impact | Scan threshold comparisons exact at boundary; independent closure from PC-041 database path. |
| 14 | Potential negative impact | Scan loop performance may decrease vs native float. |
| 15 | Other findings affected | PC-041, PC-006 |
| 16 | Required downstream revalidation | IVV boundary tests at 0.0001 USDT on scan modules only |
| 17 | Shared ownership or NONE with justification | NONE — sub-finding PC-009.c owned under Register J independently of parent closure |
| 18 | Objective acceptance criteria | Boundary property tests at 0.0001 USDT thresholds pass exactly on fee_matrix and fast_scan_engine outputs. |
| 19 | Verification mechanism | Hypothesis property tests on scan output |
| 20 | Failure condition | Float cast reintroduced in fast_scan_engine |
| 21 | Evidence output required | E-DATA/scan-decimal-migration.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: APPLICABLE — scan path uses authoritative decimal before execution authorization; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### CC-009.d — Single portfolio read repository

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | CC-009.d |
| 2 | Finding ID | PC-009.d |
| 3 | Control type | CORRECTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 sub-finding PC-009.d (parent PC-009): Holdings display and rebalance preview may disagree across dashboard and rebalancer. |
| 5 | Exact repository evidence files | bd_platform/portfolio_rebalancer.py, dashboard.py |
| 6 | Exact symbols/settings/routes/tables/functions | portfolio rebalance API; dashboard holdings routes |
| 7 | Current defective behavior | Holdings display and rebalance preview may disagree across dashboard and rebalancer. |
| 8 | Required target behavior | Consolidate to portfolio_read_model.py single source for UI and API rebalance preview. |
| 9 | Control mechanism | PROPOSED_ARTIFACT — STAGE 3 MUST DECIDE LOCATION: portfolio_read_model.py; dashboard routes call read model. |
| 10 | Enforcement point | Contract test + CI |
| 11 | Explicit affected files or bounded file families | bd_platform/portfolio_rebalancer.py, dashboard.py, portfolio_read_model.py (PROPOSED_ARTIFACT) |
| 12 | Authority/owning bounded context | Portfolio authority / Register B, C |
| 13 | Positive impact | CAP-081 single read authority for P05. |
| 14 | Potential negative impact | Dashboard route refactor to read model. |
| 15 | Other findings affected | PC-009, PC-009.d |
| 16 | Required downstream revalidation | IVV fixture holdings hash match |
| 17 | Shared ownership or NONE with justification | NONE — sub-finding PC-009.d owned under Register B independently of parent closure |
| 18 | Objective acceptance criteria | UI and API rebalance preview return identical holdings hash for fixture user. |
| 19 | Verification mechanism | Contract test fixture comparison |
| 20 | Failure condition | Dual holdings numbers shown to user |
| 21 | Evidence output required | E-PLATFORM/portfolio-read-model.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### CC-010.a — Connector DENY without authorize_execution

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | CC-010.a |
| 2 | Finding ID | PC-010.a |
| 3 | Control type | CORRECTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 sub-finding PC-010.a (parent PC-010): CEX-DEX executor delegates to execute_order without unified authorize_execution gate. |
| 5 | Exact repository evidence files | bd_platform/cex_dex_executor.py |
| 6 | Exact symbols/settings/routes/tables/functions | execute_cex_dex_opportunity L49-52; CEX_DEX_EXECUTION_ENABLED |
| 7 | Current defective behavior | CEX-DEX executor delegates to execute_order without unified authorize_execution gate. |
| 8 | Required target behavior | cex_dex_executor raises ExecutionDenied before execute_order when authorize_execution returns false. |
| 9 | Control mechanism | Guard call at L49 before delegation; CEX_DEX flag subordinate to master EXECUTION_ENABLED. |
| 10 | Enforcement point | Security negative tests + CI |
| 11 | Explicit affected files or bounded file families | bd_platform/cex_dex_executor.py, execution_authorization.py (PROPOSED_ARTIFACT) |
| 12 | Authority/owning bounded context | Connector execution / Register D |
| 13 | Positive impact | CEX-DEX path cannot bypass institutional execution gate. |
| 14 | Potential negative impact | Extra latency on arb execute POST. |
| 15 | Other findings affected | PC-005, PC-010 |
| 16 | Required downstream revalidation | IVV cex-dex bypass matrix DENY |
| 17 | Shared ownership or NONE with justification | NONE — sub-finding PC-010.a owned under Register D independently of parent closure |
| 18 | Objective acceptance criteria | Direct POST execute with master off returns 403/deny regardless of CEX_DEX flag. |
| 19 | Verification mechanism | Security negative matrix |
| 20 | Failure condition | Live CEX leg with master off |
| 21 | Evidence output required | E-EXEC/cex-dex-deny-wrap.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### CC-011.a — Hourly stale integrity veto in G3 assessor

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | CC-011.a |
| 2 | Finding ID | PC-011.a |
| 3 | Control type | CORRECTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 sub-finding PC-011.a (parent PC-011): Assessor can PASS with degraded hourly integrity if weighting allows partial hours. |
| 5 | Exact repository evidence files | scripts/g3_reliability_soak_test.py |
| 6 | Exact symbols/settings/routes/tables/functions | integrity thresholds stale >10%; HOURLY_OPERATION_REPORTS/ |
| 7 | Current defective behavior | Assessor can PASS with degraded hourly integrity if weighting allows partial hours. |
| 8 | Required target behavior | G3 assessor FAIL when any hour exceeds stale threshold; emit hourly integrity artifact. |
| 9 | Control mechanism | Hourly veto logic in g3_reliability_soak_test.py; output HOURLY_OPERATION_REPORTS/ JSON per hour. |
| 10 | Enforcement point | G3 harness + CI |
| 11 | Explicit affected files or bounded file families | scripts/g3_reliability_soak_test.py, HOURLY_OPERATION_REPORTS/ (PROPOSED_ARTIFACT output dir) |
| 12 | Authority/owning bounded context | G3 integrity / Register G |
| 13 | Positive impact | Institutional 24h gate cannot pass with bad hour. |
| 14 | Potential negative impact | Stricter soak may extend finalize time. |
| 15 | Other findings affected | PC-011, PC-011.b |
| 16 | Required downstream revalidation | IVV stale hour injection unit test |
| 17 | Shared ownership or NONE with justification | NONE — sub-finding PC-011.a owned under Register G independently of parent closure |
| 18 | Objective acceptance criteria | Unit test injecting stale hour produces FAIL assessment with signed hourly artifact. |
| 19 | Verification mechanism | Stale hour fixture test |
| 20 | Failure condition | Bad hour ignored in assessor |
| 21 | Evidence output required | E-G3/hourly-veto-logic.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### CC-011.b — gate_scope schema field with hours cross-validation

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | CC-011.b |
| 2 | Finding ID | PC-011.b |
| 3 | Control type | CORRECTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 sub-finding PC-011.b (parent PC-011): Pilot and institutional durations share assessor without machine-readable scope distinction. |
| 5 | Exact repository evidence files | scripts/g3_reliability_soak_test.py, schemas/g3_assessment.schema.json |
| 6 | Exact symbols/settings/routes/tables/functions | --hours min 1; no gate_scope field |
| 7 | Current defective behavior | Pilot and institutional durations share assessor without machine-readable scope distinction. |
| 8 | Required target behavior | Schema requires gate_scope; validator rejects INSTITUTIONAL_24H when hours < 24. |
| 9 | Control mechanism | JSON schema if/then rules in g3_assessment.schema.json (PROPOSED_ARTIFACT). |
| 10 | Enforcement point | validate_evidence.py + CI |
| 11 | Explicit affected files or bounded file families | schemas/g3_assessment.schema.json (PROPOSED_ARTIFACT), scripts/g3_reliability_soak_test.py |
| 12 | Authority/owning bounded context | G3 schema / Register G |
| 13 | Positive impact | Misclassification of pilot as institutional blocked at validator. |
| 14 | Potential negative impact | Schema migration for existing artifacts. |
| 15 | Other findings affected | PC-011, PC-029 |
| 16 | Required downstream revalidation | IVV INSTITUTIONAL_24H with hours=1 fails |
| 17 | Shared ownership or NONE with justification | NONE — sub-finding PC-011.b owned under Register G independently of parent closure |
| 18 | Objective acceptance criteria | JSON with INSTITUTIONAL_24H and hours=1 fails validation. |
| 19 | Verification mechanism | JSON schema if/then |
| 20 | Failure condition | Institutional scope on 1-hour run accepted |
| 21 | Evidence output required | E-G3/gate-scope-crosswalk.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### CC-012.a — Deprecate parallel oracle entrypoints

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | CC-012.a |
| 2 | Finding ID | PC-012.a |
| 3 | Control type | CORRECTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 sub-finding PC-012.a (parent PC-012): research_lab and oracle_retrainer are parallel inference entrypoints outside stack facade. |
| 5 | Exact repository evidence files | research_lab.py, oracle_retrainer.py |
| 6 | Exact symbols/settings/routes/tables/functions | build_research_lab_report, run_oracle_retrain_step |
| 7 | Current defective behavior | research_lab and oracle_retrainer are parallel inference entrypoints outside stack facade. |
| 8 | Required target behavior | Mark exports deprecated; route callers through oracle_inference_stack. |
| 9 | Control mechanism | Deprecation warnings + caller migration checklist in oracle_inference_stack module doc. |
| 10 | Enforcement point | Import lint + CI |
| 11 | Explicit affected files or bounded file families | research_lab.py, oracle_retrainer.py, oracle_inference_stack.py (PROPOSED_ARTIFACT) |
| 12 | Authority/owning bounded context | Oracle entrypoints / Register I |
| 13 | Positive impact | Single oracle entry enforced over time. |
| 14 | Potential negative impact | Caller migration effort across routes. |
| 15 | Other findings affected | PC-012, PC-028 |
| 16 | Required downstream revalidation | IVV zero external callers outside stack |
| 17 | Shared ownership or NONE with justification | NONE — sub-finding PC-012.a owned under Register I independently of parent closure |
| 18 | Objective acceptance criteria | Zero production callers outside stack module per static analysis. |
| 19 | Verification mechanism | Static caller inventory diff |
| 20 | Failure condition | New direct oracle_retrainer caller |
| 21 | Evidence output required | E-ORACLE/entrypoint-deprecation.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### CC-012.b — CAP-053 lineage E2E proof artifact

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | CC-012.b |
| 2 | Finding ID | PC-012.b |
| 3 | Control type | CORRECTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 sub-finding PC-012.b (parent PC-012): Lineage fields not proven end-to-end signal→prediction→audit for each decision class. |
| 5 | Exact repository evidence files | research_lab.py, oracle_integrity.py, database oracle tables |
| 6 | Exact symbols/settings/routes/tables/functions | prediction_source, filter_live_predictions |
| 7 | Current defective behavior | Lineage fields not proven end-to-end signal→prediction→audit for each decision class. |
| 8 | Required target behavior | E2E test proving lineage fields populated for each decision class with signed JSON artifact. |
| 9 | Control mechanism | tests/e2e/test_oracle_lineage_cap053.py (PROPOSED_ARTIFACT) producing signed JSON artifact. |
| 10 | Enforcement point | CI blocking E2E |
| 11 | Explicit affected files or bounded file families | research_lab.py, oracle_integrity.py, database.py oracle tables, tests/e2e/test_oracle_lineage_cap053.py (PROPOSED_ARTIFACT) |
| 12 | Authority/owning bounded context | Oracle lineage / Register I |
| 13 | Positive impact | CAP-053 provenance DD-evidence ready. |
| 14 | Potential negative impact | E2E test maintenance on schema change. |
| 15 | Other findings affected | PC-012, PC-012.a |
| 16 | Required downstream revalidation | IVV artifact non-null lineage all classes |
| 17 | Shared ownership or NONE with justification | NONE — sub-finding PC-012.b owned under Register I independently of parent closure |
| 18 | Objective acceptance criteria | Artifact shows non-null lineage fields for all classes in matrix. |
| 19 | Verification mechanism | E2E test + schema validation |
| 20 | Failure condition | Null lineage in production path |
| 21 | Evidence output required | E-ORACLE/cap053-lineage-e2e.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### CC-013.a — Fixture key mode for CI reproducibility

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | CC-013.a |
| 2 | Finding ID | PC-013.a |
| 3 | Control type | CORRECTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 sub-finding PC-013.a (parent PC-013): Exchange validation depends on gitignored keys/ tree; CI cannot reproduce key-dependent tests. |
| 5 | Exact repository evidence files | .gitignore, execution_keys.py, keys/ |
| 6 | Exact symbols/settings/routes/tables/functions | keys/ gitignored; committed keys/ absent |
| 7 | Current defective behavior | Exchange validation depends on gitignored keys/ tree; CI cannot reproduce key-dependent tests. |
| 8 | Required target behavior | Commit sandbox fixture keys under tests/fixtures/keys/; KEYS_MODE fixture-or-live boundary documented. |
| 9 | Control mechanism | KEYS_MODE env; CI uses fixture; live jobs in separate workflow with secrets. |
| 10 | Enforcement point | CI + docs |
| 11 | Explicit affected files or bounded file families | .gitignore, execution_keys.py, tests/fixtures/keys/ (PROPOSED_ARTIFACT) |
| 12 | Authority/owning bounded context | Secrets CI / Register E |
| 13 | Positive impact | CI green without gitignored keys/ directory. |
| 14 | Potential negative impact | Live workflow separation documentation. |
| 15 | Other findings affected | PC-013, PC-013.a |
| 16 | Required downstream revalidation | IVV CI pass without keys/ dir |
| 17 | Shared ownership or NONE with justification | NONE — sub-finding PC-013.a owned under Register E independently of parent closure |
| 18 | Objective acceptance criteria | CI green without gitignored keys/; live workflow documented separately. |
| 19 | Verification mechanism | CI env KEYS_MODE check |
| 20 | Failure condition | CI depends on local keys/ |
| 21 | Evidence output required | E-SEC/fixture-key-mode.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### CC-013.b — Tenant context middleware on all user-scoped repositories

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | CC-013.b |
| 2 | Finding ID | PC-013.b |
| 3 | Control type | CORRECTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 sub-finding PC-013.b (parent PC-013): Subscription tier scoping is not multi-tenant org isolation; repositories lack tenant predicate. |
| 5 | Exact repository evidence files | auth_service.py, database.py |
| 6 | Exact symbols/settings/routes/tables/functions | TIER_FEATURES; user-scoped CRUD without tenant_id |
| 7 | Current defective behavior | Subscription tier scoping is not multi-tenant org isolation; repositories lack tenant predicate. |
| 8 | Required target behavior | Introduce tenant_id column pattern and middleware injecting tenant context; repositories require tenant filter. |
| 9 | Control mechanism | PROPOSED_ARTIFACT — STAGE 3 MUST DECIDE LOCATION: tenant_context.py middleware + db repository base class enforcing tenant predicate on user-scoped tables. |
| 10 | Enforcement point | Runtime middleware + independent CI path gate |
| 11 | Explicit affected files or bounded file families | database.py user-scoped repositories, tenant_context.py (PROPOSED_ARTIFACT), auth_service.py |
| 12 | Authority/owning bounded context | Tenancy isolation / Register E |
| 13 | Positive impact | Cross-tenant CRUD blocked at repository layer with independent CI enforcement. |
| 14 | Potential negative impact | Repository base class refactor across user tables. |
| 15 | Other findings affected | PC-013, PC-027 |
| 16 | Required downstream revalidation | IVV cross-tenant repository negative matrix independent of general tenant suite |
| 17 | Shared ownership or NONE with justification | NONE — sub-finding PC-013.b owned under Register E independently of parent closure |
| 18 | Objective acceptance criteria | Cross-tenant read/write on user-scoped repositories fail 403/404; DB repository change without isolation test update fails tenant-repository-isolation-gate independently. |
| 19 | Verification mechanism | Cross-tenant repository CRUD negatives |
| 20 | Failure condition | Cross-tenant repository read succeeds |
| 21 | Evidence output required | E-SEC/tenant-repository-middleware.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: APPLICABLE — P11 tenant repository isolation within modular monolith |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### CC-013.c — Production demo route deny at startup

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | CC-013.c |
| 2 | Finding ID | PC-013.c |
| 3 | Control type | CORRECTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 sub-finding PC-013.c (parent PC-013): Public demo feed reachable without production hard deny. |
| 5 | Exact repository evidence files | dashboard.py, config.py |
| 6 | Exact symbols/settings/routes/tables/functions | /api/b2b/demo L1401-1416; B2B_DEMO_API_KEY default |
| 7 | Current defective behavior | Public demo feed reachable without production hard deny. |
| 8 | Required target behavior | Remove or 404 /api/b2b/demo when ENV=production regardless of demo key env. |
| 9 | Control mechanism | production_route_filter excludes demo routes; startup audit confirms zero demo paths. |
| 10 | Enforcement point | Startup + security test + CI |
| 11 | Explicit affected files or bounded file families | dashboard.py, production_route_filter.py (PROPOSED_ARTIFACT), config.py |
| 12 | Authority/owning bounded context | Production demo isolation / Register E |
| 13 | Positive impact | Demo surface eliminated in production profile. |
| 14 | Potential negative impact | Demo testing only in non-prod profiles. |
| 15 | Other findings affected | PC-030, PC-013.c |
| 16 | Required downstream revalidation | IVV prod request to demo returns 404 |
| 17 | Shared ownership or NONE with justification | NONE — sub-finding PC-013.c owned under Register E independently of parent closure |
| 18 | Objective acceptance criteria | Production profile request to demo returns 404; audit log lists zero demo routes. |
| 19 | Verification mechanism | Prod profile HTTP test |
| 20 | Failure condition | Demo 200 in ENV=production |
| 21 | Evidence output required | E-SEC/demo-route-deny.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### CC-013.d — MFA policy and ADMIN_MFA_REQUIRED gate

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | CC-013.d |
| 2 | Finding ID | PC-013.d |
| 3 | Control type | CORRECTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 sub-finding PC-013.d (parent PC-013): Enterprise MFA/SSO not implemented for admin tier. |
| 5 | Exact repository evidence files | auth_service.py, dashboard.py admin routes |
| 6 | Exact symbols/settings/routes/tables/functions | ADMIN tier login; no MFA module |
| 7 | Current defective behavior | Enterprise MFA/SSO not implemented for admin tier. |
| 8 | Required target behavior | Implement TOTP/WebAuthn MFA for admin tier when ADMIN_MFA_REQUIRED=true. |
| 9 | Control mechanism | MFA module in auth_service; login flow branch; policy doc in SECURITY.md. |
| 10 | Enforcement point | Runtime + CI |
| 11 | Explicit affected files or bounded file families | auth_service.py, dashboard.py admin routes, SECURITY.md |
| 12 | Authority/owning bounded context | Admin MFA / Register E |
| 13 | Positive impact | Admin tier meets enterprise MFA expectation when flag set. |
| 14 | Potential negative impact | MFA enrollment UX for admins. |
| 15 | Other findings affected | PC-013, PC-013.d |
| 16 | Required downstream revalidation | IVV admin login MFA branch |
| 17 | Shared ownership or NONE with justification | NONE — sub-finding PC-013.d owned under Register E independently of parent closure |
| 18 | Objective acceptance criteria | Admin login without MFA fails when flag true; passes with valid second factor. |
| 19 | Verification mechanism | MFA integration test |
| 20 | Failure condition | Admin access with password only when MFA required |
| 21 | Evidence output required | E-SEC/admin-mfa-policy.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### CC-013.e — Signed production route manifest at startup

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | CC-013.e |
| 2 | Finding ID | PC-013.e |
| 3 | Control type | CORRECTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 sub-finding PC-013.e (parent PC-013): Dev/prod route parity not audited at startup. |
| 5 | Exact repository evidence files | dashboard.py, platform_api.py, production_guard.py |
| 6 | Exact symbols/settings/routes/tables/functions | route includes at FastAPI init |
| 7 | Current defective behavior | Dev/prod route parity not audited at startup. |
| 8 | Required target behavior | Emit signed JSON route manifest on prod startup matching allow list; diff against dev manifest logged. |
| 9 | Control mechanism | production_route_manifest.json (PROPOSED_ARTIFACT) artifact; HMAC with startup key. |
| 10 | Enforcement point | Startup audit + CI |
| 11 | Explicit affected files or bounded file families | dashboard.py, platform_api.py, production_guard.py |
| 12 | Authority/owning bounded context | Production route audit / Register E |
| 13 | Positive impact | Unexpected prod routes fail startup or CI golden diff. |
| 14 | Potential negative impact | Manifest signing key management. |
| 15 | Other findings affected | PC-030, PC-013.e |
| 16 | Required downstream revalidation | IVV manifest hash matches golden |
| 17 | Shared ownership or NONE with justification | NONE — sub-finding PC-013.e owned under Register E independently of parent closure |
| 18 | Objective acceptance criteria | Manifest hash matches golden; unexpected route fails startup in prod. |
| 19 | Verification mechanism | Startup manifest HMAC + golden diff |
| 20 | Failure condition | Undeclared route in prod profile |
| 21 | Evidence output required | E-SEC/prod-route-manifest.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### CC-013.f — P09 RBAC facade centralizing tier checks

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | CC-013.f |
| 2 | Finding ID | PC-013.f |
| 3 | Control type | CORRECTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 sub-finding PC-013.f (parent PC-013): Tier authorization scattered vs P09 facade. |
| 5 | Exact repository evidence files | auth_service.py, platform_api.py, dashboard.py |
| 6 | Exact symbols/settings/routes/tables/functions | TIER_FEATURES, require_feature scattered |
| 7 | Current defective behavior | Tier authorization scattered vs P09 facade. |
| 8 | Required target behavior | Create bd_platform/rbac_facade.py; all tier-gated routes use facade not ad hoc auth_service calls. |
| 9 | Control mechanism | FastAPI dependency require_platform_action() routing through rbac_facade. |
| 10 | Enforcement point | Static route audit + CI |
| 11 | Explicit affected files or bounded file families | auth_service.py, platform_api.py, dashboard.py, bd_platform/rbac_facade.py (PROPOSED_ARTIFACT) |
| 12 | Authority/owning bounded context | RBAC facade / Register E |
| 13 | Positive impact | Tier gating consistent across 61+ routes. |
| 14 | Potential negative impact | Route dependency refactor. |
| 15 | Other findings affected | PC-013, PC-009 |
| 16 | Required downstream revalidation | IVV zero require_feature outside rbac_facade |
| 17 | Shared ownership or NONE with justification | NONE — sub-finding PC-013.f owned under Register E independently of parent closure |
| 18 | Objective acceptance criteria | Zero routes use require_feature directly outside rbac_facade module. |
| 19 | Verification mechanism | Static route RBAC scan |
| 20 | Failure condition | Tier check bypass on new route |
| 21 | Evidence output required | E-SEC/rbac-facade-centralize.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### CC-015.a — Record FEATURE_REALITY_MATRIX status in pointer

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | CC-015.a |
| 2 | Finding ID | PC-015.a |
| 3 | Control type | CORRECTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 sub-finding PC-015.a (parent PC-015): Referenced audit matrix absent; cannot mark HISTORICAL_NON_CURRENT in repo. |
| 5 | Exact repository evidence files | FEATURE_REALITY_MATRIX.md (HISTORICAL_REFERENCE_NOT_PRESENT) |
| 6 | Exact symbols/settings/routes/tables/functions | absent audit matrix file |
| 7 | Current defective behavior | Referenced audit matrix absent; cannot mark HISTORICAL_NON_CURRENT in repo. |
| 8 | Required target behavior | SSOT pointer entry: FEATURE_REALITY_MATRIX status ARCHIVED_NOT_IN_REPO with external hash if known. |
| 9 | Control mechanism | Pointer section in CURRENT_PROGRAM_STATUS_POINTER.md with optional archived hash field. |
| 10 | Enforcement point | ssot-doc-lint CI |
| 11 | Explicit affected files or bounded file families | docs/institutional/CURRENT_PROGRAM_STATUS_POINTER.md (PROPOSED_ARTIFACT) |
| 12 | Authority/owning bounded context | Taxonomy documentation / Register A, K |
| 13 | Positive impact | Absent matrix cannot be cited as live authority. |
| 14 | Potential negative impact | External hash provenance if unknown. |
| 15 | Other findings affected | PC-036, PC-015 |
| 16 | Required downstream revalidation | IVV lint passes absent file class |
| 17 | Shared ownership or NONE with justification | NONE — sub-finding PC-015.a owned under Register A independently of parent closure |
| 18 | Objective acceptance criteria | Pointer contains ARCHIVED_NOT_IN_REPO status; lint passes absent file class. |
| 19 | Verification mechanism | ssot-doc-lint ABSENT rule |
| 20 | Failure condition | Matrix referenced as CURRENT without file |
| 21 | Evidence output required | E-GOV/absent-matrix-pointer.json |
| 22 | Architectural-decision compatibility | DEC-A: APPLICABLE — absent audit matrix marked non-authoritative; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### CC-015.b — Grid vs CAP disclaimer in registry module

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | CC-015.b |
| 2 | Finding ID | PC-015.b |
| 3 | Control type | CORRECTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 sub-finding PC-015.b (parent PC-015): 40-point grid ids conflict with 88-CAP institutional narrative without disclaimer. |
| 5 | Exact repository evidence files | bd_platform/registry.py |
| 6 | Exact symbols/settings/routes/tables/functions | FEATURE_MATRIX ids 1-40 vs 88-CAP narrative |
| 7 | Current defective behavior | 40-point grid ids conflict with 88-CAP institutional narrative without disclaimer. |
| 8 | Required target behavior | Module docstring and API docs state grid ids 1-40 are not CAP-### mappings. |
| 9 | Control mechanism | registry.py header + OpenAPI description on /features endpoint. |
| 10 | Enforcement point | Doc lint + API test + CI |
| 11 | Explicit affected files or bounded file families | bd_platform/registry.py, OpenAPI spec for /api/platform/features |
| 12 | Authority/owning bounded context | Feature taxonomy / Register A |
| 13 | Positive impact | Grid-CAP confusion prevented pending DEC-B crosswalk. |
| 14 | Potential negative impact | Manual crosswalk work post OD-01. |
| 15 | Other findings affected | PC-003, PC-037 |
| 16 | Required downstream revalidation | IVV disclaimer text in registry module |
| 17 | Shared ownership or NONE with justification | NONE — sub-finding PC-015.b owned under Register A independently of parent closure |
| 18 | Objective acceptance criteria | Disclaimer text present; test forbids grid id in CAP crosswalk generator. |
| 19 | Verification mechanism | Docstring + governance test |
| 20 | Failure condition | Grid id emitted as CAP-### in code |
| 21 | Evidence output required | E-GOV/grid-cap-disclaimer.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: APPLICABLE — prohibits grid-to-CAP automap outside attested crosswalk; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### CC-019.a — Anti-leakage test for training directories

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | CC-019.a |
| 2 | Finding ID | PC-019.a |
| 3 | Control type | CORRECTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 sub-finding PC-019.a (parent PC-019): Training artifact directories not guarded from serving paths in CI. |
| 5 | Exact repository evidence files | ml/, data/models/, flywheel config |
| 6 | Exact symbols/settings/routes/tables/functions | training artifact paths vs serving config |
| 7 | Current defective behavior | Training artifact directories not guarded from serving paths in CI. |
| 8 | Required target behavior | CI test fails if serving loader config paths overlap training export directories. |
| 9 | Control mechanism | tests/ml/test_training_serving_path_isolation.py (PROPOSED_ARTIFACT) overlapping path fixture. |
| 10 | Enforcement point | CI path-filter |
| 11 | Explicit affected files or bounded file families | ml/, data/models/, flywheel_saturation_guard.py, ml_serving_boundary.py (PROPOSED_ARTIFACT) |
| 12 | Authority/owning bounded context | ML serving boundary / Register I |
| 13 | Positive impact | Training data cannot leak to serving via config error. |
| 14 | Potential negative impact | Stricter serving path allowlist. |
| 15 | Other findings affected | PC-019, PC-012 |
| 16 | Required downstream revalidation | IVV overlapping path fixture fails |
| 17 | Shared ownership or NONE with justification | NONE — sub-finding PC-019.a owned under Register I independently of parent closure |
| 18 | Objective acceptance criteria | Overlapping path fixture fails isolation test. |
| 19 | Verification mechanism | Path overlap unit test |
| 20 | Failure condition | Serving loads from training export dir |
| 21 | Evidence output required | E-ML/training-leakage-test.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### CC-021.a — Zero diff CI vs Docker resolved runtime deps

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | CC-021.a |
| 2 | Finding ID | PC-021.a |
| 3 | Control type | CORRECTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 sub-finding PC-021.a (parent PC-021): Manifest divergence breaks CI↔Docker parity for runtime imports. |
| 5 | Exact repository evidence files | Dockerfile, requirements.txt, requirements-prod.txt, ci.yml |
| 6 | Exact symbols/settings/routes/tables/functions | COPY requirements-prod; ci installs dev requirements |
| 7 | Current defective behavior | Manifest divergence breaks CI↔Docker parity for runtime imports. |
| 8 | Required target behavior | manifest-reconcile job proves import-available package set identical in CI runner and Docker smoke container. |
| 9 | Control mechanism | Import smoke script listing critical modules executed in CI runner and post-build Docker container. |
| 10 | Enforcement point | CI merge gate |
| 11 | Explicit affected files or bounded file families | Dockerfile, requirements*.txt, .github/workflows/ci.yml |
| 12 | Authority/owning bounded context | Deploy parity / Register H |
| 13 | Positive impact | Production image imports match CI-tested modules. |
| 14 | Potential negative impact | Docker build time for smoke step. |
| 15 | Other findings affected | PC-001, PC-021 |
| 16 | Required downstream revalidation | IVV empty diff report for runtime deps |
| 17 | Shared ownership or NONE with justification | NONE — sub-finding PC-021.a owned under Register H independently of parent closure |
| 18 | Objective acceptance criteria | Diff report empty for runtime deps between CI and Docker. |
| 19 | Verification mechanism | Dual-environment import smoke |
| 20 | Failure condition | ccxt importable in CI not in Docker |
| 21 | Evidence output required | E-BUILD/ci-docker-import-parity.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### CC-022.a — Independent blocking pytest collection gate with baseline artifact

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | CC-022.a |
| 2 | Finding ID | PC-022.a |
| 3 | Control type | CORRECTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 sub-finding PC-022.a (parent PC-022): No blocking full-collection pytest job; wave1 baseline absent; subset CI green while 30+ modules untested. |
| 5 | Exact repository evidence files | .github/workflows/ci.yml, tests/, data/wave1_full_regression.txt (HISTORICAL_REFERENCE_NOT_PRESENT) |
| 6 | Exact symbols/settings/routes/tables/functions | pytest --collect-only; absent wave1 baseline; ci subset only |
| 7 | Current defective behavior | No blocking full-collection pytest job; wave1 baseline absent; subset CI green while 30+ modules untested. |
| 8 | Required target behavior | Dedicated blocking ci.yml job pytest-collection-gate with committed data/ci/test_collection_baseline.json independent of CC-002 parent scope. |
| 9 | Control mechanism | ci.yml job pytest-collection-gate with its own needs graph and baseline artifact data/ci/test_collection_baseline.json (PROPOSED_ARTIFACT); does not share closure evidence with CC-002 parent wording. |
| 10 | Enforcement point | CI merge gate — independent required check |
| 11 | Explicit affected files or bounded file families | .github/workflows/ci.yml, tests/, data/ci/test_collection_baseline.json (PROPOSED_ARTIFACT) |
| 12 | Authority/owning bounded context | QA collection gate / Register F |
| 13 | Positive impact | Sub-finding PC-022.a closes independently with its own blocking collection gate evidence. |
| 14 | Potential negative impact | Two similar collection jobs if not deduplicated carefully in Stage 3. |
| 15 | Other findings affected | PC-002, PC-039 |
| 16 | Required downstream revalidation | IVV merge blocked when only subset test passes but collection gate fails |
| 17 | Shared ownership or NONE with justification | NONE — sub-finding PC-022.a owned under Register F independently of parent closure |
| 18 | Objective acceptance criteria | Sub-finding closes when pytest-collection-gate blocks merge independently; baseline committed; wave1 file dependency removed. |
| 19 | Verification mechanism | Independent collection gate CI run + branch protection config audit |
| 20 | Failure condition | Collection gate skipped while subset test green merges |
| 21 | Evidence output required | E-TEST/collection-gate-independent.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### CC-022.b — SSE E2E CI job

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | CC-022.b |
| 2 | Finding ID | PC-022.b |
| 3 | Control type | CORRECTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 sub-finding PC-022.b (parent PC-022): No SSE/stream E2E in CI for Feature 002 streaming UI. |
| 5 | Exact repository evidence files | bd_platform/sse_stream.py, tests/ |
| 6 | Exact symbols/settings/routes/tables/functions | absence of tests/e2e/ SSE tests |
| 7 | Current defective behavior | No SSE/stream E2E in CI for Feature 002 streaming UI. |
| 8 | Required target behavior | Add tests/e2e/test_sse_stream_ci.py validating SSE endpoint contract with signed log output. |
| 9 | Control mechanism | pytest job with httpx SSE client against test app fixture producing E-TEST/sse-e2e-log.json. |
| 10 | Enforcement point | CI blocking |
| 11 | Explicit affected files or bounded file families | bd_platform/sse_stream.py, tests/e2e/test_sse_stream_ci.py (PROPOSED_ARTIFACT) |
| 12 | Authority/owning bounded context | SSE E2E / Register F |
| 13 | Positive impact | Streaming UI regressions caught in CI. |
| 14 | Potential negative impact | SSE test flakiness under load. |
| 15 | Other findings affected | PC-022, PC-022.b |
| 16 | Required downstream revalidation | IVV E-TEST/sse-e2e-log.json produced |
| 17 | Shared ownership or NONE with justification | NONE — sub-finding PC-022.b owned under Register F independently of parent closure |
| 18 | Objective acceptance criteria | Job green produces E-TEST/sse-e2e-log.json with contract assertions pass. |
| 19 | Verification mechanism | httpx SSE E2E test |
| 20 | Failure condition | SSE regression undetected |
| 21 | Evidence output required | E-TEST/sse-e2e-job.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### CC-022.c — Execution concurrency test suite

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | CC-022.c |
| 2 | Finding ID | PC-022.c |
| 3 | Control type | CORRECTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 sub-finding PC-022.c (parent PC-022): Execution concurrency races not in test suite. |
| 5 | Exact repository evidence files | execution_engine.py, startup_orchestrator.py |
| 6 | Exact symbols/settings/routes/tables/functions | asyncio loop tasks; manual execute paths |
| 7 | Current defective behavior | Execution concurrency races not in test suite. |
| 8 | Required target behavior | Add tests/concurrency/test_execution_races.py covering loop vs manual execute vs freeze load. |
| 9 | Control mechanism | asyncio stress tests with timeout bounds producing concurrency artifact. |
| 10 | Enforcement point | CI blocking |
| 11 | Explicit affected files or bounded file families | execution_engine.py, startup_orchestrator.py, tests/concurrency/test_execution_races.py (PROPOSED_ARTIFACT) |
| 12 | Authority/owning bounded context | Execution concurrency / Register D, F |
| 13 | Positive impact | Race class defects detected before production. |
| 14 | Potential negative impact | Stress test runtime in CI. |
| 15 | Other findings affected | PC-014, PC-022.e |
| 16 | Required downstream revalidation | IVV 100 iterations without race failure |
| 17 | Shared ownership or NONE with justification | NONE — sub-finding PC-022.c owned under Register D independently of parent closure |
| 18 | Objective acceptance criteria | Suite passes 100 iterations without race failure. |
| 19 | Verification mechanism | asyncio stress iteration |
| 20 | Failure condition | Race condition in execute path |
| 21 | Evidence output required | E-TEST/concurrency-suite.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### CC-022.d — Backup/restore drill integration test

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | CC-022.d |
| 2 | Finding ID | PC-022.d |
| 3 | Control type | CORRECTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 sub-finding PC-022.d (parent PC-022): Backup/restore drill not evidenced in tests. |
| 5 | Exact repository evidence files | database.py, SQLite backup paths |
| 6 | Exact symbols/settings/routes/tables/functions | no tests/ops/ restore drill |
| 7 | Current defective behavior | Backup/restore drill not evidenced in tests. |
| 8 | Required target behavior | Add tests/ops/test_backup_restore_drill.py producing signed restore drill JSON with RTO metric. |
| 9 | Control mechanism | SQLite backup/restore cycle test with timing capture in tests/ops/. |
| 10 | Enforcement point | CI + scheduled workflow |
| 11 | Explicit affected files or bounded file families | database.py, tests/ops/test_backup_restore_drill.py (PROPOSED_ARTIFACT) |
| 12 | Authority/owning bounded context | DR ops / Register F |
| 13 | Positive impact | DR capability continuously evidenced. |
| 14 | Potential negative impact | Weekly workflow maintenance. |
| 15 | Other findings affected | PC-022, PC-027 |
| 16 | Required downstream revalidation | IVV restore_success=true in artifact |
| 17 | Shared ownership or NONE with justification | NONE — sub-finding PC-022.d owned under Register F independently of parent closure |
| 18 | Objective acceptance criteria | Artifact includes restore_success=true and duration_ms. |
| 19 | Verification mechanism | Backup/restore integration test |
| 20 | Failure condition | Restore drill never run |
| 21 | Evidence output required | E-OPS/restore-drill-test.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### CC-022.e — Execution bypass DENY matrix tests

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | CC-022.e |
| 2 | Finding ID | PC-022.e |
| 3 | Control type | CORRECTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 sub-finding PC-022.e (parent PC-022): Negative execution bypass tests incomplete across flag combinations. |
| 5 | Exact repository evidence files | execution_engine.py, bd_platform/cex_dex_executor.py, execution_keys.py |
| 6 | Exact symbols/settings/routes/tables/functions | freeze, exposure, master switch env vars |
| 7 | Current defective behavior | Negative execution bypass tests incomplete across flag combinations. |
| 8 | Required target behavior | Comprehensive negative matrix: freeze+live flag, exposure exceeded, missing auth, env conflicts — all DENY. |
| 9 | Control mechanism | tests/security/test_execution_bypass_matrix.py (PROPOSED_ARTIFACT) producing CSV artifact. |
| 10 | Enforcement point | CI blocking security matrix |
| 11 | Explicit affected files or bounded file families | execution_engine.py, bd_platform/cex_dex_executor.py, tests/security/test_execution_bypass_matrix.py (PROPOSED_ARTIFACT) |
| 12 | Authority/owning bounded context | Execution bypass / Register D, F |
| 13 | Positive impact | 100% DENY provable for institutional execution safety DD. |
| 14 | Potential negative impact | Large combinatorial test matrix maintenance. |
| 15 | Other findings affected | PC-005, PC-010.a |
| 16 | Required downstream revalidation | IVV matrix CSV 100% DENY rows |
| 17 | Shared ownership or NONE with justification | NONE — sub-finding PC-022.e owned under Register D independently of parent closure |
| 18 | Objective acceptance criteria | Matrix CSV artifact shows 100% DENY rows. |
| 19 | Verification mechanism | Bypass matrix pytest + artifact parser |
| 20 | Failure condition | SUCCESS row in bypass matrix |
| 21 | Evidence output required | E-EXEC/bypass-matrix.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### CC-034.a — Unified workflow chaining security to full suite

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | CC-034.a |
| 2 | Finding ID | PC-034.a |
| 3 | Control type | CORRECTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 sub-finding PC-034.a (parent PC-034): Security workflow can pass while collection gate and full test fail. |
| 5 | Exact repository evidence files | .github/workflows/security.yml, .github/workflows/ci.yml |
| 6 | Exact symbols/settings/routes/tables/functions | separate workflow jobs without needs |
| 7 | Current defective behavior | Security workflow can pass while collection gate and full test fail. |
| 8 | Required target behavior | Consolidate workflows or add orchestrator where security job needs: [pytest-collection-gate, test]. |
| 9 | Control mechanism | Single ci.yml or reusable workflow quality-gate.yml (PROPOSED_ARTIFACT) with explicit needs graph. |
| 10 | Enforcement point | GitHub Actions needs graph + CI meta-test |
| 11 | Explicit affected files or bounded file families | .github/workflows/security.yml, .github/workflows/ci.yml |
| 12 | Authority/owning bounded context | CI workflow orchestration / Register F |
| 13 | Positive impact | Security green implies upstream full suite green on same run. |
| 14 | Potential negative impact | Workflow YAML refactor across repos. |
| 15 | Other findings affected | PC-033, PC-034 |
| 16 | Required downstream revalidation | IVV security job skipped when upstream test fails |
| 17 | Shared ownership or NONE with justification | NONE — sub-finding PC-034.a owned under Register F independently of parent closure |
| 18 | Objective acceptance criteria | security job skipped/fails when upstream test job fails. |
| 19 | Verification mechanism | Workflow YAML parse |
| 20 | Failure condition | Security passes with failing collection gate |
| 21 | Evidence output required | E-CI/security-needs-chain.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

---

## Sub-Finding Preventive Controls

### PCtrl-008.a — Auto-exec default parity CI test

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | PCtrl-008.a |
| 2 | Finding ID | PC-008.a |
| 3 | Control type | PREVENTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 sub-finding PC-008.a enabling condition: failure of existing controls allowed Orchestrator default false, engine status default true, compose sets true — three sources disagree.. |
| 5 | Exact repository evidence files | startup_orchestrator.py, execution_engine.py, docker-compose.yml |
| 6 | Exact symbols/settings/routes/tables/functions | AUTO_EXECUTION_LOOP defaults |
| 7 | Current defective behavior | Without independent blocking gate for PC-008.a, sub-scope defect can persist while parent PC-008 appears closed. |
| 8 | Required target behavior | tests/arch/test_auto_exec_default_parity.py reads compose, orchestrator, engine defaults; mismatch fails CI. |
| 9 | Control mechanism | Parsed env default extraction test across three sources per profile. |
| 10 | Enforcement point | CI merge gate |
| 11 | Explicit affected files or bounded file families | startup_orchestrator.py, execution_engine.py, docker-compose.yml, tests/arch/test_auto_exec_default_parity.py (PROPOSED_ARTIFACT) |
| 12 | Authority/owning bounded context | Composition root / Register B preventive sub-gate |
| 13 | Positive impact | Independent regression block for sub-finding PC-008.a. |
| 14 | Potential negative impact | Additional CI path filters for sub-scope files. |
| 15 | Other findings affected | PC-005, PC-007, PC-031 |
| 16 | Required downstream revalidation | IVV sub-finding PC-008.a synthetic regression injection |
| 17 | Shared ownership or NONE with justification | NONE — sub-finding PC-008.a owned under Register B independently of parent closure |
| 18 | Objective acceptance criteria | Mismatch between orchestrator and engine defaults fails CI. |
| 19 | Verification mechanism | CI auto-exec parity test |
| 20 | Failure condition | Default conflict undetected |
| 21 | Evidence output required | E-STARTUP/auto-exec-parity-gate.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### PCtrl-008.b — Route inventory drift gate

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | PCtrl-008.b |
| 2 | Finding ID | PC-008.b |
| 3 | Control type | PREVENTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 sub-finding PC-008.b enabling condition: failure of existing controls allowed 61 handlers in monolith; route ownership not machine-attributed to P01-P16.. |
| 5 | Exact repository evidence files | platform_api.py |
| 6 | Exact symbols/settings/routes/tables/functions | 61 @router decorators, /api/platform prefix |
| 7 | Current defective behavior | Without independent blocking gate for PC-008.b, sub-scope defect can persist while parent PC-008 appears closed. |
| 8 | Required target behavior | CI fails if live route count ≠ governance/platform_route_inventory.json without inventory regen. |
| 9 | Control mechanism | Diff job on OpenAPI change blocking merge without inventory update. |
| 10 | Enforcement point | CI merge gate |
| 11 | Explicit affected files or bounded file families | platform_api.py, governance/platform_route_inventory.json, tests/arch/test_route_inventory_drift.py (PROPOSED_ARTIFACT) |
| 12 | Authority/owning bounded context | Platform API / Register B preventive sub-gate |
| 13 | Positive impact | Independent regression block for sub-finding PC-008.b. |
| 14 | Potential negative impact | Additional CI path filters for sub-scope files. |
| 15 | Other findings affected | PC-009, PC-008.b |
| 16 | Required downstream revalidation | IVV sub-finding PC-008.b synthetic regression injection |
| 17 | Shared ownership or NONE with justification | NONE — sub-finding PC-008.b owned under Register B independently of parent closure |
| 18 | Objective acceptance criteria | New route without inventory update fails CI. |
| 19 | Verification mechanism | CI route inventory drift gate |
| 20 | Failure condition | Inventory stale after route add |
| 21 | Evidence output required | E-PLATFORM/route-inventory-drift-log.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### PCtrl-008.c — ADR required for decision pipeline changes

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | PCtrl-008.c |
| 2 | Finding ID | PC-008.c |
| 3 | Control type | PREVENTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 sub-finding PC-008.c enabling condition: failure of existing controls allowed Decision scoring module absent; P06/P10 boundary unimplemented.. |
| 5 | Exact repository evidence files | decision_intelligence_pipeline.py (HISTORICAL_REFERENCE_NOT_PRESENT), research_lab.py, api/routers/oracle.py |
| 6 | Exact symbols/settings/routes/tables/functions | missing decision_intelligence_pipeline.py; oracle scoring ad hoc |
| 7 | Current defective behavior | Without independent blocking gate for PC-008.c, sub-scope defect can persist while parent PC-008 appears closed. |
| 8 | Required target behavior | Path filter requires ADR update when adding decision/scoring modules. |
| 9 | Control mechanism | CI check for ADR_DECISION_PIPELINE.md touch on decision/scoring path changes. |
| 10 | Enforcement point | CI path-filter merge gate |
| 11 | Explicit affected files or bounded file families | docs/institutional/ADR_DECISION_PIPELINE.md (PROPOSED_ARTIFACT), research_lab.py, api/routers/oracle.py |
| 12 | Authority/owning bounded context | Decision intelligence / Register B, I preventive sub-gate |
| 13 | Positive impact | Independent regression block for sub-finding PC-008.c. |
| 14 | Potential negative impact | Additional CI path filters for sub-scope files. |
| 15 | Other findings affected | PC-012, PC-008 |
| 16 | Required downstream revalidation | IVV sub-finding PC-008.c synthetic regression injection |
| 17 | Shared ownership or NONE with justification | NONE — sub-finding PC-008.c owned under Register B independently of parent closure |
| 18 | Objective acceptance criteria | New decision module without ADR fails path gate. |
| 19 | Verification mechanism | CI ADR path gate |
| 20 | Failure condition | Decision module added without ADR |
| 21 | Evidence output required | E-ARCH/decision-adr-gate.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### PCtrl-008.d — Verdict emitter static analysis

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | PCtrl-008.d |
| 2 | Finding ID | PC-008.d |
| 3 | Control type | PREVENTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 sub-finding PC-008.d enabling condition: failure of existing controls allowed Compliance transformation imported from multiple route call sites without mandatory facade.. |
| 5 | Exact repository evidence files | regulatory_compliance_guard.py, dashboard.py, platform routes |
| 6 | Exact symbols/settings/routes/tables/functions | apply_regulatory_compliance, to_public_verdict |
| 7 | Current defective behavior | Without independent blocking gate for PC-008.d, sub-scope defect can persist while parent PC-008 appears closed. |
| 8 | Required target behavior | AST scan ensures all routes returning verdict-shaped JSON call compliance_facade. |
| 9 | Control mechanism | scripts/lint_verdict_emitters.py (PROPOSED_ARTIFACT) AST scan blocking new route bypassing facade. |
| 10 | Enforcement point | CI lint merge gate |
| 11 | Explicit affected files or bounded file families | dashboard.py, platform_api.py, scripts/lint_verdict_emitters.py (PROPOSED_ARTIFACT) |
| 12 | Authority/owning bounded context | Regulatory compliance / Register L preventive sub-gate |
| 13 | Positive impact | Independent regression block for sub-finding PC-008.d. |
| 14 | Potential negative impact | Additional CI path filters for sub-scope files. |
| 15 | Other findings affected | PC-024, PC-008.d |
| 16 | Required downstream revalidation | IVV sub-finding PC-008.d synthetic regression injection |
| 17 | Shared ownership or NONE with justification | NONE — sub-finding PC-008.d owned under Register L independently of parent closure |
| 18 | Objective acceptance criteria | New route bypassing facade fails lint. |
| 19 | Verification mechanism | CI lint_verdict_emitters |
| 20 | Failure condition | Duplicate guard calls persist |
| 21 | Evidence output required | E-LEGAL/verdict-emitter-lint.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### PCtrl-009.a — Prohibited API to bd_platform import lint

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | PCtrl-009.a |
| 2 | Finding ID | PC-009.a |
| 3 | Control type | PREVENTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 sub-finding PC-009.a enabling condition: failure of existing controls allowed API layer reaches platform internals bypassing P13 facades.. |
| 5 | Exact repository evidence files | platform_api.py |
| 6 | Exact symbols/settings/routes/tables/functions | direct bd_platform.* imports throughout file |
| 7 | Current defective behavior | Without independent blocking gate for PC-009.a, sub-scope defect can persist while parent PC-009 appears closed. |
| 8 | Required target behavior | Zero-tolerance lint on platform_api.py imports from bd_platform except facades package. |
| 9 | Control mechanism | lint_prohibited_imports rule api_internal_import_ban fails new internal imports. |
| 10 | Enforcement point | CI merge gate |
| 11 | Explicit affected files or bounded file families | platform_api.py, scripts/lint_prohibited_imports.py, bd_platform/facades/ |
| 12 | Authority/owning bounded context | Platform facade / Register B preventive sub-gate |
| 13 | Positive impact | Independent regression block for sub-finding PC-009.a. |
| 14 | Potential negative impact | Additional CI path filters for sub-scope files. |
| 15 | Other findings affected | PC-009, PC-009.a |
| 16 | Required downstream revalidation | IVV sub-finding PC-009.a synthetic regression injection |
| 17 | Shared ownership or NONE with justification | NONE — sub-finding PC-009.a owned under Register B independently of parent closure |
| 18 | Objective acceptance criteria | New internal import in platform_api fails lint. |
| 19 | Verification mechanism | CI api_internal_import_ban |
| 20 | Failure condition | Lint not run on platform_api change |
| 21 | Evidence output required | E-PLATFORM/api-import-lint.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### PCtrl-009.b — API response authority field regression test

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | PCtrl-009.b |
| 2 | Finding ID | PC-009.b |
| 3 | Control type | PREVENTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 sub-finding PC-009.b enabling condition: failure of existing controls allowed Import success equals live feature in API summaries.. |
| 5 | Exact repository evidence files | bd_platform/registry.py |
| 6 | Exact symbols/settings/routes/tables/functions | FEATURE_MATRIX, feature_summary() |
| 7 | Current defective behavior | Without independent blocking gate for PC-009.b, sub-scope defect can persist while parent PC-009 appears closed. |
| 8 | Required target behavior | Contract test fails if enumeration_authority field removed from features endpoint. |
| 9 | Control mechanism | tests/test_platform_features_authority.py blocks field removal. |
| 10 | Enforcement point | CI contract test merge gate |
| 11 | Explicit affected files or bounded file families | bd_platform/registry.py, tests/test_platform_features_authority.py (PROPOSED_ARTIFACT) |
| 12 | Authority/owning bounded context | Feature enumeration / Register A preventive sub-gate |
| 13 | Positive impact | Independent regression block for sub-finding PC-009.b. |
| 14 | Potential negative impact | Additional CI path filters for sub-scope files. |
| 15 | Other findings affected | PC-003, PC-015.b |
| 16 | Required downstream revalidation | IVV sub-finding PC-009.b synthetic regression injection |
| 17 | Shared ownership or NONE with justification | NONE — sub-finding PC-009.b owned under Register A independently of parent closure |
| 18 | Objective acceptance criteria | Field absence fails CI contract test. |
| 19 | Verification mechanism | CI platform features authority test |
| 20 | Failure condition | Field removed without test failure |
| 21 | Evidence output required | E-GOV/features-authority-test.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### PCtrl-009.c — Decimal boundary property tests on scan hot path only

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | PCtrl-009.c |
| 2 | Finding ID | PC-009.c |
| 3 | Control type | PREVENTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 sub-finding PC-009.c enabling condition: failure of existing controls allowed Fee and profit scan paths compute in float before threshold compare; marginal opportunities flip nea. |
| 5 | Exact repository evidence files | fee_matrix.py, fast_scan_engine.py |
| 6 | Exact symbols/settings/routes/tables/functions | float tables; L19-24 float conversion on bids/asks/fees |
| 7 | Current defective behavior | Without independent blocking gate for PC-009.c, sub-scope defect can persist while parent PC-009 appears closed. |
| 8 | Required target behavior | Property tests on fast_scan_engine and fee_matrix output using hypothesis at fee thresholds; scoped to scan modules only. |
| 9 | Control mechanism | tests/property/test_scan_decimal_boundaries.py (PROPOSED_ARTIFACT) hypothesis tests at 0.0001 USDT thresholds on scan output only. |
| 10 | Enforcement point | CI merge gate on fee_matrix.py and fast_scan_engine.py |
| 11 | Explicit affected files or bounded file families | fee_matrix.py, fast_scan_engine.py, tests/property/test_scan_decimal_boundaries.py (PROPOSED_ARTIFACT) |
| 12 | Authority/owning bounded context | Financial scan compute / Register J, C preventive sub-gate |
| 13 | Positive impact | Independent regression block for sub-finding PC-009.c. |
| 14 | Potential negative impact | Additional CI path filters for sub-scope files. |
| 15 | Other findings affected | PC-041, PC-006 |
| 16 | Required downstream revalidation | IVV sub-finding PC-009.c synthetic regression injection |
| 17 | Shared ownership or NONE with justification | NONE — sub-finding PC-009.c owned under Register J independently of parent closure |
| 18 | Objective acceptance criteria | Float regression in scan modules fails property tests. |
| 19 | Verification mechanism | CI scan decimal property gate |
| 20 | Failure condition | Property tests not scoped to scan modules |
| 21 | Evidence output required | E-DATA/scan-decimal-property-gate.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: APPLICABLE — scan path uses authoritative decimal before execution authorization; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### PCtrl-009.d — Portfolio consistency contract test

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | PCtrl-009.d |
| 2 | Finding ID | PC-009.d |
| 3 | Control type | PREVENTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 sub-finding PC-009.d enabling condition: failure of existing controls allowed Holdings display and rebalance preview may disagree across dashboard and rebalancer.. |
| 5 | Exact repository evidence files | bd_platform/portfolio_rebalancer.py, dashboard.py |
| 6 | Exact symbols/settings/routes/tables/functions | portfolio rebalance API; dashboard holdings routes |
| 7 | Current defective behavior | Without independent blocking gate for PC-009.d, sub-scope defect can persist while parent PC-009 appears closed. |
| 8 | Required target behavior | CI contract test compares dashboard holdings API vs rebalance preview for fixture accounts. |
| 9 | Control mechanism | tests/contract/test_portfolio_single_authority.py hash mismatch fails CI. |
| 10 | Enforcement point | CI merge gate |
| 11 | Explicit affected files or bounded file families | dashboard.py, bd_platform/portfolio_rebalancer.py, tests/contract/test_portfolio_single_authority.py (PROPOSED_ARTIFACT) |
| 12 | Authority/owning bounded context | Portfolio authority / Register B, C preventive sub-gate |
| 13 | Positive impact | Independent regression block for sub-finding PC-009.d. |
| 14 | Potential negative impact | Additional CI path filters for sub-scope files. |
| 15 | Other findings affected | PC-009, PC-009.d |
| 16 | Required downstream revalidation | IVV sub-finding PC-009.d synthetic regression injection |
| 17 | Shared ownership or NONE with justification | NONE — sub-finding PC-009.d owned under Register B independently of parent closure |
| 18 | Objective acceptance criteria | Hash mismatch between dashboard and API fails contract test. |
| 19 | Verification mechanism | CI portfolio consistency test |
| 20 | Failure condition | Contract test skipped on portfolio change |
| 21 | Evidence output required | E-PLATFORM/portfolio-consistency-gate.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### PCtrl-010.a — Connector bypass security test in CI matrix

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | PCtrl-010.a |
| 2 | Finding ID | PC-010.a |
| 3 | Control type | PREVENTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 sub-finding PC-010.a enabling condition: failure of existing controls allowed CEX-DEX executor delegates to execute_order without unified authorize_execution gate.. |
| 5 | Exact repository evidence files | bd_platform/cex_dex_executor.py |
| 6 | Exact symbols/settings/routes/tables/functions | execute_cex_dex_opportunity L49-52; CEX_DEX_EXECUTION_ENABLED |
| 7 | Current defective behavior | Without independent blocking gate for PC-010.a, sub-scope defect can persist while parent PC-010 appears closed. |
| 8 | Required target behavior | test_connector_execution_denials.py cex-dex section must show 100% DENY on bypass rows. |
| 9 | Control mechanism | tests/security/test_connector_execution_denials.py cex-dex matrix blocking CI. |
| 10 | Enforcement point | CI blocking security matrix |
| 11 | Explicit affected files or bounded file families | bd_platform/cex_dex_executor.py, tests/security/test_connector_execution_denials.py |
| 12 | Authority/owning bounded context | Connector execution / Register D preventive sub-gate |
| 13 | Positive impact | Independent regression block for sub-finding PC-010.a. |
| 14 | Potential negative impact | Additional CI path filters for sub-scope files. |
| 15 | Other findings affected | PC-005, PC-010 |
| 16 | Required downstream revalidation | IVV sub-finding PC-010.a synthetic regression injection |
| 17 | Shared ownership or NONE with justification | NONE — sub-finding PC-010.a owned under Register D independently of parent closure |
| 18 | Objective acceptance criteria | CEX-DEX bypass row returning SUCCESS fails CI. |
| 19 | Verification mechanism | CI connector denial parser |
| 20 | Failure condition | Bypass success row in matrix |
| 21 | Evidence output required | E-EXEC/cex-dex-bypass-matrix.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### PCtrl-011.a — Stale hour injection unit test

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | PCtrl-011.a |
| 2 | Finding ID | PC-011.a |
| 3 | Control type | PREVENTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 sub-finding PC-011.a enabling condition: failure of existing controls allowed Assessor can PASS with degraded hourly integrity if weighting allows partial hours.. |
| 5 | Exact repository evidence files | scripts/g3_reliability_soak_test.py |
| 6 | Exact symbols/settings/routes/tables/functions | integrity thresholds stale >10%; HOURLY_OPERATION_REPORTS/ |
| 7 | Current defective behavior | Without independent blocking gate for PC-011.a, sub-scope defect can persist while parent PC-011 appears closed. |
| 8 | Required target behavior | Unit test forces stale hour into assessor fixture; expects FAIL verdict. |
| 9 | Control mechanism | tests/g3/test_hourly_stale_veto.py (PROPOSED_ARTIFACT) injects stale hour expecting FAIL. |
| 10 | Enforcement point | CI G3 unit test merge gate |
| 11 | Explicit affected files or bounded file families | scripts/g3_reliability_soak_test.py, tests/g3/test_hourly_stale_veto.py (PROPOSED_ARTIFACT) |
| 12 | Authority/owning bounded context | G3 integrity / Register G preventive sub-gate |
| 13 | Positive impact | Independent regression block for sub-finding PC-011.a. |
| 14 | Potential negative impact | Additional CI path filters for sub-scope files. |
| 15 | Other findings affected | PC-011, PC-011.b |
| 16 | Required downstream revalidation | IVV sub-finding PC-011.a synthetic regression injection |
| 17 | Shared ownership or NONE with justification | NONE — sub-finding PC-011.a owned under Register G independently of parent closure |
| 18 | Objective acceptance criteria | PASS on stale injection fails unit test. |
| 19 | Verification mechanism | CI hourly veto test |
| 20 | Failure condition | Hourly artifact not emitted |
| 21 | Evidence output required | E-G3/stale-hour-veto-test.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### PCtrl-011.b — gate_scope validator cross-check

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | PCtrl-011.b |
| 2 | Finding ID | PC-011.b |
| 3 | Control type | PREVENTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 sub-finding PC-011.b enabling condition: failure of existing controls allowed Pilot and institutional durations share assessor without machine-readable scope distinction.. |
| 5 | Exact repository evidence files | scripts/g3_reliability_soak_test.py, schemas/g3_assessment.schema.json |
| 6 | Exact symbols/settings/routes/tables/functions | --hours min 1; no gate_scope field |
| 7 | Current defective behavior | Without independent blocking gate for PC-011.b, sub-scope defect can persist while parent PC-011 appears closed. |
| 8 | Required target behavior | validate_evidence.py enforces gate_scope/hours consistency on every G3 artifact commit. |
| 9 | Control mechanism | Schema if/then validation in validate_evidence.py on evidence path changes. |
| 10 | Enforcement point | CI evidence path merge gate |
| 11 | Explicit affected files or bounded file families | scripts/validate_evidence.py (PROPOSED_ARTIFACT), schemas/g3_assessment.schema.json |
| 12 | Authority/owning bounded context | G3 schema / Register G preventive sub-gate |
| 13 | Positive impact | Independent regression block for sub-finding PC-011.b. |
| 14 | Potential negative impact | Additional CI path filters for sub-scope files. |
| 15 | Other findings affected | PC-011, PC-029 |
| 16 | Required downstream revalidation | IVV sub-finding PC-011.b synthetic regression injection |
| 17 | Shared ownership or NONE with justification | NONE — sub-finding PC-011.b owned under Register G independently of parent closure |
| 18 | Objective acceptance criteria | Inconsistent scope/hours fails validator. |
| 19 | Verification mechanism | CI gate_scope cross-check |
| 20 | Failure condition | Validator skips hours cross-check |
| 21 | Evidence output required | E-G3/gate-scope-crosscheck-log.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### PCtrl-012.a — Oracle entrypoint caller inventory gate

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | PCtrl-012.a |
| 2 | Finding ID | PC-012.a |
| 3 | Control type | PREVENTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 sub-finding PC-012.a enabling condition: failure of existing controls allowed research_lab and oracle_retrainer are parallel inference entrypoints outside stack facade.. |
| 5 | Exact repository evidence files | research_lab.py, oracle_retrainer.py |
| 6 | Exact symbols/settings/routes/tables/functions | build_research_lab_report, run_oracle_retrain_step |
| 7 | Current defective behavior | Without independent blocking gate for PC-012.a, sub-scope defect can persist while parent PC-012 appears closed. |
| 8 | Required target behavior | CI compares caller inventory to allowed list; fails on new external caller. |
| 9 | Control mechanism | scripts/oracle_caller_inventory.py (PROPOSED_ARTIFACT) diff in CI on oracle path changes. |
| 10 | Enforcement point | CI caller inventory merge gate |
| 11 | Explicit affected files or bounded file families | research_lab.py, oracle_retrainer.py, scripts/oracle_caller_inventory.py (PROPOSED_ARTIFACT) |
| 12 | Authority/owning bounded context | Oracle entrypoints / Register I preventive sub-gate |
| 13 | Positive impact | Independent regression block for sub-finding PC-012.a. |
| 14 | Potential negative impact | Additional CI path filters for sub-scope files. |
| 15 | Other findings affected | PC-012, PC-028 |
| 16 | Required downstream revalidation | IVV sub-finding PC-012.a synthetic regression injection |
| 17 | Shared ownership or NONE with justification | NONE — sub-finding PC-012.a owned under Register I independently of parent closure |
| 18 | Objective acceptance criteria | New caller outside stack fails inventory diff. |
| 19 | Verification mechanism | CI oracle caller gate |
| 20 | Failure condition | Inventory diff not run on oracle change |
| 21 | Evidence output required | E-ORACLE/caller-inventory-gate.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### PCtrl-012.b — Lineage field presence lint on E2E artifact

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | PCtrl-012.b |
| 2 | Finding ID | PC-012.b |
| 3 | Control type | PREVENTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 sub-finding PC-012.b enabling condition: failure of existing controls allowed Lineage fields not proven end-to-end signal→prediction→audit for each decision class.. |
| 5 | Exact repository evidence files | research_lab.py, oracle_integrity.py, database oracle tables |
| 6 | Exact symbols/settings/routes/tables/functions | prediction_source, filter_live_predictions |
| 7 | Current defective behavior | Without independent blocking gate for PC-012.b, sub-scope defect can persist while parent PC-012 appears closed. |
| 8 | Required target behavior | CI validates CAP-053 E2E artifact JSON schema requires lineage fields non-null. |
| 9 | Control mechanism | Schema check on test output artifact blocking null lineage fields. |
| 10 | Enforcement point | CI merge gate |
| 11 | Explicit affected files or bounded file families | tests/e2e/test_oracle_lineage_cap053.py, schemas/oracle_lineage.schema.json (PROPOSED_ARTIFACT) |
| 12 | Authority/owning bounded context | Oracle lineage / Register I preventive sub-gate |
| 13 | Positive impact | Independent regression block for sub-finding PC-012.b. |
| 14 | Potential negative impact | Additional CI path filters for sub-scope files. |
| 15 | Other findings affected | PC-012, PC-012.a |
| 16 | Required downstream revalidation | IVV sub-finding PC-012.b synthetic regression injection |
| 17 | Shared ownership or NONE with justification | NONE — sub-finding PC-012.b owned under Register I independently of parent closure |
| 18 | Objective acceptance criteria | Null lineage field fails schema validation. |
| 19 | Verification mechanism | CI lineage schema gate |
| 20 | Failure condition | E2E artifact not produced |
| 21 | Evidence output required | E-ORACLE/lineage-schema-gate.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### PCtrl-013.a — Fixture keys required in CI env

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | PCtrl-013.a |
| 2 | Finding ID | PC-013.a |
| 3 | Control type | PREVENTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 sub-finding PC-013.a enabling condition: failure of existing controls allowed Exchange validation depends on gitignored keys/ tree; CI cannot reproduce key-dependent tests.. |
| 5 | Exact repository evidence files | .gitignore, execution_keys.py, keys/ |
| 6 | Exact symbols/settings/routes/tables/functions | keys/ gitignored; committed keys/ absent |
| 7 | Current defective behavior | Without independent blocking gate for PC-013.a, sub-scope defect can persist while parent PC-013 appears closed. |
| 8 | Required target behavior | CI sets KEYS_MODE=fixture; test fails if live key paths required without skip marker. |
| 9 | Control mechanism | tests/conftest.py (PROPOSED_ARTIFACT) fixture key injection; CI env KEYS_MODE=fixture enforced. |
| 10 | Enforcement point | CI merge gate |
| 11 | Explicit affected files or bounded file families | tests/conftest.py, .github/workflows/ci.yml, execution_keys.py |
| 12 | Authority/owning bounded context | Secrets CI / Register E preventive sub-gate |
| 13 | Positive impact | Independent regression block for sub-finding PC-013.a. |
| 14 | Potential negative impact | Additional CI path filters for sub-scope files. |
| 15 | Other findings affected | PC-013, PC-013.a |
| 16 | Required downstream revalidation | IVV sub-finding PC-013.a synthetic regression injection |
| 17 | Shared ownership or NONE with justification | NONE — sub-finding PC-013.a owned under Register E independently of parent closure |
| 18 | Objective acceptance criteria | CI run requiring gitignored keys/ fails without explicit skip marker. |
| 19 | Verification mechanism | CI fixture key injection test |
| 20 | Failure condition | Live keys required in default CI |
| 21 | Evidence output required | E-SEC/fixture-key-ci-gate.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### PCtrl-013.b — Independent tenant isolation gate for user-scoped repository changes

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | PCtrl-013.b |
| 2 | Finding ID | PC-013.b |
| 3 | Control type | PREVENTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 sub-finding PC-013.b enabling condition: failure of existing controls allowed Subscription tier scoping is not multi-tenant org isolation; repositories lack tenant predicate.. |
| 5 | Exact repository evidence files | auth_service.py, database.py |
| 6 | Exact symbols/settings/routes/tables/functions | TIER_FEATURES; user-scoped CRUD without tenant_id |
| 7 | Current defective behavior | Without independent blocking gate for PC-013.b, sub-scope defect can persist while parent PC-013 appears closed. |
| 8 | Required target behavior | Path-filtered blocking CI job tenant-repository-isolation-gate runs on database.py user-scoped repository changes independently of PCtrl-013 parent suite. |
| 9 | Control mechanism | Dedicated CI job tenant-repository-isolation-gate (PROPOSED_ARTIFACT workflow step) path-filtered on database.py user-scoped repository diffs; requires tests/security/test_tenant_repository_isolation.py (PROPOSED_ARTIFACT) pass. |
| 10 | Enforcement point | CI path-filter blocking merge gate — independent from PCtrl-013 |
| 11 | Explicit affected files or bounded file families | database.py, tests/security/test_tenant_repository_isolation.py (PROPOSED_ARTIFACT), .github/workflows/ci.yml tenant-repository-isolation-gate job |
| 12 | Authority/owning bounded context | Tenancy isolation / Register E preventive sub-gate |
| 13 | Positive impact | Independent regression block for sub-finding PC-013.b. |
| 14 | Potential negative impact | Additional CI path filters for sub-scope files. |
| 15 | Other findings affected | PC-013, PC-027 |
| 16 | Required downstream revalidation | IVV sub-finding PC-013.b synthetic regression injection |
| 17 | Shared ownership or NONE with justification | NONE — sub-finding PC-013.b owned under Register E independently of parent closure |
| 18 | Objective acceptance criteria | User-scoped repository change merges without tenant-repository-isolation-gate update. |
| 19 | Verification mechanism | Independent CI path gate on database.py user-scoped diffs |
| 20 | Failure condition | Repository change bypasses isolation gate via parent suite only |
| 21 | Evidence output required | E-SEC/tenant-repository-isolation-gate-log.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: APPLICABLE — P11 tenant repository isolation within modular monolith |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### PCtrl-013.c — Demo route production deny regression test

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | PCtrl-013.c |
| 2 | Finding ID | PC-013.c |
| 3 | Control type | PREVENTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 sub-finding PC-013.c enabling condition: failure of existing controls allowed Public demo feed reachable without production hard deny.. |
| 5 | Exact repository evidence files | dashboard.py, config.py |
| 6 | Exact symbols/settings/routes/tables/functions | /api/b2b/demo L1401-1416; B2B_DEMO_API_KEY default |
| 7 | Current defective behavior | Without independent blocking gate for PC-013.c, sub-scope defect can persist while parent PC-013 appears closed. |
| 8 | Required target behavior | test_security.py section asserting demo 404 in prod profile. |
| 9 | Control mechanism | Parametrized prod profile fixture in tests/security/test_production_demo_deny.py (PROPOSED_ARTIFACT). |
| 10 | Enforcement point | CI security test merge gate |
| 11 | Explicit affected files or bounded file families | dashboard.py, tests/security/test_production_demo_deny.py (PROPOSED_ARTIFACT) |
| 12 | Authority/owning bounded context | Production demo isolation / Register E preventive sub-gate |
| 13 | Positive impact | Independent regression block for sub-finding PC-013.c. |
| 14 | Potential negative impact | Additional CI path filters for sub-scope files. |
| 15 | Other findings affected | PC-030, PC-013.c |
| 16 | Required downstream revalidation | IVV sub-finding PC-013.c synthetic regression injection |
| 17 | Shared ownership or NONE with justification | NONE — sub-finding PC-013.c owned under Register E independently of parent closure |
| 18 | Objective acceptance criteria | Demo reachable in prod fails security test. |
| 19 | Verification mechanism | CI demo deny regression |
| 20 | Failure condition | Demo deny test not parametrized for prod |
| 21 | Evidence output required | E-SEC/demo-deny-regression-log.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### PCtrl-013.d — MFA enforcement regression test

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | PCtrl-013.d |
| 2 | Finding ID | PC-013.d |
| 3 | Control type | PREVENTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 sub-finding PC-013.d enabling condition: failure of existing controls allowed Enterprise MFA/SSO not implemented for admin tier.. |
| 5 | Exact repository evidence files | auth_service.py, dashboard.py admin routes |
| 6 | Exact symbols/settings/routes/tables/functions | ADMIN tier login; no MFA module |
| 7 | Current defective behavior | Without independent blocking gate for PC-013.d, sub-scope defect can persist while parent PC-013 appears closed. |
| 8 | Required target behavior | Admin login test with ADMIN_MFA_REQUIRED=true rejects single-factor success. |
| 9 | Control mechanism | tests/security/test_admin_mfa.py (PROPOSED_ARTIFACT) blocking single-factor when MFA required. |
| 10 | Enforcement point | CI security test merge gate |
| 11 | Explicit affected files or bounded file families | auth_service.py, tests/security/test_admin_mfa.py (PROPOSED_ARTIFACT) |
| 12 | Authority/owning bounded context | Admin MFA / Register E preventive sub-gate |
| 13 | Positive impact | Independent regression block for sub-finding PC-013.d. |
| 14 | Potential negative impact | Additional CI path filters for sub-scope files. |
| 15 | Other findings affected | PC-013, PC-013.d |
| 16 | Required downstream revalidation | IVV sub-finding PC-013.d synthetic regression injection |
| 17 | Shared ownership or NONE with justification | NONE — sub-finding PC-013.d owned under Register E independently of parent closure |
| 18 | Objective acceptance criteria | Single-factor pass fails when MFA required. |
| 19 | Verification mechanism | CI admin MFA regression |
| 20 | Failure condition | MFA flag ignored in login flow |
| 21 | Evidence output required | E-SEC/admin-mfa-regression-log.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### PCtrl-013.e — Route manifest golden diff

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | PCtrl-013.e |
| 2 | Finding ID | PC-013.e |
| 3 | Control type | PREVENTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 sub-finding PC-013.e enabling condition: failure of existing controls allowed Dev/prod route parity not audited at startup.. |
| 5 | Exact repository evidence files | dashboard.py, platform_api.py, production_guard.py |
| 6 | Exact symbols/settings/routes/tables/functions | route includes at FastAPI init |
| 7 | Current defective behavior | Without independent blocking gate for PC-013.e, sub-scope defect can persist while parent PC-013 appears closed. |
| 8 | Required target behavior | CI diffs prod route manifest against golden allow list on router changes. |
| 9 | Control mechanism | tests/security/test_production_route_manifest.py (PROPOSED_ARTIFACT) golden diff on router changes. |
| 10 | Enforcement point | CI path-filter merge gate |
| 11 | Explicit affected files or bounded file families | dashboard.py, platform_api.py, tests/security/test_production_route_manifest.py (PROPOSED_ARTIFACT) |
| 12 | Authority/owning bounded context | Production route audit / Register E preventive sub-gate |
| 13 | Positive impact | Independent regression block for sub-finding PC-013.e. |
| 14 | Potential negative impact | Additional CI path filters for sub-scope files. |
| 15 | Other findings affected | PC-030, PC-013.e |
| 16 | Required downstream revalidation | IVV sub-finding PC-013.e synthetic regression injection |
| 17 | Shared ownership or NONE with justification | NONE — sub-finding PC-013.e owned under Register E independently of parent closure |
| 18 | Objective acceptance criteria | New prod route not in golden fails CI diff. |
| 19 | Verification mechanism | CI route manifest golden test |
| 20 | Failure condition | Golden manifest stale |
| 21 | Evidence output required | E-SEC/route-manifest-golden-log.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### PCtrl-013.f — RBAC centralization static audit

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | PCtrl-013.f |
| 2 | Finding ID | PC-013.f |
| 3 | Control type | PREVENTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 sub-finding PC-013.f enabling condition: failure of existing controls allowed Tier authorization scattered vs P09 facade.. |
| 5 | Exact repository evidence files | auth_service.py, platform_api.py, dashboard.py |
| 6 | Exact symbols/settings/routes/tables/functions | TIER_FEATURES, require_feature scattered |
| 7 | Current defective behavior | Without independent blocking gate for PC-013.f, sub-scope defect can persist while parent PC-013 appears closed. |
| 8 | Required target behavior | Static analysis lists all routes; fails if tier check not via rbac_facade dependency. |
| 9 | Control mechanism | scripts/audit_route_rbac.py (PROPOSED_ARTIFACT) blocking CI on ad hoc tier checks. |
| 10 | Enforcement point | CI RBAC audit merge gate |
| 11 | Explicit affected files or bounded file families | platform_api.py, dashboard.py, scripts/audit_route_rbac.py (PROPOSED_ARTIFACT) |
| 12 | Authority/owning bounded context | RBAC facade / Register E preventive sub-gate |
| 13 | Positive impact | Independent regression block for sub-finding PC-013.f. |
| 14 | Potential negative impact | Additional CI path filters for sub-scope files. |
| 15 | Other findings affected | PC-013, PC-009 |
| 16 | Required downstream revalidation | IVV sub-finding PC-013.f synthetic regression injection |
| 17 | Shared ownership or NONE with justification | NONE — sub-finding PC-013.f owned under Register E independently of parent closure |
| 18 | Objective acceptance criteria | Ad hoc require_feature on route fails audit. |
| 19 | Verification mechanism | CI audit_route_rbac |
| 20 | Failure condition | RBAC audit not run on router change |
| 21 | Evidence output required | E-SEC/rbac-audit-gate.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### PCtrl-015.a — Absent matrix lint rule

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | PCtrl-015.a |
| 2 | Finding ID | PC-015.a |
| 3 | Control type | PREVENTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 sub-finding PC-015.a enabling condition: failure of existing controls allowed Referenced audit matrix absent; cannot mark HISTORICAL_NON_CURRENT in repo.. |
| 5 | Exact repository evidence files | FEATURE_REALITY_MATRIX.md (HISTORICAL_REFERENCE_NOT_PRESENT) |
| 6 | Exact symbols/settings/routes/tables/functions | absent audit matrix file |
| 7 | Current defective behavior | Without independent blocking gate for PC-015.a, sub-scope defect can persist while parent PC-015 appears closed. |
| 8 | Required target behavior | ssot-doc-lint ABSENT_ARCHIVED rule for FEATURE_REALITY_MATRIX references. |
| 9 | Control mechanism | ssot-doc-lint ABSENT_AUTHORITY_FILE rule cross-checks pointer only for absent matrix. |
| 10 | Enforcement point | CI ssot-doc-lint merge gate |
| 11 | Explicit affected files or bounded file families | scripts/ssot_doc_lint.py (PROPOSED_ARTIFACT), docs/institutional/CURRENT_PROGRAM_STATUS_POINTER.md |
| 12 | Authority/owning bounded context | Taxonomy documentation / Register A, K preventive sub-gate |
| 13 | Positive impact | Independent regression block for sub-finding PC-015.a. |
| 14 | Potential negative impact | Additional CI path filters for sub-scope files. |
| 15 | Other findings affected | PC-036, PC-015 |
| 16 | Required downstream revalidation | IVV sub-finding PC-015.a synthetic regression injection |
| 17 | Shared ownership or NONE with justification | NONE — sub-finding PC-015.a owned under Register A independently of parent closure |
| 18 | Objective acceptance criteria | Stale LIVE marker for absent matrix fails lint. |
| 19 | Verification mechanism | CI absent matrix lint |
| 20 | Failure condition | Pointer omits matrix status |
| 21 | Evidence output required | E-GOV/absent-matrix-lint.json |
| 22 | Architectural-decision compatibility | DEC-A: APPLICABLE — absent audit matrix marked non-authoritative; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### PCtrl-015.b — Grid-CAP crosswalk prohibition test

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | PCtrl-015.b |
| 2 | Finding ID | PC-015.b |
| 3 | Control type | PREVENTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 sub-finding PC-015.b enabling condition: failure of existing controls allowed 40-point grid ids conflict with 88-CAP institutional narrative without disclaimer.. |
| 5 | Exact repository evidence files | bd_platform/registry.py |
| 6 | Exact symbols/settings/routes/tables/functions | FEATURE_MATRIX ids 1-40 vs 88-CAP narrative |
| 7 | Current defective behavior | Without independent blocking gate for PC-015.b, sub-scope defect can persist while parent PC-015 appears closed. |
| 8 | Required target behavior | Test forbids automated grid id to CAP-### mapping in code or docs outside attested crosswalk file. |
| 9 | Control mechanism | tests/governance/test_no_grid_cap_automap.py (PROPOSED_ARTIFACT) blocking automap scripts. |
| 10 | Enforcement point | CI governance test merge gate |
| 11 | Explicit affected files or bounded file families | bd_platform/registry.py, tests/governance/test_no_grid_cap_automap.py (PROPOSED_ARTIFACT) |
| 12 | Authority/owning bounded context | Feature taxonomy / Register A preventive sub-gate |
| 13 | Positive impact | Independent regression block for sub-finding PC-015.b. |
| 14 | Potential negative impact | Additional CI path filters for sub-scope files. |
| 15 | Other findings affected | PC-003, PC-037 |
| 16 | Required downstream revalidation | IVV sub-finding PC-015.b synthetic regression injection |
| 17 | Shared ownership or NONE with justification | NONE — sub-finding PC-015.b owned under Register A independently of parent closure |
| 18 | Objective acceptance criteria | Automap script in repo fails governance test. |
| 19 | Verification mechanism | CI no-grid-cap-automap test |
| 20 | Failure condition | Disclaimer missing from registry module |
| 21 | Evidence output required | E-GOV/grid-cap-automap-gate.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: APPLICABLE — prohibits grid-to-CAP automap outside attested crosswalk; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### PCtrl-019.a — Serving path allowlist CI check

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | PCtrl-019.a |
| 2 | Finding ID | PC-019.a |
| 3 | Control type | PREVENTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 sub-finding PC-019.a enabling condition: failure of existing controls allowed Training artifact directories not guarded from serving paths in CI.. |
| 5 | Exact repository evidence files | ml/, data/models/, flywheel config |
| 6 | Exact symbols/settings/routes/tables/functions | training artifact paths vs serving config |
| 7 | Current defective behavior | Without independent blocking gate for PC-019.a, sub-scope defect can persist while parent PC-019 appears closed. |
| 8 | Required target behavior | ml_serving_boundary allowlist checked on every ml/ or flywheel config change. |
| 9 | Control mechanism | Path-filtered isolation test on ml/ and flywheel_saturation_guard.py config changes. |
| 10 | Enforcement point | CI path-filter merge gate |
| 11 | Explicit affected files or bounded file families | ml/, tests/ml/test_training_serving_path_isolation.py (PROPOSED_ARTIFACT) |
| 12 | Authority/owning bounded context | ML serving boundary / Register I preventive sub-gate |
| 13 | Positive impact | Independent regression block for sub-finding PC-019.a. |
| 14 | Potential negative impact | Additional CI path filters for sub-scope files. |
| 15 | Other findings affected | PC-019, PC-012 |
| 16 | Required downstream revalidation | IVV sub-finding PC-019.a synthetic regression injection |
| 17 | Shared ownership or NONE with justification | NONE — sub-finding PC-019.a owned under Register I independently of parent closure |
| 18 | Objective acceptance criteria | Config pointing to training dir fails scan. |
| 19 | Verification mechanism | CI ML path isolation path gate |
| 20 | Failure condition | Isolation test not triggered on ml change |
| 21 | Evidence output required | E-ML/serving-allowlist-gate.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### PCtrl-021.a — Docker import smoke in CI

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | PCtrl-021.a |
| 2 | Finding ID | PC-021.a |
| 3 | Control type | PREVENTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 sub-finding PC-021.a enabling condition: failure of existing controls allowed Manifest divergence breaks CI↔Docker parity for runtime imports.. |
| 5 | Exact repository evidence files | Dockerfile, requirements.txt, requirements-prod.txt, ci.yml |
| 6 | Exact symbols/settings/routes/tables/functions | COPY requirements-prod; ci installs dev requirements |
| 7 | Current defective behavior | Without independent blocking gate for PC-021.a, sub-scope defect can persist while parent PC-021 appears closed. |
| 8 | Required target behavior | Docker smoke container runs import smoke for ccxt/pandas/sklearn/kafka matching CI runner list. |
| 9 | Control mechanism | docker smoke step post-build blocking on import mismatch. |
| 10 | Enforcement point | CI Docker smoke merge gate |
| 11 | Explicit affected files or bounded file families | Dockerfile, .github/workflows/ci.yml, scripts/import_smoke.py (PROPOSED_ARTIFACT) |
| 12 | Authority/owning bounded context | Deploy parity / Register H preventive sub-gate |
| 13 | Positive impact | Independent regression block for sub-finding PC-021.a. |
| 14 | Potential negative impact | Additional CI path filters for sub-scope files. |
| 15 | Other findings affected | PC-001, PC-021 |
| 16 | Required downstream revalidation | IVV sub-finding PC-021.a synthetic regression injection |
| 17 | Shared ownership or NONE with justification | NONE — sub-finding PC-021.a owned under Register H independently of parent closure |
| 18 | Objective acceptance criteria | Import missing in container fails smoke. |
| 19 | Verification mechanism | CI Docker import smoke |
| 20 | Failure condition | Smoke step skipped on Dockerfile change |
| 21 | Evidence output required | E-BUILD/docker-smoke-gate.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### PCtrl-022.a — Independent collection gate required check registration

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | PCtrl-022.a |
| 2 | Finding ID | PC-022.a |
| 3 | Control type | PREVENTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 sub-finding PC-022.a enabling condition: failure of existing controls allowed No blocking full-collection pytest job; wave1 baseline absent; subset CI green while 30+ modules unt. |
| 5 | Exact repository evidence files | .github/workflows/ci.yml, tests/, data/wave1_full_regression.txt (HISTORICAL_REFERENCE_NOT_PRESENT) |
| 6 | Exact symbols/settings/routes/tables/functions | pytest --collect-only; absent wave1 baseline; ci subset only |
| 7 | Current defective behavior | Without independent blocking gate for PC-022.a, sub-scope defect can persist while parent PC-022 appears closed. |
| 8 | Required target behavior | Branch protection lists pytest-collection-gate as required check separate from subset test job; meta-test asserts independent job registration. |
| 9 | Control mechanism | docs/ci/REQUIRED_CHECKS.md (PROPOSED_ARTIFACT) lists pytest-collection-gate as standalone required check; tests/meta/test_collection_gate_independent.py (PROPOSED_ARTIFACT) verifies job separateness from subset test job. |
| 10 | Enforcement point | GitHub branch protection independent required check |
| 11 | Explicit affected files or bounded file families | .github/workflows/ci.yml, docs/ci/REQUIRED_CHECKS.md (PROPOSED_ARTIFACT), tests/meta/test_collection_gate_independent.py (PROPOSED_ARTIFACT) |
| 12 | Authority/owning bounded context | QA collection gate / Register F preventive sub-gate |
| 13 | Positive impact | Independent regression block for sub-finding PC-022.a. |
| 14 | Potential negative impact | Additional CI path filters for sub-scope files. |
| 15 | Other findings affected | PC-002, PC-039 |
| 16 | Required downstream revalidation | IVV sub-finding PC-022.a synthetic regression injection |
| 17 | Shared ownership or NONE with justification | NONE — sub-finding PC-022.a owned under Register F independently of parent closure |
| 18 | Objective acceptance criteria | Merge allowed when only subset test passes without collection gate required check. |
| 19 | Verification mechanism | Meta-test collection gate independence |
| 20 | Failure condition | Collection gate not listed as separate required check |
| 21 | Evidence output required | E-TEST/collection-gate-required-check-log.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### PCtrl-022.b — SSE job required on sse_stream changes

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | PCtrl-022.b |
| 2 | Finding ID | PC-022.b |
| 3 | Control type | PREVENTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 sub-finding PC-022.b enabling condition: failure of existing controls allowed No SSE/stream E2E in CI for Feature 002 streaming UI.. |
| 5 | Exact repository evidence files | bd_platform/sse_stream.py, tests/ |
| 6 | Exact symbols/settings/routes/tables/functions | absence of tests/e2e/ SSE tests |
| 7 | Current defective behavior | Without independent blocking gate for PC-022.b, sub-scope defect can persist while parent PC-022 appears closed. |
| 8 | Required target behavior | Path filter triggers SSE E2E job when bd_platform/sse_stream.py changes. |
| 9 | Control mechanism | CI paths filter on bd_platform/sse_stream.py requiring sse-e2e job. |
| 10 | Enforcement point | CI path-filter merge gate |
| 11 | Explicit affected files or bounded file families | bd_platform/sse_stream.py, .github/workflows/ci.yml, tests/e2e/test_sse_stream_ci.py (PROPOSED_ARTIFACT) |
| 12 | Authority/owning bounded context | SSE E2E / Register F preventive sub-gate |
| 13 | Positive impact | Independent regression block for sub-finding PC-022.b. |
| 14 | Potential negative impact | Additional CI path filters for sub-scope files. |
| 15 | Other findings affected | PC-022, PC-022.b |
| 16 | Required downstream revalidation | IVV sub-finding PC-022.b synthetic regression injection |
| 17 | Shared ownership or NONE with justification | NONE — sub-finding PC-022.b owned under Register F independently of parent closure |
| 18 | Objective acceptance criteria | SSE change without e2e job trigger fails path policy test. |
| 19 | Verification mechanism | CI SSE path filter meta-test |
| 20 | Failure condition | SSE e2e job not in workflow paths |
| 21 | Evidence output required | E-TEST/sse-path-filter-gate.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### PCtrl-022.c — Concurrency suite on execution_engine changes

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | PCtrl-022.c |
| 2 | Finding ID | PC-022.c |
| 3 | Control type | PREVENTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 sub-finding PC-022.c enabling condition: failure of existing controls allowed Execution concurrency races not in test suite.. |
| 5 | Exact repository evidence files | execution_engine.py, startup_orchestrator.py |
| 6 | Exact symbols/settings/routes/tables/functions | asyncio loop tasks; manual execute paths |
| 7 | Current defective behavior | Without independent blocking gate for PC-022.c, sub-scope defect can persist while parent PC-022 appears closed. |
| 8 | Required target behavior | Path filter runs concurrency suite on execution_engine.py changes. |
| 9 | Control mechanism | CI paths filter on execution_engine.py requiring concurrency job. |
| 10 | Enforcement point | CI path-filter merge gate |
| 11 | Explicit affected files or bounded file families | execution_engine.py, tests/concurrency/test_execution_races.py (PROPOSED_ARTIFACT), .github/workflows/ci.yml |
| 12 | Authority/owning bounded context | Execution concurrency / Register D, F preventive sub-gate |
| 13 | Positive impact | Independent regression block for sub-finding PC-022.c. |
| 14 | Potential negative impact | Additional CI path filters for sub-scope files. |
| 15 | Other findings affected | PC-014, PC-022.e |
| 16 | Required downstream revalidation | IVV sub-finding PC-022.c synthetic regression injection |
| 17 | Shared ownership or NONE with justification | NONE — sub-finding PC-022.c owned under Register D independently of parent closure |
| 18 | Objective acceptance criteria | Engine change skipping concurrency job fails meta-test. |
| 19 | Verification mechanism | CI concurrency path filter |
| 20 | Failure condition | Concurrency job skipped on engine edit |
| 21 | Evidence output required | E-TEST/concurrency-path-gate.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### PCtrl-022.d — Restore drill scheduled on main weekly

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | PCtrl-022.d |
| 2 | Finding ID | PC-022.d |
| 3 | Control type | PREVENTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 sub-finding PC-022.d enabling condition: failure of existing controls allowed Backup/restore drill not evidenced in tests.. |
| 5 | Exact repository evidence files | database.py, SQLite backup paths |
| 6 | Exact symbols/settings/routes/tables/functions | no tests/ops/ restore drill |
| 7 | Current defective behavior | Without independent blocking gate for PC-022.d, sub-scope defect can persist while parent PC-022 appears closed. |
| 8 | Required target behavior | Scheduled workflow .github/workflows/ops-drill.yml (PROPOSED_ARTIFACT) cron weekly on main; artifact retained 90 days. |
| 9 | Control mechanism | Weekly cron workflow blocking alert if artifact missing. |
| 10 | Enforcement point | Scheduled CI + artifact retention |
| 11 | Explicit affected files or bounded file families | tests/ops/test_backup_restore_drill.py (PROPOSED_ARTIFACT), .github/workflows/ops-drill.yml (PROPOSED_ARTIFACT) |
| 12 | Authority/owning bounded context | DR ops / Register F preventive sub-gate |
| 13 | Positive impact | Independent regression block for sub-finding PC-022.d. |
| 14 | Potential negative impact | Additional CI path filters for sub-scope files. |
| 15 | Other findings affected | PC-022, PC-027 |
| 16 | Required downstream revalidation | IVV sub-finding PC-022.d synthetic regression injection |
| 17 | Shared ownership or NONE with justification | NONE — sub-finding PC-022.d owned under Register F independently of parent closure |
| 18 | Objective acceptance criteria | Missing weekly artifact triggers alert script. |
| 19 | Verification mechanism | Scheduled ops-drill workflow |
| 20 | Failure condition | Weekly artifact missing without alert |
| 21 | Evidence output required | E-OPS/weekly-drill-schedule-log.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### PCtrl-022.e — Bypass matrix must stay 100% DENY

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | PCtrl-022.e |
| 2 | Finding ID | PC-022.e |
| 3 | Control type | PREVENTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 sub-finding PC-022.e enabling condition: failure of existing controls allowed Negative execution bypass tests incomplete across flag combinations.. |
| 5 | Exact repository evidence files | execution_engine.py, bd_platform/cex_dex_executor.py, execution_keys.py |
| 6 | Exact symbols/settings/routes/tables/functions | freeze, exposure, master switch env vars |
| 7 | Current defective behavior | Without independent blocking gate for PC-022.e, sub-scope defect can persist while parent PC-022 appears closed. |
| 8 | Required target behavior | CI parses bypass matrix artifact; any SUCCESS row fails build. |
| 9 | Control mechanism | Post-test artifact validator script blocking SUCCESS rows. |
| 10 | Enforcement point | CI merge gate |
| 11 | Explicit affected files or bounded file families | tests/security/test_execution_bypass_matrix.py (PROPOSED_ARTIFACT), scripts/validate_bypass_matrix.py (PROPOSED_ARTIFACT) |
| 12 | Authority/owning bounded context | Execution bypass / Register D, F preventive sub-gate |
| 13 | Positive impact | Independent regression block for sub-finding PC-022.e. |
| 14 | Potential negative impact | Additional CI path filters for sub-scope files. |
| 15 | Other findings affected | PC-005, PC-010.a |
| 16 | Required downstream revalidation | IVV sub-finding PC-022.e synthetic regression injection |
| 17 | Shared ownership or NONE with justification | NONE — sub-finding PC-022.e owned under Register D independently of parent closure |
| 18 | Objective acceptance criteria | Inject success row in fixture fails validator. |
| 19 | Verification mechanism | CI bypass matrix validator |
| 20 | Failure condition | Validator accepts SUCCESS row |
| 21 | Evidence output required | E-EXEC/bypass-matrix-validator-log.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |

### PCtrl-034.a — Workflow needs-graph meta-test

| # | Field | Value |
|---:|---|---|
| 1 | Control ID | PCtrl-034.a |
| 2 | Finding ID | PC-034.a |
| 3 | Control type | PREVENTIVE |
| 4 | Verified Stage 1 root cause addressed | Stage 1 sub-finding PC-034.a enabling condition: failure of existing controls allowed Security workflow can pass while collection gate and full test fail.. |
| 5 | Exact repository evidence files | .github/workflows/security.yml, .github/workflows/ci.yml |
| 6 | Exact symbols/settings/routes/tables/functions | separate workflow jobs without needs |
| 7 | Current defective behavior | Without independent blocking gate for PC-034.a, sub-scope defect can persist while parent PC-034 appears closed. |
| 8 | Required target behavior | Meta-test parses workflow YAML asserting security job needs full-suite jobs. |
| 9 | Control mechanism | tests/meta/test_security_workflow_needs.py (PROPOSED_ARTIFACT) fails if needs dependency removed. |
| 10 | Enforcement point | CI meta-test merge gate |
| 11 | Explicit affected files or bounded file families | .github/workflows/ci.yml, tests/meta/test_security_workflow_needs.py (PROPOSED_ARTIFACT) |
| 12 | Authority/owning bounded context | CI workflow orchestration / Register F preventive sub-gate |
| 13 | Positive impact | Independent regression block for sub-finding PC-034.a. |
| 14 | Potential negative impact | Additional CI path filters for sub-scope files. |
| 15 | Other findings affected | PC-033, PC-034 |
| 16 | Required downstream revalidation | IVV sub-finding PC-034.a synthetic regression injection |
| 17 | Shared ownership or NONE with justification | NONE — sub-finding PC-034.a owned under Register F independently of parent closure |
| 18 | Objective acceptance criteria | Removing needs: dependency fails meta-test. |
| 19 | Verification mechanism | CI security needs meta-test |
| 20 | Failure condition | needs graph not enforced |
| 21 | Evidence output required | E-CI/security-needs-meta-test.json |
| 22 | Architectural-decision compatibility | DEC-A: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-B: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-C: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-D: NOT_APPLICABLE — control scope does not intersect this decision binding; DEC-E: NOT_APPLICABLE — control scope does not intersect this decision binding |
| 23 | Stage-boundary declaration | DESIGN_ONLY — NOT EXECUTABLE |


---

## Control Coverage Index

| Category | Count | IDs |
|----------|-------|-----|
| Parent corrective | 42 | CC-001–CC-042 |
| Parent preventive | 42 | PCtrl-001–PCtrl-042 |
| Sub corrective | 29 | CC-008.a–CC-034.a (see Sub-Finding sections) |
| Sub preventive | 29 | PCtrl-008.a–PCtrl-034.a (see Sub-Finding sections) |
| **Total controls** | **142** | |

Every parent PC-001–PC-042 and sub-finding PC-008.a–PC-034.a (29 subs) has exactly one CC and one PCtrl. Sub-finding controls address independent closure evidence from Stage 1 with scope narrower than their parent.

---

## Register Cross-Reference

| Register | Primary control themes |
|----------|------------------------|
| A | CC-003, CC-015, CC-036, CC-037, CC-009.b, CC-015.a/b, PCtrl-003, PCtrl-015, PCtrl-036, PCtrl-037 |
| B | CC-007–009, CC-031, CC-008.a–d, CC-009.a/d, CC-020, platform route/import/topology controls |
| C | CC-004, CC-026, CC-009.c, CC-009.d, PCtrl-004, PCtrl-026, PCtrl-009.c |
| D | CC-005, CC-010, CC-014, CC-010.a, CC-022.c/e, PCtrl-005, PCtrl-010 |
| E | CC-013, CC-030, CC-013.a–f, PCtrl-013, PCtrl-030, PCtrl-013.b |
| F | CC-002, CC-022, CC-033, CC-034, CC-039, CC-022.a–e, CC-034.a, PCtrl-002, PCtrl-022 |
| G | CC-011, CC-029, CC-035, CC-040, CC-011.a/b, PCtrl-011, PCtrl-029, PCtrl-035 |
| H | CC-001, CC-007, CC-016, CC-017, CC-021, CC-025, CC-021.a, PCtrl-001, PCtrl-007, PCtrl-021 |
| I | CC-012, CC-019, CC-028, CC-012.a/b, CC-019.a, PCtrl-012, PCtrl-019 |
| J | CC-006, CC-027, CC-041, CC-009.c, PCtrl-006, PCtrl-027, PCtrl-041 |
| K | CC-023, CC-032, CC-036, CC-037, CC-042, CC-015.a, PCtrl-023, PCtrl-032, PCtrl-042 |
| L | CC-024, CC-038, CC-008.d, CC-013.d/e, PCtrl-024, PCtrl-008.d |

---

## Stage 2 IVV Checklist (design-level)

1. 42/42 parent CC + 42/42 parent PCtrl present with unique statements and all 23 fields populated
2. 29/29 sub CC + 29/29 sub PCtrl present with distinct scope from parent
3. Zero controls use parameter-substituted boilerplate or delegated "see parent" closures
4. Every control references concrete files, jobs, or modules from ROOT_CAUSE_REGISTER v4.0 evidence
5. All PCtrl controls specify blocking CI, runtime, schema, or static-analysis enforcement (no advisory-only)
6. Special repairs verified: PC-031 topology contract, PC-036 taxonomy authority, PC-037 attestation binding, PCtrl-020 blocking composition invariant, CC-009.c independent scan decimal path, CC-022.a independent collection gate, PCtrl-013.b independent tenant repository gate
7. No MIG-01–MIG-07 references; no R0-Sxx step references in control bodies
8. Proposed new artifacts marked PROPOSED_ARTIFACT — STAGE 3 MUST DECIDE LOCATION
9. Stage-boundary declaration on every control: DESIGN_ONLY — NOT EXECUTABLE

**Stage 2 status:** REMEDIATED_PENDING_IVV
