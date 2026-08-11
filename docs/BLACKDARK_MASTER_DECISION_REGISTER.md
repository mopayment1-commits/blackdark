# BLACKDARK MASTER DECISION REGISTER

**Canonical HEAD audited:** `f1a4815c7f87db6526619c8fcd3406ea1d2c2403`  
**Branch:** `cursor/institutional-hardening-120d`  
**Audit date:** 2026-08-11  
**Rule:** Only FINAL / APPROVED / BINDING / VERIFIED decisions are obligations. PROPOSED / REJECTED / SUPERSEDED listed separately.

Status key:

| Status | Meaning |
|---|---|
| VERIFIED_IMPLEMENTED | Code + tests/runtime evidence on this HEAD |
| PARTIALLY_IMPLEMENTED | Material slice missing or competing path remains |
| IMPLEMENTED_BUT_UNVERIFIED | Code present; required tests/evidence missing |
| NOT_IMPLEMENTED | No adequate implementation on this HEAD |
| SUPERSEDED | Replaced by a later canonical decision |
| CONFLICTED | Two final-looking decisions disagree; needs resolution |
| NEEDS_EXTERNAL_VERIFICATION | Requires user/ops/external credential or signed evidence |
| REJECTED_EXCLUDED | Explicitly rejected — not an implementation obligation |

---

## A. Product / UX / Strategy (DEC-0001 …)

