# BLACKDARK — INSTITUTIONAL TECHNICAL DUE-DILIGENCE PROGRAM 2026
## V4.2 — Operationally Enforceable Package Edition

# 0. SSOT DEFINITION

## FINAL CURSOR FILE SET

The SSOT for execution is exactly these files together:

1. `BLACKDARK_INSTITUTIONAL_DD_PROGRAM_V4_1.md`
2. `BLACKDARK_PARENT_DOMAIN_EXAMINATION_PROGRAM_2026.md`
3. `procedure.schema.json`
4. `evidence.schema.json`
5. `gate_verifier.txt` (source payload; Cursor must copy it byte-for-byte to `gate_verifier.py` inside the audit workspace before execution)
6. `OWNER_ACCEPTANCE_RECORD.json`
7. `RESUME_STATE.json`
8. `DISCOVERY_FREEZE.json`
9. `SCOPE_CHANGE_NOTICE.json`
10. `LOW_POPULATION_REGISTER.json`
11. `INTERIM_SCOPED_REPORT_TEMPLATE.md`
12. `PACKAGE_MANIFEST_SHA256.json`
13. `BUILD_GOVERNANCE_SOURCE_REGISTER.json`
14. `CAPABILITY_MASTER_REGISTER.json`

If any one of the distribution files above is missing, `PROGRAM_PACKAGE_GATE = FAIL`.
No ZIP is required or permitted as the sole delivery mechanism.


**The SSOT is the complete package, not this Markdown file alone.**

Mandatory package contents:
- `BLACKDARK_INSTITUTIONAL_DD_PROGRAM_V4.md`
- `procedure.schema.json`
- `evidence.schema.json`
- `gate_verifier.txt` (source payload; Cursor must copy it byte-for-byte to `gate_verifier.py` inside the audit workspace before execution)
- `OWNER_ACCEPTANCE_RECORD.json`
- `RESUME_STATE.json`
- `DISCOVERY_FREEZE.json`
- `SCOPE_CHANGE_NOTICE.json`

If any mandatory package file is absent:
`PROGRAM_PACKAGE_GATE = FAIL`
and fieldwork must not start.

---

# 1. Mandatory First-Page Disclaimer — Arabic + English

Every report, interim or full, must begin with the following Arabic statement:

> **هذا فحص تقني مؤسسي بمساعدة الذكاء الاصطناعي، وليس تدقيقًا مستقلاً أو شهادة أو رأيًا قانونيًا، ولا يجوز الاعتماد عليه وحده لاتخاذ قرار استثماري أو استحواذ أو إطلاق إنتاجي. أي استخدام خارجي يتطلب مراجعة بشرية مستقلة مؤهلة وفق نطاق الاستخدام.**

And the English equivalent:

> **This is an AI-assisted institutional technical due-diligence examination, not independent assurance, not a certification, not a legal opinion, and not by itself sufficient for an investment, acquisition, regulatory, or production-go-live decision. External reliance requires qualified independent human review appropriate to the intended use.**

Every report must state:
`THIRD_PARTY_SHARING = YES / NO / WITH_CONDITIONS`

---

# 2. Default Engagement Class

Unless the owner explicitly selects another permitted class in Phase 0:

`DEFAULT = CLASS_A — AGREED-UPON TECHNICAL PROCEDURES`

Cursor cannot issue independent assurance.

---

# 3. Owner Acceptance — Source Provenance Required

Before fieldwork, the owner acceptance record must be backed by a real owner-originated artifact.

Accepted sources:
- signed owner record;
- exported/chat message containing explicit owner acceptance;
- approved scope document attributable to the owner.

`OWNER_ACCEPTANCE_RECORD.json` must contain:
- owner identity/name;
- scope version;
- engagement class;
- accepted scope;
- accepted limitations;
- third-party sharing permission;
- acceptance status;
- acceptance timestamp;
- `acceptance_source_artifact_path`;
- `acceptance_source_sha256`.

Cursor may create the JSON container, but **may not invent owner acceptance**.

If source artifact/hash is missing:
`OWNER_ACCEPTANCE_GATE = FAIL`

---

# 4. Independent Human Review for External Sharing

If:
`THIRD_PARTY_SHARING = YES` or `WITH_CONDITIONS`

then before external circulation:
`HUMAN_REVIEW_STATUS = PENDING_HUMAN_REVIEW`

