# Root Cause Register — Stage 1 Evidence-Anchored Baseline

**Version:** 4.0 (Stage 1 reconstruction)  
**Date:** 2026-08-05  
**Validation branch:** `cursor/g2-g3-quality-gates-soak`  
**Validation commit:** `14112859677b68932c79b31d09a8aed49272794a`  
**Scope:** Diagnosis only — no corrective or preventive controls in this artifact.

## Stage 1 Notice

This register replaces semantically invalid generated finding prose. Stages 2+ (controls, steps, test matrix, migrations) remain **SEMANTICALLY_INVALID — DO NOT EXECUTE** in sibling artifacts until independently verified.

Historical references absent from the current tree are marked **HISTORICAL_REFERENCE_NOT_PRESENT** and are not cited as live runtime evidence.

---

## Parent Findings (PC-001–PC-042)

### PC-001 — Dependency resolution is not lockfile-pinned

| Field | Value |
|-------|-------|
| Original severity | CRITICAL |
| Current validated severity | CRITICAL |
| Category | Reproducibility |
| Exact files | `requirements.txt`, `requirements-prod.txt` |
| Exact symbols | pip install targets (no `requirements-lock.txt`, no `pip-compile` output) |
| Evidence | `requirements.txt` L1–24 uses semver ranges (`pandas>=2.2.0`, `ccxt>=4.4.0`). No lockfile exists in repo. |
| Immediate defect | Identical `pip install -r requirements.txt` on two dates can resolve different transitive versions. |
| Systemic root cause | The project adopted range-based manifests for developer convenience but never introduced a single resolved dependency artifact as the deploy/CI authority, so reproducibility was never a hard contract. |
| Enabling condition | CI and Docker install from manifests without comparing resolved trees across environments. |
| Why existing controls failed | `.github/workflows/security.yml` runs pip-audit on whatever resolves at job time; it does not freeze or compare trees. No CI job diffs resolved dependencies. |
| Current runtime impact | Production incidents from dependency drift cannot be replayed with the same package set used during DD. |
| Future construction impact | Wave 2 modules inherit unpinned transitive deps; regression attribution becomes impossible. |
| Data impact | Indirect — ML/scientific stack versions can shift between runs. |
| Security impact | CVE fixes in transitive deps appear silently between clones. |
| Acquisition impact | Buyer cannot reproduce stated test/DD environment from commit alone. |
| Feature Registry blocking | No |
| Capability Mapping blocking | No |
| Implementation blocking | Yes — G1 reproducibility gate |
| Confidence | HIGH |
| Linked registers | H |
| Linked sub-findings | PC-021.a |
| Required decision type | Build authority (single lockfile owner) |

### PC-002 — CI does not execute the claimed full test corpus

| Field | Value |
|-------|-------|
| Original severity | CRITICAL |
| Current validated severity | CRITICAL |
| Category | Test / Evidence |
| Exact files | `.github/workflows/ci.yml`, `tests/` |
| Exact symbols | CI job `test`; local `launch_checklist.py::_run_pytest_quick` |
| Evidence | `ci.yml` L25–29 runs only four modules with a 90% coverage gate. `tests/` contains 34 `test_*.py` files. `launch_checklist.py` L32 runs `pytest tests/ -q` locally — broader than CI. |
| Immediate defect | Institutional “full suite” claims are not enforced on every merge. |
| Systemic root cause | CI was optimized for fast profit/fee feedback during fee-matrix work; the workflow never gained a blocking full-collection job, so speed became the de facto quality gate. |
| Enabling condition | No meta-test asserts `pytest --collect-only` count against a stored baseline; `data/wave1_full_regression.txt` is **HISTORICAL_REFERENCE_NOT_PRESENT**. |
| Why existing controls failed | Subset tests pass independently; `scripts/due_diligence_verify.py` smoke does not invoke pytest collection count. |
| Current runtime impact | Regressions in 30+ untested modules can merge while CI stays green. |
| Future construction impact | Any Wave 2 feature can ship without automated regression detection. |
| Data impact | None direct |
| Security impact | Security workflow (`.github/workflows/security.yml`) also runs a subset (`tests/test_security.py`, `tests/test_risk_manager.py`) — orthogonal to main CI. |
| Acquisition impact | DD materials referencing “862 tests” or full regression are not CI-provable at this commit. |
| Feature Registry blocking | No |
| Capability Mapping blocking | No |
| Implementation blocking | Yes — G1 |
| Confidence | HIGH |
| Linked registers | F |
| Linked sub-findings | PC-022.a |
| Required decision type | QA gate policy |

### PC-003 — No attested Feature Registry; runtime grid acts as enumeration

| Field | Value |
|-------|-------|
| Original severity | CRITICAL |
| Current validated severity | CRITICAL |
| Category | Feature Authority |
| Exact files | `bd_platform/registry.py`; docs/institutional/ (HISTORICAL_REFERENCE_NOT_PRESENT) |
| Exact symbols | `FEATURE_MATRIX`, `feature_summary()` |
| Evidence | `bd_platform/registry.py` L10–51 defines 40 features with ids 1–40, modules, endpoints. `feature_summary()` L54–77 counts import success. `docs/institutional/` directory **HISTORICAL_REFERENCE_NOT_PRESENT**. |
| Immediate defect | Feature identity is inferred from a product roadmap grid, not an owner-attested FCP master list. |
| Systemic root cause | Engineering built a 40-point delivery tracker (`FEATURE_MATRIX`) for internal roadmap visibility; it was never formally separated from institutional feature authority (DEC-A), so DD consumers treat importable modules as “live features.” |
| Enabling condition | Dashboard and `/api/platform/features` expose grid-derived counts without an attestation boundary. |
| Why existing controls failed | No document marks the grid as non-authoritative; no CI test forbids feature ID assignment from the grid. |
| Current runtime impact | Feature completion percentages in API responses reflect import success, not attested capability state. |
| Future construction impact | DEC-A Feature Registry and DEC-B crosswalk cannot start until enumeration authority is settled. |
| Data impact | None |
| Security impact | Tier gating uses separate `auth_service.TIER_FEATURES` — a third feature view. |
| Acquisition impact | Feature inventory in DD cannot be signed by product owner. |
| Feature Registry blocking | Yes |
| Capability Mapping blocking | Yes |
| Implementation blocking | Yes — Wave 2 feature claims |
| Confidence | HIGH |
| Linked registers | A, K |
| Linked sub-findings | PC-009.b, PC-015.b |
| Required decision type | Owner attestation (OD-01) |

### PC-004 — Price authority is split; canonical APIs absent

| Field | Value |
|-------|-------|
| Original severity | CRITICAL |
| Current validated severity | CRITICAL |
| Category | Data Authority |
| Exact files | `live_book_hub.py`, `market_context.py`, `scripts/g2_live_ws_validation.py` |
| Exact symbols | `get_best_price`, `probe_price_sources`; missing `get_canonical_price`, `compute_ugp` |
| Evidence | `live_book_hub.py` L85–99: in-memory `_books` + `get_best_price`. `market_context.py` has REST/multi-source helpers but no canonical price API. `g2_live_ws_validation.py` L263 imports `unified_global_price.compute_ugp` — module **HISTORICAL_REFERENCE_NOT_PRESENT** (import would fail if executed). |
| Immediate defect | Execution and scan paths read hub prices directly; G2 validation assumes a UGP module that does not exist. |
| Systemic root cause | WS hub was built first as the live substrate; a second “canonical price” layer was specified in remediation DEC-C but never implemented, while G2 scripts were written against the planned module. |
| Enabling condition | `fast_scan_engine.py` L13–24 reads `get_best_price` per venue without freshness authority contract. |
| Why existing controls failed | G2 cross-source test can pass venue mids while `ugp_price` is null (observed in validation logs pattern); no contract test binds execution to one price authority. |
| Current runtime impact | Profit scans use whichever hub row exists; stale or single-venue prices can enter fee math. |
| Future construction impact | DEC-C cannot be enforced; dual price truth persists under any Wave 2 execution work. |
| Data impact | High — all PnL paths inherit hub semantics |
| Security impact | Medium — stale prices could affect execution decisions if live mode enabled |
| Acquisition impact | “Single price truth” claims are not implementable at this commit |
| Feature Registry blocking | No |
| Capability Mapping blocking | Yes — CAP price substrates unmapped |
| Implementation blocking | Yes — G2/G3 price evidence |
| Confidence | HIGH |
| Linked registers | C |
| Linked sub-findings | — |
| Required decision type | Architecture (DEC-C implementation) |

### PC-005 — Execution kill-switch authority is fragmented

| Field | Value |
|-------|-------|
| Original severity | CRITICAL |
| Current validated severity | CRITICAL |
| Category | Execution Safety |
| Exact files | `execution_engine.py`, `execution_keys.py`, `instant_alert_engine.py`, `startup_orchestrator.py` |
| Exact symbols | `AUTO_EXECUTION_ENABLED`, `AUTO_EXECUTION_DRY_RUN`, `AUTO_EXECUTION_LOOP`; missing `EXECUTION_ENABLED`, `execution_safety_guard` |
| Evidence | `execution_engine.py` L64–65: `_live_enabled()` reads `AUTO_EXECUTION_ENABLED` default `"false"`. L116: loop status uses `AUTO_EXECUTION_LOOP` default `"true"`. `startup_orchestrator.py` L247–250: auto-exec task gated with `AUTO_EXECUTION_LOOP` default **`"false"`**. `execution_safety_guard.py` **HISTORICAL_REFERENCE_NOT_PRESENT**. |
| Immediate defect | Three modules disagree on default loop behavior; no single master switch with UNKNOWN=DENY semantics. |
| Systemic root cause | Auto-execution grew incrementally (keys file, engine, orchestrator, docker-compose overrides) without a consolidated authorization module; each layer added its own env flag. |
| Enabling condition | `docker-compose.yml` arbitrage service sets `AUTO_EXECUTION_LOOP: "true"` while orchestrator defaults false — environment profile determines divergent behavior. |
| Why existing controls failed | `tests/test_execution_keys.py` covers key file parsing, not cross-module default consistency or fail-closed master gate. |
| Current runtime impact | Operator cannot determine live-trading posture from one flag; misconfiguration enables background loops in some profiles only. |
| Future construction impact | DEC-D unified execution authorization cannot be verified. |
| Data impact | Orders may be placed when one layer thinks live is off and another starts loops. |
| Security impact | Critical — split authority is an execution-safety class defect |
| Acquisition impact | Live-trading safety story fails institutional review |
| Feature Registry blocking | No |
| Capability Mapping blocking | No |
| Implementation blocking | Yes — any live execution |
| Confidence | HIGH |
| Linked registers | D |
| Linked sub-findings | PC-010.a, PC-022.e |
| Required decision type | Architecture (DEC-D) |

### PC-006 — Monetary columns use SQLite REAL (binary float)

| Field | Value |
|-------|-------|
| Original severity | CRITICAL |
| Current validated severity | CRITICAL |
| Category | Financial Safety |
| Exact files | `database.py` |
| Exact symbols | DDL `REAL` on financial columns |
| Evidence | Sample: L32–34 `pricing_logs.price/volume/opportunity_score REAL`; L72–77 `evaluated_opportunities.net_profit_usdt REAL`; L180–187 `oracle_predictions.price_at_prediction REAL`. No `NUMERIC`/`DECIMAL` types in schema. |
| Immediate defect | Cumulative fee/profit aggregates suffer IEEE-754 representation error at scale. |
| Systemic root cause | SQLite schema was authored with REAL for simplicity before institutional financial precision requirements; migration to exact decimal types was deferred. |
| Enabling condition | Python code reads/writes floats end-to-end (`fee_matrix.py`, `fast_scan_engine.py` also use float). |
| Why existing controls failed | Profit/fee CI subset tests assert business logic on small numbers; no property test enforces decimal invariants on aggregate columns. |
| Current runtime impact | Track-record and fee totals may drift at high precision requirements. |
| Future construction impact | Institutional P03/P04 financial claims require decimal migration before production scale. |
| Data impact | Direct — all persisted money fields |
| Security impact | Low direct |
| Acquisition impact | Financial DD precision questions cannot be answered affirmatively |
| Feature Registry blocking | No |
| Capability Mapping blocking | No |
| Implementation blocking | Yes — financial migration gate |
| Confidence | HIGH |
| Linked registers | J |
| Linked sub-findings | PC-009.c |
| Required decision type | Data migration policy |

### PC-007 — Runtime topology varies by entry path and SERVICE_MODE defaults