| ID | Decision | Category | Source | Status | Evidence / Gap |
|---|---|---|---|---|---|
| DEC-0001 | One product: BLACKDARK Trust OS (not 16 platforms) | PRODUCT | CANONICAL_BINDING, STRATEGIC_CORRECTION | VERIFIED_IMPLEMENTED | `pricing_catalog.py`, `/api/trust-os`, overclaim denylist APIs |
| DEC-0002 | Four value layers only | PRODUCT | CANONICAL_BINDING, TRUST_OS_VALUE_LAYERS | VERIFIED_IMPLEMENTED | trust-os API + docs; tests in heroes/trust suites |
| DEC-0003 | Six heroes only; no 7th product button | PRODUCT | HEROES_STRATEGY_BINDING | VERIFIED_IMPLEMENTED | `api/routers/heroes.py`, heroes tests |
| DEC-0004 | Quiet engines never retail nav | PRODUCT | STRATEGIC_CORRECTION | PARTIALLY_IMPLEMENTED | Intent/strategy APIs exist; full nav audit not exhaustively proven |
| DEC-0005 | Reject FalconAI 16 platforms / 120 caps as product shape | PRODUCT | STRATEGIC_CORRECTION | VERIFIED_IMPLEMENTED | Binding docs + correction API; not marketed as 16 platforms in catalog |
| DEC-0006 | Reject ARENA / FOMO seat counters / Neuro-Design product surface | PRODUCT/UX | STRATEGIC_CORRECTION, DESIGN_SYSTEM | VERIFIED_IMPLEMENTED | Rejected in bindings; no ARENA SKU in `pricing_catalog.py` |
| DEC-0007 | Reject guaranteed 65–70% accuracy marketing | PRODUCT | STRATEGIC_CORRECTION, ZERO_TOLERANCE | VERIFIED_IMPLEMENTED | Anti-hype / overclaim surfaces; ledger stats only |
| DEC-0008 | CSO priority: Excellence→…→Acquisition (not Features-first) | PRODUCT | CSO_PRIORITY_CHAIN | VERIFIED_IMPLEMENTED | `cso_priority_chain.py`, `/priority-chain`, API |
| DEC-0009 | Zero-Tolerance 7 defects binding | PRODUCT/SECURITY | ZERO_TOLERANCE_BINDING | VERIFIED_IMPLEMENTED | `zero_tolerance.py`, tests, pages/API |
| DEC-0010 | D1 Proof-Native Oracle | PRODUCT | PRODUCT_CONSTITUTION | VERIFIED_IMPLEMENTED | certificates / prediction_id / accuracy ledger surfaces + tests |
| DEC-0011 | D2 Contradiction Veto | PRODUCT | PRODUCT_CONSTITUTION | VERIFIED_IMPLEMENTED | conflict/veto paths in oracle/dashboard |
| DEC-0012 | D3 Net-Edge Truth (no false gross profit) | FINANCIAL | PRODUCT_CONSTITUTION | VERIFIED_IMPLEMENTED | `net_edge_truth` + `decision_enrichment` fail-closed on unknown withdrawal; execution/rewalk hardened; tests `test_p0_financial_executability` / XSS fee assertions |
| DEC-0013 | D4 Opportunity Half-Life | PRODUCT | PRODUCT_CONSTITUTION | VERIFIED_IMPLEMENTED | half-life fields + execution half-life gates |
| DEC-0014 | D5 Regime-Conditional Models | AI/ML | PRODUCT_CONSTITUTION | PARTIALLY_IMPLEMENTED | regime modules/tests exist; not all paths proven |
| DEC-0015 | D6 Evidence Pack API | ACQUISITION | PRODUCT_CONSTITUTION | VERIFIED_IMPLEMENTED | evidence/data-room APIs + pages |
| DEC-0016 | D7 English-first Persona Clarity | UX | PRODUCT_CONSTITUTION / SOURCE_BINDING | CONFLICTED → see DEC-0017 | English-first still true; later i18n expands locales |
| DEC-0017 | i18n: English default + 15 locales must ship | UX | MORNING_SESSION / Sat-Sun FINAL | VERIFIED_IMPLEMENTED | `i18n_service` 15 locales + switcher tests; **supersedes pure English-only** for locale support while keeping English default |
| DEC-0018 | D8 Signal Registry (unnamed signals die) | PRODUCT | PRODUCT_CONSTITUTION | VERIFIED_IMPLEMENTED | signal registry modules + tests |
| DEC-0019 | Unified decision engine `unified_multimodal_v1` — no parallel oracle | ARCHITECTURE | PRODUCT_CONSTITUTION, AI_FINANCIAL_MODEL | VERIFIED_IMPLEMENTED | unified oracle path present (architecture audit closed unify) |
| DEC-0020 | Fail-closed on Truth reject / Drift / OOD / sharp conflict | FINANCIAL/AI | PRODUCT_CONSTITUTION, AI model design | PARTIALLY_IMPLEMENTED | gates exist; not every surface proven fail-closed |
| DEC-0021 | Lenses: Prove → Operate → Desk → Room | UX | MORNING_SESSION, TRUST_OS_LENSES | VERIFIED_IMPLEMENTED | lens UX docs + tests (`test_trust_os_lenses_ux` partial failures elsewhere) |
| DEC-0022 | Trust Pulse = live Act/Wait + Why + ledger honesty (not news) | UX | MORNING_SESSION, TRUST_PULSE | VERIFIED_IMPLEMENTED | `trust_pulse.py`, dashboard Trust Pulse, tests |
| DEC-0023 | Sealed landing: brand + “We publish the miss.” + full-bleed + Trust Pulse | UX | DESIGN_SYSTEM, MORNING | PARTIALLY_IMPLEMENTED | Landing exists with Trust Pulse; first-viewport purity not fully certified |
| DEC-0024 | Design: Syne + IBM Plex; cyan `#22D3EE`; reject Inter/purple/gold defaults | UX | DESIGN_SYSTEM | VERIFIED_IMPLEMENTED | `static/css/trust-os.css` imports Syne + IBM Plex; cyan accent used |
| DEC-0025 | Exactly three intentional motions (pulseIn / flipFlash / sharePop) | UX | DESIGN_SYSTEM | VERIFIED_IMPLEMENTED | `tests/test_dec_motion_and_oqs_weights.py` asserts pulseIn/flipFlash/sharePop + keyframes |
| DEC-0026 | Anti-Hype footer on every AI surface | UX | HEROES_STRATEGY | PARTIALLY_IMPLEMENTED | Dashboard/Trust Pulse/anti_hype_mode; not proven on every AI surface |
| DEC-0027 | Companion rail: share/follow/contact/FAQ/how-it-works/status/legal | UX | MORNING_SESSION | PARTIALLY_IMPLEMENTED | Site companion services exist; completeness vs binding list not fully verified |
| DEC-0028 | Glass Box = launch narrative (not 7th product); announce HUMAN_OPS | LAUNCH | HEROES / DEFERRED_HUMAN | NEEDS_EXTERNAL_VERIFICATION | Code/operator APIs exist; announce timing human-deferred |
| DEC-0029 | 60s acceptance grasp bar | LAUNCH | CANONICAL_BINDING | PARTIALLY_IMPLEMENTED | `/api/acceptance/60s` + script; founder H3 confirm deferred |
| DEC-0030 | Time split 60/30/10 heroes/engines/feedback | PRODUCT | HEROES_STRATEGY | NEEDS_EXTERNAL_VERIFICATION | Process rule — not enforceable in code |

