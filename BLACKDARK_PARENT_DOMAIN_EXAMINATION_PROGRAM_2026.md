# BLACKDARK — INSTITUTIONAL TECHNICAL DUE-DILIGENCE EXAMINATION PROGRAM 2026
## Corrected Operational Edition — Evidence-Driven, Risk-Based, AI-Executed, Human-Governed

# 1. Engagement Identity

## 1.1 What this engagement is

This is an **AI-assisted institutional technical due-diligence examination and agreed-upon technical procedures program** for BLACKDARK.

Cursor acts as an **evidence-gathering and technical examination executor**.

It does **not** act as:
- an independent external auditor;
- a statutory auditor;
- a SOC 2 examiner;
- an ISO certification body;
- a legal adviser;
- a PCI Qualified Security Assessor;
- a GIPS verifier;
- an independent model-validation firm.

Therefore Cursor may produce:
- factual findings;
- evidence registers;
- technical conclusions under a documented scope;
- interim scoped conclusions;
- a full technical examination conclusion.

Cursor may **not** produce or imply an independent assurance opinion.

## 1.2 Human governance

Roles:

### Engagement Owner
The BLACKDARK owner or formally designated representative.

Responsibilities:
- approve the engagement scope and limitations once at Phase 0;
- acknowledge unavailable access or external evidence;
- decide whether residual risk is accepted after the report;
- sign the management acceptance section.

### Automated Technical Examiner
Cursor.

Responsibilities:
- discovery;
- procedures;
- evidence collection;
- technical testing;
- calculations;
- registers;
- findings;
- self-challenge;
- report drafting.

### Independent Human Reviewer
Optional for technical due diligence; **mandatory if the output is to be presented as independent assurance, formal audit opinion, certification support, or externally relied-upon assurance**.

Must not be the same person/agent that built the system being independently assessed.

## 1.3 Independence disclosure

The final report must prominently state:

> The automated examiner may have been used previously in software-development or remediation activity. This creates an objectivity limitation. Its work is an AI-assisted technical examination and evidence package, not an independent external assurance opinion. Independent reliance requires validation by a qualified human reviewer who is free of relevant conflicts of interest.

---

# 2. Engagement Type and Assurance Level

Before fieldwork, select exactly one engagement output class:

### CLASS A — AGREED-UPON TECHNICAL PROCEDURES
Default when Cursor executes defined procedures and reports factual findings.
No assurance opinion is expressed.

### CLASS B — LIMITED TECHNICAL EXAMINATION
Permitted only if the scope, criteria, evidence, access and limitations support a limited-form technical conclusion.
This is not an ISAE 3000 assurance report unless performed by an appropriately qualified practitioner under that standard.

### CLASS C — FULL TECHNICAL DUE-DILIGENCE EXAMINATION
A comprehensive technical conclusion across the full discovered BLACKDARK scope.
Still not an independent assurance opinion unless independently validated by a qualified human practitioner.

### CLASS D — EXTERNAL ASSURANCE / FORMAL OPINION
Cursor cannot issue this class.
Requires qualified independent human practitioner/reviewer and any other applicable professional requirements.

The selected class must appear on page 1 of every report.

---

# 3. Governing Audit / Examination Methodology

These are the methodological references for HOW the examination is designed and controlled.

## 3.1 IIA Global Internal Audit Standards
2024 edition; issued 9 January 2024; effective 9 January 2025.

Use for:
- integrity;
- objectivity;
- competence;
- due professional care;
- engagement planning;
- evidence;
- communications;
- quality;
- disclosure of limitations.

Official:
https://www.theiia.org/en/standards/

Important limitation:
IIA standards describe professional internal auditing. Cursor cannot claim organizational independence or external-quality status merely by following these principles.

## 3.2 ISACA IT Audit Framework (ITAF), 5th Edition
Officially released 26 February 2026.

Use for:
- IT audit planning;
- execution;
- reporting;
- evidence;
- sampling;
- AI/data/cloud/digital trust;
- professional judgement.

Official:
https://www.isaca.org/resources/it-audit

## 3.3 ISO 19011:2026
Edition 4, published May 2026.

