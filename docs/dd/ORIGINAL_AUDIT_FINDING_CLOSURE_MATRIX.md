# ORIGINAL AUDIT FINDING CLOSURE MATRIX

**Original audit context:** BLACKDARK Capability Reality Audit  
**Prior tip audited:** `e00971a034043046f4eefd3df1807c7b59101859`  
**Remediation PR:** #72  
**Candidate tip:** `819ed7bb5dee01ef420d2b18379dcfe62bd1cc7b`  
**Rule:** No finding may disappear via rename/de-scope/doc deletion.

| ID | ORIGINAL FINDING | ORIGINAL STATUS | ROOT CAUSE | CLOSURE IMPLEMENTATION | FILES | TESTS / NEGATIVE | CURRENT |
|---|---|---|---|---|---|---|---|
| O-SSO-01 | ENTERPRISE_SSO_DEMO default true; empty code demo | STILL_PRESENT @ e00971a | Demo-as-default | Default false; demo requires opt-in + code | `enterprise_sso.py` | `test_institutional_honesty_closure` | CLOSED |
| O-SSO-02 | product_complete without IdP verify | STILL_PRESENT | Claim without crypto | JWKS id_token verify required | `oidc_jwks_verify.py`, `enterprise_sso.py` | tampered/expired/wrong aud | CLOSED |
| O-SSO-03 | scim_ready True without SCIM | STILL_PRESENT | False complete | Real SCIM Users/Groups | `scim_service.py`, institutional router | CRUD + HTTP | CLOSED |
| O-SSO-04 | BD_SAML_AUTHN stub claimed complete | STILL_PRESENT | Scaffold SAML | Real AuthnRequest + signed Response | `saml_service.py` | signature/audience/expiry | CLOSED |
| O-SL-01 | Soft Launch waives Postgres/billing in prod | STILL_PRESENT | Demo waiver | INSTITUTIONAL_LAUNCH force-off Soft Launch | `production_guard.py` | honesty tests | CLOSED |
| O-DATA-01 | No Canonical Data Layer | MISSING | Architecture gap | Layer + adoption on critical arb/stream | `canonical_data_layer.py`, `canonical_adoption.py` | stale-as-live, normalize | CLOSED |
| O-STREAM-01 | Stale can appear live | PARTIAL | No freshness class | stream_freshness_truth + institutional streaming | `stream_freshness_truth.py`, `streaming_institutional.py` | forge LIVE blocked | CLOSED |
| O-FUND-01 | Funding slippage_bps=0.0 | STILL_PRESENT | Missing depth | Depth required; fail closed | `arbitrage_engine.py` | no books → [] | CLOSED |
| O-CEXDEX-01 | CEX-DEX partial/indicative only | PARTIAL | Mid-price only | Depth/impact executable gate + SC risk on exec | `cex_dex_arbitrage.py`, `cex_dex_executor.py` | blocks indicative | CLOSED |
| O-FEE-01 | Unknown fee → invent | FIXED prior | — | fee_matrix None | `fee_matrix.py` | unknown→None | CLOSED |
| O-EXEC-01 | Indicative as executable | PARTIAL | Labeling | executable_edge_truth + risk gate | `executable_edge_truth.py` | financial tests | CLOSED |
| O-OMS-01 | execution_engine ≠ OMS | MISSING | Missing OMS | Real OMS lifecycle + cancel/replace | `oms.py` | state machine tests | CLOSED |
| O-RISK-01 | Missing full risk domains | MISSING/PARTIAL | Incomplete | risk_intelligence + flash/stress/micro | multiple | fail-closed unknowns | CLOSED |
| O-CORR-01 | Correlation/contagion missing | MISSING | — | correlation_contagion_risk | `risk_intelligence.py` | unit | CLOSED |
| O-FLASH-01 | Flash-crash missing | MISSING | — | flash_crash_protection | `flash_crash_protection.py` | block signals | CLOSED |
| O-SC-01 | Smart-contract risk missing | MISSING | — | smart_contract_risk + CEX-DEX gate | `risk_intelligence.py` | unknown audit fail-closed | CLOSED |
| O-DEC-01 | Decision Graph missing | MISSING | — | decision_graph + engine | `decision_graph.py`, `decision_intelligence_engine.py` | append-only | CLOSED |
| O-CONF-01 | Uncalibrated as probability | STILL_PRESENT | Heuristic misuse | confidence_truth typing | `confidence_truth.py` | heuristic≠probability | CLOSED |
| O-MEM-01 | Institutional memory missing | MISSING | — | institutional_memory | `institutional_memory.py` | append-only | CLOSED |
| O-LEARN-01 | Continuous learning missing | MISSING | — | continuous_learning guards | `continuous_learning.py` | look-ahead forbidden | CLOSED |
| O-WHALE-01 | Whale evidence open | OPEN | No measured proof | whale_execution_evidence | `whale_execution_evidence.py` | multi-venue depth | CLOSED |
| O-B2B-01 | B2B partial | PARTIAL | Thin surface | b2b ops + alerts ack/silence/dedupe | `b2b_institutional_ops.py` | unit | CLOSED |
| O-WL-01 | White label missing/partial | PARTIAL | — | white_label | `white_label.py` | brand export | CLOSED |
| O-PORT-01 | Portfolio AI partial | PARTIAL | — | portfolio_intelligence | `portfolio_intelligence.py` | fail-closed unknown notional | CLOSED |
| O-100-01 | 100 platforms / 105 assets claim partial | PARTIAL | Catalog vs live | config universe + regression gate | `config.py`, prohibited tests | ≥100/≥105 | CLOSED |
| O-CLAIM-01 | False COMPLETE claims | PRESENT | Honesty drift | SSO/SCIM/SAML honesty + plan_audit 46/46 | multiple | honesty suite | CLOSED |
| O-MOCK-01 | Production mock sentiment/macro | PRESENT | Silent fallback | Prod forbids mock sentiment/macro | `sentiment_engine.py`, `macro_correlations.py` | prod raises | CLOSED |
| O-EXT-PSP | Live PSP proof | EXTERNAL | Credentials | Subscription code complete; live proof EXTERNAL | billing modules | — | EXTERNAL |
| O-EXT-COUNSEL | Legal counsel | EXTERNAL | Legal | Repo license/SBOM support only | docs | — | EXTERNAL |
| O-EXT-DR | Live DR drill | EXTERNAL | Infra | Runbooks/impl repo-side; live drill EXTERNAL | ops docs | — | EXTERNAL |

## Counts

| Metric | Value |
|---|---|
| ORIGINAL MATERIAL FINDINGS (repo-fixable in this matrix) | 27 |
| CLOSED WITH EVIDENCE | 27 |
| RECURRENT | 0 |
| UNVERIFIED | 0 |
| SILENTLY DE-SCOPED | 0 |
| EXTERNAL ONLY | 3 (PSP, counsel, live DR) |

## Recurrence contract

If a clean-room auditor rediscovers any CLOSED finding as STILL_PRESENT on the candidate SHA, that finding becomes RECURRENT and remediation must continue automatically.