| Field | Value |
|-------|-------|
| Original severity | HIGH |
| Current validated severity | HIGH |
| Category | Runtime Topology |
| Exact files | `run_service.py`, `config.py`, `dashboard.py`, `microservices/lifecycle.py`, `Dockerfile`, `docker-compose.yml`, `launch_verify.bat` |
| Exact symbols | `MODES`, `SERVICE_MODE`, `lifespan`, `startup()`, `current_mode()` |
| Evidence | `config.py` L99–101: default `SERVICE_MODE` is `"web"` on Railway else `"all"`. `run_service.py` L22–28 defines five modes; L38 sets env; L47 `health_port = port + 100`. `dashboard.py` L260–276: when `SERVICE_MODE=="web"`, calls `microservices.lifecycle.startup("web")` and **returns without** `startup_orchestrator`. L278–283: all other modes use `run_background_startup`. `lifecycle.py` L64–65: mode `"all"` logs “use dashboard monolith lifespan” — no worker boot. `Dockerfile` L8 `SERVICE_MODE=web`. `launch_verify.bat` L8 invokes `scripts/launch_verify.py` — does **not** call `run_service.py`. `START.bat` **HISTORICAL_REFERENCE_NOT_PRESENT**. |
| Immediate defect | Same repository commit produces different background-service graphs depending on whether the operator uses Docker (`web`), local default (`all`), or compose multi-service workers. |
| Systemic root cause | The codebase is mid-transition between monolith (`startup_orchestrator`) and microservice workers (`microservices/lifecycle.py`); entry-point documentation and defaults were never unified, so “the running system” is not a single defined topology. |
| Enabling condition | Multiple valid boot paths (direct uvicorn, `run_service.py`, compose services) each set different env defaults. |
| Why existing controls failed | `production_guard.py` checks `SERVICE_MODE=web` for prod readiness but does not validate orchestrator vs lifecycle path. No architecture test asserts one canonical boot graph per profile. |
| Current runtime impact | Operators following `launch_verify.bat` validate HTTP on :8080 but not the background trading/ingestion stack that production Docker enables differently. |
| Future construction impact | Wave 2 P03/P07 coupling depends on which services actually start — platform boundaries cannot be tested against one topology. |
| Data impact | Ingestion and price feeds may be absent in `web`-only path while present in `all`. |
| Security impact | Auto-exec and ingestion exposure differs by boot path (see PC-005). |
| Acquisition impact | “What runs in production?” cannot be answered from one diagram. |
| Feature Registry blocking | No |
| Capability Mapping blocking | No |
| Implementation blocking | Yes — operability and soak tests |
| Confidence | HIGH |
| Linked registers | H, B |
| Linked sub-findings | PC-008.a |
| Required decision type | Operations / architecture (canonical boot profile) |

### PC-008 — Composition root activates broad domains without governed opt-in

| Field | Value |
|-------|-------|
| Original severity | HIGH |
| Current validated severity | HIGH |
| Category | Hidden Coupling |
| Exact files | `startup_orchestrator.py`, `platform_api.py`, `dashboard.py` |
| Exact symbols | `run_background_startup`, `RuntimeState`, `platform_api.router` |
| Evidence | `startup_orchestrator.py` L40–297 sequentially starts keys, aggregator, telegram, instant alerts, B2B WS, exchange WS, price stream, fee matrix, ingestion, ML flywheel, reports, optional auto-exec, DB maintenance, cloud sync. Most gated only by env defaults (`RUN_AGGREGATOR` default true L77). `platform_api.py` mounts 61 route handlers on `/api/platform`. |
| Immediate defect | HTTP readiness does not imply a minimal safe runtime — heavy trading/ML domains start unless env overrides are known and set. |
| Systemic root cause | `startup_orchestrator` was designed as a “convenience launcher” to avoid slow dashboard bind times, not as a policy-enforced composition root with explicit capability opt-in per platform (P01–P16). |
| Enabling condition | `SERVICE_MODE=all` path always runs full orchestrator sequence after DB init. |
| Why existing controls failed | No architecture test enumerates required opt-in flags per domain; `tests/test_core_modules.py` imports modules but does not assert startup graph. |
| Current runtime impact | Dev/staging environments may run exchange WS + auto-exec paths unintentionally. |
| Future construction impact | Cannot enforce P03/P07 isolation while orchestrator bundles domains. |
| Data impact | Ingestion and WS feeds start writing without separate approval. |
| Security impact | Broader attack surface when all background services start by default. |
| Acquisition impact | Due diligence cannot map “minimal production footprint.” |
| Feature Registry blocking | No |
| Capability Mapping blocking | Yes — platform activation boundaries unclear |
| Implementation blocking | Yes — Wave 2 platform separation |
| Confidence | HIGH |
| Linked registers | B |
| Linked sub-findings | PC-008.a, PC-008.b, PC-008.c, PC-008.d |
| Required decision type | Architecture (composition root policy) |

### PC-009 — Platform API layer overlaps P01/P02 registry boundaries

| Field | Value |
|-------|-------|
| Original severity | HIGH |
| Current validated severity | HIGH |
| Category | Platform Boundary |
| Exact files | `platform_api.py`, `bd_platform/registry.py`, `dashboard.py` |
| Exact symbols | `APIRouter(prefix="/api/platform")`, `FEATURE_MATRIX` |
| Evidence | `platform_api.py` L11: router prefix; 61 `@router` handlers spanning keys, ML, derivatives, arb, onchain, bots, etc. `bd_platform/registry.py` maps overlapping endpoints (e.g. `/api/platform/arb/cex-dex` id 9). Direct imports from `bd_platform.*` throughout `platform_api.py`. |
| Immediate defect | HTTP surface area is owned by a monolithic router file, not per-platform facades (P13). |
| Systemic root cause | Early B2B API expansion added routes to `platform_api.py` faster than platform registry governance; the 40-point grid documented modules but did not enforce import or route ownership boundaries. |
| Enabling condition | `dashboard.py` includes `platform_api.router` without route-level ownership metadata. |
| Why existing controls failed | No static analysis counts routes per platform; `tests/test_platform_features.py` checks feature endpoints exist, not boundary compliance. |
| Current runtime impact | Any platform change can require edits to shared 500+ line API file — merge conflicts and cross-platform regressions. |
| Future construction impact | DEC-E P01–P16 modular monolith cannot be validated while API sprawl continues. |
| Data impact | Portfolio and arb endpoints may duplicate logic elsewhere (PC-009.d). |
| Security impact | Auth tiers applied per-route inconsistently across large surface. |
| Acquisition impact | Platform map for DD does not match code ownership. |
| Feature Registry blocking | No |
| Capability Mapping blocking | Yes |
| Implementation blocking | Yes — P13 facade work |
| Confidence | HIGH |
| Linked registers | B, J |
| Linked sub-findings | PC-009.a, PC-009.b, PC-009.c, PC-009.d |
| Required decision type | Architecture (platform routing) |

### PC-010 — Execution authorization is not centralized before venue connectors

| Field | Value |
|-------|-------|
| Original severity | HIGH |
| Current validated severity | HIGH |
| Category | Platform Boundary / Execution Safety |
| Exact files | `bd_platform/cex_dex_executor.py`, `execution_engine.py`, `platform_api.py` |
| Exact symbols | `execute_cex_dex_opportunity`, `execute_order`, `_live_enabled` |
| Evidence | `cex_dex_executor.py` L49–52: CEX leg calls `execution_engine.execute_order`. L18–21: dry-run gated on `CEX_DEX_EXECUTION_ENABLED` + `AUTO_EXECUTION_DRY_RUN` — separate from engine live flag. `platform_api.py` exposes `/arb/cex-dex/execute`. No `authorize_execution()` or exposure/freeze consult visible in executor path. |
| Immediate defect | Venue-level execution can proceed through connector modules without a unified risk/exposure gate. |
| Systemic root cause | CEX-DEX feature was integrated by delegating to `execution_engine` dry-run defaults, assuming engine flags suffice; institutional execution-gating (P09/P04/P07 overlap) was never wired as a mandatory pre-connector service. |
| Enabling condition | API POST to execute path reachable when platform keys and env flags align. |
| Why existing controls failed | `tests/test_cex_dex.py` validates functional paths; no negative test proves freeze/exposure denial at connector boundary. |
| Current runtime impact | Live CEX leg could place orders if env enables execution even when risk freeze state loaded elsewhere is not consulted in executor. |
| Future construction impact | Wave 2 execution safety claims fail without centralized gate. |
| Data impact | Order placement |
| Security impact | High — bypass class for freeze/exposure |
| Acquisition impact | Execution safety DD gap |
| Feature Registry blocking | No |
| Capability Mapping blocking | Yes — P06/P04 |
| Implementation blocking | Yes — live trading |
| Confidence | HIGH |
| Linked registers | D, B |
| Linked sub-findings | PC-010.a |
| Required decision type | Architecture (DEC-D connector wrapper) |

### PC-011 — G3 soak gate scope is not machine-distinguishable from pilot runs

| Field | Value |
|-------|-------|
| Original severity | HIGH |
| Current validated severity | HIGH |
| Category | G3 / Evidence |
| Exact files | `scripts/g3_reliability_soak_test.py`, `FEATURE_001_G3_SOAK_TEST_REPORT.md` |
| Exact symbols | `TREND_MILESTONE_HOURS`, `hours_required`, `--hours` |
| Evidence | `g3_reliability_soak_test.py` L47 milestones (1,6,12,18,24); L539/L1064 default `hours_required=24`; L1052 `--hours` min 1 for smoke. Report L3 status **IN PROGRESS**; L82–84 awaiting 24/24 snapshots. No `gate_scope` field in assessment JSON schema at this commit. |
| Immediate defect | A 1-hour smoke run and a 24-hour institutional soak use the same assessor code path with only CLI duration differing — artifacts can be misread as institutional PASS. |
| Systemic root cause | G3 harness was built incrementally for Feature 001 pilot; institutional gate taxonomy (pilot vs production soak) was never encoded in evidence schema or assessor output. |
| Enabling condition | `--hours 1` allowed without mandatory `gate_scope: PILOT` marker in output JSON. |
| Why existing controls failed | No CI schema validation on G3 artifacts; report is human-maintained markdown. |
| Current runtime impact | G3 status in report is IN PROGRESS — no finalized institutional artifact exists yet. |
| Future construction impact | Feature closure gates G3/G7 cannot be automated until scope is machine-readable. |
| Data impact | Assessment JSON semantics |
| Security impact | Low |
| Acquisition impact | Pilot evidence could be mistaken for institutional 24h proof |
| Feature Registry blocking | Yes — Features 001/002 G3 |
| Capability Mapping blocking | No |
| Implementation blocking | Yes — G3 |
| Confidence | HIGH |
| Linked registers | G |
| Linked sub-findings | PC-011.a, PC-011.b |
| Required decision type | Evidence schema |

### PC-012 — Oracle/research inference paths lack single stack authority

| Field | Value |
|-------|-------|
| Original severity | HIGH |
| Current validated severity | HIGH |
| Category | Oracle Architecture |
| Exact files | `research_lab.py`, `oracle_retrainer.py`, `oracle_integrity.py`, `api/routers/oracle.py` |
| Exact symbols | `build_research_lab_report`, `run_oracle_retrain_step`, `prediction_source`, `filter_live_predictions` |
| Evidence | `research_lab.py` L212–270 builds signed research reports with oracle audit sections. `oracle_retrainer.py` imported from `api/routers/oracle.py` L173 and `startup_orchestrator.py` L183. `oracle_integrity.py` L12–29 classifies synthetic vs live sources. `cap047_oracle.py`, `decision_intelligence_pipeline.py` **HISTORICAL_REFERENCE_NOT_PRESENT**. |
| Immediate defect | Research reporting, retraining, and integrity filtering are separate entrypoints without one documented inference/provenance stack. |
| Systemic root cause | Oracle capabilities grew as independent modules (research narrative, retrain loop, integrity SQL filters) without a CAP-053 lineage contract binding them. |
| Enabling condition | Dashboard `/api/research/lab` and oracle router both expose inference-related outputs. |
| Why existing controls failed | `tests/test_oracle_audit_chain.py` covers chain integrity partially; no E2E test proves lineage fields on every decision path. |
| Current runtime impact | Provenance claims in research export may omit retrain-path predictions. |
| Future construction impact | P06/P10 institutional grade blocked. |
| Data impact | Oracle prediction tables |
| Security impact | Medium — synthetic/live boundary relies on convention |
| Acquisition impact | XAI/provenance DD incomplete |
| Feature Registry blocking | No |
| Capability Mapping blocking | Yes — CAP-053 |
| Implementation blocking | Yes — oracle institutional gate |
| Confidence | HIGH |
| Linked registers | I |
| Linked sub-findings | PC-012.a, PC-012.b |
| Required decision type | Architecture (oracle stack) |

### PC-013 — Tenancy, secrets, and production isolation are not institution-grade

