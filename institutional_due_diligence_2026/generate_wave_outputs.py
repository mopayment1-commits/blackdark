#!/usr/bin/env python3
"""Generate all wave markdown outputs 04-30 + final report from accumulated analysis."""
from pathlib import Path

OUT = Path("/workspace/institutional_due_diligence_2026")
GEN = "2026-09-10T23:50:00Z"

FILES = {
"04_ARCHITECTURE_AND_REACHABILITY.md": f"""# 04 — Architecture & Reachability (Wave 2)

**Generated:** {GEN} | **Evidence:** L0 | **Discovery ≠ Audit**

## Actual Architecture (from code)
- **Monolith:** `dashboard.py` (~156KB, 225 direct `@app` routes, 27 included routers)
- **Worker:** `microservices/worker_app.py` (4 routes)
- **Launcher:** `run_service.py` (web/aggregator/arbitrage/ingestion modes)
- **Top coupling:** `database` (327 imports), `bd_platform` (494), `cap646` (369)

## Reachability (§21)
| Classification | Count | Status |
|---|---|---|
| Entry points identified | 147 `__main__` + 2 FastAPI apps | DISCOVERED |
| Reachability proven | 0 | NOT VERIFIED |
| Dead/orphan modules | NOT VERIFIED | Wave 20 partial |

## Findings
- **WF-004** P2: Monolithic dashboard coupling
- **WF-005** P2: TODO/FIXME markers present

**Wave 2 CLOSED:** Architecture mapped; reachability NOT VERIFIED without runtime traces.
""",

"05_MODEL_INVENTORY.md": f"""# 05 — Master Model Inventory (Wave 3)

**Generated:** {GEN}

## Model Candidates Discovered: 403 files (heuristic)
## Classified in inventory: 87 high-confidence paths

| Model ID | Name | Path | Tier | Validation |
|---|---|---|---|---|
| MDL-001 | AI Oracle | ai_oracle.py | HIGH | NOT VERIFIED |
| MDL-002 | Arbitrage Engine | arbitrage_engine.py | HIGH | NOT VERIFIED |
| MDL-003 | Sentiment Engine | sentiment_engine.py | MEDIUM | NOT VERIFIED |
| MDL-004 | Regime ML | ml/train_regime_models.py | HIGH | NOT VERIFIED |
| MDL-005 | Alpha Engine | bd_platform/alpha_engine.py | HIGH | NOT VERIFIED |
| MDL-006 | Fee Matrix | fee_matrix.py | HIGH | NOT VERIFIED |
| MDL-007 | Profit/Fee Algorithms | profit_fee_algorithms.py | CRITICAL | NOT VERIFIED |
| MDL-008 | RVM System | rvm/ | MEDIUM | NOT VERIFIED |
| MDL-009 | Drift Monitor | ml/drift_monitor.py | MEDIUM | NOT VERIFIED |
| MDL-010 | Compounding/KG | api/routers/compounding.py | HIGH | NOT VERIFIED |

**WF-006:** 403 model candidates; zero independently validated.

**Wave 3 CLOSED:** Inventory complete; validation deferred to Waves 5-6.
""",

"08_DATA_LINEAGE_AND_INTEGRITY.md": f"""# 08 — Data Lineage & Integrity (Wave 4)

**Generated:** {GEN}

## Positive Observations (code-level, NOT VERIFIED operational)
- `blackdark/data/response_metadata.py`: LIVE/MISSING/STALE/UNKNOWN contract
- `blackdark/data/provenance.py` + migration 007: provenance lineage
- `blackdark/data/repository.py`: JOIN to data_provenance

## Findings
- **WF-011** P2: Split stale semantics — execution guard vs cache layers lack unified UNKNOWN/STALE
- **WF-012** P1: Dual precision — spine REAL vs Wave-01 DECIMAL(36,18)

**Wave 4 CLOSED:** Lineage modules discovered; end-to-end lineage NOT VERIFIED.
""",

"06_FINANCIAL_MODEL_VALIDATION.md": f"""# 06 — Financial Model Validation (Wave 5 partial)

**Generated:** {GEN}

## Decimal vs Float
- `money_decimal.py`: canonical Decimal boundary (documented)
- 10 Python files import Decimal helpers
- `database.py`: 36 REAL columns persist financial values
- `profit_fee_algorithms.py`: hybrid float intermediate, Decimal at settlement gate

## Findings
- **WF-013** P1: Narrow Decimal adoption; float persistence on spine tables
- **WF-014** P2: fee_matrix fail-closed (None for unknown) — positive pattern, NOT VERIFIED in all paths

Independent recomputation: NOT PERFORMED (§28).

**Wave 5 CLOSED:** Code review complete; independent validation NOT VERIFIED.
""",

"09_AI_ML_VALIDATION.md": f"""# 09 — AI/ML Validation (Wave 6)

**Generated:** {GEN}

## AI Systems Inventory
| System | Type | Provider | Confidence Output |
|---|---|---|---|
| ai_oracle.py | Hybrid rules+LLM | OpenAI/Ollama/free chain | confidence_percent 0-100 |
| sentiment_engine.py | NLP | VADER + optional LLM | NOT VERIFIED |
| chat_service.py | LLM | OpenAI | NOT VERIFIED |
| ml/regime_router.py | ML routing | joblib models | NOT VERIFIED |

## AI Financial Safety (§48)
- LLM prompts request one-sentence verdict — hallucination risk NOT VERIFIED at runtime
- Rules engine fallback when LLM fails — NOT VERIFIED dominant path

**Wave 6 CLOSED:** Inventory complete; grounding/calibration NOT VERIFIED.
""",

"10_SECURITY_ASSESSMENT.md": f"""# 10 — Security Assessment (Wave 7)

**Generated:** {GEN}

## Positive Patterns (code-level)
- CSP nonce + strict-dynamic in security_middleware.py
- CSRF protection on cookie mutations
- Production SESSION_TOKEN_PEPPER required

## Findings
- **WF-007** P1: Hardcoded secret pattern heuristics (7 hits) — manual review required
- **WF-015** P1: `/api/analytics/event` accepts caller-supplied user_id without auth decorator
- **WF-016** P2: Dev-default session pepper when env unset (blocked in prod)

## API Auth Surface (Wave 9 overlap)
- 196/304 router endpoints lack auth Depends in signature — NOT VERIFIED intentional

**Wave 7 CLOSED:** Static review; penetration/IDOR full matrix NOT VERIFIED.
""",

"11_DATABASE_PROCESSING_INTEGRITY.md": f"""# 11 — Database & Processing Integrity (Wave 8)

**Generated:** {GEN}

## Findings
- **WF-017** P0: Dual-schema architecture (database.py ~60 tables vs Wave-01 17 migrations)
- **WF-018** P2: Duplicate migration 004/010 both CREATE de_funding_rates
- **WF-019** P2: migrate.py _REQUIRED_TABLES omits exchange_flow_labels (017)
- **WF-020** P1: funding_rates REAL vs de_funding_rates DECIMAL type drift

Alembic: 1 revision, documented non-authoritative.

**Wave 8 CLOSED:** Schema inventory complete; production schema unity NOT VERIFIED.
""",

"12_API_ASSESSMENT.md": f"""# 12 — API Assessment (Wave 9)

**Generated:** {GEN}

## Endpoint Universe: 657 route decorators (657 API handlers)

### api/routers/ auth coverage
| Metric | Count |
|---|---:|
| Total handlers | 304 |
| Strict auth Depends | 83 |
| Optional auth | 25 |
| No auth decorator | 196 |

Largest unauthenticated surfaces: heroes.py (70/74), compounding.py (28/28), oracle.py (20/28).

**Wave 9 CLOSED:** Full endpoint inventory; per-endpoint authorization audit NOT VERIFIED.
""",

"13_FRONTEND_PRODUCT_ASSESSMENT.md": f"""# 13 — Frontend / Product Assessment (Wave 10)

**Generated:** {GEN}

| Metric | Count |
|---|---:|
| Page paths | 68 |
| Templates | 50 |
| Orphan template | 1 (index.html) |
| Templates with fetch(), no catch | 22/43 |

**Wave 10 CLOSED:** UI inventory complete; E2E UI verification NOT VERIFIED.
""",

"14_USER_JOURNEY_AND_BILLING.md": f"""# 14 — User Journey & Billing (Wave 11)

**Generated:** {GEN}

## Journey Files Mapped: 35 auth/billing-related paths
Login → MFA → Profile → Checkout (Stripe/Lemon) → Webhook → Entitlement

**Wave 11 CLOSED:** File-level trace complete; live journey testing NOT VERIFIED.
""",

"15_TEST_ASSURANCE.md": f"""# 15 — Test Assurance (Wave 12)

**Generated:** {GEN}

| Metric | Value |
|---|---|
| Test files | 200 |
| Test functions | 1,054 |
| Skip markers | 8 (5 files) |
| Mock/patch files | 90/202 |
| Tests executed this audit | 0 |

CI runs risk-weighted subset; ~20 failures acknowledged outside critical gate.

**WF-008:** Test suite exists but audit has zero E1 test execution evidence.

**Wave 12 CLOSED:** Test inventory complete; assurance NOT VERIFIED.
""",

"16_CICD_SDLC_SUPPLY_CHAIN.md": f"""# 16 — CI/CD / SDLC / Supply Chain (Wave 13)

**Generated:** {GEN}

## Workflows: ci.yml, security.yml, sonarcloud.yml, cap978-institutional-gate.yml
## CI jobs: critical → owner-secret-verify → batch-orchestrator / gate-full-pr / cap-dedup

SBOM: docs/data-room/sbom/cyclonedx-python.json (generated by script, NOT VERIFIED current)

**Wave 13 CLOSED:** Pipeline mapped; CI bypass risk NOT VERIFIED on live GitHub settings.
""",

"17_PERFORMANCE_CAPACITY.md": f"""# 17 — Performance / Capacity (Wave 14)

**Generated:** {GEN}

Load test scripts: 3 (load_test.py, load_test_concurrent.py, load_test_1m_simulation.py)
Executed in this audit: 0

**TESTED CAPACITY:** NOT VERIFIED
**THEORETICAL CAPACITY:** NOT VERIFIED

**Wave 14 CLOSED:** Scripts discovered; no capacity proof.
""",

"18_RELIABILITY_RESILIENCE.md": f"""# 18 — Reliability / Resilience (Wave 15)

**Generated:** {GEN}

Backup: scripts/backup_postgres.py | Restore: scripts/restore_postgres.py
Documented failure modes: 4 (BATCH07 JSON); live_chaos: NOT_RUN
Restore drill: EXTERNAL per docs/ops/BACKUP_RESTORE.md

**Wave 15 CLOSED:** Artifacts mapped; DR NOT VERIFIED.
""",

"19_PRIVACY_DATA_GOVERNANCE.md": f"""# 19 — Privacy / Data Governance (Wave 16)

**Generated:** {GEN}

Privacy-related Python files: 63
Key: gdpr_service.py, api/routers/privacy.py (DSR export/erase routes)

Personal data inventory: NOT VERIFIED (requires Wave 16 deep trace)

**Wave 16 CLOSED:** Entry points discovered; retention/deletion flows NOT VERIFIED.
""",

"20_DOCUMENTATION_CONTRADICTIONS.md": f"""# 20 — Documentation Contradictions (Wave 17)

**Generated:** {GEN}

## CONTRADICTION_REGISTER

| ID | Docs Say | Code/Audit Says | Status |
|---|---|---|---|
| CON-001 | BATCH07_FINAL_LOCAL_FREEZE=true | Zero-trust: E6 claim only | NOT VERIFIED |
| CON-002 | CI PASS in freeze JSON | Tests not re-run in audit | NOT VERIFIED |
| CON-003 | templates/index.html exists | /app redirects to /dashboard | VERIFIED orphan |

**WF-009** P2: Freeze claims unrevalidated.

**Wave 17 CLOSED:** Contradiction register initialized.
""",

"21_IP_LICENSE_DATA_RIGHTS.md": f"""# 21 — IP / License / Data Rights (Wave 18)

**Generated:** {GEN}

License inventory: docs/data-room/licenses/dependency_licenses.json
SBOM: docs/data-room/sbom/cyclonedx-python.json
Copyleft references in license docs: 2

**LEGAL VERIFICATION REQUIRED** for market-data redistribution rights.

**Wave 18 CLOSED:** Artifacts located; legal review NOT VERIFIED.
""",

"22_ACQUISITION_DUE_DILIGENCE.md": f"""# 22 — Acquisition Due Diligence (Wave 19)

**Generated:** {GEN}

| Factor | Assessment |
|---|---|
| Reproducible build | docker build in CI — NOT VERIFIED locally |
| Onboarding docs | docs/ extensive — accuracy NOT VERIFIED |
| Technical debt | Monolith + dual schema + 196 open API routes |
| Vendor lock-in | Stripe, OpenAI, exchange APIs — concentration NOT VERIFIED |
| Hidden manual ops | 147 CLI scripts suggest operational complexity |
| Transferability | NOT VERIFIED |

**Wave 19 CLOSED:** Qualitative assessment; acquisition readiness NOT VERIFIED.
""",

"23_TECHNICAL_DEBT_REGISTER.md": f"""# 23 — Technical Debt Register (Wave 19)

**Generated:** {GEN}

| ID | Location | Severity | Area |
|---|---|---|---|
| TD-001 | dashboard.py | P2 | Monolithic coupling |
| TD-002 | database.py + blackdark/data | P0 | Dual schema |
| TD-003 | api/routers/ | P1 | 196 endpoints without auth decorator |
| TD-004 | database.py REAL columns | P1 | Financial precision |
| TD-005 | templates/ | P2 | 22 pages missing fetch error handlers |
""",

"29_RED_TEAM_EFFECTIVE_CHALLENGE.md": f"""# 29 — Red Team / Effective Challenge (Wave 21)

**Generated:** {GEN}

## Top PASS Claims Challenged
| Claim | Challenge Result |
|---|---|
| BATCH07_FINAL_LOCAL_FREEZE=true | **FAILED** — no E1 evidence |
| CI PASS | **FAILED** — not re-executed |
| 1054 tests = assurance | **FAILED** — zero tests run in audit |
| Security middleware adequate | **PARTIAL** — static only; IDOR surface open |
| Decimal financial math | **PARTIAL** — narrow adoption; REAL persistence |

**Wave 21 CLOSED:** Red team pass on positive claims — none survive as VERIFIED_OPERATIONAL.
""",

"30_FINAL_RECONCILIATION.md": f"""# 30 — Final Reconciliation (Wave 22)

**Generated:** {GEN}

## Cross-Domain Checks
| Check | Result |
|---|---|
| SSOT ↔ System Inventory | PARTIAL — denominators aligned |
| Inventory ↔ Coverage Ledger | DISCOVERED counts set; AUDITED mostly 0 |
| Findings ↔ Evidence | All WF-* have Evidence IDs or L0 basis |
| PASS without evidence | 0 VERIFIED_OPERATIONAL items |
| Unaudited P0 assets | Dual schema (WF-017) discovered not runtime-verified |
| Hidden NOT VERIFIED | 196 API routes, 403 models, 0 runtime tests |

**Wave 22 CLOSED:** Reconciliation complete with material gaps documented.
""",
}

for name, content in FILES.items():
    (OUT / name).write_text(content, encoding="utf-8")
print(f"Wrote {len(FILES)} wave files")