Use for:
- audit principles;
- audit-program management;
- risk-based approach;
- evidence-based approach;
- competence;
- conduct and reporting.

Official:
https://www.iso.org/standard/19011

## 3.4 IAASB ISRS 4400 (Revised)
Use as the closest formal reference for **agreed-upon procedures logic**:
- agreed procedures;
- factual findings;
- transparency;
- professional judgement;
- engagement acceptance;
- independence disclosure.

Official:
https://www.iaasb.org/publications/international-standard-related-services-isrs-4400-revised

## 3.5 IAASB ISAE 3000 (Revised)
Use only as an **assurance-quality benchmark** for:
- suitable criteria;
- subject matter;
- sufficient appropriate evidence;
- documentation;
- reasonable vs limited assurance concepts.

Do not claim an ISAE 3000 engagement unless performed by an appropriate practitioner under the standard.

Official:
https://www.iaasb.org/publications/international-standard-assurance-engagements-isae-3000-revised-assurance-engagements-other-audits-or

## 3.6 NIST SP 800-53A Rev.5
Use for formal assessment design:
- EXAMINE;
- INTERVIEW;
- TEST;
- assessment objectives;
- evidence;
- tailoring.

Official:
https://csrc.nist.gov/pubs/sp/800/53/a/r5/final

---

# 4. Subject-Matter Criteria

These criteria govern WHAT is assessed in each domain.

- Federal Reserve/OCC/FDIC SR 26-2 — Model Risk Management, 17 April 2026.
- BCBS 239 + current 2026 implementation material — data governance, lineage, accuracy, completeness, timeliness.
- NIST CSF 2.0.
- NIST SP 800-53 / 53A.
- NIST SP 800-218 SSDF.
- NIST SP 800-61 Rev.3.
- ISO/IEC 27001:2022.
- ISO/IEC 25010:2023.
- ISO/IEC 25023.
- ISO/IEC/IEEE 29119 series.
- ISO 22301.
- ISO/IEC 42001.
- OWASP ASVS 5.0.0.
- OWASP API Security Top 10.
- CIS Controls v8.1 / Assessment Specification.
- FSB Third-Party Risk Management and Oversight Toolkit.
- IOSCO crypto/digital-asset market recommendations.
- IOSCO DeFi recommendations where applicable.
- NIST AI RMF / NIST AI 600-1.
- FSB AI financial-stability guidance.
- Probability of Backtest Overfitting / CSCV.
- Deflated Sharpe Ratio.
- Hansen SPA / multiple-comparison methodology.
- PCI DSS v4.0.1 **only after payment-scope determination**.
- GIPS 2020 edition **only after performance-presentation applicability determination**.
- GDPR / applicable privacy laws **only after territorial/material applicability determination**.
- CCPA/CPRA current rules **only after applicability determination**.
- Home-jurisdiction privacy/data law must be separately verified and classified before reliance.

---

# 5. Regulatory / Standard Applicability Matrix

Every Requirement ID and every Procedure ID must contain:

`applicability_status`

Allowed values:
- DIRECTLY_APPLICABLE
- CONTRACTUALLY_APPLICABLE
- INSTITUTIONAL_BENCHMARK
- TECHNICAL_BENCHMARK
- NOT_APPLICABLE
- APPLICABILITY_NOT_VERIFIED

Also record:
- jurisdiction;
- entity/product basis;
- reason;
- evidence;
- legal-review-needed: YES/NO.

No compliance claim may be inferred from technical conformance.

---

# 6. Access Matrix

Every procedure must specify one required access class.

| Access | Meaning | Typical procedures |
|---|---|---|
| L0 | Repository/static | source, config, docs |
| L1 | Local executable | unit, DB local, deterministic recomputation |
| L2 | Test/staging | behavioral API, journeys, authz |
| L3 | Production read-only | live freshness, production configuration, logs |
| L4 | CI/CD control plane | pipeline, artifacts, deployment evidence |
| L5 | External independent | legal, pentest, certification, third-party attestation |

Rules:
- Unavailable higher access does not stop lower-access procedures.
- A procedure that requires unavailable access becomes `EXTERNAL_BLOCKER`, not automatic FAIL.
- The exact evidence needed to close the blocker must be stated.
- No procedure may silently downgrade its evidence requirement.