---

## B. Pricing / Payments (DEC-0100 …)

| ID | Decision | Category | Source | Status | Evidence / Gap |
|---|---|---|---|---|---|
| DEC-0100 | Ladder: Free $0 / Pro $29 / Desk $49 / Institutional from $3000 open | PAYMENTS | MORNING_SESSION, PRICING_TRUST_OS | VERIFIED_IMPLEMENTED | `pricing_catalog.py` prices match |
| DEC-0101 | Reject Essential/$15, Observer/$9, Explorer/$19, Desk@$199 as Pro ladder | PAYMENTS | MORNING_SESSION | VERIFIED_IMPLEMENTED | Not in catalog |
| DEC-0102 | USD only for self-serve SKUs | PAYMENTS | PAYMENTS_USD_SECURITY | VERIFIED_IMPLEMENTED | `payments_usd.py`, tests |
| DEC-0103 | Never store PAN/CVV; PCI SAQ A hosted checkout | PAYMENTS/SECURITY | PAYMENTS_USD_SECURITY | VERIFIED_IMPLEMENTED | Hosted Lemon/Stripe paths; no PAN storage codepath |
| DEC-0104 | Lemon primary / Stripe alt | PAYMENTS | MORNING / PAYMENTS | VERIFIED_IMPLEMENTED | Billing service dual path |
| DEC-0105 | Institutional Talk-to-us / invoice-wire — not self-serve checkout | PAYMENTS | PRICING_TRUST_OS | VERIFIED_IMPLEMENTED | Catalog institutional CTA Talk to us |
| DEC-0106 | Signup chooses plan; Pro trial only when plan=pro | PAYMENTS/AUTH | PRICING_TRUST_OS | VERIFIED_IMPLEMENTED | Register plan picker + auth register plan field |
| DEC-0107 | Free: 3 certified decisions/day + watermark | PRODUCT | PRICING_TRUST_OS | VERIFIED_IMPLEMENTED | Tier entitlements / oracle usage limits (tests in pricing/trust suites) |
| DEC-0108 | No guaranteed returns language | PRODUCT | PAYMENTS / Anti-Hype | PARTIALLY_IMPLEMENTED | Policy present; residual hype surfaces OPEN (ledger P1-FIN-07) |

---

## C. Auth / Security (DEC-0200 …)