| Field | Value |
|-------|-------|
| Original severity | HIGH |
| Current validated severity | HIGH |
| Category | Tenancy / Security |
| Exact files | `.gitignore`, `auth_service.py`, `dashboard.py`, `production_guard.py`, `execution_keys.py` |
| Exact symbols | `keys/`, `TIER_FEATURES`, `evaluate_production_guard`, `B2B_DEMO_API_KEY` |
| Evidence | `.gitignore` L19–21 excludes `keys/`. `auth_service.py` L17–61: tier-based `TIER_FEATURES` — no org/tenant id. `dashboard.py` L1401–1416: public `/api/b2b/demo`. `config.py` L489 default demo key. `production_guard.py` L28–107: infra checks only. Committed `keys/` directory absent (expected — gitignored). |
| Immediate defect | Multi-tenant isolation, MFA, and production demo isolation are not enforced as a unified P11 contract. |
| Systemic root cause | Product shipped as single-tenant tier gating; enterprise tenancy and production hardening were documented as goals but not encoded as mandatory middleware or startup audits. |
| Enabling condition | Secrets required for live validation live only in gitignored paths; demo endpoints keyed off env defaults. |
| Why existing controls failed | `tests/test_security.py` covers auth endpoints; no cross-tenant negative suite; demo route production deny not tested. |
| Current runtime impact | Clone-only CI cannot reproduce exchange-key-dependent live proofs. |
| Future construction impact | Multi-tenant Wave 2 and enterprise MFA blocked. |
| Data impact | user-scoped rows without tenant guard |
| Security impact | High |
| Acquisition impact | Enterprise security DD gaps |
| Feature Registry blocking | No |
| Capability Mapping blocking | Yes — P11 |
| Implementation blocking | Yes — production tenancy |
| Confidence | HIGH |
| Linked registers | E, L |
| Linked sub-findings | PC-013.a–PC-013.f |
| Required decision type | Security architecture |

### PC-014 — Execution and runtime control state is primarily in-memory

| Field | Value |
|-------|-------|
| Original severity | HIGH |
| Current validated severity | HIGH |
| Category | Execution State |
| Exact files | `startup_orchestrator.py`, `dashboard.py`, `execution_engine.py` |
| Exact symbols | `RuntimeState`, `app.state.runtime`, module-level loop tasks |
| Evidence | `RuntimeState` L22–37: dataclass fields for tasks/flags only — no persistence hooks. `dashboard.py` L281–283 attaches runtime to `app.state`. Process restart clears all task handles and in-flight gating context unless separately reloaded (`load_persistent_freeze` L256 is risk-specific, not full execution authority). |
| Immediate defect | Restart drops orchestrator task graph and execution loop state; recovery depends on implicit re-read of env/files. |
| Systemic root cause | Background services were modeled as asyncio tasks in memory for fast iteration; durable execution authority store was planned but not implemented before G3 soak requirements. |
| Enabling condition | Deployments restart pods/processes during soak and production rollouts. |
| Why existing controls failed | No restart/recovery integration test asserts freeze + loop state after SIGTERM. |
| Current runtime impact | G3 recovery metrics may show reconnect behavior but not execution authority continuity. |
| Future construction impact | DEC-D persisted safety state requirement unmet. |
| Data impact | None persisted for runtime task graph |
| Security impact | Medium — freeze may reload but auto-exec state may not |
| Acquisition impact | Operability / DR questions |
| Feature Registry blocking | No |
| Capability Mapping blocking | No |
| Implementation blocking | Yes — execution persistence |
| Confidence | HIGH |
| Linked registers | D |
| Linked sub-findings | — |
| Required decision type | Architecture (state persistence) |

### PC-015 — Parallel feature taxonomies coexist without authority marker

| Field | Value |
|-------|-------|
| Original severity | HIGH |
| Current validated severity | HIGH |
| Category | Feature Taxonomy |
| Exact files | `bd_platform/registry.py`, `auth_service.py`, `plan_audit.py` |
| Exact symbols | `FEATURE_MATRIX`, `TIER_FEATURES`, plan audit feature list |
| Evidence | Three live views: (1) grid ids 1–40 in `bd_platform/registry.py`; (2) tier feature flags in `auth_service.py` L21–61; (3) institutional plan strings in `plan_audit.py` L55. `FEATURE_REALITY_MATRIX.md` **HISTORICAL_REFERENCE_NOT_PRESENT**. |
| Immediate defect | DD and internal audits can cite different feature counts/names for the same capability. |
| Systemic root cause | Roadmap grid, subscription tiers, and plan audit script evolved independently; DEC-A single enumeration was specified in remediation docs but not reflected in code or surviving markdown authority files. |
| Enabling condition | API consumers can call `/api/platform/features` (grid) and tier-gated routes (auth list) in same session. |
| Why existing controls failed | No SSOT pointer document exists (`docs/institutional/` absent — PC-023). |
| Current runtime impact | Product/marketing/ engineering feature lists diverge. |
| Future construction impact | Feature Registry and CAP crosswalk blocked (DEC-A/B). |
| Data impact | None |
| Security impact | Tier gates may not match grid “live” modules |
| Acquisition impact | Feature inventory unreliable |
| Feature Registry blocking | Yes |
| Capability Mapping blocking | Yes |
| Implementation blocking | Yes |
| Confidence | HIGH |
| Linked registers | A, K |
| Linked sub-findings | PC-015.a, PC-015.b |
| Required decision type | Owner attestation + taxonomy |

### PC-016 — Health probe contract assumes sidecar boot path

| Field | Value |
|-------|-------|
| Original severity | MEDIUM |
| Current validated severity | MEDIUM |
| Category | Deploy |
| Exact files | `Dockerfile`, `health_sidecar.py`, `run_service.py`, `launch_verify.bat` |
| Exact symbols | `HEALTHCHECK`, `start_health_sidecar`, `HEALTH_PORT` |
| Evidence | `Dockerfile` L35–36 probes `8180/health/live`. `health_sidecar.py` L4–5 documents sidecar on `port+100`. `run_service.py` L47–49 starts sidecar. `launch_verify.bat` validates `:8080` via `launch_verify.py` — does not confirm sidecar. Direct `uvicorn dashboard:app` would not start sidecar but Docker HEALTHCHECK would still probe 8180. |
| Immediate defect | Container health and operator launch scripts validate different endpoints; non-`run_service.py` starts produce false unhealthy containers. |
| Systemic root cause | Sidecar pattern was added for fast probes without making `run_service.py` the sole supported container entry and documenting the port+100 contract in all operator paths. |
| Enabling condition | Mixed boot documentation (compose comment L5 mentions 8180; launch scripts mention 8080 only). |
| Why existing controls failed | Docker build smoke in CI builds image but does not assert HEALTHCHECK success against running container. |
| Current runtime impact | Misleading unhealthy status if sidecar fails to bind. |
| Future construction impact | K8s/Railway deploy templates must encode sidecar contract explicitly. |
| Data impact | None |
| Security impact | Low — availability signal only |
| Acquisition impact | Operability DD minor gap |
| Feature Registry blocking | No |
| Capability Mapping blocking | No |
| Implementation blocking | No — deploy hygiene |
| Confidence | HIGH |
| Linked registers | H |
| Linked sub-findings | — |
| Required decision type | Operations documentation |

### PC-017 — Optional infra services diverge between compose and code paths

| Field | Value |
|-------|-------|
| Original severity | MEDIUM |
| Current validated severity | MEDIUM |
| Category | Infrastructure |
| Exact files | `docker-compose.yml`, `bd_platform/kafka_bridge.py`, `production_guard.py` |
| Exact symbols | `kafka`, `redis`, `vault` services; Kafka bridge module |
| Evidence | `docker-compose.yml` defines `redis`, `postgres`, `kafka`, `vault` services. `production_guard.py` checks postgres/redis/sentry/telegram — not kafka/vault uniformly. Kafka usage guarded by optional imports in platform modules. |
| Immediate defect | Staging compose topology can include Kafka/Vault while `web`-only Railway deploy may omit them — feature code paths differ silently. |
| Systemic root cause | Infra was added as compose extras for scale-out narrative; application code treats them as optional without a declared “minimal vs full” infra profile contract. |
| Enabling condition | Developers run compose with all services; production trial uses slim Dockerfile without compose. |
| Why existing controls failed | No contract test asserts feature degradation when kafka/redis absent. |
| Current runtime impact | Platform features depending on bus/vault may no-op without loud failure. |
| Future construction impact | P01–P16 infra assumptions unclear for Wave 2. |
| Data impact | Event bus paths |
| Security impact | Vault optional — secrets paths differ |
| Acquisition impact | Infrastructure DD inconsistency |
| Feature Registry blocking | No |
| Capability Mapping blocking | No |
| Implementation blocking | Partial — infra-dependent features |
| Confidence | MEDIUM |
| Linked registers | H |
| Linked sub-findings | — |
| Required decision type | Infra profile declaration |

### PC-018 — Completed-gaps doc points at missing institutional tree

| Field | Value |
|-------|-------|
| Original severity | MEDIUM |
| Current validated severity | MEDIUM |
| Category | Documentation |
| Exact files | `docs/GAPS_COMPLETED.md`; docs/institutional/ (HISTORICAL_REFERENCE_NOT_PRESENT) |
| Exact symbols | markdown links to institutional paths |
| Evidence | `docs/GAPS_COMPLETED.md` references institutional completion paths. `docs/institutional/` directory **HISTORICAL_REFERENCE_NOT_PRESENT** in current tree. |
| Immediate defect | Navigation from “gaps completed” to authoritative program docs fails on clone. |
| Systemic root cause | Institutional doc scaffold was planned and referenced in gap-closure notes before the directory was committed to this branch. |
| Enabling condition | DD readers follow GAPS_COMPLETED as entry point. |
| Why existing controls failed | No link checker CI on docs; ssot-doc-lint not implemented (PC-042). |
| Current runtime impact | None runtime — governance navigation broken |
| Future construction impact | R0 institutional sequencing blocked |
| Data impact | None |
| Security impact | None |
| Acquisition impact | Program maturity narrative contradicts repo |
| Feature Registry blocking | Yes — indirect |
| Capability Mapping blocking | No |
| Implementation blocking | Yes — R0 docs |
| Confidence | HIGH |
| Linked registers | K |
| Linked sub-findings | — |
| Required decision type | Documentation scaffold |

### PC-019 — ML flywheel guards do not cover all training-serving paths

| Field | Value |
|-------|-------|
| Original severity | MEDIUM |
| Current validated severity | MEDIUM |
| Category | ML Safety |
| Exact files | `flywheel_saturation_guard.py`, `startup_orchestrator.py`, `ml/` |
| Exact symbols | `_enabled`, ML flywheel startup block |
| Evidence | `flywheel_saturation_guard.py` L28–29 gates crowd saturation for alerts/execution slots. Orchestrator starts ML flywheel when env enables. `data/models/` may exist locally; no repo-wide anti-leakage gate on training artifact paths in CI. |
| Immediate defect | Saturation guard protects alert broadcast economics but not training-data leakage into live-serving paths. |
| Systemic root cause | ML safety investment focused on flywheel crowd economics (product differentiator) rather than a unified training/serving separation policy for all model directories. |
| Enabling condition | Flywheel scheduler runs in full orchestrator profile. |
| Why existing controls failed | `tests/test_ml_integrity.py` exists but does not scan all model paths for serving isolation. |
| Current runtime impact | Model files in workspace could influence serving if wired incorrectly. |
| Future construction impact | P08 institutional ML governance incomplete. |
| Data impact | Model artifacts |
| Security impact | Medium — data leakage class |
| Acquisition impact | ML governance DD gap |
| Feature Registry blocking | No |
| Capability Mapping blocking | Yes — P08 |
| Implementation blocking | Partial |
| Confidence | MEDIUM |
| Linked registers | I |
| Linked sub-findings | PC-019.a |
| Required decision type | ML governance policy |

### PC-020 — Dashboard module concentrates application composition

| Field | Value |
|-------|-------|
| Original severity | LOW |
| Current validated severity | LOW |
| Category | Maintainability |
| Exact files | `dashboard.py` |
| Exact symbols | `lifespan`, route registrations, `FastAPI` app |
| Evidence | `dashboard.py` ~2398 lines: mounts routers, defines lifespan branching, hosts UI routes, research endpoints, demo feed, GraphQL, etc. |
| Immediate defect | Single file change blast radius for unrelated features. |
| Systemic root cause | FastAPI monolith pattern chosen for velocity; platform split (DEC-E) not yet reflected in physical module boundaries at the app root. |
| Enabling condition | Most new features add routes or lifespan hooks to `dashboard.py`. |
| Why existing controls failed | No architecture test limiting dashboard line count or route ownership. |
| Current runtime impact | Merge conflicts and review burden — not a runtime failure. |
| Future construction impact | Slows Wave 2 parallel platform work. |
| Data impact | None |
| Security impact | Low — auth must be applied per-route manually |
| Acquisition impact | Maintainability note for DD |
| Feature Registry blocking | No |
| Capability Mapping blocking | No |
| Implementation blocking | No |
| Confidence | HIGH |
| Linked registers | B |
| Linked sub-findings | — |
| Required decision type | Refactor scheduling (non-blocking) |