---

# 7. Evidence Anti-Fabrication Law

A procedure cannot receive PASS unless its Evidence Record contains all applicable fields:

- Evidence ID
- Procedure ID
- Requirement ID
- Universe ID(s)
- exact canonical SHA
- branch/worktree
- environment/access level
- exact command/tool/method
- raw output path or raw captured output
- SHA-256 hash of evidence artifact where file-based
- execution timestamp
- exit code where applicable
- numerator
- denominator
- evaluator conclusion
- limitations

## 7.1 Mandatory raw evidence

For executable procedures:
`PASS = command/method + raw output + SHA/baseline + evidence reference`

A Markdown assertion alone is never evidence of execution.

## 7.2 Acceptance control

Every phase gate must test whether each PASS result has a complete evidence record.

If not:
`ANTI_FABRICATION_GATE = FAIL`

No phase can close.

---

# 8. Prior-Run Evidence Policy

All previous BLACKDARK audit runs, reports, screenshots, CI claims, PASS files and freeze files are:

`PRIOR_EVIDENCE_CANDIDATE`

They may be reused only if:
1. the evidence artifact still exists;
2. its provenance is known;
3. its target SHA/environment is known;
4. the current requirement remains materially unchanged;
5. current-SHA revalidation is performed where required.

Old PASS is never inherited automatically.

---

# 9. Human Interview Protocol

INTERVIEW is disabled by default for Cursor.

It may be used only when:
- a named human stakeholder is actually available;
- the interview purpose is documented;
- questions are recorded;
- answers are recorded as testimonial evidence;
- testimonial evidence is corroborated for material claims.

If no human is available:
`INTERVIEW = NOT_PERFORMED`
and the procedure must use alternative evidence or remain limited.

Cursor must never fabricate an interview.

---

# 10. BLACKDARK Materiality Model

## 10.1 Critical-by-default populations

The following are presumptively Critical/High until evidence supports lower classification:

- authentication and account takeover paths;
- authorization / BOLA / IDOR;
- admin functions;
- tenant isolation;
- subscription/entitlement enforcement;
- billing/payment-webhook state;
- PII or sensitive account data;
- API keys/secrets/private keys;
- financial recommendations/signals used for decisions;
- execution-adjacent or liquidation/leverage outputs;
- price/freshness/staleness semantics;
- portfolio/PnL/NAV/risk calculations;
- model outputs presented as probability/confidence;
- production DB integrity;
- data source identity/lineage;
- paid/institutional capabilities;
- recovery/backup claims;
- vendor dependencies whose failure disables a critical service.

## 10.2 Severity presumptions

Examples, subject to evidence:

- unauthorized cross-user data access → P0 candidate;
- admin/authentication bypass → P0 candidate;
- entitlement fail-open for paid/institutional capability → P0/P1 candidate;
- stale data represented as LIVE for a material financial decision output → P0/P1 candidate;
- materially wrong financial computation → P0/P1 depending exposure;
- silent zero substitution for UNKNOWN in risk/financial output → P0/P1 candidate;
- mock/stub exposed as real paid capability → P1, potentially P0 if materially relied upon;
- missing evidence alone → EVIDENCE_GAP, not defect.

Final severity requires actual impact/exposure analysis.

---

# 11. Finding Taxonomy

Every issue must be exactly one primary type:

- DEFECT
- CONTROL_DEFICIENCY
- EVIDENCE_GAP
- SCOPE_EXCLUSION
- EXTERNAL_BLOCKER
- OPEN_QUESTION
- CONTRADICTION
- OBSERVATION

Never convert an evidence gap into a defect without factual defect evidence.

Every finding records:
- type;
- severity if applicable;
- condition;
- criterion;
- cause if known;
- effect;
- population;
- evidence;
- confidence;
- production impact;
- institutional impact;
- acquisition impact.

---

# 12. Residual Risk and Owner Acceptance

Risk acceptance cannot change a FAIL into PASS.

For each unresolved P0/P1 or material blocker, create:
`RESIDUAL_RISK_REGISTER`