| ID | Decision | Category | Source | Status | Evidence / Gap |
|---|---|---|---|---|---|
| DEC-0200 | Email/password + Google OAuth; no phone/SMS v1 | AUTH | AUTH_IDENTITY / MORNING | VERIFIED_IMPLEMENTED | Auth routers; phone deferred |
| DEC-0201 | MFA TOTP optional for users; admin MFA for privileged | AUTH/SECURITY | AUTH + remediation | VERIFIED_IMPLEMENTED | `/api/auth/mfa/*`; `assert_admin_mfa` in `require_admin` |
| DEC-0202 | Terms acceptance required at register | AUTH | AUTH_IDENTITY | VERIFIED_IMPLEMENTED | Register `accepted_terms` |
| DEC-0203 | Password min 10 + blocked commons | AUTH | AUTH_IDENTITY | VERIFIED_IMPLEMENTED | `identity_service.validate_password` |
| DEC-0204 | Sessions hashed + pepper; HttpOnly cookie sealed | SECURITY | SECURITY_HARDENING / remediation | VERIFIED_IMPLEMENTED | Fernet cookie + pepper hashing |
| DEC-0205 | Production rejects unsealed legacy cookies | SECURITY | Remediation Batch 4 | VERIFIED_IMPLEMENTED | `cookie_to_session_bearer` + tests |
| DEC-0206 | CSRF fail-closed when Origin/Referer both missing (cookie mutators) | SECURITY | Remediation Batch 4 | VERIFIED_IMPLEMENTED | `test_p1_session_hardening` |
| DEC-0207 | No reusable bearer in localStorage from login | SECURITY | Remediation Batch 4 | VERIFIED_IMPLEMENTED | login/profile/reset clear token storage |
| DEC-0208 | Omit auth token from JSON body in production | SECURITY | Remediation Batch 4 | VERIFIED_IMPLEMENTED | `_session_response_body` |
| DEC-0209 | No loopback/localhost admin trust | SECURITY | Remediation Batch 1 / audit P0 | VERIFIED_IMPLEMENTED | `require_admin` / `_local_or_admin` |
| DEC-0210 | Institutional mutations require authentication/authorization | SECURITY | Remediation Batch 1 | VERIFIED_IMPLEMENTED | institutional router deps + tests |
| DEC-0211 | Universe activate-full requires admin | SECURITY | Remediation Batch 1 | VERIFIED_IMPLEMENTED | dashboard Depends(require_admin) |
| DEC-0212 | EXPOSE_B2B_DEMO_KEY gates demo key | SECURITY | SECURITY_HARDENING | VERIFIED_IMPLEMENTED | dashboard b2b gate + tests |
| DEC-0213 | Production guard fails closed on missing secrets | SECURITY | ENV_MATRIX / production_guard | VERIFIED_IMPLEMENTED | tests; override via FAIL_CLOSED flag exists |
| DEC-0214 | Soft Launch forbids live execution + public demo key | SECURITY | production_guard | VERIFIED_IMPLEMENTED | tests |
| DEC-0215 | Login rate limit 10/5min; Redis when available | SECURITY | SECURITY_REMEDIATION | VERIFIED_IMPLEMENTED | `check_login_rate_limit` |
| DEC-0216 | Webhook signatures fail closed when configured | SECURITY | Remediation / payments | VERIFIED_IMPLEMENTED | Stripe/Lemon verify paths + tests |
| DEC-0217 | CSP / security headers shipped | SECURITY | SECURITY_HARDENING | PARTIALLY_IMPLEMENTED | Headers present; `script-src 'unsafe-inline'` weakens XSS posture |
| DEC-0218 | XSS: no unsafe unescaped dynamic HTML | SECURITY | Remediation mission | PARTIALLY_IMPLEMENTED | `dom_escape.js`/`dom_safe.js` + priority template escapes + `test_xss_sink_hardening`; **~151 innerHTML sinks** remain; CSP still `unsafe-inline` |
| DEC-0219 | Softlaunch CLI must not OS-command-taint admin email | SECURITY | PR #54 / tip | VERIFIED_IMPLEMENTED | `scripts/open_softlaunch_env.py` in-process + email metachar reject; `tests/test_softlaunch_no_shell_taint.py` |
| DEC-0220 | Bandit zero HIGH/MEDIUM/LOW on production scan | QUALITY | PR #50 | NEEDS_EXTERNAL_VERIFICATION | Unmerged branch; not proven on this HEAD |
| DEC-0221 | Ruff report 22 findings cleared | QUALITY | PR #51 | NEEDS_EXTERNAL_VERIFICATION | Unmerged branch; not proven on this HEAD |

---

## D. Financial / Execution (DEC-0300 …)

| ID | Decision | Category | Source | Status | Evidence / Gap |
|---|---|---|---|---|---|
| DEC-0300 | Net profit after fees + withdrawal + slippage before “profitable/executable” | FINANCIAL | Constitution D3 + remediation | VERIFIED_IMPLEMENTED | Canonical + `net_edge_truth` + enrichment preserve unknown withdrawal as None/reject |
| DEC-0301 | ToB/mid scans are indicative only | FINANCIAL | Remediation Batch 2 | VERIFIED_IMPLEMENTED | `mark_indicative_only` + tests |
| DEC-0302 | Execution fail-closed on stale quotes | EXECUTION | Remediation Batch 2 | VERIFIED_IMPLEMENTED | `enforce_execution_quote_truth` |
| DEC-0303 | Rewalk must recompute NET EXECUTABLE PROFIT | EXECUTION | Remediation Batch 2 | VERIFIED_IMPLEMENTED | slippage_guard + profit_fee |
| DEC-0304 | Unknown withdrawal fee must not invent 0 | FINANCIAL | Remediation Batch 2/5 | VERIFIED_IMPLEMENTED | `fee_matrix` None; `net_edge_truth._parse_withdrawal_fee_usdt`; `decision_enrichment._truth_withdrawal_fee_usdt` |
| DEC-0305 | fee_matrix is single fee authority | FINANCIAL | Remediation | PARTIALLY_IMPLEMENTED | `cex_dex_arbitrage` mid path uses fee_matrix; residual `DEFAULT_TAKER_FEE` remains in `arbitrage_engine`/`fast_scan`/`trade_simulator` as defaults/fallbacks |
| DEC-0306 | Decimal half-even at net decision boundary | FINANCIAL | Remediation Batch 5 | VERIFIED_IMPLEMENTED | `money_decimal.py` + `money_model` field + tests |
| DEC-0307 | Risk gate + panic stop before orders | EXECUTION | Constitution / risk_manager | VERIFIED_IMPLEMENTED | risk + execution freeze paths |
| DEC-0308 | Live execution off by default / guarded | EXECUTION | production_guard / LIVE flags | VERIFIED_IMPLEMENTED | flags + soft-launch forbid |
| DEC-0309 | OQS weights 40/35/25 (net/liquidity/slip) | FINANCIAL | AI_FINANCIAL_MODEL | VERIFIED_IMPLEMENTED | `tests/test_dec_motion_and_oqs_weights.py` asserts `_CORE_WEIGHTS` 40/35/25 |
| DEC-0310 | Stale data must never show as LIVE | MARKET DATA | ZERO_TOLERANCE #2 | PARTIALLY_IMPLEMENTED | stale guards exist; freshness UX not universally proven |