### PC-021 — CI and container resolve different dependency manifests

| Field | Value |
|-------|-------|
| Original severity | HIGH |
| Current validated severity | HIGH |
| Category | Deploy / Reproducibility |
| Exact files | `requirements.txt`, `requirements-prod.txt`, `Dockerfile`, `.github/workflows/ci.yml` |
| Exact symbols | pip install lines; COPY requirements-prod |
| Evidence | `requirements.txt` includes pandas, pyarrow, ccxt, scikit-learn, pytest*. `requirements-prod.txt` omits those, adds kafka-python/hvac. `Dockerfile` L18–19 copies prod→requirements.txt. `ci.yml` L21 installs dev requirements.txt. |
| Immediate defect | Code tested in CI may import packages absent from production image (and vice versa). |
| Systemic root cause | Production slimming was done via a second manifest without a reconciliation gate tying CI, Docker, and local dev to one resolved graph with profile overlays. |
| Enabling condition | Developers assume green CI implies deployable image. |
| Why existing controls failed | No `manifest-reconcile` diff job; Docker build smoke does not import-test critical modules inside image. |
| Current runtime impact | Production ImportError risk for ML/ccxt paths if invoked. |
| Future construction impact | Blocks reproducible deploy claims (extends PC-001). |
| Data impact | Indirect |
| Security impact | Different CVE surface prod vs CI |
| Acquisition impact | Reproducibility DD failure |
| Feature Registry blocking | No |
| Capability Mapping blocking | No |
| Implementation blocking | Yes — deploy gate |
| Confidence | HIGH |
| Linked registers | H |
| Linked sub-findings | PC-021.a |
| Required decision type | Build authority |

### PC-022 — Test architecture lacks institutional breadth (E2E, concurrency, DR)

| Field | Value |
|-------|-------|
| Original severity | HIGH |
| Current validated severity | HIGH |
| Category | Test Architecture |
| Exact files | `.github/workflows/ci.yml`, `tests/`, `bd_platform/sse_stream.py` |
| Exact symbols | CI jobs; absence of SSE E2E, concurrency suite, restore drill |
| Evidence | CI subset (PC-002). No `tests/e2e/` SSE tests in repo. No `tests/concurrency/` for execution races. No backup/restore drill test artifact. |
| Immediate defect | Institutional quality claims (SSE UI, concurrent execution, DR) are not continuously evidenced. |
| Systemic root cause | Test investment tracked fee-matrix and security subsets aligned with immediate roadmap; institutional test classes were listed in remediation program but not implemented in repo. |
| Enabling condition | Manual testing deferred for SSE and soak recovery scenarios. |
| Why existing controls failed | G3 script exists but finalize not complete; tests not wired to CI. |
| Current runtime impact | Undetected regressions in streaming UI and race conditions. |
| Future construction impact | G1/G7 gates incomplete. |
| Data impact | None |
| Security impact | Concurrency/race class |
| Acquisition impact | Test maturity DD gap |
| Feature Registry blocking | Yes — Feature 002 SSE |
| Capability Mapping blocking | No |
| Implementation blocking | Yes |
| Confidence | HIGH |
| Linked registers | F |
| Linked sub-findings | PC-022.a–PC-022.e |
| Required decision type | QA architecture |

### PC-023 — No institutional SSOT pointer or scaffold in repository

| Field | Value |
|-------|-------|
| Original severity | HIGH |
| Current validated severity | HIGH |
| Category | SSOT / Navigation |
| Exact files | `docs/`; docs/institutional/ (HISTORICAL_REFERENCE_NOT_PRESENT); CURRENT_PROGRAM_STATUS_POINTER.md (HISTORICAL_REFERENCE_NOT_PRESENT) |
| Exact symbols | `CURRENT_PROGRAM_STATUS_POINTER.md` (absent) |
| Evidence | `docs/institutional/` **HISTORICAL_REFERENCE_NOT_PRESENT**. No `CURRENT_PROGRAM_STATUS_POINTER.md` at repo root or under docs. Remediation artifacts reference expected SSOT layout. |
| Immediate defect | Authority documents cannot be discovered or validated from a single pointer. |
| Systemic root cause | Institutional governance pack was specified in remediation design before being committed; engineering branch focused on G2/G3 runtime harnesses. |
| Enabling condition | Multiple docs (`GAPS_COMPLETED`, remediation v3) imply institutional tree exists. |
| Why existing controls failed | ssot-doc-lint specified but not implemented. |
| Current runtime impact | Governance only |
| Future construction impact | Blocks R0 and DEC-A attestation file placement |
| Data impact | None |
| Security impact | None |
| Acquisition impact | Program governance immature |
| Feature Registry blocking | Yes |
| Capability Mapping blocking | Yes |
| Implementation blocking | Yes — R0 |
| Confidence | HIGH |
| Linked registers | K |
| Linked sub-findings | — |
| Required decision type | Governance scaffold |

### PC-024 — Audit and compliance signals emitted from multiple modules

| Field | Value |
|-------|-------|
| Original severity | HIGH |
| Current validated severity | HIGH |
| Category | Audit Authority |
| Exact files | `oracle_integrity.py`, `database.py`, `weekly_report.py`, `regulatory_compliance_guard.py` |
| Exact symbols | `fetch_oracle_audit_stats`, `filter_live_predictions`, `apply_regulatory_compliance` |
| Evidence | Oracle audit stats queried in `weekly_report.py` L34–35, `gtm_service.py`, `market_intel.py`. Integrity filters in `oracle_integrity.py`. Compliance verdict transformation in `regulatory_compliance_guard.py` at route layer. No single `audit_authority` module. |
| Immediate defect | Compliance and audit consumers can receive differently filtered views depending on import path. |
| Systemic root cause | Audit reporting grew as feature-specific SQL helpers; regulatory guard added later at API boundary — no consolidation milestone completed. |
| Enabling condition | DD scripts pull audit from database helpers directly. |
| Why existing controls failed | No invariant test that all audit exports pass one authority filter. |
| Current runtime impact | DD reports may include synthetic predictions if caller forgets `include_synthetic=False`. |
| Future construction impact | MIG-07 unified audit path prerequisite unclear in code. |
| Data impact | Audit tables |
| Security impact | Compliance narrative risk |
| Acquisition impact | Audit trail DD questions |
| Feature Registry blocking | No |
| Capability Mapping blocking | Yes — P16 |
| Implementation blocking | Yes |
| Confidence | HIGH |
| Linked registers | L |
| Linked sub-findings | — |
| Required decision type | Audit architecture |

### PC-025 — Startup configuration validation is not fail-closed

| Field | Value |
|-------|-------|
| Original severity | HIGH |
| Current validated severity | HIGH |
| Category | Configuration |
| Exact files | `config.py`, `startup_orchestrator.py`, `production_guard.py` |
| Exact symbols | env reads throughout startup; `evaluate_production_guard` |
| Evidence | Orchestrator continues on exceptions (L48–49, L61–62 pattern: log and skip). `production_guard.py` evaluates but does not block HTTP bind on failure — logs only via `log_production_guard`. Many env vars read with permissive defaults across modules. |
| Immediate defect | Misconfiguration can reach live HTTP and background tasks without hard stop. |
| Systemic root cause | Resilience pattern “bind HTTP fast, best-effort background” prioritized availability over configuration validation gates. |
| Enabling condition | Missing keys/env often caught only when specific code path executes. |
| Why existing controls failed | `tests/test_production_guard.py` may assert evaluation shape, not abort behavior on invalid prod profile. |
| Current runtime impact | Partial service graphs run with silent skips. |
| Future construction impact | R3/R4 config-startup integration gate cannot be tested. |
| Data impact | Partial ingestion |
| Security impact | Medium — unsafe partial configs |
| Acquisition impact | Operability concern |
| Feature Registry blocking | No |
| Capability Mapping blocking | No |
| Implementation blocking | Yes |
| Confidence | HIGH |
| Linked registers | H, D |
| Linked sub-findings | — |
| Required decision type | Startup policy |

### PC-026 — REST and hub fallback paths lack execution-grade freshness contract

| Field | Value |
|-------|-------|
| Original severity | MEDIUM |
| Current validated severity | MEDIUM |
| Category | Price Architecture |
| Exact files | `market_context.py`, `fast_scan_engine.py`, `live_book_hub.py` |
| Exact symbols | `probe_price_sources`, `get_best_price`, `require_fresh` |
| Evidence | `market_context.py` implements multi-source REST probes. `fast_scan_engine.py` L21–24 calls `get_best_price` without requiring fresh flag semantics consistently. Hub stores last update per venue in memory only. |
| Immediate defect | Scan engines can use stale hub rows when WS lagging; REST fallback has no execution-authority gate. |
| Systemic root cause | Price ingestion prioritized availability (REST fill-in) over a strict freshness contract tied to execution authorization (DEC-C). |
| Enabling condition | WS outage triggers REST/oracle paths still consumed by scans. |
| Why existing controls failed | G2 tests venue mids; does not fail closed on stale age for scan authorization. |
| Current runtime impact | False arbitrage signals during feed lag. |
| Future construction impact | Must be resolved with PC-004 canonical price work. |
| Data impact | Scan inputs |
| Security impact | Indirect execution risk if tied to auto-exec |
| Acquisition impact | Data quality DD |
| Feature Registry blocking | No |
| Capability Mapping blocking | Yes — price CAPs |
| Implementation blocking | Partial |
| Confidence | HIGH |
| Linked registers | C |
| Linked sub-findings | — |
| Required decision type | Architecture (DEC-C) |

### PC-027 — Database access monolith impedes bounded migrations

| Field | Value |
|-------|-------|
| Original severity | MEDIUM |
| Current validated severity | MEDIUM |
| Category | Database |
| Exact files | `database.py` |
| Exact symbols | module-level CRUD functions (~3700+ lines) |
| Evidence | Single `database.py` hosts schema DDL, oracle tables, user keys, forecasts, risk — all CRUD in one module importers pull from everywhere. |
| Immediate defect | Financial migration (REAL→decimal) and repository split require editing a high-churn monolith with no domain seams in code. |
| Systemic root cause | SQLite-first rapid development kept all persistence in one file; postgres/backend duality added branches without physical split. |
| Enabling condition | Any migration touches shared file affecting unrelated domains. |
| Why existing controls failed | `tests/test_postgres_backend.py` tests backend switch, not module boundary size. |
| Current runtime impact | None immediate — maintenance hazard |
| Future construction impact | MIG-05 blocked until MIG-03 rollback boundary proven (dependency on PC-006). |
| Data impact | All persisted domains |
| Security impact | Low |
| Acquisition impact | Engineering scalability note |
| Feature Registry blocking | No |
| Capability Mapping blocking | No |
| Implementation blocking | Yes — migration sequencing |
| Confidence | HIGH |
| Linked registers | J |
| Linked sub-findings | — |
| Required decision type | Migration sequencing |

### PC-028 — Oracle consumers import without prohibited-import governance

| Field | Value |
|-------|-------|
| Original severity | MEDIUM |
| Current validated severity | MEDIUM |
| Category | Oracle Migration |
| Exact files | `market_context.py`, `voice_service.py`, `research_lab.py`, `api/routers/oracle.py` |
| Exact symbols | various oracle/research imports |
| Evidence | Multiple modules call oracle stats/research functions directly. Planned `cap047_oracle.py` facade **HISTORICAL_REFERENCE_NOT_PRESENT**. No `scripts/lint_prohibited_imports.py` in repo. |
| Immediate defect | New oracle callers can be added without architectural review. |
| Systemic root cause | Oracle access patterns established before facade migration plan; lint tooling was specified in remediation docs but not committed. |
| Enabling condition | Feature work adds imports to `database.fetch_oracle_*` helpers ad hoc. |
| Why existing controls failed | No CI import boundary test. |
| Current runtime impact | Provenance filtering inconsistent per caller. |
| Future construction impact | MIG-06 exit criteria (zero legacy callers) cannot be measured. |
| Data impact | Oracle tables |
| Security impact | Low |
| Acquisition impact | Architecture governance |
| Feature Registry blocking | No |
| Capability Mapping blocking | Yes |
| Implementation blocking | Yes — oracle migration |
| Confidence | MEDIUM |
| Linked registers | I |
| Linked sub-findings | — |
| Required decision type | Import governance |

### PC-029 — G3/G2 evidence JSON lacks validated schema enforcement