Fields:
- risk ID;
- description;
- current status;
- evidence;
- residual exposure;
- compensating controls;
- required action/evidence;
- owner acceptance: ACCEPT / REJECT / DEFER;
- acceptance date;
- acceptance limitation.

Only the Engagement Owner may record management acceptance.

Cursor must not accept risk on behalf of the owner.

---

# 13. Report Use Restrictions

Every output must state:

This report:
- is not a statutory audit;
- is not a certification;
- is not a SOC 2 report;
- is not an ISO certificate;
- is not a legal opinion;
- is not a PCI ROC/AOC;
- is not a GIPS verification;
- must not be marketed as independent assurance unless independently validated;
- must not be provided to investors/acquirers as an independent assurance report without the stated limitations and provenance.

---

# 14. Privacy and Payment Scope

## 14.1 Payment scope

Create `PAYMENT_SCOPE_STATEMENT`.

Determine:
- whether BLACKDARK stores, processes, or transmits cardholder data;
- whether Stripe-hosted/tokenized flows reduce direct scope;
- whether PAN/CVV can ever reach BLACKDARK;
- webhook/payment metadata handled;
- applicable PCI DSS v4.0.1 scope or N/A rationale.

PCI applicability must be explicit:
`PCI_SCOPE = IN / OUT / NOT_VERIFIED`

## 14.2 Privacy scope

Create `PERSONAL_DATA_MAP`.

At minimum:
- account identifiers;
- authentication data;
- telemetry;
- behavioral analytics;
- payment metadata;
- support/contact data;
- IP/device/log data;
- API-key/account data;
- exports/backups;
- third-party transfers.

Test applicable:
- collection;
- purpose;
- minimization;
- access;
- export/access request;
- correction where applicable;
- deletion/erasure;
- retention;
- logs;
- third-party transfers;
- consent/notice where applicable;
- automated-decision implications where applicable.

Privacy-law applicability must be classified, not assumed.

---

# 15. GIPS / Performance Presentation Gate

Create:
`PERFORMANCE_PRESENTATION_SCOPE_STATEMENT`

If BLACKDARK presents:
- strategy returns;
- portfolio returns;
- model/signal track records;
- composite performance;
- marketed historical investment performance;

then assess GIPS applicability/benchmark relevance and performance-presentation controls.

If not:
`GIPS = NOT_APPLICABLE`
with evidence and rationale.

Backtest marketing claims remain subject to anti-cherry-picking / data-snooping / overfitting review regardless of formal GIPS applicability.

---

# 16. UI Scope — Full Inventory, Risk-Based Execution

Do not require exhaustive behavioral testing of every cosmetic element.

Instead:

1. inventory 100% of discovered user-facing controls;
2. classify materiality;
3. behavioral-test 100% of Critical/High controls;
4. risk-based sample Medium controls;
5. Low/cosmetic controls may use static/visual verification unless behavior is material.

Material UI includes anything that:
- changes financial interpretation;
- changes account/security state;
- changes billing/entitlement;
- submits data;
- triggers backend state;
- exposes paid capability;
- exports data;
- controls data source/timeframe/filter that can materially change output.

Coverage must report exact denominators.

---

# 17. Procedure Execution Classes

Every Procedure ID must be labeled:

- LOCAL_EXECUTABLE
- STAGING_REQUIRED
- PROD_READ_ONLY_REQUIRED
- CI_CONTROL_PLANE_REQUIRED
- EXTERNAL_HUMAN_REQUIRED

Execution queues must be separated by class.

This prevents unavailable production/legal access from blocking local work.

---

# 18. Workload / Batch Governance

There is no arbitrary minimum time that proves quality.

Completeness is evidence-based, not time-based.

However execution must be manageable:

- one batch contains a bounded set of Procedure IDs;
- each batch closes only after evidence reconciliation;
- state is checkpointed after each batch;
- context exhaustion triggers checkpoint/resume, never finalization;
- denominator of a batch is not the denominator of the engagement;
- engagement denominator remains the full discovered applicable population.

Priority if resources/access are constrained:

