# BLACKDARK Final Remediation Register — RC1

**RC1 SHA:** `de6537fb29d6bc6203d58b572924db55b9c74d53`  
**Rule:** This is the **ONE** canonical remediation list from RC1 DD. Future fixes must map to `FINDING_ID`.  
**Rule:** No production remediation was performed during this audit.

## Pre-close mandatory (conditions for PROCEED WITH CONDITIONS)

| FINDING_ID | Action | Effort | Owner |
|---|---|---|---|
| F-XFER-01 | Deliver technical handover pack: secrets map, account ownership, deploy/rollback, Glass Box/PSP runbooks, tabletop without founder | L | Founder + Ops |
| F-XFER-02 | Remove hardcoded founder email from ops playbooks; parameterize owner contacts | XS | Eng/Founder |
| F-OPS-01 | Expand RUNBOOK to incident/deploy/rollback/DR sufficient for on-call | M | Ops/Eng |
| F-ARC-02 | Resolve Vault documentation vs compose contradiction | S | Eng |
| F-SC-01 | Publish CI SBOM (CycloneDX or SPDX) for lockfiles | S | DevSecOps |
| F-IP-01 | Generate dependency license inventory + engage counsel | M | Eng + Counsel |
| F-EXT-01 | Evidence live PSP configuration / test purchase (or Soft Launch-only sale disclosure) | — | Founder |
| F-EXT-02 | GitHub Code Scanning UI: open Critical/High/Medium = 0 on RC1 SHA | — | Founder |
| F-EXT-04 | Export/prove branch protection & required checks | — | Founder/Admin |
| F-EXT-05 | Counsel IP/license opinion | — | Counsel |
| F-EXT-06 | Counsel memo on financial-advice/marketing boundaries | — | Counsel |
| F-EXT-07 | Cloud/DNS/vendor account ownership schedule | — | Founder |
| F-EXT-08 | SonarCloud New Code = Previous version (or equivalent meaningful baseline); re-analyze main; do **not** empty coverage attribution to fake QG | — | Founder/Admin |
| F-SEC-01 | Written attestation: production `CSP_NONCE_MODE` default-on (not false) | XS | Ops |
| F-EXT-03 | Backup/restore evidence (or contracted RPO/RTO waiver) | — | Ops |
| F-EXT-09 | Pentest/WAF evidence or explicit buyer waiver | — | Founder/Vendor |

## Post-close modernization

| FINDING_ID | Action | Effort |
|---|---|---|
| F-ARC-01 | Unify or contract-bound dual oracle paths | L |
| F-FIN-01 | Decimalize remaining arbitrage_engine fee math | M |
| F-FIN-02 | Harden advisory vs executable UI labeling | S |
| F-FIN-03 | DeFi gas freshness fail-closed SLAs | M |
| F-SEC-02 | Reduce style-src unsafe-inline | S |
| F-SEC-03 | Telegram setup secret file hygiene | S |
| F-SEC-04 | Full CORS allowlist review | S |
| F-CQ-01 | Modularize dashboard.py | L |
| F-CQ-02 | Triage Bandit LOW in money/auth paths | M |
| F-REL-01 | Chaos pack (DB/Redis/provider) | M |
| F-PERF-01 | Optional HA remeasure on release tag | S |
| F-OPS-02 | Metrics/tracing baseline | L |
| F-OPS-03 | Pager integration | S |
| F-SC-02 | Pin GitHub Actions to SHA | S |
| F-SC-03 | Model provenance inventory | S |
| F-IP-02 | NOTICE completeness | S |
| F-COMP-01 | Privacy technical controls roadmap | L |
| F-COMP-02 | Immutable admin audit log | M |
| F-TEST-02 | Pytest fixture isolation hardening | S |
| F-EXT-10 | Optional 60s founder walkthrough recording | — |

## Explicitly not remediated in RC1 (by design)

No code, test, Sonar setting, coverage baseline, or alert dismissal was changed during this DD.