External sharing is prohibited until:
`HUMAN_REVIEW_STATUS = COMPLETE`

A qualified reviewer must have:
- relevant competence for relied-upon domains;
- independence from implementation of the specific controls/models being reviewed, or disclosed conflict with independent coverage;
- access to workpapers/evidence;
- documented scope;
- conflict-of-interest disclosure;
- documented exceptions;
- sign-off.

---

# 5. Gate Verifier — Normative Specification

The package includes:
`gate_verifier.txt` (source payload; Cursor must copy it byte-for-byte to `gate_verifier.py` inside the audit workspace before execution)

## Inputs
It reads, when present:
- `OWNER_ACCEPTANCE_RECORD.json`
- `RESUME_STATE.json`
- `DISCOVERY_FREEZE.json`
- `PROCEDURES.json`
- `EVIDENCE_INDEX.json`
- evidence artifacts referenced by Evidence records

## Output
JSON containing:
- owner_acceptance_gate
- discovery_freeze_gate
- evidence_hash_and_sha_gate
- errors[]
- warnings[]
- GATE_STATUS
- INTERIM_REPORT_ALLOWED
- FINAL_REPORT_ALLOWED

## Exit Codes
- `0` = gate checks passed
- `3` = gate failure / closure prohibited
- `4` = reserved for malformed/unreadable mandatory inputs

## Final rule
Any verifier error causes:
`GATE_STATUS = FAIL`
`FINAL_REPORT_ALLOWED = false`

Interim scoped reporting may continue with explicit failures/blockers.

No Markdown statement may override verifier FAIL.

---

# 6. Evidence Binding to Repository State

Every evidence record must contain both:

- `canonical_sha`
- `observed_repo_sha_at_execution`

They must match the active Discovery Freeze SHA unless the record is explicitly classified as DELTA_SCOPE.

A correct file hash from an old commit is not sufficient.

If execution SHA differs:
`EVIDENCE_SHA_GATE = FAIL`
or the evidence is moved into the documented delta-scope process.

---

# 7. Unified Schemas

Every Procedure must validate against:
`procedure.schema.json`

Every Evidence record must validate against:
`evidence.schema.json`

No session may use an alternate structure.

---

# 8. Discovery Freeze with Controlled Low Residual

Freeze is allowed when:

- Critical unclassified = 0
- High unclassified = 0
- Medium unclassified = 0
- unresolved population mismatches = 0
- Low unclassified residual is documented and ≤ **1%** of discovered Low objects

If Low residual >0:
- every residual item is listed;
- rationale is documented;
- no item has security/financial/data/entitlement/PII/production materiality.

Record in:
`DISCOVERY_FREEZE.json`

A residual Low item that later proves material reopens the freeze.

---

# 9. Refreeze Rule

Mandatory re-freeze occurs at the earliest of:

- 7 calendar days after freeze; OR
- 10 material commits after freeze; OR
- any material scope-change trigger.

Material scope-change triggers include:
- externally exposed service/API
- new auth/tenant boundary
- new payment path
- new financial/model path
- new production datastore
- new critical vendor
- new execution/custody/transfer capability
- new PII category
- new jurisdiction/regulatory exposure

---

# 10. Minimal Standards Set by Engagement Class

Currentness is always verified at execution from official sources.

## CLASS A — mandatory minimum
- IIA principles relevant to integrity/objectivity/due care
- ISRS 4400 (AUP logic)
- NIST SP 800-53A
- domain standards actually implicated by discovered scope

## CLASS B
CLASS A plus:
- ITAF
- ISO 19011
- relevant ISO/NIST/OWASP/CIS/BCBS/FSB/IOSCO criteria for material domains

## CLASS C
CLASS B plus:
- complete currentness review of all material subject-matter criteria used in the final report
- formal applicability matrix
- full coverage/reliance limitations

No class may skip a standard that is materially required by actual BLACKDARK scope.

---

# 11. Home Jurisdiction First

Before evaluating GDPR/CCPA/MiCA/FATF or other jurisdictional rules, record:

- legal entity jurisdiction
- operating jurisdiction
- target-user jurisdictions
- data-subject jurisdictions
- payment/service jurisdictions
- unresolved jurisdiction facts

Field:
`HOME_JURISDICTION_STATUS = VERIFIED / NOT_VERIFIED`

If not verified:
legal conclusions remain:
`APPLICABILITY_NOT_VERIFIED`

Cursor does not provide legal opinions.

---