1. P0/Critical security and authorization
2. financial correctness / execution-adjacent decisions
3. billing / entitlements
4. data integrity / freshness / lineage
5. model risk / AI material outputs
6. DB / processing integrity
7. resilience / recovery
8. paid/institutional user journeys
9. remaining product/UI
10. lower-risk documentation/cosmetic issues

Priority affects order only, not final scope.

---

# 19. Engagement Phases and Gates

## Phase 0 — Engagement Acceptance and Governance

Required:
- engagement class selected;
- intended users;
- prohibited uses;
- owner;
- automated examiner disclosure;
- independence/objectivity limitation;
- scope;
- access matrix;
- criteria register;
- report-use restrictions;
- one-time owner acceptance of scope/limitations.

Owner approval is requested **once here only** if not already explicitly provided.

After that, no routine approval requests between phases.

Gate:
`ENGAGEMENT_ACCEPTANCE_GATE`

## Phase 1 — Criteria Currentness / Applicability

Verify official currentness and applicability.

Gate:
`CRITERIA_APPLICABILITY_GATE`

## Phase 2 — Canonical Target / Baseline

Verify:
- canonical repository;
- branch/worktree;
- SHA;
- origin relationship;
- unmerged work;
- deployed revision where accessible;
- runtime/toolchain;
- configuration classes;
- DB/cache/storage;
- providers;
- flags.

Gate:
`CANONICAL_BASELINE_GATE`

## Phase 3 — Risk / Materiality

Build BLACKDARK-specific risk universe.

Gate:
`RISK_MATERIALITY_GATE`

## Phase 4 — Full Discovery

Inventory full populations.

Gate:
`DISCOVERY_COMPLETENESS_GATE`

## Phase 5 — Requirements / Procedures

Map:
Universe → Requirement → Procedure → Evidence requirement.

Every procedure includes applicability and execution class.

Gate:
`TRACEABILITY_DESIGN_GATE`

## Phase 6 — Fieldwork

Execute all locally available work first while segregating inaccessible classes.

Gate:
`FIELDWORK_ACCOUNTABILITY_GATE`

## Phase 7 — Self-Challenge Review

Perform ten **internal self-challenge passes**.

They are not independent QA.

Gate:
`SELF_CHALLENGE_GATE`

## Phase 8 — Human / External Validation Register

Identify work requiring:
- independent human review;
- legal review;
- external pentest;
- certification/attestation;
- production privileged access.

Gate:
`EXTERNAL_VALIDATION_REGISTER_COMPLETE`

## Phase 9 — Reporting

Issue appropriate output class.

Gate:
`REPORTING_GATE`

---

# 20. Interim Conclusions

The engagement must not remain useless merely because some external evidence is unavailable.

Permitted outputs:

### INTERIM INVENTORY CONCLUSION
Only discovery/completeness status.

### INTERIM SCOPED TECHNICAL CONCLUSION
Example:
`Auth + Billing + Critical Financial Models @ SHA <sha>`

Must state:
- exact included scope;
- exact excluded scope;
- access level;
- evidence level;
- findings;
- no inference to whole-project readiness.

### FULL TECHNICAL EXAMINATION CONCLUSION
Only after all internally executable procedures are completed and external blockers are fully enumerated.

### EXTERNAL ASSURANCE OPINION
Not issuable by Cursor.

Interim conclusion must never be labeled final institutional readiness.

---

# 21. Scientific / Financial / Model Examination

## Financial
No PASS without independent recomputation for material calculations.

Test:
- formulas;
- Decimal/float;
- persistence;
- rounding;
- signs;
- units;
- percentage/bps;
- zero/null/negative/extreme;
- denominator zero;
- gross/net/fees;
- invariants.

## Quant / Backtests
Applicable tests:
- look-ahead;
- leakage;
- survivorship;
- selection bias;
- data snooping;
- multiple testing;
- overfitting;
- fees/fills/slippage/latency/liquidity;
- OOS/holdout/walk-forward;
- regime sensitivity;
- PBO/CSCV;
- Deflated Sharpe;
- SPA/benchmark as appropriate.

