# BLACKDARK Final DD Findings Register — RC1

**RC1 SHA:** `de6537fb29d6bc6203d58b572924db55b9c74d53`  
**Audit mode:** READ-ONLY — no remediation during DD  

| FINDING_ID | CONTROL_ID | DOMAIN | TITLE | CLASSIFICATION | SEVERITY | EVIDENCE | ROOT_CAUSE | BUSINESS_IMPACT | ACQUISITION_IMPACT | REMEDIATION_REQUIRED | EFFORT | OWNER_TYPE | PRE_CLOSE_OR_POST_CLOSE |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| F-ARC-02 | D2-07 | Architecture | ARCHITECTURE.md denies HashiCorp Vault while compose ships vault -dev | CRITICAL_REMEDIATION | MEDIUM | E2: ARCHITECTURE.md vs docker-compose.yml vault service | Documentation drift | Buyer confusion on secrets architecture | Pre-close doc honesty condition | Align docs with shipped compose **or** remove non-prod vault from default path and document Fernet-only | S | Engineering | PRE_CLOSE |
| F-ARC-01 | D2-06 | Architecture | Dual oracle decision paths (oracle_unified vs ai_oracle) | POST_CLOSE_REMEDIATION | MEDIUM | E2: oracle_unified.py, ai_oracle.py; FULL_ARCHITECTURE_AUDIT H1 | Historical dual evolution | Integration & reasoning complexity | Increases integration risk | Unify or formally contract-bound dual modes with tests | L | Engineering | POST_CLOSE |
| F-FIN-01 | D2-03 / D5-06 | Financial | Dual float (arbitrage_engine) vs Decimal (profit_fee_algorithms) money paths | POST_CLOSE_REMEDIATION | MEDIUM | E2/E3: arbitrage_engine float fees; money_decimal in profit_fee; tests pass fail-closed None | Incomplete Decimal migration | Sub-cent divergence risk; not proven false executable profit | Non-blocking if monitored | Route arb fee math through money_decimal | M | Engineering | POST_CLOSE |
| F-FIN-02 | D5-10 | Financial | Directional Truth enrichment soft-pass (reject Forced False) | ACCEPTED_RISK_CANDIDATE | LOW | E2: decision_enrichment directional_advisory | Advisory UX design | User may misread advisory as executable if UI unclear | Disclosure risk | Ensure UI labels advisory; optional harden | S | Product/Eng | POST_CLOSE |
| F-FIN-03 | D5-14 | Financial | DeFi gas cost path separate; freshness vendor-dependent | POST_CLOSE_REMEDIATION | LOW | E2: gas_oracle / defi_arbitrage_engine | Domain separation | Stale gas → bad DeFi edge if live | Limited if live DeFi off by default | Freshness SLAs + fail-closed on stale gas | M | Engineering | POST_CLOSE |
| F-SEC-01 | D6-02 | Security | CSP_NONCE_MODE=false emergency reopen of script-src unsafe-inline | ACCEPTED_RISK_CANDIDATE | MEDIUM | E2: security_middleware rollback branch | Break-glass design | XSS surface if mis-set in prod | Ops control condition | Prod config attestation: nonce ON | XS | Ops | PRE_CLOSE (attestation) |
| F-SEC-02 | D6-03 | Security | style-src 'unsafe-inline' residual | ACCEPTED_RISK_CANDIDATE | LOW | E2: CSP header | CSS convenience | CSS injection only if HTML injection exists | Low | Tighten styles post-close | S | Engineering | POST_CLOSE |
| F-SEC-03 | D6-11 | Security | setup_telegram.py writes TELEGRAM_BOT_TOKEN to .env cleartext | POST_CLOSE_REMEDIATION | LOW | E2: setup_telegram.py | Legacy setup UX | Secret-at-rest weaker than Stripe private-file pattern | Low if script unused in prod | Align with private 0600 secret file pattern | S | Engineering | POST_CLOSE |
| F-SEC-04 | D6-23 | Security | CORS matrix not fully enumerated this DD | ENHANCEMENT | INFORMATIONAL | E2 sample only | Scope limit | Unknown edge CORS misconfig | Low | Explicit CORS allowlist review | S | Engineering | POST_CLOSE |
| F-CQ-01 | D2-14 / D3-08 | Code Quality | Oversized dashboard.py module | POST_CLOSE_REMEDIATION | MEDIUM | E2: large dashboard.py; sonar exclusions | Monolith growth | Maintainability / review cost | Integration friction | Modularize routers/services | L | Engineering | POST_CLOSE |
| F-CQ-02 | D3-04 | Code Quality | Bandit LOW try/except pass backlog (112 LOW) | ENHANCEMENT | LOW | E3: Bandit LOW=112 | Defensive coding style | May hide errors | Low | Triage material B110 in money/auth paths | M | Engineering | POST_CLOSE |
| F-REL-01 | D8-05 | Reliability | Full dependency chaos (DB down / multi-fault) not executed | ENHANCEMENT | LOW | NOT_TESTED chaos | DD scope | Unknown failure modes under compound outage | Condition for deeper DD | Chaos test pack | M | SRE | POST_CLOSE |
| F-PERF-01 | D9-06 | Performance | Signed HA load evidence not remeasured on RC1 SHA | EXTERNAL_EVIDENCE | LOW | E1/E3 prior tip 9bae7c4 | Time/cost | Same-SHA purity gap | Disclose applicability | Optional re-run on RC tag | S | SRE | POST_CLOSE |
| F-OPS-01 | D10-08 / D14-05 | Operations | Runbooks thin for 03:00 autonomous ops | CRITICAL_REMEDIATION | MEDIUM | E1: short RUNBOOK.md | Founder-centric ops | Buyer ops risk | Pre-close handover pack | Expand incident/deploy/rollback runbooks | M | Ops/Eng | PRE_CLOSE |
| F-OPS-02 | D14-04 | Observability | Limited first-class metrics/tracing | POST_CLOSE_REMEDIATION | MEDIUM | E2 inventory | Early-stage SRE | Detectability of incidents | Post-close | Prometheus/OTel baseline | L | SRE | POST_CLOSE |
| F-OPS-03 | D14-06 | Observability | Pager / on-call integration unclear | POST_CLOSE_REMEDIATION | LOW | E2 weak evidence | Missing tooling | Slow incident response | Post-close | Wire alerting to pager | S | Ops | POST_CLOSE |
| F-SC-01 | D12-04 | Supply Chain | No formal SBOM (CycloneDX/SPDX) artifact | CRITICAL_REMEDIATION | MEDIUM | E2: absent SBOM | Not produced | Buyer supply-chain DD friction | Pre-close or immediate post-close condition | Generate SBOM in CI | S | Eng/DevSecOps | PRE_CLOSE |
| F-SC-02 | D12-05 | Supply Chain | GitHub Actions often pinned by major tag not immutable SHA | POST_CLOSE_REMEDIATION | LOW | E2: actions/checkout@v4 | Convenience | Action supply-chain risk | Post-close | Pin actions to SHA | S | DevSecOps | POST_CLOSE |
| F-SC-03 | D12-06 | Supply Chain | ML artifacts / training external (DEC-0014) | EXTERNAL_EVIDENCE | LOW | E1/E2 DEC-0014 | Training outside repo | Model provenance incomplete | Disclosure | Inventory model provenance | S | Eng/Founder | POST_CLOSE |
| F-IP-01 | D13-01 | License/IP | No formal dependency license inventory | CRITICAL_REMEDIATION | MEDIUM | E2: absent license report | Not produced | Legal DD blocker risk | Pre-close counsel pack | Generate license report + counsel review | M | Eng + Counsel | PRE_CLOSE |
| F-IP-02 | D13-06 | License/IP | NOTICE/attribution completeness uncertain | POST_CLOSE_REMEDIATION | LOW | E2 incomplete | Incomplete hygiene | Attribution gaps | Post-close | NOTICE file completeness | S | Eng | POST_CLOSE |
| F-COMP-01 | D15-04 | Compliance Tech | Retention/deletion not a full privacy program | POST_CLOSE_REMEDIATION | MEDIUM | E2 partial retention | Product stage | Privacy program gap | Counsel-guided | Privacy technical controls roadmap | L | Eng + Counsel | POST_CLOSE |
| F-COMP-02 | D15-06 | Compliance Tech | Admin audit trail not SIEM-grade | POST_CLOSE_REMEDIATION | LOW | E2 partial logs | Stage | Forensics gap | Post-close | Immutable admin audit log | M | Eng | POST_CLOSE |
| F-XFER-01 | D14-07 / D16-07 / KG-10 | Transferability | Founder/key-person dependency for secrets, Glass Box, PSP, 60s, Sonar admin | CRITICAL_REMEDIATION | HIGH | E1: DEFERRED_HUMAN_STEPS; Glass Box runbook; cert external list | Single-operator knowledge | Acquirer cannot operate autonomously at close | **Material condition** | Handover pack: secrets map, runbooks, account ownership, tabletop | L | Founder + Ops | PRE_CLOSE |
| F-XFER-02 | D16-03 | Transferability | Ops playbook hardcodes founder email mopayment1@gmail.com | CRITICAL_REMEDIATION | MEDIUM | E2: FREE_HUMAN_OPS_PLAYBOOK_AR.md | Founder-centric docs | Blocks clean transfer narrative | Pre-close | Parameterize owner contacts | XS | Eng/Founder | PRE_CLOSE |
| F-TEST-01 | D11-05 / D11-06 | Testing/SDLC | Sonar main QG failed (28.3% new coverage) while PR QG OK — MIXED tool/baseline vs suite scope | EXTERNAL_EVIDENCE | MEDIUM | E3: CI run 31584454484 QG fail; coverage.xml imported; PR analyses historically OK | Main New Code window ≠ PR diff; coverage inclusions narrowed | Scanner gate red on main | **Not classified as financial/security product defect**; admin New Code setting required for meaningful main QG | Admin: New Code=Previous version; re-analyze — **do not fake by emptying coverage** | S | Founder/Admin | PRE_CLOSE |
| F-TEST-02 | D11-08 | Testing/SDLC | Full suite sensitive to env pollution (DATABASE_URL/Redis) | ENHANCEMENT | LOW | E3 prior + clean-env 603 pass | Global client caching | Flaky CI/local noise | Low | Harden fixtures isolation | S | Eng | POST_CLOSE |
| F-EXT-01 | D4-09 | External | Live PSP / test purchase not evidenced | EXTERNAL_EVIDENCE | HIGH | E0/E1 deferred human | No live credentials in DD | Cannot verify paid path | Condition | Founder PSP setup evidence | — | Founder | PRE_CLOSE |
| F-EXT-02 | D6-15 | External | Main Code Scanning open alert counts unverifiable (API 403) | EXTERNAL_EVIDENCE | HIGH | E3 API 403 | Token scope | Unknown residual CodeQL alerts | Condition | Founder UI screenshot open=0 @ RC1 | — | Founder | PRE_CLOSE |
| F-EXT-03 | D7-07 | External | Backup/restore drill not evidenced | EXTERNAL_EVIDENCE | MEDIUM | NOT_TESTED | No DR drill | Data loss recovery unproven | Condition | Restore tabletop + artifact | — | Ops | PRE_CLOSE or immediate POST |
| F-EXT-04 | D10-06 | External | Branch protection rules not verifiable | EXTERNAL_EVIDENCE | MEDIUM | API 403 | Permissions | Governance unknown | Condition | Export branch protection settings | — | Founder/Admin | PRE_CLOSE |
| F-EXT-05 | D13-03 / KG-08 | External | Counsel license/IP opinion absent | EXTERNAL_EVIDENCE | HIGH | No counsel letter | Legal scope | IP risk unknown | Condition | Qualified counsel review | — | Counsel | PRE_CLOSE |
| F-EXT-06 | D15-07 | External | Regulatory posture (advice/marketing) needs counsel | EXTERNAL_EVIDENCE | MEDIUM | Product is financial-adjacent | Legal | Mis-selling/regulatory risk | Condition | Counsel memo | — | Counsel | PRE_CLOSE |
| F-EXT-07 | D16-02 | External | Cloud/DNS/vendor account ownership inventory absent | EXTERNAL_EVIDENCE | HIGH | Not provided | Handover gap | Cannot transfer control plane | Condition | Account ownership schedule | — | Founder | PRE_CLOSE |
| F-EXT-08 | D16-09 / F-TEST-01 | External | SonarCloud New Code admin action required | EXTERNAL_EVIDENCE | MEDIUM | Main QG fail 28.3% | Project setting | Main QG not institutionally meaningful | Condition | Set New Code=Previous version; confirm QG | — | Founder/Admin | PRE_CLOSE |
| F-EXT-09 | — | External | WAF / pentest / CDN evidence absent | EXTERNAL_EVIDENCE | MEDIUM | Deferred human | Not performed | Unknown residual exploit | Condition | Pentest report or scoped waiver | — | Founder/Vendor | PRE_CLOSE or waiver |
| F-EXT-10 | — | External | Founder H3 / 60s acceptance walkthrough absent | EXTERNAL_EVIDENCE | LOW | DEC-0029 external | Process | Product grasp unverified by founder ritual | Soft condition | Recorded walkthrough | — | Founder | PRE_CLOSE optional |

## Counts

| Classification | Count |
|---|---|
| BLOCKER | **0** |
| CRITICAL_REMEDIATION | **6** (F-ARC-02, F-OPS-01, F-SC-01, F-IP-01, F-XFER-01, F-XFER-02) |
| POST_CLOSE_REMEDIATION | **14** |
| ACCEPTED_RISK_CANDIDATE | **3** |
| EXTERNAL_EVIDENCE | **12** (incl. F-TEST-01, F-PERF-01, F-SC-03, F-EXT-*) |
| ENHANCEMENT | **4** |
| FALSE_POSITIVE | **0** |

| Severity (defects only) | Count |
|---|---|
| CRITICAL | **0** |
| HIGH | **1** (F-XFER-01) |
| MEDIUM | **12** |
| LOW | **10** |
| INFORMATIONAL | **1** |