# 12. FATF / MiCA / GenAI Gates

## FATF
Record:
`FATF_SCOPE = IN / OUT / APPLICABILITY_NOT_VERIFIED`

Assess only if activity could enter VASP/CASP/payment-transfer scope.

## MiCA
Record:
`MICA_SCOPE = IN / OUT / APPLICABILITY_NOT_VERIFIED`

Assess service/marketing implications only after jurisdiction/service scope is known.

## GenAI / Agentic
GenAI/agentic systems always receive AI-specific evaluation under:
- NIST AI RMF
- NIST AI 600-1 where applicable
- ISO/IEC 42001 benchmark
- tool-abuse / prompt-injection / authorization / leakage controls

SR 26-2 model-risk treatment does not replace this AI-specific path.

---

# 13. Finding Taxonomy and Evidence-Gap Escalation

Primary types:
- DEFECT
- CONTROL_DEFICIENCY
- EVIDENCE_GAP
- SCOPE_EXCLUSION
- EXTERNAL_BLOCKER
- OPEN_QUESTION
- CONTRADICTION
- OBSERVATION

An EVIDENCE_GAP on a Critical control escalates to CONTROL_DEFICIENCY only when:
1. evidence should reasonably exist;
2. repeated independent attempts fail;
3. the absence prevents demonstration of operation/monitoring/accountability.

---

# 14. Compound Risk Register

Mandatory:
`COMPOUND_RISK_REGISTER`

Search explicitly for combined risk patterns such as:
- stale data + no disclosure + high confidence;
- weak authorization + predictable identifiers;
- AI tool access + prompt injection + privileged backend tool;
- provider concentration + no fallback + no freshness alert;
- backup claim + no restore evidence;
- entitlement fail-open + premium/institutional feature.

---

# 15. Positive Evidence Register

Mandatory:
`POSITIVE_CONTROL_EVIDENCE_REGISTER`

Verified strengths require positive evidence.

Absence of a finding is not a strength.

---

# 16. Batch and Resume Control

Maximum batch:
- 25 Procedure IDs; OR
- one tightly related Critical population if >25 is technically inseparable.

After every batch update:
`RESUME_STATE.json`

It must record:
- canonical SHA
- freeze ID
- phase
- last completed procedure
- open procedures
- blocked procedures
- open findings
- open contradictions
- delta-scope state
- next action

Resume is prohibited if SHA/freeze mismatch is unresolved.

---

# 17. Sharing and Short-Form Control

If:
`THIRD_PARTY_SHARING = NO`

then creation of:
`BLACKDARK_TECHNICAL_DUE_DILIGENCE_EXTERNAL_SUMMARY.md`

is prohibited.

If sharing is allowed:
- human review must be COMPLETE;
- short form must preserve material findings, blockers, coverage and reliance restrictions;
- promotional/selective omission is prohibited.

---

# 18. Arabic Owner Summary — Mandatory

Every report begins with a one-page Arabic owner summary containing:

- نوع الفحص
- مستوى الاعتماد
- الحكم المختصر
- جاهزية الإنتاج
- الجاهزية المؤسسية
- جاهزية الاستحواذ
- أخطر 10 نقاط
- أقوى 10 نقاط مثبتة
- ما تم فحصه
- ما لم يُفحص
- الـblockers
- نسب coverage حسب access class
- هل القيود المادية تمنع الاعتماد
- **هل يُسمح بعرض التقرير على طرف ثالث؟ نعم / لا / بشروط**
- حالة المراجعة البشرية
- القرار المقترح للمالك

---

# 19. Management Acceptance

Final owner status:
- ACCEPTED
- PARTIALLY_ACCEPTED
- REJECTED
- NOT_REVIEWED

If PARTIALLY_ACCEPTED or REJECTED:
- rejected findings/limitations are listed;
- third-party sharing defaults to NO;
- report cannot be represented as fully management-approved.

---

# 20. Full Technical Conclusion — Reliance Control

Any Full Technical Examination Conclusion must state in the first paragraph:

- coverage ratios by execution class;
- exact blocker counts;
- L0/L1/L2/L3/L4/L5 coverage;
- whether blocked evidence materially limits reliance.

If material access is blocked:
`RELIANCE_LIMITATION = MATERIAL`

“Full” means the defined technical examination program was completed to its documented access boundary.

It does **not** mean inaccessible environments were examined.
It does **not** mean independent assurance was obtained.

---