| Field | Value |
|-------|-------|
| Original severity | MEDIUM |
| Current validated severity | MEDIUM |
| Category | Evidence Schema |
| Exact files | `scripts/g3_reliability_soak_test.py`, `data/g2_validation_logs/` |
| Exact symbols | assessment output structure; JSON log files |
| Evidence | G3 script writes assessment JSON with performance/integrity/recovery sections — no checked-in JSON schema or CI validator. G2 logs in `data/g2_validation_logs/` lack `schema_version` field (PC-040). `scripts/validate_evidence.py` **HISTORICAL_REFERENCE_NOT_PRESENT**. |
| Immediate defect | Evidence artifacts cannot be machine-validated on commit. |
| Systemic root cause | Harnesses built for engineering feedback loops before institutional evidence schema was codified. |
| Enabling condition | CI does not run evidence validation on PR. |
| Why existing controls failed | DD smoke scripts don't validate JSON schema. |
| Current runtime impact | Manual review only for gate PASS. |
| Future construction impact | G3 automation blocked (PC-011). |
| Data impact | Evidence artifacts |
| Security impact | Low |
| Acquisition impact | Evidence reproducibility |
| Feature Registry blocking | Yes — G3 |
| Capability Mapping blocking | No |
| Implementation blocking | Yes |
| Confidence | HIGH |
| Linked registers | G |
| Linked sub-findings | PC-011.b |
| Required decision type | Evidence schema |

### PC-030 — Production guard does not gate router mounting

| Field | Value |
|-------|-------|
| Original severity | MEDIUM |
| Current validated severity | MEDIUM |
| Category | Production Guard |
| Exact files | `production_guard.py`, `dashboard.py`, `platform_api.py` |
| Exact symbols | `evaluate_production_guard`, route includes |
| Evidence | Guard evaluates infra preconditions (postgres, redis, billing, sentry) but dashboard mounts platform and demo routes unconditionally at import time. |
| Immediate defect | Production profile can expose routes/features not validated by guard semantics. |
| Systemic root cause | Production guard written as observability checklist, not as hard router registry filter for prod vs dev profiles. |
| Enabling condition | `ENV=production` not uniformly enforcing route deny lists at startup. |
| Why existing controls failed | `tests/test_production_guard.py` does not assert demo/dev routes absent in prod profile. |
| Current runtime impact | Demo feed remains reachable (PC-013.c). |
| Future construction impact | P11 production isolation incomplete. |
| Data impact | None |
| Security impact | Medium |
| Acquisition impact | Production security DD |
| Feature Registry blocking | No |
| Capability Mapping blocking | Yes — P11 |
| Implementation blocking | Partial |
| Confidence | HIGH |
| Linked registers | E |
| Linked sub-findings | PC-013.c, PC-013.e |
| Required decision type | Production profile policy |

### PC-031 — Microservice extraction signals conflict with modular monolith decision

| Field | Value |
|-------|-------|
| Original severity | MEDIUM |
| Current validated severity | MEDIUM |
| Category | Microservices |
| Exact files | `microservices/`, `docker-compose.yml`, `docs/MICROSERVICES_ARCHITECTURE.md` |
| Exact symbols | `worker_app.py`, `lifecycle.startup`, compose scale directives |
| Evidence | Compose supports `--scale arbitrage=2 --scale web=2`. `microservices/worker_app.py` exposes separate uvicorn apps per mode. DEC-E in remediation specifies P01–P16 modular monolith — physical split exists for workers. |
| Immediate defect | DD readers see microservice topology while architectural decision says monolith platforms. |
| Systemic root cause | Infrastructure narrative (HaasCloud-style scale-out) advanced in docs/compose before DEC-E binding was recorded; code supports both monolith and worker modes concurrently. |
| Enabling condition | Buyers evaluate `MICROSERVICES_ARCHITECTURE.md` alongside remediation DEC-E. |
| Why existing controls failed | No architecture test forbids P17-style premature extraction. |
| Current runtime impact | Operational complexity — dual modes |
| Future construction impact | Platform boundary testing ambiguous. |
| Data impact | None |
| Security impact | Low |
| Acquisition impact | Architecture story conflict |
| Feature Registry blocking | No |
| Capability Mapping blocking | Yes |
| Implementation blocking | Partial |
| Confidence | MEDIUM |
| Linked registers | B |
| Linked sub-findings | — |
| Required decision type | Architecture (DEC-E clarification) |

### PC-032 — Wave 2 master navigation index absent

| Field | Value |
|-------|-------|
| Original severity | LOW |
| Current validated severity | LOW |
| Category | Documentation |
| Exact files | WAVE2_MASTER_REFERENCE_INDEX.md (HISTORICAL_REFERENCE_NOT_PRESENT) |
| Exact symbols | (file absent) |
| Evidence | `WAVE2_MASTER_REFERENCE_INDEX.md` **HISTORICAL_REFERENCE_NOT_PRESENT**. Referenced in remediation DEC/R0-S10 design only. |
| Immediate defect | Wave 2 reference material has no mandated navigation index in repo. |
| Systemic root cause | Index planned as R0 deliverable before commit to branch. |
| Enabling condition | Engineers rely on scattered docs under `docs/`. |
| Why existing controls failed | Not applicable — doc not created. |
| Current runtime impact | None |
| Future construction impact | R0-S10 deliverable missing |
| Data impact | None |
| Security impact | None |
| Acquisition impact | Minor governance |
| Feature Registry blocking | No |
| Capability Mapping blocking | No |
| Implementation blocking | No |
| Confidence | HIGH |
| Linked registers | K |
| Linked sub-findings | — |
| Required decision type | Documentation |

### PC-033 — Security CI job is not coupled to full test gate

| Field | Value |
|-------|-------|
| Original severity | LOW |
| Current validated severity | LOW |
| Category | CI Security |
| Exact files | `.github/workflows/security.yml`, `.github/workflows/ci.yml` |
| Exact symbols | separate workflow jobs |
| Evidence | Security workflow runs pip-audit + subset pytest independently of main CI test job (PC-002). No `needs: full-suite` dependency. |
| Immediate defect | Security workflow can pass while main functional regressions exist (and vice versa). |
| Systemic root cause | Security workflow added as parallel concern without pipeline orchestration tying it to full test success. |
| Enabling condition | GitHub Actions treats workflows independently. |
| Why existing controls failed | No meta-test for workflow ordering. |
| Current runtime impact | False confidence in combined green status across workflows. |
| Future construction impact | Institutional CI story incomplete. |
| Data impact | None |
| Security impact | Process — not direct vuln |
| Acquisition impact | CI maturity note |
| Feature Registry blocking | No |
| Capability Mapping blocking | No |
| Implementation blocking | Partial |
| Confidence | HIGH |
| Linked registers | F |
| Linked sub-findings | PC-034.a |
| Required decision type | CI orchestration |

### PC-034 — Security verification subset can pass in isolation

| Field | Value |
|-------|-------|
| Original severity | MEDIUM |
| Current validated severity | MEDIUM |
| Category | Evidence |
| Exact files | `tests/test_security.py`, `.github/workflows/ci.yml`, `.github/workflows/security.yml` |
| Exact symbols | pytest selections |
| Evidence | Security tests not gated on full collection count; main CI runs different subset (profit/fee). `security_verification.py` **HISTORICAL_REFERENCE_NOT_PRESENT** — security coverage measured via pytest files only. |
| Immediate defect | “15/15 security tests pass” class claims decoupled from full regression health. |
| Systemic root cause | Security maturity marketed via focused test file before full-suite CI existed. |
| Enabling condition | Stakeholders read security workflow green as global quality signal. |
| Why existing controls failed | See PC-002, PC-033. |
| Current runtime impact | Reporting ambiguity |
| Future construction impact | G1/G7 evidence coupling |
| Data impact | None |
| Security impact | Process |
| Acquisition impact | DD evidence interpretation |
| Feature Registry blocking | No |
| Capability Mapping blocking | No |
| Implementation blocking | Partial |
| Confidence | HIGH |
| Linked registers | F, L |
| Linked sub-findings | PC-034.a |
| Required decision type | CI policy |

### PC-035 — Infra metrics coverage is partial across platforms

| Field | Value |
|-------|-------|
| Original severity | LOW |
| Current validated severity | LOW |
| Category | Observability |
| Exact files | `infra_metrics.py`, `bd_platform/infra_status.py` |
| Exact symbols | service_mode reporting; platform infra endpoints |
| Evidence | `infra_metrics.py` L18 reads `SERVICE_MODE` env. Not all platform modules emit unified metrics hooks for G3 soak sections. |
| Immediate defect | G3 soak may lack platform-level metric completeness for institutional trends. |
| Systemic root cause | Metrics added for core infra narrative; per-platform instrumentation not uniform. |
| Enabling condition | G3 assessor expects performance trends — some subsystems silent. |
| Why existing controls failed | G3 not finalized; metrics gaps not yet blocking. |
| Current runtime impact | Incomplete soak dashboards |
| Future construction impact | G3 performance section fidelity |
| Data impact | Metrics |
| Security impact | None |
| Acquisition impact | Observability minor gap |
| Feature Registry blocking | No |
| Capability Mapping blocking | No |
| Implementation blocking | Partial — G3 |
| Confidence | MEDIUM |
| Linked registers | G |
| Linked sub-findings | — |
| Required decision type | Observability scope |

### PC-036 — Audit-style feature matrix markdown absent from repository

| Field | Value |
|-------|-------|
| Original severity | INFORMATIONAL |
| Current validated severity | INFORMATIONAL |
| Category | Documentation |
| Exact files | FEATURE_REALITY_MATRIX.md (HISTORICAL_REFERENCE_NOT_PRESENT) |
| Exact symbols | (absent) |
| Evidence | File **HISTORICAL_REFERENCE_NOT_PRESENT**. Referenced only in remediation verification standard as a file class to lint — not in working tree. |
| Immediate defect | Third taxonomy referenced in governance design cannot be inspected or marked HISTORICAL_NON_CURRENT in repo. |
| Systemic root cause | Audit matrix existed in prior review cycle or planning docs but was never committed to this branch (or removed). |
| Enabling condition | Remediation docs assume matrix exists for ssot-doc-lint rules. |
| Why existing controls failed | N/A — artifact missing |
| Current runtime impact | None |
| Future construction impact | ssot-doc-lint rule set must handle absent file |
| Data impact | None |
| Security impact | None |
| Acquisition impact | Clarify to DD that matrix is not in repo |
| Feature Registry blocking | No |
| Capability Mapping blocking | No |
| Implementation blocking | No |
| Confidence | HIGH |
| Linked registers | A, K |
| Linked sub-findings | PC-015.a |
| Required decision type | Documentation status |

### PC-037 — Marketing docs may exceed attested feature scope

| Field | Value |
|-------|-------|
| Original severity | INFORMATIONAL |
| Current validated severity | INFORMATIONAL |
| Category | Marketing |
| Exact files | `docs/MKT_COMPETITIVE_MATRIX.md`, `docs/MKT_ICP.md`, `docs/MKT_MARKET_BARRIERS.md` |
| Exact symbols | marketing claims (qualitative) |
| Evidence | MKT docs describe market positioning and competitive claims. No linkage to attested Feature Registry (PC-003). |
| Immediate defect | External narrative not bound to FCP enumeration authority. |
| Systemic root cause | Marketing pack authored in parallel with engineering roadmap grid without formal crosswalk to attested features. |
| Enabling condition | DD bundle includes marketing + engineering docs together. |
| Why existing controls failed | No doc lint ties MKT claims to feature IDs. |
| Current runtime impact | None code |
| Future construction impact | External comms risk post-acquisition |
| Data impact | None |
| Security impact | None |
| Acquisition impact | Narrative reconciliation needed |
| Feature Registry blocking | No |
| Capability Mapping blocking | No |
| Implementation blocking | No |
| Confidence | MEDIUM |
| Linked registers | K |
| Linked sub-findings | — |
| Required decision type | Comms governance |

### PC-038 — Legal disclaimers not bound to feature registry entries

| Field | Value |
|-------|-------|
| Original severity | INFORMATIONAL |
| Current validated severity | INFORMATIONAL |
| Category | Legal |
| Exact files | `legal_content.py`, `regulatory_compliance_guard.py` |
| Exact symbols | `REGULATORY_DISCLAIMER`, compliance verdict constants |
| Evidence | `regulatory_compliance_guard.py` L18–22 static disclaimer. `legal_content.py` holds UI legal strings. No feature-id linkage. |
| Immediate defect | Legal/compliance text can drift from feature capability claims independently. |
| Systemic root cause | Compliance guard implemented as text transformation layer decoupled from feature registry metadata. |
| Enabling condition | New features ship without updating legal mapping table. |
| Why existing controls failed | No test links feature rollout to disclaimer coverage. |
| Current runtime impact | Compliance copy may not reference all live endpoints. |
| Future construction impact | Institutional compliance packaging |
| Data impact | None |
| Security impact | Regulatory narrative |
| Acquisition impact | Legal DD hygiene |
| Feature Registry blocking | No |
| Capability Mapping blocking | No |
| Implementation blocking | No |
| Confidence | MEDIUM |
| Linked registers | L |
| Linked sub-findings | — |
| Required decision type | Legal/compliance mapping |