---

## E. Database / Infra / DevOps (DEC-0400 …)

| ID | Decision | Category | Source | Status | Evidence / Gap |
|---|---|---|---|---|---|
| DEC-0400 | Runtime schema authority = `database.SCHEMA` + `_apply_migrations` | DATABASE | DATABASE_MIGRATIONS | VERIFIED_IMPLEMENTED | `init_db`; Alembic non-runtime |
| DEC-0401 | Do not run competing Alembic path in prod | DATABASE | DATABASE_MIGRATIONS | VERIFIED_IMPLEMENTED | Code + `ARCHITECTURE.md` + `DATABASE_MIGRATIONS.md` agree: runtime = `database.SCHEMA` + `_apply_migrations` |
| DEC-0402 | PG commit/rollback must be real | DATABASE | Remediation Batch 3 | VERIFIED_IMPLEMENTED | adapter + clean PG test |
| DEC-0403 | Strict production requires PostgreSQL | DATABASE | ARCHITECTURE / production_guard | VERIFIED_IMPLEMENTED | guard checks |
| DEC-0404 | Viral HA requires Postgres + Redis + multi-instance + VIRAL_MODE | CLOUD | VIRAL_LAUNCH_CAPACITY | VERIFIED_IMPLEMENTED | production_guard viral_ha checks |
| DEC-0405 | SERVICE_BUS_LOCAL must not silently become prod multi-replica bus | DEVOPS | Remediation Batch 5 | VERIFIED_IMPLEMENTED | `service_bus` fail-closed + tests |
| DEC-0406 | Controlled degradation (429/503), not infinite capacity claims | PERFORMANCE | VIRAL_LAUNCH_CAPACITY | VERIFIED_IMPLEMENTED | honesty flags; capacity claims gated |
| DEC-0407 | Signed Postgres+Redis multi-worker load log required for HA claim | PERFORMANCE | CANONICAL_BINDING / LOAD_TEST_RUN_LOG | PARTIALLY_IMPLEMENTED | Soft Launch Postgres+Redis measured row in `LOAD_TEST_RUN_LOG.md` (1 worker); **not** signed HA multi-worker proof |
| DEC-0408 | CI critical gate must be real (not fake “full suite”) | DEVOPS | Remediation | VERIFIED_IMPLEMENTED | `.github/workflows/ci.yml` renamed/expanded; critical green |
| DEC-0409 | Full tests/ suite must be green for institutional completeness | TESTING | Remediation mission | VERIFIED_IMPLEMENTED | Broader unit suite **530 passed / 0 failed** (4 load/network deselected) on tip |
| DEC-0410 | Sonar AA and CI scanner mutually exclusive | DEVOPS | PR #53 / sonarcloud.yml | VERIFIED_IMPLEMENTED | Workflow policy |
| DEC-0411 | Coverage must be imported into Sonar for institutional gate | COVERAGE | Remediation / PR #57 | NOT_IMPLEMENTED / NEEDS_EXTERNAL | coverage.xml artifact exists; import blocked (AA + user skip) |
| DEC-0412 | Quality gates CodeQL / Sonar / security scans keep green | QUALITY | MORNING_SESSION | PARTIALLY_IMPLEMENTED | CodeQL+security green on tip; Sonar tip QG with coverage import not evidenced |
| DEC-0413 | Microservices optional via Redis bus; monolith OK for soft launch | ARCHITECTURE | MICROSERVICES_ARCHITECTURE | VERIFIED_IMPLEMENTED | service_bus + SERVICE_MODE |