# 21. Documentation QA vs Execution QA

Two separate statuses are mandatory.

## DOCUMENTATION_QA
Checks whether the program specifies the required controls.

## EXECUTION_ENFORCEMENT_QA
Checks whether:
- package files exist;
- schemas are used;
- evidence files exist;
- hashes validate;
- execution SHA matches freeze;
- gates actually execute;
- owner acceptance provenance validates;
- state/freeze consistency holds.

`DOCUMENTATION_QA = PASS` is never execution proof.

---

# 22. Risk Priority

If sequencing is constrained:

1. auth/authz/tenant/secrets
2. financial correctness / execution-adjacent outputs
3. billing/entitlements
4. data integrity/freshness/lineage
5. model/AI
6. DB/processing integrity
7. resilience/recovery
8. institutional/paid journeys
9. remaining product/UI
10. low-risk docs/cosmetic

Order changes. Scope does not.

---

# 23. Final Machine Rules

Before fieldwork:
- package gate PASS
- owner acceptance PASS
- criteria currentness appropriate to engagement class
- canonical target PASS

Before freeze:
- Critical/High/Medium unclassified = 0
- Low residual ≤1%, documented
- population mismatch = 0

Before any PASS:
- schema-valid Procedure
- schema-valid Evidence
- real artifact
- valid SHA-256
- observed_repo_sha_at_execution matches freeze/canonical SHA

Before final:
- `python gate_verifier.py` exit code 0
- all material procedures accounted for
- all Critical/High executable work complete or legitimately blocked
- contradictions reconciled
- ten self-challenge passes complete
- compound risk register complete
- positive evidence register complete
- external validation register complete
- management acceptance status recorded
- coverage/reliance statement complete

A verifier exit code 3 means:
- final closure prohibited;
- interim report allowed with explicit failure details.



# 24. Substance Hierarchy and Parent-Program Relationship

The enforceable package does not replace the detailed subject-matter depth of `BLACKDARK_PARENT_DOMAIN_EXAMINATION_PROGRAM_2026.md`, which is the mandatory parent domain examination program.

Governing hierarchy:

1. `BLACKDARK_INSTITUTIONAL_DD_PROGRAM_V4_1.md` governs enforcement, package integrity, state, evidence binding, gates, freeze, resumption, and reporting controls.
2. `BLACKDARK_PARENT_DOMAIN_EXAMINATION_PROGRAM_2026.md` governs examination depth, domain-specific test substance, and required subject-matter coverage unless explicitly superseded here.
3. On conflict about enforcement or execution control, V4.1 wins.
4. On conflict about examination depth, the stricter material requirement wins.

No domain may be omitted merely because V4.1 summarizes operational controls rather than restating the full domain program.

---

# 25. Runtime Artifacts — Mandatory After Phase 0

The following are runtime artifacts and MUST exist before executable fieldwork begins:

- `PROCEDURES.json`
- `EVIDENCE_INDEX.json`
- `FINDINGS_REGISTER.json`
- `CONTRADICTION_REGISTER.json`
- `COMPOUND_RISK_REGISTER.json`
- `POSITIVE_CONTROL_EVIDENCE_REGISTER.json`

Rules:
- absence of `PROCEDURES.json` or `EVIDENCE_INDEX.json` after Phase 0 causes `RUNTIME_ARTIFACT_GATE = FAIL`;
- they are not required in the unopened distribution package before Phase 0;
- after creation, they become part of the live audit SSOT.

---

# 26. Verifier Conformance Self-Check

At every new audit run or verifier change:

1. calculate SHA-256 of `gate_verifier.txt` (source payload; Cursor must copy it byte-for-byte to `gate_verifier.py` inside the audit workspace before execution);
2. compare it with `PACKAGE_MANIFEST_SHA256.json`;
3. execute a verifier conformance self-test;
4. confirm documented exit-code behavior;
5. record:
   - verifier SHA
   - self-test timestamp
   - self-test result
   - package version

Required status:
`VERIFIER_CONFORMANCE = PASS`

If verifier code differs from the package manifest without an approved package-version change:
`PROGRAM_PACKAGE_GATE = FAIL`

An exit code 0 from the verifier means only that package/gate conditions passed.
It does NOT mean BLACKDARK itself is defect-free, production-ready, or institutionally approved.

---

# 27. Recovery from Verifier Input Error