### PC-039 — Full regression baseline file not in repository

| Field | Value |
|-------|-------|
| Original severity | INFORMATIONAL |
| Current validated severity | INFORMATIONAL |
| Category | Test Data |
| Exact files | data/wave1_full_regression.txt (HISTORICAL_REFERENCE_NOT_PRESENT) |
| Exact symbols | (absent) |
| Evidence | `data/wave1_full_regression.txt` **HISTORICAL_REFERENCE_NOT_PRESENT**. `data/` contains JSON artifacts (e.g. `operational_manifest.json`, `g2_validation_logs/`) only. |
| Immediate defect | Documented Wave 1 full regression count cannot be verified from committed baseline artifact. |
| Systemic root cause | Regression baseline maintained locally or in prior branch during Wave 1; not checked into this commit. |
| Enabling condition | DD materials cite numeric test counts without artifact pointer. |
| Why existing controls failed | CI does not store collection count artifact (PC-002). |
| Current runtime impact | None |
| Future construction impact | Blocks automated regression drift detection until baseline restored or regenerated. |
| Data impact | None |
| Security impact | None |
| Acquisition impact | Test count claims need re-baseline |
| Feature Registry blocking | No |
| Capability Mapping blocking | No |
| Implementation blocking | Partial — G1 |
| Confidence | HIGH |
| Linked registers | F |
| Linked sub-findings | PC-022.a |
| Required decision type | QA baseline |

### PC-040 — G2 validation logs lack schema version field

| Field | Value |
|-------|-------|
| Original severity | INFORMATIONAL |
| Current validated severity | INFORMATIONAL |
| Category | Test Data |
| Exact files | `data/g2_validation_logs/` |
| Exact symbols | JSON log structure |
| Evidence | G2 JSON logs present (4 runs). Fields include run metadata and test sections — no `schema_version` key observed in harness output design at this commit. |
| Immediate defect | Cross-run automated comparison can break silently when harness output shape changes. |
| Systemic root cause | G2 harness built for engineering pass/fail feedback before institutional evidence versioning policy. |
| Enabling condition | Multiple G2 runs stored for DD without version tag. |
| Why existing controls failed | No validator rejects unversioned logs. |
| Current runtime impact | Manual comparison only |
| Future construction impact | Evidence reproducibility gate (G2→G3 chain) |
| Data impact | Evidence JSON |
| Security impact | None |
| Acquisition impact | Minor evidence hygiene |
| Feature Registry blocking | No |
| Capability Mapping blocking | No |
| Implementation blocking | Partial |
| Confidence | HIGH |
| Linked registers | G |
| Linked sub-findings | — |
| Required decision type | Evidence schema |

### PC-041 — Float arithmetic persists on authoritative profit/fee paths

| Field | Value |
|-------|-------|
| Original severity | MEDIUM |
| Current validated severity | MEDIUM |
| Category | Float Migration |
| Exact files | `fee_matrix.py`, `fast_scan_engine.py`, `profit_fee_algorithms.py` |
| Exact symbols | `float()` casts, `dict[str, dict[str, float]]`, profit scan math |
| Evidence | `fee_matrix.py` L19–31 float-typed fee tables. `fast_scan_engine.py` L19–24 float prices/fees. Coexists with PC-006 REAL columns — double float path. |
| Immediate defect | Migrating DB to DECIMAL alone leaves Python float paths that reintroduce precision loss before persist. |
| Systemic root cause | Performance-sensitive scan code used native float for speed; decimal migration planning treated storage and compute as independent tracks. |
| Enabling condition | Fast scan runs on every orchestrator profile with fee matrix loaded. |
| Why existing controls failed | Profit/fee CI tests use tolerances suited to float, not exact decimal invariants. |
| Current runtime impact | Precision loss before DB write. |
| Future construction impact | MIG-03 rollback boundary must include compute paths (PC-006). |
| Data impact | PnL calculations |
| Security impact | Low |
| Acquisition impact | Financial engineering DD |
| Feature Registry blocking | No |
| Capability Mapping blocking | Yes — P03/P04 |
| Implementation blocking | Yes — with PC-006 |
| Confidence | HIGH |
| Linked registers | C, J |
| Linked sub-findings | PC-009.c |
| Required decision type | Financial compute policy |

### PC-042 — SSOT document lint contract specified but not implemented

| Field | Value |
|-------|-------|
| Original severity | MEDIUM |
| Current validated severity | MEDIUM |
| Category | Governance |
| Exact files | `docs/remediation/REMEDIATION_VERIFICATION_STANDARD.md`, `.github/workflows/ci.yml` |
| Exact symbols | ssot-doc-lint job (specified); `scripts/ssot_doc_lint.py` (absent) |
| Evidence | Verification standard defines ssot-doc-lint implementable contract. `scripts/ssot_doc_lint.py` and `tests/governance/test_ssot_doc_lint.py` **HISTORICAL_REFERENCE_NOT_PRESENT**. `ci.yml` has no ssot-doc-lint job. |
| Immediate defect | Duplicate SSOT authority markers cannot be blocked at merge time. |
| Systemic root cause | Governance tooling specified in meta-remediation before implementation landed on feature branch focused on G2/G3 runtime. |
| Enabling condition | Multiple docs reference institutional authority without automated enforcement. |
| Why existing controls failed | Tool not built. |
| Current runtime impact | Governance drift possible via doc edits. |
| Future construction impact | DEC-A/B enforcement blocked |
| Data impact | None |
| Security impact | Low |
| Acquisition impact | Governance maturity |
| Feature Registry blocking | Yes — indirect |
| Capability Mapping blocking | No |
| Implementation blocking | Yes — R0 |
| Confidence | HIGH |
| Linked registers | K |
| Linked sub-findings | PC-015.a |
| Required decision type | CI governance tooling |

---

## Sub-Findings (29 standalone diagnostic records)

### PC-008.a — Background auto-execution opt-in defaults disagree across modules

| Field | Value |
|-------|-------|
| Sub-finding ID | PC-008.a |
| Parent ID | PC-008 |
| Originating register | B — Platform boundary / startup coupling |
| Severity | HIGH |
| Current repository evidence | `startup_orchestrator.py` L247–250 gates `auto_exec_task` on `AUTO_EXECUTION_LOOP` default **false**. `execution_engine.py` L116 reports loop default **true**. `docker-compose.yml` arbitrage service sets `AUTO_EXECUTION_LOOP: "true"`. `hybrid_execution_router.py` **HISTORICAL_REFERENCE_NOT_PRESENT**. |
| Immediate defect | Operators cannot tell whether auto-execution starts from orchestrator without reading three env sources. |
| Systemic root cause | Auto-exec loop was wired separately in orchestrator vs engine status reporting; compose profile added a third override for worker topology. |
| Enabling condition | `SERVICE_MODE=all` or arbitrage compose service with keys loaded. |
| Failure of existing controls | `tests/test_execution_keys.py` validates key files, not orchestrator-vs-engine default parity. |
| Current impact | Unintended background order evaluation in some profiles. |
| Future impact | Wave 2 P03/P07 cannot certify opt-in semantics. |
| Distinct scope from parent | Parent covers whole orchestrator graph; this isolates **auto-exec default conflict** only. |
| Independent closure evidence required | Proof that one documented default applies across orchestrator, engine, and compose for each profile. |

### PC-008.b — Platform API router concentration (61 handlers)

| Field | Value |
|-------|-------|
| Sub-finding ID | PC-008.b |
| Parent ID | PC-008 |
| Originating register | B |
| Severity | HIGH |
| Current repository evidence | `platform_api.py`: 61 `@router` decorators; prefix `/api/platform` L11. Routes span keys, ML, derivatives, arb, onchain, bots, SSE, vault, etc. |
| Immediate defect | Route ownership cannot be attributed to a single P0x platform module for change control. |
| Systemic root cause | B2B API expansion appended endpoints to one router for shipping speed rather than per-platform routers registered from composition root. |
| Enabling condition | Any platform feature adds HTTP surface via editing shared file. |
| Failure of existing controls | Route inventory not automated; count not asserted in CI. |
| Current impact | High merge conflict and review risk on shared API file. |
| Future impact | P13 facade and prohibited-import migration blocked. |
| Distinct scope from parent | Parent addresses orchestrator coupling; this isolates **HTTP route sprawl** in `platform_api.py`. |
| Independent closure evidence required | Machine-readable route inventory mapped 1:1 to P01–P16 owners. |

### PC-008.c — Decision pipeline module absent; P06/P10 boundary unimplemented

| Field | Value |
|-------|-------|
| Sub-finding ID | PC-008.c |
| Parent ID | PC-008 |
| Originating register | B, I |
| Severity | HIGH |
| Current repository evidence | `decision_intelligence_pipeline.py` **HISTORICAL_REFERENCE_NOT_PRESENT**. Oracle scoring spread across `research_lab.py`, `database` oracle tables, `api/routers/oracle.py` without shared-kernel contract. |
| Immediate defect | Decision scoring and persistence lineage cannot be tested as one bounded module. |
| Systemic root cause | CAP-053-style pipeline specified in planning docs but never committed; features used ad hoc SQL + research report builders instead. |
| Enabling condition | DD references decision intelligence pipeline as architectural element. |
| Failure of existing controls | No contract test — module missing entirely. |
| Current impact | Provenance gaps between score generation and persistence paths. |
| Future impact | P06/P10 separation unenforceable until module exists or explicitly retired from scope. |
| Distinct scope from parent | Parent is orchestrator-wide; this is **missing shared decision kernel** specifically. |
| Independent closure evidence required | Either committed pipeline with boundary tests or formal scope retirement signed by architecture owner. |

### PC-008.d — Regulatory compliance applied at route layer in multiple places

| Field | Value |
|-------|-------|
| Sub-finding ID | PC-008.d |
| Parent ID | PC-008 |
| Originating register | L |
| Severity | HIGH |
| Current repository evidence | `regulatory_compliance_guard.py` provides `apply_regulatory_compliance`, `to_public_verdict`. Imported from `dashboard.py` and platform/oracle routes (multiple call sites). No single P16 facade entry enforced. |
| Immediate defect | Compliance transformation logic can diverge if one route bypasses guard helpers. |
| Systemic root cause | Guard added as importable functions for quick SEC/MiFID wording mitigation rather than mandatory middleware on all public verdict fields. |
| Enabling condition | New routes return oracle/signal text without calling guard. |
| Failure of existing controls | No architecture test enumerates all verdict emitters through one function. |
| Current impact | Inconsistent public wording on some endpoints. |
| Future impact | Regulatory packaging for acquisition incomplete. |
| Distinct scope from parent | Isolates **compliance entrypoint duplication** vs general orchestrator coupling. |
| Independent closure evidence required | Static proof all verdict paths call one compliance facade. |

### PC-009.a — Direct `bd_platform` imports from API layer

| Field | Value |
|-------|-------|
| Sub-finding ID | PC-009.a |
| Parent ID | PC-009 |
| Originating register | B |
| Severity | HIGH |
| Current repository evidence | `platform_api.py` imports numerous `bd_platform.*` modules at module level and inside handlers (pattern throughout file). |
| Immediate defect | API layer reaches into platform internals bypassing declared P13 facades. |
| Systemic root cause | Pre-registry integration style persisted after 40-point grid documented modules. |
| Enabling condition | New platform features follow same import pattern. |
| Failure of existing controls | No prohibited-import lint in CI. |
| Current impact | Refactors inside `bd_platform` break API layer unpredictably. |
| Future impact | Modular monolith boundaries (DEC-E) unmeasurable. |
| Distinct scope from parent | Parent covers overlap with grid; this isolates **import direction violation** API→bd_platform. |
| Independent closure evidence required | Zero prohibited imports from API layer to internal platform modules per published allow list. |

### PC-009.b — FEATURE_MATRIX treated as live feature enumeration

| Field | Value |
|-------|-------|
| Sub-finding ID | PC-009.b |
| Parent ID | PC-009 |
| Originating register | A |
| Severity | HIGH |
| Current repository evidence | `bd_platform/registry.py` L10–51 `FEATURE_MATRIX`; `feature_summary()` import-probes modules for `/api/platform/features` style responses. |
| Immediate defect | Import success equals “live feature” in API summaries. |
| Systemic root cause | Roadmap grid doubled as runtime status dashboard without attestation separation (DEC-A). |
| Enabling condition | DD reads grid ids as product feature ids F-xxx analogs. |
| Failure of existing controls | No test forbids registry from emitting feature authority. |
| Current impact | Overstated live feature counts. |
| Future impact | Feature Registry attestation blocked. |
| Distinct scope from parent | Isolates **grid enumeration semantics** vs general API sprawl. |
| Independent closure evidence required | Registry outputs labeled non-authoritative; no F-### ids from grid. |