---

## F. Acquisition / Institutional (DEC-0500 …)

| ID | Decision | Category | Source | Status | Evidence / Gap |
|---|---|---|---|---|---|
| DEC-0500 | Institutional Trust before Institutional Scale | ACQUISITION | CANONICAL_BINDING | VERIFIED_IMPLEMENTED | Product posture + APIs |
| DEC-0501 | Acquisition READY only with evidence gates A–L | ACQUISITION | Remediation mission | NOT_IMPLEMENTED | Report verdict **NOT COMPLETE** |
| DEC-0502 | No green-badge optimization (no weaken tests/suppress scanners) | QUALITY | Remediation mission | VERIFIED_IMPLEMENTED | Critical CI truthful; fail-under not set to 0 as final money gate |
| DEC-0503 | Evidence pack / data room for buyers | ACQUISITION | Constitution D6 | VERIFIED_IMPLEMENTED | data-room + evidence surfaces |
| DEC-0504 | Human ops deferred explicitly (Glass Box announce, signed HA, PSP keys, browser ext) | LAUNCH | DEFERRED_HUMAN / Sat-Sun | NEEDS_EXTERNAL_VERIFICATION | Intentionally not code |

---

## G. Rejected / Superseded (not obligations)

| ID | Decision | Disposition |
|---|---|---|
| DEC-R001 | FalconAI 16 platforms product map | REJECTED_EXCLUDED |
| DEC-R002 | FalconAI BD-DEC-0031 as sole canonical map | SUPERSEDED by CANONICAL_BINDING |
| DEC-R003 | ARENA / Viral Community Engine as product | REJECTED_EXCLUDED |
| DEC-R004 | English-only with zero locale switcher | SUPERSEDED by DEC-0017 |
| DEC-R005 | Desk priced far above $49 / Pro@$49 neural ladder | SUPERSEDED by DEC-0100 |
| DEC-R006 | Loopback admin trust for soft launch | SUPERSEDED by DEC-0209 |
| DEC-R007 | Dual fee tables as independent authorities | SUPERSEDED by DEC-0305 (partially realized) |
| DEC-R008 | Alembic as production runtime authority | SUPERSEDED by DEC-0400 |
| DEC-R009 | CI job named “Full Test Suite” meaning full tree | SUPERSEDED by DEC-0408 |
| DEC-R010 | Institutional / Acquisition READY claims pre-evidence | SUPERSEDED by DEC-0501 NOT COMPLETE |

---

## H. Decision conflicts

| Conflict ID | Earlier | Later / Canonical | Class |
|---|---|---|---|
| CF-01 | English-only public UI (Heroes/SOURCE) | English default + 15 locales (Sat/Sun / Morning) | **RESOLVED** → DEC-0017 canonical |
| CF-02 | ARCHITECTURE.md “Alembic (+ _apply_migrations)” | DATABASE_MIGRATIONS.md single runtime authority | **RESOLVED** — ARCHITECTURE.md updated to single runtime authority |
| CF-03 | net_edge_truth `withdrawal or 0.0` | fee_matrix unknown→None fail-closed | **RESOLVED** — net_edge_truth + decision_enrichment preserve None / reject |
| CF-04 | Sonar AA-only policy (PR #53) vs institutional coverage-import requirement | Both “final” in different eras | **NEEDS USER DECISION** (user skipped AA disable) |
| CF-05 | Open PRs #50/#51/#54/#57 slices vs hardening tip | Softlaunch (#54 intent) on tip; Ruff cherry-picks partial; Bandit #50 not merged | **PARTIALLY RECONCILED** — #54 intent landed; #50/#51 still open |

---

## I. Counts (this register)

| Bucket | Count |
|---|---|
| FINAL obligations catalogued (DEC-0001–0504 material set) | **91** |
| REJECTED/SUPERSEDED excluded | **10** |
| VERIFIED_IMPLEMENTED | **69** |
| PARTIALLY_IMPLEMENTED | **14** |
| IMPLEMENTED_BUT_UNVERIFIED | **0** |
| NOT_IMPLEMENTED | **2** |
| NEEDS_EXTERNAL_VERIFICATION | **6** (includes DEC-0411 dual tag) |
| CONFLICTED (open DEC rows) | **1** (DEC-0016 → see DEC-0017) |
| Unresolved CF-* needing user | **CF-04** (Sonar AA/token); CF-05 Bandit #50 still open |