If `gate_verifier.txt` (source payload; Cursor must copy it byte-for-byte to `gate_verifier.py` inside the audit workspace before execution) returns exit code 4:

1. do not alter findings or downgrade requirements;
2. identify the malformed or unreadable mandatory input;
3. repair only the invalid input structure/content;
4. preserve the previous artifact and hash it in an error-recovery folder;
5. rerun the verifier;
6. record the recovery event in `RESUME_STATE.json`.

Final closure remains prohibited until a subsequent verifier run returns 0.

---

# 28. Material Commit Definition

A commit is `MATERIAL` if it changes any of the following:

- authentication, authorization, tenancy, admin, session or secret handling;
- billing, subscription, entitlement or payment-webhook behavior;
- financial formulas, indicators, recommendations, risk or execution-adjacent logic;
- model/AI behavior, prompts, tools, policies or inference routing;
- public/private API behavior or schema;
- data-source/provider mapping, freshness, lineage, normalization or fallback;
- database schema, migration, transaction or persistence semantics;
- production configuration, deployment topology or resilience behavior;
- privacy/PII handling;
- feature flags or runtime configuration that can alter a material behavior.

Non-material commits are limited to changes demonstrably incapable of altering material runtime behavior, such as cosmetic documentation-only edits.

When uncertain:
`MATERIAL_COMMIT = YES`

---

# 29. Human Review Freshness and Expiry

For any externally shareable report:

- `HUMAN_REVIEW_STATUS = COMPLETE`
- `HUMAN_REVIEW_COMPLETED_AT_UTC` must be recorded.
- `HUMAN_REVIEW_BASELINE_SHA` must match the externally shared report baseline.
- `HUMAN_REVIEW_EXPIRY_STATUS` must be CURRENT.

Human review becomes stale when the earliest occurs:

- a material commit after the reviewed SHA;
- a material scope-change notice;
- a mandatory refreeze;
- 30 calendar days after human review for externally relied-upon outputs.

If stale:
`HUMAN_REVIEW_STATUS = EXPIRED`
and third-party sharing is prohibited until refreshed.

---

# 30. Low Residual Denominator Integrity

The ≤1% Low residual allowance may be calculated only after:

1. all discovered objects have a preliminary classification;
2. Critical/High/Medium populations are closed;
3. Low population definition is frozen;
4. the Low denominator is exported to `LOW_POPULATION_REGISTER.json`;
5. every residual object has a unique Universe ID.

The denominator is:
`all objects classified LOW before residual exclusion`

It is prohibited to reduce the denominator by removing uncertain objects.

Objects with uncertain materiality are not Low.
They remain `UNCLASSIFIED_MATERIALITY` and prevent freeze.

---

# 31. Feature Flags / Dark Launch / Runtime Configuration

Discovery and freeze MUST include behavior-changing runtime state, including:

- feature flags;
- dark launches;
- experiments;
- kill switches;
- remote configuration;
- environment variables;
- tenant-specific overrides;
- staged rollout percentages;
- hidden/admin-only toggles;
- provider-routing configuration.

At freeze:
- record relevant flag/config state;
- hash/export configuration where possible;
- classify each material flag.

Any post-freeze material flag/config change triggers `DELTA_SCOPE` even if repository SHA is unchanged.

---

# 32. Interim Scoped Report Template

Permitted filename:

`BLACKDARK_INTERIM_SCOPED_TECHNICAL_EXAMINATION_<SCOPE>_<SHA>.md`

Mandatory first-page fields:

- engagement class;
- baseline SHA;
- freeze ID;
- exact included scope;
- exact excluded scope;
- execution classes covered;
- coverage numerator/denominator;
- blockers;
- material limitations;
- findings;
- reliance restriction;
- third-party sharing status;
- human-review status.

Mandatory statement:

> This interim scoped conclusion applies only to the explicitly listed scope and evidence boundary. It must not be interpreted as a conclusion on BLACKDARK as a whole.

---

# 33. External Owner-Acceptance Strengthening

For internal use, owner-originated chat/export evidence with hash is acceptable.

For any external reliance:
- the owner must provide a signed or otherwise authenticated acceptance/reliance acknowledgment;
- the external-use acceptance must reference the report version, SHA, scope and limitations;
- a simple agent-generated text file is insufficient.

Record:
`EXTERNAL_OWNER_ACK_STATUS = COMPLETE / PENDING / NOT_REQUIRED`