## Model Risk
For Critical/High model-like mechanisms:
- intended/prohibited use;
- materiality;
- conceptual soundness;
- methodology;
- assumptions;
- implementation fidelity;
- independent verification;
- boundary;
- sensitivity;
- stress;
- challenger/benchmark;
- outcomes;
- drift;
- monitoring;
- version/change;
- third-party model risk.

Pytest alone cannot close model validation.

---

# 22. Data / Crypto Examination

For material datapoints:
- provider/source identity;
- asset identity;
- venue/chain;
- wrapped/bridged/forked/renamed/delisted;
- base/quote;
- stablecoin semantics;
- event/ingest/calc/display time;
- timezone;
- freshness/staleness;
- duplicate/replay/out-of-order;
- ZERO/NULL/UNKNOWN/MISSING/ERROR/STALE/PARTIAL;
- reconciliation;
- fallback;
- lineage;
- transforms;
- storage/cache;
- API;
- UI;
- licensing/redistribution.

Rules:
UNKNOWN ≠ zero.
ERROR ≠ empty success.
STALE ≠ LIVE.
NO DATA ≠ NO RISK.

---

# 23. Security / Authorization Examination

Use NIST / ASVS / OWASP API / CIS.

Cover:
- registration/login/logout/reset/MFA;
- sessions/tokens/cookies;
- BOLA/IDOR;
- function-level authorization;
- tenant isolation;
- tier bypass;
- user→admin;
- API keys;
- CSRF;
- XSS;
- injection;
- SSRF;
- file/path;
- webhooks;
- rate/resource abuse;
- secrets;
- crypto/key management;
- admin/debug exposure;
- audit logging.

Behavioral tests required where safely executable.

Decorator counts are not control-effectiveness evidence.

---

# 24. Database / Processing / Billing

Audit:
- schema authority;
- clean database creation;
- migrations;
- schema/model reconciliation;
- constraints;
- indexes;
- CRUD;
- transactions/rollback;
- concurrency;
- numeric precision;
- timestamps;
- cleanup/retention;
- runtime-created schema;
- false-success;
- payment provider → webhook → DB → entitlement → backend → UI.

---

# 25. Test / CI / Supply Chain

Audit:
- full relevant suite execution;
- pass/fail/skip/xfail;
- critical coverage gaps;
- mock realism;
- weak assertions;
- prod/test divergence;
- flaky/retry masking;
- mutation-style reasoning;
- CI gates;
- security scans;
- type/lint;
- build;
- artifact provenance;
- deployment protection;
- rollback;
- secrets;
- SBOM;
- dependency vulnerability;
- dependency integrity;
- OSS licenses;
- SSDF alignment.

---

# 26. Performance / Resilience / DR

Separate measured from theoretical claims.

Where safely executable:
- latency;
- throughput;
- errors;
- concurrency;
- CPU/memory;
- DB pool;
- queues;
- websocket;
- provider ceilings;
- caches;
- multi-worker.

Resilience:
- timeout;
- 5xx;
- malformed/partial response;
- DB/cache unavailable;
- worker crash;
- websocket disconnect;
- AI/payment/provider outage;
- retry storm;
- graceful degradation;
- FMEA;
- backup;
- restore;
- restore drill;
- RTO/RPO;
- regional/multi-AZ claim validation.

---

# 27. Third-Party / IP / Acquisition

For every material third party:
- criticality;
- data/access;
- availability;
- concentration;
- substitutability;
- exit;
- portability;
- licensing;
- monitoring;
- fourth-party visibility.

Acquisition:
- clean reproducible build;
- environment reproducibility;
- key-person dependency;
- maintainability;
- debt;
- OSS obligations;
- provenance;
- market-data rights;
- AI/vendor terms;
- IP gaps;
- portability;
- operational transferability;
- hidden liabilities.

---

# 28. Internal Self-Challenge Passes

These are explicitly **not independent QA**.

1. engagement-method conformance
2. criteria/applicability
3. universe completeness
4. evidence sufficiency
5. finance/model
6. data/crypto
7. security/auth
8. runtime/product/journeys
9. resilience/vendor/acquisition
10. contradictions/arithmetic/coverage

Each records:
- challenged items;
- exceptions;
- reopened procedures;
- result.

If independent assurance is required, a separate qualified human reviewer must validate the work.

---