### PC-009.c — Fee and profit scan paths compute in float

| Field | Value |
|-------|-------|
| Sub-finding ID | PC-009.c |
| Parent ID | PC-009 |
| Originating register | J, C |
| Severity | HIGH |
| Current repository evidence | `fee_matrix.py` float tables; `fast_scan_engine.py` L19–24 float conversion on bids/asks/fees; related to PC-041. |
| Immediate defect | Profit thresholds and fee comparisons subject to float error before any DB persist. |
| Systemic root cause | Scan loop optimized for native float math on hot path; decimal requirement not propagated to scan engines when financial gate raised. |
| Enabling condition | `run_fast_scan` invoked from orchestrator price stream path. |
| Failure of existing controls | Property tests for decimal invariants absent on scan output. |
| Current impact | Marginal opportunities may flip near threshold boundaries incorrectly. |
| Future impact | MIG-03 incomplete if only DB migrated. |
| Distinct scope from parent | Isolates **compute-path float** vs platform routing overlap. |
| Independent closure evidence required | Authoritative fee/profit path uses decimal end-to-end with property tests. |

### PC-009.d — Portfolio logic split between dashboard and rebalancer module

| Field | Value |
|-------|-------|
| Sub-finding ID | PC-009.d |
| Parent ID | PC-009 |
| Originating register | B, C |
| Severity | HIGH |
| Current repository evidence | `bd_platform/portfolio_rebalancer.py` exposes rebalance API; `dashboard.py` includes holdings/portfolio UI routes that may compute/display holdings separately (multiple portfolio touchpoints in dashboard). |
| Immediate defect | Two code paths can disagree on holdings/allocation numbers shown vs API rebalance actions. |
| Systemic root cause | UI-first portfolio views built before CAP-081 consolidation into single P05 read model. |
| Enabling condition | User compares dashboard holdings to `/api/platform/portfolio/rebalance` output. |
| Failure of existing controls | No contract test single portfolio authority. |
| Current impact | Data authority conflict in DD demos. |
| Future impact | CAP-081 merge risk for Wave 2 P05. |
| Distinct scope from parent | Isolates **portfolio dual authority** vs general platform_api grid overlap. |
| Independent closure evidence required | One read repository serves UI and API rebalance preview. |

### PC-010.a — CEX-DEX executor can reach live engine without unified risk gate

| Field | Value |
|-------|-------|
| Sub-finding ID | PC-010.a |
| Parent ID | PC-010 |
| Originating register | D |
| Severity | HIGH |
| Current repository evidence | `bd_platform/cex_dex_executor.py` L49–52 delegates to `execution_engine.execute_order`; env gates `CEX_DEX_EXECUTION_ENABLED` separate from master execution authority (PC-005). |
| Immediate defect | Connector path does not consult a unified `authorize_execution()` exposing freeze/exposure/idempotency. |
| Systemic root cause | CEX-DEX feature shipped as executor wrapper assuming engine env flags equal institutional execution gate. |
| Enabling condition | POST `/api/platform/arb/cex-dex/execute` with keys and flags set. |
| Failure of existing controls | Security negative tests for connector bypass not present. |
| Current impact | Live leg risk under split flags. |
| Future impact | DEC-D connector wrapper requirement. |
| Distinct scope from parent | Isolates **connector entrypoint** vs general P09/P04 overlap statement. |
| Independent closure evidence required | Direct connector invocation without auth service raises deterministic DENY. |

### PC-011.a — G3 assessor lacks mandatory fail on stale integrity hour

| Field | Value |
|-------|-------|
| Sub-finding ID | PC-011.a |
| Parent ID | PC-011 |
| Originating register | G |
| Severity | HIGH |
| Current repository evidence | `g3_reliability_soak_test.py` L450–457 integrity thresholds (stale >10%); `HOURLY_OPERATION_REPORTS/` not present until finalize — no committed stale-hour failure artifact. Historical assessment with stale h1 **HISTORICAL_REFERENCE_NOT_PRESENT** in repo. |
| Immediate defect | Assessor can theoretically PASS with degraded hourly integrity if weighting allows partial hours. |
| Systemic root cause | Integrity section built as trend warnings before hard hourly veto logic for institutional gate. |
| Enabling condition | Long soak with one bad hour near end of window. |
| Failure of existing controls | No unit test injecting stale hour forcing FAIL. |
| Current impact | Risk of optimistic G3 narrative if pilot run accepted early. |
| Future impact | Institutional 24h gate credibility. |
| Distinct scope from parent | Isolates **hour-level integrity veto** vs gate_scope taxonomy (PC-011.b). |
| Independent closure evidence required | Assessor output FAIL when any hour exceeds stale threshold with signed hourly artifact. |

### PC-011.b — Pilot duration and institutional duration share assessor without scope field

| Field | Value |
|-------|-------|
| Sub-finding ID | PC-011.b |
| Parent ID | PC-011 |
| Originating register | G |
| Severity | HIGH |
| Current repository evidence | `g3_reliability_soak_test.py` `--hours` min 1 L1052 vs default `hours_required=24`; output JSON has no `gate_scope` enum field at this commit. |
| Immediate defect | Consumers cannot distinguish smoke pilot JSON from institutional soak JSON programmatically. |
| Systemic root cause | Single assessor script served engineering smoke and institutional gate without schema versioning for scope. |
| Enabling condition | DD reviewer opens latest JSON without reading CLI invocation. |
| Failure of existing controls | No schema validator in CI (PC-029). |
| Current impact | Misclassification risk in acquisition data room. |
| Future impact | Automated feature closure blocked. |
| Distinct scope from parent | Isolates **gate_scope metadata** vs hourly integrity (PC-011.a). |
| Independent closure evidence required | Schema rejects institutional claims when `gate_scope != INSTITUTIONAL_24H`. |

### PC-012.a — Parallel oracle/research entrypoints (`research_lab` vs `oracle_retrainer`)

| Field | Value |
|-------|-------|
| Sub-finding ID | PC-012.a |
| Parent ID | PC-012 |
| Originating register | I |
| Severity | HIGH |
| Current repository evidence | `research_lab.py` `build_research_lab_report`; `oracle_retrainer.py` `run_oracle_retrain_step` invoked from `api/routers/oracle.py` L173 and orchestrator L183. Both touch oracle prediction domain. |
| Immediate defect | Two stacks can mutate/read oracle state without unified public entry API. |
| Systemic root cause | Research narrative feature and retrain ops feature developed on separate schedules without merge to single inference stack. |
| Enabling condition | Both paths run in full orchestrator profile. |
| Failure of existing controls | No test enforcing single callable inference entrypoint. |
| Current impact | DD cannot trace which path produced a prediction row. |
| Future impact | Oracle migration (MIG-06) caller inventory incomplete. |
| Distinct scope from parent | Isolates **dual stack** vs lineage field completeness (PC-012.b). |
| Independent closure evidence required | Architecture diagram matches single runtime entry with deprecation list empty. |

### PC-012.b — Decision lineage fields not proven end-to-end

| Field | Value |
|-------|-------|
| Sub-finding ID | PC-012.b |
| Parent ID | PC-012 |
| Originating register | I |
| Severity | HIGH |
| Current repository evidence | `oracle_integrity.py` filters synthetic sources; `cap047_oracle.py` **HISTORICAL_REFERENCE_NOT_PRESENT**. No E2E test artifact proving CAP-053 lineage on all decision paths. |
| Immediate defect | Provenance chain from signal → prediction → audit export has gaps per path. |
| Systemic root cause | Lineage requirements specified at CAP level before wiring completed in code paths that bypass oracle_integrity filters. |
| Enabling condition | GTM/weekly reports pull audit stats with different `include_synthetic` defaults. |
| Failure of existing controls | Partial audit chain tests do not cover all emitters. |
| Current impact | XAI/acquisition lineage questions unanswered. |
| Future impact | P06 institutional grade gate fails. |
| Distinct scope from parent | Isolates **lineage completeness** vs dual stack presence. |
| Independent closure evidence required | E2E test shows lineage fields populated for every decision class with IVV artifact. |

### PC-013.a — Exchange validation depends on gitignored `keys/` tree

| Field | Value |
|-------|-------|
| Sub-finding ID | PC-013.a |
| Parent ID | PC-013 |
| Originating register | E, H |
| Severity | HIGH |
| Current repository evidence | `.gitignore` L19–21; `execution_keys.py` and `startup_orchestrator.py` L43–47 load `keys/platform_keys.env`, `keys/exchange_keys.env`. Directory not in clone. |
| Immediate defect | CI and acquirer clones cannot reproduce live exchange validation without secret injection procedure. |
| Systemic root cause | Live-key validation prioritized over fixture/sandbox mode for automated reproducibility. |
| Enabling condition | Scripts `activate_live_execution.py`, G2 live WS tests need keys. |
| Failure of existing controls | No documented fixture mode in CI for key-dependent tests. |
| Current impact | Live proof non-reproducible from git alone. |
| Future impact | G2/G3 live sections blocked in sanitized CI. |
| Distinct scope from parent | Isolates **secret reproducibility** vs tenant scoping. |
| Independent closure evidence required | CI green on fixture keys with documented injection boundary for live-only jobs. |

### PC-013.b — Subscription tier scoping is not multi-tenant org isolation

| Field | Value |
|-------|-------|
| Sub-finding ID | PC-013.b |
| Parent ID | PC-013 |
| Originating register | E |
| Severity | HIGH |
| Current repository evidence | `auth_service.py` L133–183 sessions keyed by `user_id`; `TIER_FEATURES` gating only — no org/tenant column enforcement pattern across `database.py` repositories. |
| Immediate defect | Data access relies on caller passing correct `user_id` without mandatory tenant context middleware. |
| Systemic root cause | Product architecture single-tenant SaaS tiers; enterprise multi-tenant model not introduced at persistence boundary. |
| Enabling condition | Shared database instance serves multiple customers. |
| Failure of existing controls | No cross-tenant negative tests per engine. |
| Current impact | Theoretical cross-user data read if handler omits user filter. |
| Future impact | Enterprise tenancy blocker. |
| Distinct scope from parent | Isolates **user_id vs tenant_id** model gap. |
| Independent closure evidence required | Cross-tenant access attempts fail on all CRUD paths with signed negative test suite. |

### PC-013.c — Public demo feed reachable without production hard deny

| Field | Value |
|-------|-------|
| Sub-finding ID | PC-013.c |
| Parent ID | PC-013 |
| Originating register | E |
| Severity | HIGH |
| Current repository evidence | `dashboard.py` L1401–1416 `GET /api/b2b/demo`; `config.py` default `B2B_DEMO_API_KEY`. `api/routers/demo.py` **HISTORICAL_REFERENCE_NOT_PRESENT** — demo is on dashboard, not separate router file. |
| Immediate defect | Demo B2B surface not proven 404/403 in production profile by startup audit. |
| Systemic root cause | Demo endpoint shipped for sales enablement with env-based key hiding only (`EXPOSE_B2B_DEMO_KEY`), not profile-based route removal. |
| Enabling condition | Production deploy without explicit demo disable env. |
| Failure of existing controls | `tests/test_security.py` may not cover demo route production deny. |
| Current impact | Demo data/fixtures may appear on production URL space. |
| Future impact | Production isolation sign-off blocked. |
| Distinct scope from parent | Isolates **demo route mounting** vs keys/gitignore (PC-013.a). |
| Independent closure evidence required | Production profile startup audit lists zero demo routes. |

### PC-013.d — Enterprise MFA/SSO not implemented for admin tier

| Field | Value |
|-------|-------|
| Sub-finding ID | PC-013.d |
| Parent ID | PC-013 |
| Originating register | E, L |
| Severity | HIGH |
| Current repository evidence | `auth_service.py` PBKDF2 session auth; `SECURITY.md` documents security controls — no MFA enforcement path in login flow at this commit. |
| Immediate defect | Admin/whale tier accounts rely on single-factor session tokens only. |
| Systemic root cause | MVP auth shipped for product tiers; enterprise IdP/MFA integration deferred. |
| Enabling condition | Enterprise DD questionnaire asks MFA for privileged roles. |
| Failure of existing controls | No admin MFA policy test or feature flag gate. |
| Current impact | Enterprise acquisition security gap. |
| Future impact | P11 identity gate for institutional buyers. |
| Distinct scope from parent | Isolates **MFA/SSO** vs demo/tenant issues. |
| Independent closure evidence required | Documented MFA policy + enforced gate when `ADMIN_MFA_REQUIRED=true` with tests. |

### PC-013.e — Dev/prod route parity not audited at startup