If third-party sharing is permitted but external owner acknowledgment is not complete:
`THIRD_PARTY_SHARING_EFFECTIVE = NO`

---

# 34. Mandatory Arabic Owner Summary Preservation

The Arabic Owner Summary requirement is native to V4.1 and does not depend on any parent version.

Every interim and full report MUST retain the complete Arabic first-page summary specified in Section 18.

Omission:
`REPORTING_GATE = FAIL`



# 35. Mandatory Capability Reality & Duplication Examination

This section is mandatory and must be completed before any final BLACKDARK conclusion.

Cursor must build a complete capability population from:
- current codebase;
- UI/navigation;
- APIs/routes;
- backend services;
- database/schema;
- jobs/workers;
- tests;
- runtime-reachable functionality;
- current product documentation;
- all 12 historical build/governance source files registered under Section 36.

Each discovered capability receives a unique `CAPABILITY_ID`.

Every capability must receive exactly one primary implementation status:

- `IMPLEMENTED`
- `PARTIAL`
- `NOT_IMPLEMENTED`
- `DEFECTIVE`
- `BACKEND_ONLY`
- `UI_ONLY`
- `DEAD_OR_UNREACHABLE`
- `MOCK_OR_STUB`
- `BLOCKED_EXTERNAL`
- `NOT_APPLICABLE`
- `NOT_VERIFIED`

For every capability record, capture at minimum:
- Capability ID
- canonical capability name
- alternate/historical names
- originating source file(s)
- requirement/decision IDs if present
- UI surface(s)
- backend implementation path(s)
- API path(s)
- data dependency
- entitlement/tier
- test evidence
- runtime evidence
- implementation status
- defect/finding IDs
- completeness percentage only if objectively derivable
- evidence IDs
- notes/limitations

## 35.1 Mandatory Final Capability Registers

The final audit package MUST contain all of the following:

### A. `CAPABILITY_MASTER_REGISTER.json`
Complete canonical capability population.

### B. `CAPABILITIES_NOT_IMPLEMENTED.json`
All capabilities required/claimed by governing sources but absent from actual implementation.

### C. `CAPABILITIES_PARTIAL.json`
All capabilities with incomplete implementation, incomplete wiring, missing runtime path, missing data path, incomplete UI/backend integration, incomplete entitlement, incomplete tests, or other material incompleteness.

### D. `CAPABILITIES_DEFECTIVE.json`
Capabilities that exist but contain confirmed defects, incorrect behavior, false-success behavior, broken calculations, broken access control, stale/incorrect data handling, broken UI/backend wiring, or other material implementation problems.

### E. `CAPABILITY_DUPLICATION_REGISTER.json`
All exact or functional duplication.

Each duplication record must classify one of:
- `EXACT_DUPLICATE`
- `FUNCTIONAL_OVERLAP`
- `SAME_CAPABILITY_DIFFERENT_NAME`
- `BACKEND_DUPLICATE`
- `UI_DUPLICATE`
- `CONFLICTING_IMPLEMENTATIONS`
- `SUPERSEDED_IMPLEMENTATION`

Each duplication record must include:
- involved Capability IDs
- involved names
- locations
- overlap description
- whether outputs/logic differ
- user-facing consequence
- maintenance consequence
- institutional consequence
- recommended classification only; no remediation during audit

### F. `CAPABILITY_STATUS_SUMMARY.md`
Must report exact denominators and counts:

- Total canonical capabilities
- Implemented
- Partial
- Not implemented
- Defective
- Backend only
- UI only
- Dead/unreachable
- Mock/stub
- Blocked external
- Not verified
- Duplicate/overlap groups

No vague wording such as "most capabilities" is permitted.

## 35.2 Capability Completion Gate

Before final reporting:

- capabilities without status = 0
- capabilities without evidence or explicit NOT_VERIFIED reason = 0
- governing-source capability claims not reconciled = 0
- duplicate candidates not adjudicated = 0
- capability denominator mismatch = 0

Then:
`CAPABILITY_RECONCILIATION_GATE = PASS`

Otherwise:
`CAPABILITY_RECONCILIATION_GATE = FAIL`
and final closure is prohibited.

---

# 36. Mandatory 12-File Build/Governance Reconciliation

The 12 historical files previously used to govern/build BLACKDARK are mandatory audit inputs.

They are NOT automatically trusted as truth.
They are authoritative historical build/governance sources whose claims must be reconciled against the current canonical implementation.

