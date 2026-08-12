# CURRENT PRODUCT TRUTH BASELINE

**Program:** BLACKDARK 95+ Independent Re-Certification  
**Phase:** ZERO — Current Main Reconciliation (authoritative remediation register)  
**Canonical main SHA:** `e00971a034043046f4eefd3df1807c7b59101859`  
**Reconciled at:** 2026-08-12  
**Prior audit tip:** Capability Reality Audit against the same SHA (`e00971a`)  
**Note:** PR #71 (`cursor/institutional-hardening-120d` @ `4e28710`) was **NOT merged** to main at reconciliation time — its Critical/High honesty fixes are therefore **STILL_PRESENT** on canonical main until landed here.

---

## RULE ZERO OUTCOME

| Previous finding | Status on `e00971a` | Evidence |
|---|---|---|
| SSO demo default `ENTERPRISE_SSO_DEMO=true` | **STILL_PRESENT** | `enterprise_sso.py` demo branch + empty code accepted |
| `product_complete: True` without live IdP | **STILL_PRESENT** | `sso_status` / callback always True |
| `scim_ready: True` without SCIM API | **STILL_PRESENT** | configure/status hardcode True; no `scim.py` |
| SAML `BD_SAML_AUTHN_*` stub claimed product-complete | **STILL_PRESENT** | `build_sso_authorize_url` SAML branch |
| Soft Launch waives Postgres/billing in production | **STILL_PRESENT** | `production_guard.py` `soft_launch` OR-bypass; no `INSTITUTIONAL_LAUNCH` force-off |
| Canonical Data Layer | **STILL_PRESENT (MISSING)** | no `canonical_data*` module |
| Decision Graph | **STILL_PRESENT (MISSING)** | no `decision_graph*` |
| OMS (≠ execution_engine) | **STILL_PRESENT (MISSING)** | `execution_engine.py` only |
| Funding depth/slippage = 0 | **STILL_PRESENT** | `calculate_funding_arbitrage` uses `_slippage_buffer_usdt(..., 0.0, ...)` |
| CEX↔DEX executable honesty | **PARTIALLY_FIXED** | `bd_platform/cex_dex_arbitrage.py` marks `indicative=True`, `executable=False` |
| Fee unknown → invent DEFAULT | **FIXED** (core path) | `fee_matrix.py` returns `None`; arb skips |
| Cross/triangular/spot-futures depth walk | **FIXED** (strong) | `arbitrage_engine.py` walk asks/bids |
| Executable edge + slip rewalk | **FIXED** (strong) | `executable_edge_truth.py`, `slippage_guard.py` |
| Stale quote guard (exec path) | **PARTIALLY_FIXED** | `stale_price_guard` on exec; stream hub age gate exists; no universal LIVE label proof |
| Uncalibrated confidence as probability | **STILL_PRESENT** | no `confidence_calibration` authority; enrichment “calibrated_prior” heuristic |
| Liquidity / contagion / flash-crash / SC risk / stress | **STILL_PRESENT (MISSING)** | only `risk_manager.py` / `execution_risk_score.py` |
| Institutional Memory + Continuous Learning | **STILL_PRESENT (MISSING)** | absent |
| Real SSO IdP token verification | **STILL_PRESENT** | no signature/JWKS verify on callback |
| Live billing / PSP proof | **EXTERNAL** | unchanged — not repo-closable |
| Sonar main New Code post-baseline increment | **STILL_PRESENT** | main still `2026.08.12`; PR71 had `2026.08.12.1` unmerged |
| False WOW product_complete on viral boards | **SUPERSEDED / ACCEPT with scrutiny** | surfaces exist with real modules; claims must stay scoped to those surfaces |
| AuthN/AuthZ demo bypass via Soft Launch | **STILL_PRESENT** (production path risk) | Soft Launch production bypass |

### NEW issues discovered on current main (not emphasized in older DD register)

| ID | Severity | Finding |
|---|---|---|
| N-DATA-01 | CRITICAL | No canonical semantic model / provenance layer — intelligence paths ingest ad-hoc dicts |
| N-STREAM-01 | HIGH | `price_stream_engine` emits ticks without explicit `freshness_class` / anti-stale-as-LIVE contract at fanout |
| N-FUND-01 | HIGH | Funding arb claims net yield with zero depth-derived slippage |
| N-DEC-01 | HIGH | No queryable Decision Graph linking evidence→decision→outcome→learning |
| N-OMS-01 | HIGH | No OMS lifecycle; execution_engine must not be relabeled OMS |
| N-RISK-01 | HIGH | Missing liquidity/correlation/contagion/flash-crash/SC/stress modules wired to gates |
| N-SSO-01 | CRITICAL | Default-on demo SSO + false complete/SCIM claims (reconfirmed) |
| N-SL-01 | CRITICAL | Soft Launch can waive institutional production requirements |

---

## REMEDIATION REGISTER (ordered)

### P0 — Critical / High (close immediately)

1. **R-SSO-01** — Demo SSO opt-in only; never `product_complete` on demo; `scim_ready=False`; SAML scaffolding honesty; live-ready requires OIDC secret  
2. **R-SL-01** — `INSTITUTIONAL_LAUNCH` forces Soft Launch off; guard `enterprise_sso_demo_off`  
3. **R-CLAIM-01** — Eliminate false institutional `product_complete` / SCIM claims  
4. **R-DATA-01** — Ship Canonical Data Layer (schema, normalize, provenance, freshness, quality)  
5. **R-STREAM-01** — Streaming truth: stale cannot appear as LIVE  
6. **R-FUND-01** — Funding depth + slippage; no zero-slippage executable yield  
7. **R-CEXDEX-01** — Keep/strengthen CEX↔DEX indicative≠executable gates + regression  

