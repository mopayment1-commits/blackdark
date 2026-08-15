# BLACKDARK CLEAN-ROOM CAPABILITY REALITY AUDIT

Independent adversarial audit. Docs/`product_complete`/`plan_audit` self-labels are **not** evidence.

## CANDIDATE SHA:
`2f8d968e85dcdd4bc83125e526ede76fff0e4a3a`

## WORKSPACE SHA MATCH: YES

Observed: `git rev-parse HEAD` = `2f8d968e85dcdd4bc83125e526ede76fff0e4a3a` on branch `cursor/95plus-recert-phase0-120d` (audit branch `cursor/clean-room-capability-audit-1a57`).

---

## CAPABILITY INVENTORY:

**Inventory basis:** `plan_audit._PLAN_ROWS` (46) + institutional/foundation matrix caps + mandatory focus areas (deduped). Catalog/file presence alone does **not** count as VERIFIED_COMPLETE.

| Bucket | Count |
|---|---|
| Total approved capabilities discovered | **82** |
| VERIFIED_COMPLETE | **3** |
| COMPLETE_VIA_MERGE | **0** |
| PARTIAL | **41** |
| SCAFFOLD/UI_ONLY/BACKEND_ONLY/TEST_ONLY/DOCUMENTED_ONLY | **28** |
| STUB/MOCK/FAKE/PLACEHOLDER | **4** |
| NOT_IMPLEMENTED | **2** |
| UNVERIFIED | **4** |

### VERIFIED_COMPLETE (narrow; behavior + fail-closed proven in code/tests)
1. **Unknown fee fail-closed (`fee_matrix`)** — unknown venue → `None`, never invent 0 (`tests/test_prohibited_defect_eradication.py`).
2. **Funding omit-without-depth** — `calculate_funding_arbitrage` returns `[]` when books missing (default path).
3. **OIDC JWKS verify module** — cryptographic verify path exists (`oidc_jwks_verify.py`) with negative tests for aud/exp/tamper (library-complete; live IdP wiring still env-gated → institutional claim remains PARTIAL overall).

### Most material PARTIAL / SCAFFOLD / STUB / NOT_IMPLEMENTED findings

| Finding | Class | Evidence |
|---|---|---|
| **100-platform live coverage honesty collapse** | PARTIAL / FAKE (status inflation) | `data/universe_registry.json` + `config.INGESTION_READY_EXCHANGES`: **100/100** marked `ingestion_ready`; `market_fetcher_hub`: only **9 native**, **32 ccxt**, **29 coingecko**, **20 dex**, **10 perp_dex**. `compute_universe_coverage()` → `live_ingestion_sources=0`, `coverage_percent_exchanges=100.0`, `planned=0`. Operational manifest `status=pending_review`, `review.approved=False` while listing 100 operational exchanges. |
| **OMS** | SCAFFOLD / BACKEND_ONLY / TEST_ONLY | `oms.py` JSON state machine; **no** `api/` or `dashboard.py` import/route. `oms_status()["product_complete"]=True`. Only tests import OMS. No venue adapter submission wiring. |
| **Decision Graph / Decision Intelligence Engine** | SCAFFOLD / TEST_ONLY | `decision_graph.py` / `decision_intelligence_engine.py` append JSONL; **no API production wiring**. Self-label `product_complete=True`. |
| **Institutional Memory / Continuous Learning / White Label / B2B ops** | SCAFFOLD | Local JSON/JSONL writers (`institutional_memory.py`, `continuous_learning.py`, `white_label.py`, `b2b_institutional_ops.py`) with unconditional `product_complete=True`. |
| **CEX↔DEX indicative-as-executable** | PARTIAL / defect | `_cex_dex_row` can set `executable=True` from DEX pool liquidity + mid prices **without CEX L2 walk** despite comment claiming otherwise (`bd_platform/cex_dex_arbitrage.py`). Adversarial probe: executable=True with synthetic mid/liq. Executor does block `executable=False`, but classification is wrong upstream. |
| **Jupiter synthetic economics** | STUB / MOCK | `jupiter_dex_adapter.quote_swap` returns `ok=True`, `source=synthetic_economics` on network failure (observed runtime). |
| **77 arb catalog claimed complete** | PARTIAL / DOCUMENTED_ONLY honesty gap | Live catalog: **10 live / 28 proxy / 39 planned** (`arbitrage_catalog`); `plan_audit` still labels “77 arbitrage types catalog” as `complete`. |
| **SCIM** | PARTIAL | JSON file store; `scim_ready`/`product_complete` always True; no SCIM bearer token auth (router uses session/admin principal); Groups incomplete vs full RFC7644. |
| **SAML** | PARTIAL | AuthnRequest is unsigned XML deflate; `build_authn_request` sets `institutional_complete=True` without Signature; Response verify exists but custom “stable assertion” path ≠ full XML-DSig enterprise posture. |
| **Soft-launch / production separation** | PARTIAL / RECURRENT | Without `INSTITUTIONAL_LAUNCH`, `SOFT_LAUNCH=true` in `ENV=production` still **waives** Postgres + billing + webhook required checks (`production_guard.py`). Probe: checks `ok=True` with no DATABASE_URL/billing. |
| **DR / backup** | DOCUMENTED_ONLY / SCAFFOLD | `record_backup_drill` appends JSONL attestation; `backup_status()["product_complete"]=True` — no restore execution proof. |
| **Super Terminal** | UI_ONLY / PARTIAL | `emerging_fund_terminal.py` assembles export pack; not a full institutional terminal stack. |
| **Streaming multi-venue** | PARTIAL | WS hub real for binance/okx/bybit/(kraken); `streaming_institutional` lifecycle mostly unit-level; not 100-venue live WS. |
| **Oracle confidence** | PARTIAL | `ai_oracle` emits `confidence_percent` float; does **not** use `confidence_truth` typing on that path. |
| **plan_audit 46/46 complete** | False COMPLETE | Status is hardcoded; gate is `import_module` success (`plan_audit.py`). FILE≠CAPABILITY. |
| **Native iOS/Android** | NOT_IMPLEMENTED (honestly scoped as PWA) | Matrix notes PWA only — acceptable non-claim; still not store apps. |
| **Live PSP purchase / live DR restore** | UNVERIFIED / EXTERNAL | Matrix admits external; cannot invent. |

