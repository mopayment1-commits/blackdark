# BLACKDARK Launch-57 — CISA Secure by Demand Remediation Program

**Document type:** Institutional remediation program (design authority)  
**Scope lock:** BLACKDARK Launch-57  
**Baseline SHA (inventory):** `e73f398d4048723bd10670beab14a0d18ceb19ef` (PR #493)  
**Inventory source:** Launch-57 Problem Inventory (FINDING-01 … FINDING-19)  
**Alignment target:** CISA *Secure by Demand Guide: How Software Customers Can Drive a Secure Technology Ecosystem* (August 2024)  
**Status:** APPROVED FOR EXECUTION PLANNING — implementation gated on evidence per section 3  

---

## 1. Purpose and non-goals

### 1.1 Purpose

Define a **complete, phased, evidence-based** remediation program that closes every item in the Launch-57 problem inventory, with **no omitted finding**, **no implementation from guesswork**, and **no false regulatory claims** (notably: this is **not** CISA certification).

### 1.2 Non-goals

- Claiming “CISA certified”, “CISA approved”, or full alignment until **closure gates** in section 8 pass with recorded evidence.
- Remediating capabilities **outside** Launch-57 scope (`cap978/launch57_closure_scope.py` at baseline SHA) unless explicitly change-controlled into Launch-57.
- Replacing **organizational** certifications (SOC 2, ISO 27001) with engineering artifacts alone.

---

## 2. Normative references (authoritative only)

Remediation work packages **must** cite at least one primary source from this table. Wiki-only or unattributed blogs are **out of scope** as sole justification.

| ID | Source | Use in this program |
|----|--------|---------------------|
| **CISA-SBD** | CISA Secure by Demand Guide (August 2024) | Procurement assessment areas: patching, SSO/MFA, logs, SBOM, OSS governance, VDP, CVE transparency |
| **CISA-SBDf** | CISA Secure by Design principles & pledge materials (cisa.gov) | Pledge participation decision; secure defaults; transparency |
| **NIST-SSDF** | NIST SP 800-218 (SSDF) v1.1 | Patch/vulnerability management, provenance, secure release practices |
| **NIST-CSF** | NIST Cybersecurity Framework 2.0 | Prioritization (Govern, Identify, Protect, Detect, Respond) |
| **OWASP-ASVS** | OWASP Application Security Verification Standard (4.x) | XSS/output encoding, auth verification levels |
| **OWASP-XSS** | OWASP XSS Prevention Cheat Sheet | Systematic XSS class reduction |
| **RFC-9116** | RFC 9116 (`security.txt`) | Well-known security contact publication |
| **ISO-29147** | ISO/IEC 29147 (Vulnerability disclosure) | VDP structure, reporting, coordination |
| **MITRE-CWE** | CWE taxonomy | Classification in advisories |
| **CVE** | CVE Program rules / CNA processes | Product CVE assignment or vendor coordination |
| **CPE** | NIST NVD CPE specification | Product CPE naming in advisories |
| **CDX** | CycloneDX specification 1.5+ | SBOM format, metadata, dependencies |
| **NTIA-MIN** | NTIA SBOM minimum elements | SBOM completeness expectations |
| **OpenChain** | ISO/IEC 5230 (OpenChain) | OSS governance program baseline (OSPO-equivalent) |

**Traceability rule:** Every merge to Launch-57 remediation must link a work-package ID (e.g. `L57-RP-08-WP2`) to ≥1 normative ID above in PR description and evidence index.

---

## 3. Evidence and verification doctrine (mandatory)

### 3.1 Prohibited

- Closing a finding from code inspection alone when the inventory marked **NOT VERIFIED** for production/runtime.
- Closing FINDING-03, 08, 09, 14, 17, 19 without **environment-specific** evidence (staging/production parity documented).
- Asserting MFA/SSO “by default” or “at no additional cost” without **published product policy** + **automated tests** + **customer-facing documentation** aligned.

### 3.2 Required evidence classes

| Class | Description | Storage |
|-------|-------------|---------|
| **E-ART** | Version-controlled artifact (policy, SBOM, security.txt, VDP) | Repository path + SHA |
| **E-TEST** | Automated test log (CI) | CI run URL / artifact |
| **E-RUN** | Reproducible command output (curl, pytest) | `governance/launch57/evidence/<finding>/` |
| **E-OPS** | Operator attestation (WAF, retention backup) | Signed ops record, redacted where needed |
| **E-LEGAL** | Commercial/pricing commitment | MSA/pricing page snapshot + legal review ID |

### 3.3 Finding closure rule

A finding moves to **CLOSED** only when:

1. All work packages for that finding are **DONE**;
2. Acceptance criteria in section 6 are **PASS** with attached evidence class;
3. Independent verification step (section 8.3) is **PASS**;
4. Entry added to **Remediation Evidence Index** (section 9 template).

---

## 4. Priority model (institutional)

Priorities follow **CISA-SBD materiality** from the audit gap register, ordered by **NIST-CSF** Protect/Detect functions for SaaS identity and logging.

| Priority | Label | Findings | Rationale (normative) |
|----------|-------|----------|------------------------|
| **P0** | Due-diligence blockers | 08, 09, 13, 14, 15 | CISA-SBD explicit: VDP, logs/retention, vulnerability transparency |
| **P1** | Material alignment | 02, 03, 04, 05, 06, 07, 10, 11, 12 | CISA-SBD: patching, SSO/MFA, elimination/roadmap, SBOM, OSS governance |
| **P2** | Governance & assurance | 01, 16, 17, 18, 19 | Pledge transparency; institutional assurance; edge pentest (supporting, not checklist substitute) |

**Execution order:** Phase sequence in section 5 (0 → 7). Within a phase, P0 before P1 before P2.

---

## 5. Phased execution roadmap

### Phase 0 — Program mobilization (all findings)

| WP ID | Activity | Owner | Output | Normative |
|-------|----------|-------|--------|-----------|
| L57-P0-WP1 | Pin remediation branch to Launch-57 SHA lineage; tag `launch-57-cisa-remediation-baseline` | Eng Lead | Git tag | NIST-SSDF PS.3 |
| L57-P0-WP2 | Create `governance/launch57/CISA_REMEDIATION_EVIDENCE_INDEX.json` | Sec Lead | Evidence index | CISA-SBD |
| L57-P0-WP3 | RACI: Engineering, Security, Legal, Product, Ops | Program Mgr | RACI matrix | NIST-CSF Govern |
| L57-P0-WP4 | Re-run inventory tests on remediation branch; diff vs baseline | Sec Eng | Inventory delta report | Internal SSOT |

**Phase 0 gate:** Evidence index exists; all 19 FINDING IDs listed with status `OPEN`.

---

### Phase 1 — Disclosure & vulnerability transparency (P0)

**Findings:** 13, 14, 15 (primary); enables 18 coordination.

| WP ID | Activity | Normative |
|-------|----------|-----------|
| L57-P1-WP1 | Publish **Vulnerability Disclosure Policy** (authorized testing, safe harbor, scope, prohibitions, reporting channel, SLA, coordination, researcher treatment) | ISO-29147, CISA-SBD |
| L57-P1-WP2 | Extend `SECURITY.md` to point to VDP; remove ambiguous-only private disclosure wording as **sole** policy | CISA-SBD |
| L57-P1-WP3 | Add `/.well-known/security.txt` (RFC fields: Contact, Expires, Preferred-Languages, Policy, Canonical) + static/deploy route | RFC-9116 |
| L57-P1-WP4 | Define **Product Security Advisory** process: CWE classification, CPE naming, CVE assignment path (CNA or coordinated third-party) | CVE, MITRE-CWE, CPE |
| L57-P1-WP5 | Publish initial advisory template + `docs/security/PRODUCT_SECURITY_ADVISORY_TEMPLATE.md` | NIST-SSDF RV.1 |

**Phase 1 gate (section 6):** FINDING-13, 14 (repo + deployed proof), 15 (process published) acceptance PASS.

---

### Phase 2 — Customer security logging & retention (P0)

**Findings:** 08, 09.

| WP ID | Activity | Normative |
|-------|----------|-----------|
| L57-P2-WP1 | **Policy:** `docs/security/CUSTOMER_SECURITY_LOG_POLICY.md` — CISA categories (config, identity/token, access to business data), **≥180 days** retention, deletion, export | CISA-SBD |
| L57-P2-WP2 | Implement durable store (not `_MAX_BUFFER` alone): migrate `security_events` / audit security kinds to Postgres (or SIEM) with TTL ≥180d | NIST-CSF Detect |
| L57-P2-WP3 | Customer-facing API: authenticated tenant/org export; RBAC; rate limits; formats JSON/CSV | CISA-SBD |
| L57-P2-WP4 | **Commercial:** document logs included in baseline SKU (no separate security log surcharge) OR explicit institutional-only with Legal sign-off | CISA-SBD |
| L57-P2-WP5 | Automated tests: retention configuration, export authorization, category coverage fixtures | E-TEST |

**Phase 2 gate:** FINDING-08, 09 CLOSED with E-OPS retention proof + E-TEST + E-LEGAL/commercial doc.

---

### Phase 3 — Identity: SSO, MFA, phishing-resistant (P1)

**Findings:** 03, 04, 05 (+ SSO allowlist interaction with Launch-57 `PRIVATE_BY_DEFAULT`).

| WP ID | Activity | Normative |
|-------|----------|-----------|
| L57-P3-WP1 | **Product policy:** SSO availability and pricing (if “no additional cost” claimed, SSO in self-serve tiers per Legal) | CISA-SBD |
| L57-P3-WP2 | Fix OIDC bootstrap: add `/api/institutional/sso/authorize`, `/callback`, `/status` to **AUTH_FLOW** allowlist (or `INTERNAL_UNAUTHENTICATED`) with threat model | CISA-SBD, OWASP-ASVS V14 |
| L57-P3-WP3 | E2E tests: anonymous authorize → 302 IdP; callback; **without** `SOFT_LAUNCH=true` | E-TEST |
| L57-P3-WP4 | **MFA default:** policy + enforce org-wide default for new users (configurable grace) OR document exception; implement server-side | CISA-SBD |
| L57-P3-WP5 | **Phishing-resistant track:** WebAuthn/Passkeys roadmap per OWASP-ASVS; Phase 3b delivery or IdP-native passkeys documented | CISA-SBD |
| L57-P3-WP6 | Update `/api/security/status` claims to match **actual** MFA/SSO policy (no overstated defaults) | CISA-SBDf |

**Phase 3 gate:** FINDING-03, 04, 05 CLOSED per acceptance (policy + tests + production probe).

---

### Phase 4 — Patch lifecycle & supply chain (P1)

**Findings:** 02, 10, 11, 12.

| WP ID | Activity | Normative |
|-------|----------|-----------|
| L57-P4-WP1 | Publish `docs/security/SECURITY_UPDATE_POLICY.md`: severity SLAs, supported versions, EOL, KEV handling, SaaS auto-update statement | NIST-SSDF PW, CISA-SBD |
| L57-P4-WP2 | SBOM: embed `git commit`, build ID, image digest in CycloneDX metadata; regenerate on release | CDX, NTIA-MIN |
| L57-P4-WP3 | Expand SBOM: container base (Syft/Trivy cyclonedx), OS packages; document JS CDN exclusions or include | NTIA-MIN |
| L57-P4-WP4 | OSS governance: `docs/security/OPEN_SOURCE_GOVERNANCE.md` (intake, risk, update, upstream contribution, escalation) aligned to OpenChain | ISO/IEC 5230 |
| L57-P4-WP5 | CI gate: SBOM drift fails build; pip-audit + documented exception process | NIST-SSDF |

**Phase 4 gate:** FINDING-02, 10, 11, 12 CLOSED.

---

### Phase 5 — Vulnerability-class elimination (P1)

**Findings:** 06, 07.

| WP ID | Activity | Normative |
|-------|----------|-----------|
| L57-P5-WP1 | Publish `docs/security/VULNERABILITY_CLASS_ELIMINATION_ROADMAP.md` — matrix: class, prevalence, target, owner, date, verification | CISA-SBD |
| L57-P5-WP2 | XSS/URL: inventory all `innerHTML`/dynamic `href` in Launch-57 templates; remediate or justify; extend `test_xss_sink_hardening.py` | OWASP-XSS, OWASP-ASVS |
| L57-P5-WP3 | Centralize URL sinks on `safeUrl` / `safeShareUrl`; remove duplicate unsafe patterns | OWASP-XSS |
| L57-P5-WP4 | SQLi/memory-safe: maintain `sql_safety` tests; document Python/native dependency memory risk in roadmap | CISA-SBD, NIST-SSDF |

**Phase 5 gate:** FINDING-06, 07 CLOSED with roadmap + green regression suite.

---

### Phase 6 — Secure by Design pledge & governance (P2)

**Findings:** 01.

| WP ID | Activity | Normative |
|-------|----------|-----------|
| L57-P6-WP1 | Executive decision: sign CISA Secure by Design Pledge **or** publish documented rationale not to sign | CISA-SBDf |
| L57-P6-WP2 | If signed: annual progress report template + publication path | CISA-SBDf |

**Phase 6 gate:** FINDING-01 CLOSED (signed + report **or** documented decline).

---

### Phase 7 — Posture, edge, independent assurance (P2)

**Findings:** 16, 17, 18, 19.

| WP ID | Activity | Normative |
|-------|----------|-----------|
| L57-P7-WP1 | Split `/api/security/status`: public attestations vs authenticated `/api/security/status/detail` | OWASP-ASVS, least disclosure |
| L57-P7-WP2 | Ensure `SecurityHeadersMiddleware` applies to **all** responses including anonymous 401/403 (test matrix) | OWASP, internal standard |
| L57-P7-WP3 | Pentest: execute engagement; deposit signed `pentest_attestation.json` for Launch-57 SHA scope | Institutional DD (not CISA checklist item) |
| L57-P7-WP4 | WAF/CDN: activate per `docs/CDN_WAF_CHECKLIST.md`; record `CDN_WAF_ACTIVE` + rule export | CISA-SBDf edge hygiene |
| L57-P7-WP5 | Production verification script: headers, security.txt, SSO, log export smoke | E-RUN |

**Phase 7 gate:** FINDING-16, 17, 18, 19 CLOSED per section 6.

---

## 6. Per-finding remediation playbooks (complete register)

Each playbook: **Target state → Work packages → Acceptance criteria → Verification (no guesswork)**.

---

### FINDING-01 — Secure by Design Pledge

| Field | Content |
|-------|---------|
| **Baseline** | No pledge artifacts in Git at `e73f398d` |
| **Target** | Signed pledge + progress **or** formal governance decision not to sign |
| **Work packages** | L57-P6-WP1, L57-P6-WP2 |
| **Acceptance** | (A) Public CISA pledge URL reference + progress report commit, **or** (B) Board/Product signed memo in `docs/governance/` declining pledge with alternatives |
| **Verification** | E-LEGAL/Board artifact; public URL fetch 200 |

---

### FINDING-02 — Security patching & updates

| Field | Content |
|-------|---------|
| **Baseline** | CI pip-audit; no customer patch SLA |
| **Target** | Published Security Update Policy with severity SLAs, KEV, EOL, version matrix |
| **Work packages** | L57-P4-WP1, L57-P4-WP5 |
| **Acceptance** | Policy covers: critical/high/medium timelines, KEV, supported branches, SaaS update model |
| **Verification** | E-ART review checklist mapped to NIST-SSDF PW.4; CI green |

---

### FINDING-03 — Enterprise SSO / no additional cost

| Field | Content |
|-------|---------|
| **Baseline** | OIDC implemented; Institutional `From $999/mo`; SSO blocked for anonymous under `PRIVATE_BY_DEFAULT` |
| **Target** | (1) Policy-aligned pricing; (2) working OIDC bootstrap in strict mode |
| **Work packages** | L57-P3-WP1, L57-P3-WP2, L57-P3-WP3 |
| **Acceptance** | If claiming CISA no-cost SSO: SSO in documented base tier. Anonymous `GET /sso/authorize` → 302 when configured. |
| **Verification** | E-TEST without SOFT_LAUNCH; E-RUN production curl; E-LEGAL pricing snapshot |

---

### FINDING-04 — General user MFA

| Field | Content |
|-------|---------|
| **Baseline** | `mfa_enabled DEFAULT 0`; optional TOTP |
| **Target** | MFA default-on for new accounts (or documented CISA exception approved by Legal) |
| **Work packages** | L57-P3-WP4, L57-P3-WP6 |
| **Acceptance** | New user: MFA enrollment required before full session **or** exception doc published |
| **Verification** | E-TEST registration/login flows; `SECURITY.md` + status endpoint aligned |

---

### FINDING-05 — Phishing-resistant authentication

| Field | Content |
|-------|---------|
| **Baseline** | TOTP only; no WebAuthn in code |
| **Target** | Passkeys/WebAuthn available **or** IdP-enforced phishing-resistant + documented |
| **Work packages** | L57-P3-WP5 |
| **Acceptance** | WebAuthn register/auth E2E **or** enterprise IdP doc stating phishing-resistant default for SSO customers |
| **Verification** | E-TEST WebAuthn **or** E-LEGAL IdP contract appendix |

---

### FINDING-06 — XSS / unsafe HTML / dynamic URL

| Field | Content |
|-------|---------|
| **Baseline** | `dom_escape.js`, partial tests; widespread `innerHTML` |
| **Target** | Documented sink inventory with zero open HIGH sinks in Launch-57 templates |
| **Work packages** | L57-P5-WP2, L57-P5-WP3 |
| **Acceptance** | `pytest tests/test_xss_sink_hardening.py` PASS; inventory file with status `closed` per sink |
| **Verification** | E-TEST CI; E-ART inventory |

---

### FINDING-07 — Vulnerability-class elimination roadmap

| Field | Content |
|-------|---------|
| **Baseline** | Scattered DD registers; no class matrix |
| **Target** | Single SSOT roadmap with owners/dates |
| **Work packages** | L57-P5-WP1, L57-P5-WP4 |
| **Acceptance** | Roadmap lists SQLi, XSS, URL, memory/native deps; each row has verification test link |
| **Verification** | E-ART + traceability to tests |

---

### FINDING-08 — Security log retention (≥6 months)

| Field | Content |
|-------|---------|
| **Baseline** | `security_events.py` buffer 1000 + JSONL |
| **Target** | ≥180 days durable retention for security audit events |
| **Work packages** | L57-P2-WP1, L57-P2-WP2, L57-P2-WP5 |
| **Acceptance** | Config `SECURITY_LOG_RETENTION_DAYS >= 180`; proof of purge job; sample query spanning >90d |
| **Verification** | E-TEST + E-OPS backup/retention log |

---

### FINDING-09 — Customer security logs / no additional cost

| Field | Content |
|-------|---------|
| **Baseline** | Admin-only `/api/security/events`; audit export not tier-documented |
| **Target** | Customer RBAC export; baseline inclusion documented |
| **Work packages** | L57-P2-WP3, L57-P2-WP4 |
| **Acceptance** | Org admin can export CISA categories; pricing doc states no log surcharge (if claimed) |
| **Verification** | E-TEST RBAC; E-LEGAL; E-RUN export |

---

### FINDING-10 — SBOM release binding

| Field | Content |
|-------|---------|
| **Baseline** | CycloneDX `rc2` + lockfile hash only |
| **Target** | SBOM metadata includes git SHA, build ID, image digest |
| **Work packages** | L57-P4-WP2 |
| **Acceptance** | `metadata.properties` contains `blackdark:git_commit`, `blackdark:release`, `blackdark:image_digest` |
| **Verification** | E-TEST CI compares SHA to build |

---

### FINDING-11 — SBOM completeness

| Field | Content |
|-------|---------|
| **Baseline** | Python lockfile only |
| **Target** | Documented multi-part SBOM (app + container) or justified scope statement per NTIA |
| **Work packages** | L57-P4-WP3 |
| **Acceptance** | Container SBOM artifact OR `docs/security/SBOM_SCOPE_STATEMENT.md` with NTIA gap analysis approved by Sec Lead |
| **Verification** | E-ART + Syft/Trivy output archived |

---

### FINDING-12 — Open source governance

| Field | Content |
|-------|---------|
| **Baseline** | NOTICE, pip-audit; no OSPO |
| **Target** | Open Source Governance policy (OpenChain-aligned) |
| **Work packages** | L57-P4-WP4 |
| **Acceptance** | Policy covers intake, vulnerability response, upstream contribution, license compliance |
| **Verification** | E-ART checklist vs ISO/IEC 5230 core clauses |

---

### FINDING-13 — Vulnerability Disclosure Policy

| Field | Content |
|-------|---------|
| **Baseline** | One-line private disclosure in SECURITY.md |
| **Target** | Full public VDP |
| **Work packages** | L57-P1-WP1, L57-P1-WP2 |
| **Acceptance** | ISO-29147 checklist 100% addressed in published VDP |
| **Verification** | E-ART legal review ID; public URL |

---

### FINDING-14 — security.txt

| Field | Content |
|-------|---------|
| **Baseline** | No repo file; production not verified in inventory |
| **Target** | Valid RFC 9116 file in repo and on production |
| **Work packages** | L57-P1-WP3 |
| **Acceptance** | `curl -sS https://<prod>/.well-known/security.txt` returns Contact + Policy + Expires future |
| **Verification** | E-RUN from CI staging/prod job |

---

### FINDING-15 — CVE / CWE / CPE process

| Field | Content |
|-------|---------|
| **Baseline** | No product CVE process |
| **Target** | Documented advisory pipeline with CWE/CPE |
| **Work packages** | L57-P1-WP4, L57-P1-WP5 |
| **Acceptance** | Process doc + CPE dictionary entry for product + dry-run advisory |
| **Verification** | E-ART; optional CVE ID from CNA for dry-run |

---

### FINDING-16 — `/api/security/status` exposure

| Field | Content |
|-------|---------|
| **Baseline** | Public verbose posture |
| **Target** | Minimal public attestations; detail behind auth |
| **Work packages** | L57-P7-WP1 |
| **Acceptance** | Public JSON excludes internal paths, secret names, pentest control IDs |
| **Verification** | E-TEST schema snapshot; manual diff review |

---

### FINDING-17 — Security headers on denial responses

| Field | Content |
|-------|---------|
| **Baseline** | Anonymous 401 may lack full header set (prod report) |
| **Target** | Consistent CSP, HSTS, XCTO, etc. on 401/403 |
| **Work packages** | L57-P7-WP2 |
| **Acceptance** | Test matrix: 200/401/403 all include required headers |
| **Verification** | E-TEST `test_security_headers_on_denial_paths` + E-RUN prod |

---

### FINDING-18 — Independent penetration test

| Field | Content |
|-------|---------|
| **Baseline** | Template only; `attestation_verified=false` |
| **Target** | Signed attestation for Launch-57 scope |
| **Work packages** | L57-P7-WP3 |
| **Acceptance** | `verify_pentest_attestation()` true for release SHA |
| **Verification** | E-OPS signed JSON + scope matches Launch-57 |

---

### FINDING-19 — WAF / CDN

| Field | Content |
|-------|---------|
| **Baseline** | Templates; `waf_cdn_provided_by_app=false` |
| **Target** | Active edge WAF/CDN **or** explicit buyer disclosure unchanged |
| **Work packages** | L57-P7-WP4 |
| **Acceptance** | `CDN_WAF_ACTIVE` + rule export **or** MSA waiver archived |
| **Verification** | E-OPS Cloudflare/export; DNS evidence |

---

## 7. Master work-package index (no omission)

| WP ID | Phase | Findings covered |
|-------|-------|------------------|
| L57-P0-WP1 … WP4 | 0 | ALL (setup) |
| L57-P1-WP1 … WP5 | 1 | 13, 14, 15 |
| L57-P2-WP1 … WP5 | 2 | 08, 09 |
| L57-P3-WP1 … WP6 | 3 | 03, 04, 05, 16 (partial) |
| L57-P4-WP1 … WP5 | 4 | 02, 10, 11, 12 |
| L57-P5-WP1 … WP4 | 5 | 06, 07 |
| L57-P6-WP1 … WP2 | 6 | 01 |
| L57-P7-WP1 … WP5 | 7 | 16, 17, 18, 19 |

**Finding → WP mapping (complete):**

| Finding | Work packages |
|---------|----------------|
| 01 | L57-P6-WP1, L57-P6-WP2 |
| 02 | L57-P4-WP1, L57-P4-WP5 |
| 03 | L57-P3-WP1, L57-P3-WP2, L57-P3-WP3 |
| 04 | L57-P3-WP4, L57-P3-WP6 |
| 05 | L57-P3-WP5 |
| 06 | L57-P5-WP2, L57-P5-WP3 |
| 07 | L57-P5-WP1, L57-P5-WP4 |
| 08 | L57-P2-WP1, L57-P2-WP2, L57-P2-WP5 |
| 09 | L57-P2-WP3, L57-P2-WP4 |
| 10 | L57-P4-WP2 |
| 11 | L57-P4-WP3 |
| 12 | L57-P4-WP4 |
| 13 | L57-P1-WP1, L57-P1-WP2 |
| 14 | L57-P1-WP3 |
| 15 | L57-P1-WP4, L57-P1-WP5 |
| 16 | L57-P7-WP1, L57-P3-WP6 |
| 17 | L57-P7-WP2 |
| 18 | L57-P7-WP3 |
| 19 | L57-P7-WP4, L57-P7-WP5 |

---

## 8. Launch-57 closure gates

### 8.1 Program complete

All **19** findings status `CLOSED` in Evidence Index.

### 8.2 Release attestation (allowed wording)

> “BLACKDARK Launch-57 has been remediated against the August 2024 CISA Secure by Demand procurement guidance checklist areas, with evidence indexed at `governance/launch57/CISA_REMEDIATION_EVIDENCE_INDEX.json`. This is not CISA certification.”

### 8.3 Independent verification (required)

| Step | Executor | Method |
|------|----------|--------|
| V-1 | Security Lead | Re-run full inventory checklist vs remediation SHA |
| V-2 | QA | CI security workflow green + new denial-header tests |
| V-3 | Ops | Production smoke: security.txt, SSO authorize, log export window |
| V-4 | Legal | Pricing/SSO/logs/VDP alignment review |

---

## 9. Evidence index template

Create at implementation start:

```json
{
  "program": "LAUNCH57_CISA_SECURE_BY_DEMAND_REMEDIATION",
  "baseline_sha": "e73f398d4048723bd10670beab14a0d18ceb19ef",
  "remediation_sha": "",
  "findings": {
    "FINDING-01": { "status": "OPEN", "evidence": [], "normative": ["CISA-SBDf"] },
    "FINDING-02": { "status": "OPEN", "evidence": [], "normative": ["NIST-SSDF", "CISA-SBD"] }
  }
}
```

*(Extend through FINDING-19 before Phase 0 gate closes.)*

---

## 10. Implementation sequencing summary

```mermaid
flowchart LR
  P0[Phase 0 Mobilization] --> P1[Phase 1 Disclosure]
  P1 --> P2[Phase 2 Logging]
  P2 --> P3[Phase 3 Identity]
  P3 --> P4[Phase 4 Supply Chain]
  P4 --> P5[Phase 5 Vuln Classes]
  P5 --> P6[Phase 6 Pledge]
  P6 --> P7[Phase 7 Assurance]
  P7 --> G[Closure Gates V-1..V-4]
```

---

## 11. Document control

| Version | Date | Change |
|---------|------|--------|
| 1.0 | 2026-09-30 | Initial institutional program — all FINDING-01..19 |

**Next step (execution):** Begin Phase 0 on branch cut from Launch-57 baseline; no Phase 1 code until P0-WP2 Evidence Index exists.