### P1 — Foundations (before WOW expansion)

8. **R-RISK-01** — Liquidity, correlation/contagion, flash-crash, smart-contract, stress testing  
9. **R-DEC-01** — Decision Graph + confidence typing/calibration + Institutional Memory + Learning controls  
10. **R-OMS-01** — Real OMS state machine (INTENT→…→RECONCILE)  
11. **R-B2B-01** — Reporting / alert orchestration / SLA instrumentation honesty  
12. **R-OBS-01** — Observability + resilience evidence expansion  

### Explicitly DEFERRED until P0/P1 closed

- New viral/WOW surfaces  
- White-label  
- Feature-count expansion  

### EXTERNAL (must remain EXTERNAL — never fake PASS)

- Live PSP purchase evidence  
- Counsel IP/regulatory opinions  
- DR restore drill artifacts  
- Branch protection / Code Scanning UI screenshots  
- Pentest / WAF vendor reports  
- Full JWKS IdP signature verification in production IdP edge (repo can require live OIDC config + refuse demo; cryptographic verify may need operator JWKS)

---

## CAPABILITY SNAPSHOT @ `e00971a` (reconciled)

| Area | Verdict |
|---|---|
| Fee fail-closed matrix | STRONG |
| Cross / triangular / spot-futures depth | STRONG |
| Executable edge honesty helpers | STRONG |
| CEX-DEX labeling | PARTIAL (honest indicative; not depth-executable) |
| Funding arb | WEAK (zero depth slippage) |
| Canonical data | MISSING |
| Streaming institutional grade | PARTIAL |
| Decision brain / graph / calibration / memory | MISSING / PARTIAL enrichment only |
| Risk intelligence breadth | PARTIAL (basic risk_manager) |
| OMS | MISSING |
| Enterprise SSO / SCIM | FALSE-COMPLETE / STUB |
| Soft Launch vs institutional | UNSAFE defaults |
| WOW / Trust surfaces | AHEAD of foundations (do not expand first) |

---

## TARGET ARCHITECTURE (coherent — single product core)

```
Providers/Adapters
    → Canonical Data Layer (normalize + provenance + freshness + quality)
        → Streaming Truth (LIVE | STALE | DEGRADED | UNKNOWN)
            → Market / Portfolio / Risk Intelligence
                → Decision Graph (evidence → hypothesis → decision → action → outcome → learning)
                    → Execution Truth (indicative vs executable)
                        → OMS (lifecycle) → Venues
            → Observability / Audit / B2B Reporting
```

Segments (Retail / Pro / Whale / B2B / Fund / Institutional) share one core; differ by policy, capital, RBAC, and evidence packs — not fork cores.

---

## SCORING NOTE (pre-remediation)

This baseline does **not** claim ≥95. Independent re-audit after remediation must earn the score. Fabrication prohibited.

**Pre-remediation institutional readiness:** NOT READY  
**Critical/High open on main at Phase Zero:** >0 (SSO/Soft-Launch/Claims/Data/Funding/Decision/OMS/Risk)

---

## CHANGE CONTROL

Every subsequent commit in this program must reference finding IDs above.  
Do not remediate findings marked FIXED without re-verification.  
Do not expand WOW until P0 register rows are CLOSED with tests.

---

## REMEDIATION PROGRESS (this branch)

| ID | Status | Evidence |
|---|---|---|
| R-SSO-01 / N-SSO-01 | **CLOSED on branch** | `enterprise_sso.py` demo opt-in default false; `scim_ready=False`; SAML scaffolding honesty; live-ready requires OIDC secret |
| R-SL-01 / N-SL-01 | **CLOSED on branch** | `production_guard.py` `INSTITUTIONAL_LAUNCH` forces Soft Launch off; `enterprise_sso_demo_off` |
| R-CLAIM-01 | **CLOSED on branch** | `product_complete` only when live-ready OIDC; API callback default code no longer `demo_sso_ok` |
| R-DATA-01 / N-DATA-01 | **CLOSED (foundation)** | `canonical_data_layer.py` + tests |
| R-STREAM-01 / N-STREAM-01 | **CLOSED (foundation)** | `stream_freshness_truth.py` wired into `price_stream_engine.emit_tick` |
| R-FUND-01 / N-FUND-01 | **CLOSED on branch** | Funding requires depth; zero-slippage executable path removed |
| R-CEXDEX-01 | **REGRESSION GUARDED** | remains indicative≠executable |
| R-RISK-01 / N-RISK-01 | **CLOSED (foundation)** | `risk_intelligence.py` |
| R-DEC-01 / N-DEC-01 | **CLOSED (foundation)** | `decision_graph.py` + `confidence_truth.py` + `institutional_memory.py` |
| R-OMS-01 / N-OMS-01 | **CLOSED (foundation)** | `oms.py` lifecycle ≠ execution_engine |
| R-B2B-01 | **CLOSED (foundation)** | `b2b_institutional_ops.py` |
| Sonar post-baseline `2026.08.12.1` | **INCLUDED** | version bump for Previous-version New Code increment |

**Still open for later loops (not claimed 95+):** full IdP JWKS crypto verify, live PSP, chaos/DR EXTERNAL, wholesale adoption of canonical layer across every scanner path, Whale large-capital proof, independent clean-room re-audit score.