---

## ORIGINAL AUDIT DEFECT CLASSES (check recurrence):

| Defect | Status | Evidence |
|---|---|---|
| SSO demo/false complete | **CLOSED** (demo path) / **PARTIAL** (product claim) | Demo opt-in default false; live requires JWKS/cert. Demo cannot claim `product_complete`. Institutional SSO still env/config gated. |
| SCIM honesty | **RECURRENT** (soft) | Module exists + CRUD, but `product_complete`/`scim_ready` always True regardless of IdP/token posture; JSON persistence. |
| SAML honesty | **RECURRENT** (soft) | Unsigned AuthnRequest + `institutional_complete=True` on build; stub string `BD_SAML_AUTHN_` gone. |
| Soft Launch bypass | **RECURRENT** | Production+`SOFT_LAUNCH` still waives Postgres/billing unless `INSTITUTIONAL_LAUNCH` forces soft_launch=False. |
| Canonical data missing/bypass | **PARTIAL→improved / not COMPLETE** | Layer + adoption helpers exist on arb paths; not proven on all critical streams; operational ingestion not approved (`pending_review`). |
| Funding zero slippage | **CLOSED** (emit path) / **smell remains** | Opportunities omitted without depth; helper still **returns `0.0` slippage** with `depth_verified=False` (`_funding_depth_slippage_bps`). |
| CEX-DEX indicative-as-executable | **RECURRENT** | Upstream can mark executable without CEX book walk. |
| Unknown fee invent | **CLOSED** | `fee_matrix` returns None; CEX-DEX skips when fee unknown. |
| Stale-as-live | **CLOSED** (library) / **UNVERIFIED** (all consumers) | `stream_freshness_truth` / institutional prove helpers; full fanout consumer coverage not proven end-to-end here. |
| OMS missing | **RECURRENT** | File OMS exists; **not production-wired**. |
| Decision graph missing | **RECURRENT** (as product) | JSONL scaffold + tests; **no API/product wiring**. |
| Uncalibrated confidence | **RECURRENT** | `confidence_truth` exists; `ai_oracle` still exposes percent confidence without typed claim on main path. |
| Risk breadth gaps | **PARTIAL** | Heuristic modules for liq/corr/flash/SC/stress; not full institutional risk system. |
| Whale marketing-only | **PARTIAL** | `whale_execution_evidence` depth probes real; `whale_status` still self-labels complete; tracker narrative surfaces exceed proven executable whale capacity. |
| False COMPLETE claims | **RECURRENT** | Dozens of `product_complete=True`; matrix/plan_audit claim VERIFIED_COMPLETE; honesty board reports 100% live with 0 ingestion sources. |

---

## SCORES (/100):