| Field | Value |
|-------|-------|
| Sub-finding ID | PC-013.e |
| Parent ID | PC-013 |
| Originating register | E, L |
| Severity | HIGH |
| Current repository evidence | `dashboard.py` mounts many routers; `production_guard.py` does not diff registered routes against production denylist. REJECT-route concept referenced in remediation planning — no `REJECT_ROUTES` env enforcement found in `production_guard.py`. |
| Immediate defect | Routes safe in dev may remain mounted in production without automated diff. |
| Systemic root cause | Route registration static at import; environment-based filtering not implemented as fail-closed startup audit. |
| Enabling condition | Developer adds debug/admin route without prod guard. |
| Failure of existing controls | No test compares prod vs dev route tables. |
| Current impact | Expanded attack surface if misconfigured. |
| Future impact | Production sign-off blocked. |
| Distinct scope from parent | Isolates **route table audit** vs demo endpoint specifically. |
| Independent closure evidence required | Prod startup emits signed route manifest matching allow list. |

### PC-013.f — Tier authorization scattered across modules vs P09 facade

| Field | Value |
|-------|-------|
| Sub-finding ID | PC-013.f |
| Parent ID | PC-013 |
| Originating register | E, B |
| Severity | HIGH |
| Current repository evidence | `auth_service.feature_allowed` used ad hoc; `require_feature`, `require_whale` in `security_auth.py` / dashboard dependencies — no centralized P09 RBAC service module. |
| Immediate defect | Tier checks implemented per-route; new endpoints can omit gating. |
| Systemic root cause | Tier gating evolved as FastAPI dependencies before platform RBAC facade concept (P09). |
| Enabling condition | New router added without copying dependency pattern. |
| Failure of existing controls | Architecture test for RBAC centralization absent. |
| Current impact | Authorization inconsistency risk. |
| Future impact | Governance scatter blocks institutional security review. |
| Distinct scope from parent | Isolates **RBAC centralization** vs tenant or demo issues. |
| Independent closure evidence required | All tier-gated actions route through one P09 module with static proof. |

### PC-015.a — Referenced audit matrix file absent from repository

| Field | Value |
|-------|-------|
| Sub-finding ID | PC-015.a |
| Parent ID | PC-015 |
| Originating register | A, K |
| Severity | HIGH |
| Current repository evidence | `FEATURE_REALITY_MATRIX.md` **HISTORICAL_REFERENCE_NOT_PRESENT**. ssot-doc-lint rules in remediation standard reference it as scannable class. |
| Immediate defect | Third taxonomy cannot be marked HISTORICAL_NON_CURRENT in repo because file missing. |
| Systemic root cause | Audit matrix from prior review cycle not carried into this branch. |
| Enabling condition | Governance lint rules assume file exists. |
| Failure of existing controls | N/A |
| Current impact | Taxonomy confusion if external DD pack still cites matrix. |
| Future impact | ssot-doc-lint must handle absent vs stale file states. |
| Distinct scope from parent | Isolates **missing audit matrix artifact** vs live grid (PC-015.b). |
| Independent closure evidence required | Status recorded in SSOT pointer: absent or archived with hash. |

### PC-015.b — 40-point grid ids conflict with 88-CAP institutional narrative

| Field | Value |
|-------|-------|
| Sub-finding ID | PC-015.b |
| Parent ID | PC-015 |
| Originating register | A |
| Severity | HIGH |
| Current repository evidence | `bd_platform/registry.py` ids 1–40 numeric keys; CAPABILITY_REGISTRY / BD-DEC-0028 **HISTORICAL_REFERENCE_NOT_PRESENT** in repo — referenced in remediation binding docs only. |
| Immediate defect | DD materials may map grid ids to CAP-### without committed crosswalk file. |
| Systemic root cause | Roadmap grid numbering predates formal 88-capability registry packaging. |
| Enabling condition | Feature-CAP crosswalk attempted from grid alone. |
| Failure of existing controls | No crosswalk file or test prohibiting grid→F-id mapping. |
| Current impact | Capability narrative inconsistency. |
| Future impact | DEC-B crosswalk blocked. |
| Distinct scope from parent | Isolates **grid vs CAP model** vs missing FEATURE_REALITY_MATRIX. |
| Independent closure evidence required | Grid labeled capability-adjacent; crosswalk lives only in attested registry post OD-01. |

### PC-019.a — Training artifact directories not guarded from serving paths

| Field | Value |
|-------|-------|
| Sub-finding ID | PC-019.a |
| Parent ID | PC-019 |
| Originating register | I |
| Severity | MEDIUM |
| Current repository evidence | `flywheel_saturation_guard.py` guards alert broadcast economics; `ml/` package and local `data/models/` paths not uniformly gated against live serving ingestion in CI. |
| Immediate defect | Flywheel guard does not validate separation of training stores from runtime inference inputs. |
| Systemic root cause | ML safety work targeted crowd economics (product moat) not training-serving isolation invariant. |
| Enabling condition | Flywheel scheduler loads artifacts from disk paths shared with training exports. |
| Failure of existing controls | `tests/test_ml_integrity.py` partial coverage. |
| Current impact | Risk of serving stale/wrong model file if path misconfigured. |
| Future impact | P08 flywheel institutional gate. |
| Distinct scope from parent | Isolates **training path leakage** vs saturation economics. |
| Independent closure evidence required | Anti-leakage test fails CI if training dir readable by serving loader. |

### PC-021.a — Manifest divergence breaks CI↔Docker parity

| Field | Value |
|-------|-------|
| Sub-finding ID | PC-021.a |
| Parent ID | PC-021 |
| Originating register | H |
| Severity | HIGH |
| Current repository evidence | See PC-021 parent — prod manifest missing pandas/ccxt/sklearn/pytest present in dev manifest. |
| Immediate defect | Identical commit tested differently than deployed. |
| Systemic root cause | Prod slimming without reconciliation job. |
| Enabling condition | Feature code imports dev-only deps during CI passing run. |
| Failure of existing controls | Docker smoke build does not import-check ML/ccxt inside image. |
| Current impact | Production ImportError class defects. |
| Future impact | Extends PC-001 lockfile work. |
| Distinct scope from parent | Actionable manifest diff item for H register. |
| Independent closure evidence required | Resolved tree diff CI vs Docker image == 0 for runtime deps. |

### PC-022.a — No blocking full-collection pytest job

| Field | Value |
|-------|-------|
| Sub-finding ID | PC-022.a |
| Parent ID | PC-022 |
| Originating register | F |
| Severity | HIGH |
| Current repository evidence | `ci.yml` four-module subset; 34 test files exist; baseline file absent (PC-039). |
| Immediate defect | Merge gate does not require full test collection success. |
| Systemic root cause | CI speed tradeoff institutionalized without baseline artifact. |
| Enabling condition | Every PR to main. |
| Failure of existing controls | Meta-test absent. |
| Current impact | Silent regressions. |
| Future impact | G1 blocked. |
| Distinct scope from parent | Isolates **collection gate** vs SSE/concurrency/DR siblings. |
| Independent closure evidence required | CI artifact stores collection count ≥ baseline with blocking job. |

### PC-022.b — No SSE/stream E2E in CI

| Field | Value |
|-------|-------|
| Sub-finding ID | PC-022.b |
| Parent ID | PC-022 |
| Originating register | F |
| Severity | HIGH |
| Current repository evidence | `bd_platform/sse_stream.py` exists; no `tests/e2e/test_sse_stream_ci.py` or equivalent in `tests/`. |
| Immediate defect | UI streaming regressions undetected automatically. |
| Systemic root cause | SSE validated manually during Feature 002 development; institutional E2E job never added. |
| Enabling condition | Feature 002 claims institutional validation. |
| Failure of existing controls | No pytest-sse/playwright job. |
| Current impact | Stream breakage ships silently. |
| Future impact | Feature 002 closure blocked. |
| Distinct scope from parent | Isolates **SSE E2E** class. |
| Independent closure evidence required | CI job validates SSE endpoint contract with signed log. |

### PC-022.c — Execution concurrency races not in test suite

| Field | Value |
|-------|-------|
| Sub-finding ID | PC-022.c |
| Parent ID | PC-022 |
| Originating register | F, D |
| Severity | HIGH |
| Current repository evidence | `execution_engine.py` async order paths; no `tests/concurrency/` directory. |
| Immediate defect | Race conditions between loop, manual execute, and freeze load untested. |
| Systemic root cause | Concurrency tests expensive/flaky — deferred without institutional requirement encoded in CI. |
| Enabling condition | Auto-exec loop + manual API under load. |
| Failure of existing controls | Limited phase tests only. |
| Current impact | Latent race defects. |
| Future impact | P06 safety sign-off. |
| Distinct scope from parent | Isolates **concurrency** test class. |
| Independent closure evidence required | Blocking concurrency suite for auth/execution paths. |

### PC-022.d — Backup/restore drill not evidenced in tests

| Field | Value |
|-------|-------|
| Sub-finding ID | PC-022.d |
| Parent ID | PC-022 |
| Originating register | F, G |
| Severity | HIGH |
| Current repository evidence | `database.py` SQLite/postgres backends; backup scripts may exist in ops docs — no `tests/ops/test_backup_restore_drill.py` in repo. |
| Immediate defect | DR operability claim unsupported by automated drill artifact. |
| Systemic root cause | DR treated as ops manual procedure outside pytest institutional gate. |
| Enabling condition | Institutional operability DD (G7). |
| Failure of existing controls | No signed restore artifact in CI. |
| Current impact | Unknown RTO/RPO validation. |
| Future impact | G7 blocked. |
| Distinct scope from parent | Isolates **restore drill** class. |
| Independent closure evidence required | Integration test produces signed restore drill JSON. |

### PC-022.e — Negative execution bypass tests incomplete

| Field | Value |
|-------|-------|
| Sub-finding ID | PC-022.e |
| Parent ID | PC-022 |
| Originating register | F, D |
| Severity | HIGH |
| Current repository evidence | `tests/test_security.py`, `tests/test_risk_manager.py` partial; no comprehensive bypass suite for freeze/exposure/env-flag combinations. |
| Immediate defect | Attacker-class paths (force live with freeze on) not exhaustively tested. |
| Systemic root cause | Security tests focused on authn/tier not execution authorization combinatorics. |
| Enabling condition | Live execution env toggles combined with risk freeze state. |
| Failure of existing controls | Positive-path execution tests dominate. |
| Current impact | Unknown bypass surfaces. |
| Future impact | DEC-D verification incomplete. |
| Distinct scope from parent | Isolates **negative bypass** security tests. |
| Independent closure evidence required | Matrix of bypass attempts all DENY with CI artifact. |

### PC-034.a — Security workflow must depend on full-suite success

| Field | Value |
|-------|-------|
| Sub-finding ID | PC-034.a |
| Parent ID | PC-034 |
| Originating register | F |
| Severity | MEDIUM |
| Current repository evidence | `.github/workflows/security.yml` independent of `.github/workflows/ci.yml`; no `needs:` linkage possible across separate workflow files without unified workflow or reusable workflow orchestration. |
| Immediate defect | Combined “all green” misleads stakeholders. |
| Systemic root cause | Security workflow created as standalone compliance scan. |
| Enabling condition | Reviewers check both workflows separately. |
| Failure of existing controls | No orchestration meta-workflow. |
| Current impact | False confidence. |
| Future impact | Institutional CI narrative. |
| Distinct scope from parent | Isolates **workflow ordering** fix. |
| Independent closure evidence required | Single pipeline or required check policy tying security to full suite green. |

---

## Register A–L Coverage Index

| Register | Description | Mapped findings |
|----------|-------------|-----------------|
| A | Feature enumeration authority | PC-003, PC-015, PC-015.a, PC-015.b, PC-009.b, PC-036 |
| B | Platform boundary / API sprawl | PC-008, PC-008.a–d, PC-009, PC-009.a–b, PC-009.d, PC-013.f, PC-031 |
| C | Price / data authority | PC-004, PC-026, PC-041, PC-009.c, PC-009.d |
| D | Execution safety / gating | PC-005, PC-010, PC-010.a, PC-014, PC-022.c, PC-022.e |
| E | Tenancy / production isolation | PC-013, PC-013.a–f, PC-030 |
| F | Test / CI architecture | PC-002, PC-022, PC-022.a–e, PC-033, PC-034, PC-034.a, PC-039 |
| G | G3 / evidence chain | PC-011, PC-011.a–b, PC-029, PC-035, PC-040 |
| H | Deploy / reproducibility | PC-001, PC-007, PC-016, PC-017, PC-021, PC-021.a, PC-025 |
| I | Oracle / research / ML | PC-012, PC-012.a–b, PC-019, PC-019.a, PC-028 |
| J | Financial / schema migration | PC-006, PC-009.c, PC-027, PC-041 |
| K | SSOT / governance docs | PC-023, PC-032, PC-036, PC-037, PC-042, PC-015.a |
| L | Audit / compliance | PC-024, PC-013.d, PC-013.e, PC-008.d, PC-034, PC-038 |

**Unmapped register items:** 0 (all A–L items above map to at least one parent or sub-finding closure path).