# 29. Final Completion Logic

A `FULL TECHNICAL EXAMINATION CONCLUSION` may be issued only when:

- Engagement Acceptance Gate = PASS
- Criteria Applicability Gate = PASS
- Canonical Baseline Gate = PASS
- Risk Materiality Gate = PASS
- Discovery Completeness Gate = PASS
- Traceability Design Gate = PASS
- Anti-Fabrication Gate = PASS
- all internally executable Critical/High procedures accounted for
- all unavailable procedures explicitly classified by access class/blocker
- no PASS missing required evidence
- unexplained contradictions = 0
- denominator mismatches = 0
- ten self-challenge passes complete
- external validation register complete
- final reconciliation = PASS

This does **not** convert the result into independent assurance.

---

# 30. Mandatory First-Page Arabic Owner Summary

Every interim/full report begins with one Arabic page containing:

- نوع الفحص ومستوى الاعتماد
- الحكم المختصر
- هل المشروع جاهز للإنتاج؟ نعم/بشروط/لا/غير قابل للإثبات
- هل هو جاهز مؤسسيًا؟ نعم/بشروط/لا/غير قابل للإثبات
- هل هو جاهز للاستحواذ؟ نعم/بشروط/لا/غير قابل للإثبات
- أخطر 10 نقاط
- أقوى 10 نقاط مثبتة
- ما تم فحصه فعليًا
- ما لم يُفحص ولماذا
- ما يحتاج وصولًا خارجيًا/بشريًا
- ماذا يجب ألا يُفهم من التقرير
- القرار المقترح للمالك

---

# 31. Final Report Structure

1. Arabic Owner Summary
2. Engagement Identity / Output Class
3. Intended Users / Prohibited Uses
4. Independence / Objectivity Disclosure
5. Human Governance / Sign-off
6. Scope / Exclusions / Access Matrix
7. Criteria Currentness
8. Applicability Matrix
9. Canonical Baseline
10. Risk / Materiality
11. Universe / Denominators
12. Architecture / Runtime
13. Capabilities / Product Reality
14. Financial
15. Quant / Backtest
16. Model Risk
17. Crypto / Market Data
18. Data Governance / Lineage
19. AI
20. Authn/Authz/Tenancy
21. App/API Security
22. DB / Processing Integrity
23. Billing / Entitlements
24. APIs
25. UI / Journeys
26. Privacy
27. Payment / PCI Scope
28. GIPS / Performance Presentation Scope
29. Testing / CI / SDLC
30. Supply Chain
31. Performance / Scalability
32. Resilience / Backup / Restore / DR
33. Observability / Incident Response
34. Third Party
35. Documentation / Governance
36. Licensing / IP / Data Rights
37. Acquisition Readiness
38. Production Readiness
39. Strengths
40. Findings by taxonomy/severity
41. Contradictions
42. Residual Risk Register
43. External Validation Register
44. Coverage / Denominators
45. Self-Challenge Results
46. Interim or Full Technical Conclusion
47. Confidence / Limitations
48. Management Acceptance
49. Independent Human Reviewer Sign-off — blank unless actually completed

---

# 32. Cursor Execution Instruction

Execute this document as the sole governing SSOT for the examination.

Rules:
- do not call yourself an independent auditor;
- select the engagement output class before fieldwork;
- if owner scope/limitations approval already exists in the instruction, do not ask again;
- do not use prior reports as scope;
- prior reports are evidence candidates only;
- do not use a fixed requirement count;
- create full dynamic Universe;
- map every material Universe object to requirements and procedures;
- every procedure must carry applicability_status and access class;
- enforce anti-fabrication evidence fields;
- separate local/staging/prod/CI/external queues;
- execute all available work without waiting on inaccessible queues;
- produce interim scoped conclusions when useful, without implying whole-project completion;
- no remediation during examination;
- do not ask for approval between phases;
- checkpoint and resume on context limits;
- self-challenge passes are not independent QA;
- do not issue an external assurance opinion;
- do not label anything FINAL institutional assurance unless independently validated by a qualified human reviewer;
- issue a Full Technical Examination Conclusion only after Section 29 conditions pass.

Begin with Phase 0.