Create:
`BUILD_GOVERNANCE_SOURCE_REGISTER.json`

The register MUST contain exactly 12 source entries before this gate can pass.

Each source entry must contain:
- `source_id`
- exact filename
- file hash
- source type
- source date/version if known
- whether fully read
- extracted capability count
- extracted requirement count
- extracted decision count
- extracted constraint count
- extracted defect/risk count
- unresolved parsing issues
- evidence reference

Cursor must read every one of the 12 files completely.

If fewer than 12 real source files are available:
`BUILD_GOVERNANCE_SOURCE_GATE = FAIL`

Cursor must not invent missing filenames or substitute unrelated files.

## 36.1 Required Extraction

From the 12 files, extract and normalize:

- capabilities/features
- requirements
- mandatory decisions
- constraints
- architecture obligations
- data-source obligations
- security obligations
- model/financial obligations
- UI/product obligations
- pricing/entitlement obligations
- operational obligations
- testing/validation obligations
- known defects/open issues
- explicit exclusions
- superseded decisions

Create:
`BUILD_GOVERNANCE_EXTRACTED_CLAIMS.json`

Each extracted item receives:
`GOVCLAIM_ID`

## 36.2 Mandatory Reconciliation Status

Every `GOVCLAIM_ID` must receive exactly one status:

- `VERIFIED_IMPLEMENTED`
- `PARTIALLY_IMPLEMENTED`
- `NOT_IMPLEMENTED`
- `DEFECTIVE_IMPLEMENTATION`
- `DUPLICATED`
- `SUPERSEDED`
- `CONTRADICTED`
- `NOT_APPLICABLE`
- `BLOCKED_EXTERNAL`
- `NOT_VERIFIED`

Each reconciliation record must link:
- source file
- source location/reference
- Capability/Requirement/Decision ID
- code/runtime evidence
- finding IDs where applicable
- contradiction IDs where applicable

Create:
`BUILD_GOVERNANCE_RECONCILIATION_REGISTER.json`

## 36.3 Cross-File Duplication / Conflict Review

The 12 files must also be compared against each other for:

- duplicate capabilities
- duplicate requirements
- same concept under different names
- conflicting requirements
- superseded decisions
- duplicated implementation mandates
- contradictory constraints

Create:
`BUILD_GOVERNANCE_CROSS_SOURCE_DUPLICATION.json`

No duplicate is deleted silently.
Canonicalization must preserve source provenance.

## 36.4 12-File Reconciliation Gate

Required before final conclusion:

- source files registered = 12
- source files fully read = 12
- unresolved source-read failures = 0
- extracted material claims without GOVCLAIM_ID = 0
- GOVCLAIM_ID without reconciliation status = 0
- unresolved cross-source duplicate candidates = 0
- unresolved material contradictions = 0 or explicitly BLOCKED with evidence

Then:
`BUILD_GOVERNANCE_SOURCE_GATE = PASS`

Otherwise final closure is prohibited.

---

# 37. Final Report — Mandatory Capability & Governance Sections

The final report MUST contain distinct sections titled:

1. **Capabilities Fully Implemented**
2. **Capabilities Partially Implemented**
3. **Capabilities Not Implemented**
4. **Capabilities Implemented but Defective**
5. **Capability Duplication and Functional Overlap**
6. **Dead / Mock / Stub / Unreachable Capabilities**
7. **Backend-Only and UI-Only Capabilities**
8. **12-File Build/Governance Reconciliation**
9. **Cross-Source Conflicts and Superseded Decisions**
10. **Capability Denominator and Coverage Reconciliation**

For each section show exact counts and IDs.

The Arabic Owner Summary must explicitly state:

- عدد القدرات الكلي
- عدد المكتمل
- عدد غير المكتمل
- عدد غير المبني
- عدد الذي به عيوب
- عدد مجموعات التكرار/التداخل
- هل تمت مراجعة الـ12 ملف الحاكمين بالكامل؟ نعم/لا
- عدد المطالب/القرارات غير المتصالحة
- أثر ذلك على الجاهزية

---

# 38. Final Closure Extension

In addition to all previous V4.1 gates, FINAL closure now also requires:

`CAPABILITY_RECONCILIATION_GATE = PASS`
and
`BUILD_GOVERNANCE_SOURCE_GATE = PASS`

If either fails:
`FINAL_REPORT_ALLOWED = FALSE`

Interim scoped reporting remains allowed with explicit limitations.