| Area | Score | Notes |
|---|---:|---|
| Architecture | 58 | Broad modular surface; many parallel JSONL “complete” micro-modules without production spine. |
| Engineering | 62 | Real Python/FastAPI craft; excessive self-certification. |
| Data Foundation | 45 | Canonical layer present; registry/manifest honesty broken (100 ready / 0 live sources / pending_review). |
| Financial Truth | 68 | Fee/funding fail-closed strong; CEX-DEX executable labeling weak; Jupiter synthetic ok=True. |
| Execution Truth | 52 | Dry-run defaults; OMS unwired; DEX leg disclaimer still “simulated”. |
| Security | 64 | Auth hardening, JWKS, production_guard institutional force-off exist; soft-launch waive remains; SCIM not tokenized. |
| Risk | 55 | Multiple heuristic gates; breadth ≠ institutional completeness. |
| Decision Intelligence | 38 | Graph/engine/memory/learning are append-only scaffolds. |
| Streaming | 57 | Real few-venue WS + freshness helpers; not multi-venue institutional completeness. |
| OMS | 28 | Lifecycle file toy; no API/venue integration. |
| Portfolio | 50 | Analyze endpoints + fail-closed helpers; not full portfolio AI. |
| Whale | 48 | Evidence probes good; marketing completeness overstated. |
| Super Terminal | 35 | Emerging fund pack / lite surfaces. |
| B2B | 42 | JSONL reporting/alerts/SLA; WS hub exists; not enterprise ops suite. |
| Institutional | 40 | Assurance APIs mostly attestation writers. |
| Reliability | 40 | Soft-launch demo path; HA/DR drills are records. |
| Observability | 48 | Metrics/probes exist; not proven production telemetry completeness. |
| Performance | 45 | Fast-scan/WS claims; no clean-room load proof at this SHA. |
| Test Quality | 70 | Strong regression suites (51/51 honesty subset passed) but tests encode self-labels (`product_complete is True`, `enabled_exchanges()>=100`) that **cement false completeness**. |
| Transferability | 35 | External ownership/DR/PSP still external; soft-launch demo posture. |
| Acquisition Readiness | 32 | Clean-room disproofs block COMPLETE; honesty defects material for DD. |
| **OVERALL** | **46** | |

---

## DEFECTS:

### Critical
1. **Catalog/status inflation as live:** 100 venues `ingestion_ready` + 100% coverage metrics while `live_ingestion_sources=0` and operational manifest `approved=False` / `pending_review`.
2. **False COMPLETE / VERIFIED_COMPLETE product claims** across matrix, `plan_audit`, and dozens of `product_complete=True` status APIs without full DATA→…→PRODUCTION WIRING.
3. **CEX-DEX can classify `executable=True` without verified CEX L2 depth** (`bd_platform/cex_dex_arbitrage.py::_cex_dex_row`).

### High
4. **OMS / Decision Graph / Decision Engine not production-wired** (TEST_ONLY/SCAFFOLD while labeled complete).
5. **Soft Launch still waives Postgres+billing in production** unless institutional flag set.
6. **Jupiter quote silent synthetic fallback with `ok=True`.**
7. **77-type arb catalog: 39 planned + 28 proxy sold as plan_audit complete.**

### Medium
8. SCIM always-complete + JSON store + no SCIM bearer.
9. SAML AuthnRequest unsigned yet `institutional_complete=True`.
10. Oracle `confidence_percent` untyped vs `confidence_truth`.
11. DR/backup “complete” via JSONL drill records only.
12. Funding helper returns slippage `0.0` when depth missing (safe only if callers check `depth_verified`).

### Low
13. White-label JSON branding self-labeled complete.
14. Proof Arena Lite / fund terminal are lite surfaces over-claimed in marketing inventory.
15. Sentiment mock toggles exist (default off) — residual production misuse risk if env flipped.

---

## TESTS OBSERVED:

Focused honesty/financial suite run at candidate SHA:

`pytest tests/test_prohibited_defect_eradication.py tests/test_95plus_foundation_closure.py tests/test_institutional_honesty_closure.py tests/test_p0_financial_executability.py tests/test_arb_truth_gate.py -q`

**Passed: 51 / Failed: 0 / Skipped: 0**

Note: suite **passes while clean-room probes disprove completeness** — several tests assert self-labels (`product_complete is True`, `enabled_exchanges() >= 100`), so green tests ≠ product COMPLETE.

Adversarial runtime probes (non-pytest) also executed: CEX-DEX executable-without-L2, OMS/Decision API wiring=NONE, soft-launch waive, coverage honesty 100/0, Jupiter synthetic, funding zero-slip tuple, SAML unsigned institutional_complete, catalog 10/28/39.

Full repo test matrix: **NOT RUN** (out of scope for this focused audit pass).

---

## FINAL VERDICT:

# NOT COMPLETE

Reason: multiple production-blocking honesty and wiring defects remain at SHA `2f8d968e85dcdd4bc83125e526ede76fff0e4a3a` — especially live-coverage inflation, unwired OMS/decision graph, CEX-DEX executable misclassification, soft-launch production waivers, and systemic false `product_complete` / plan_audit COMPLETE claims. Prefer NOT COMPLETE when unsure; evidence here is decisive.
