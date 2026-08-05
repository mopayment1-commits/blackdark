# Constitutional Traceability

**Program:** BLACKDARK INSTITUTIONAL ENGINEERING CONSTITUTION (BIEC)  
**Document role:** Sole derivation map from constitution to downstream artifact classes  
**Article schema:** Derivation rule with machine-verifiable predicate

---

## Supremacy

| Field | Value |
|-------|-------|
| Governing authority | BLACKDARK INSTITUTIONAL ENGINEERING CONSTITUTION (BIEC) |
| Constitution documents | ENGINEERING, ARCHITECTURE, FINANCIAL, SECURITY, AI, DATA, PLATFORM, GOVERNANCE, QUALITY |
| Reference evidence class | Superseded program artifacts hold zero execution authority per ART-GOV-012 |

---

## Derivation Rules

### D-001 Architectural Decision Derivation

| Field | Value |
|-------|-------|
| Input | Any proposed architectural decision record |
| Rule | Every decision field must cite one or more constitution article identifiers as sole justification source |
| Verification predicate | Decision record with empty constitution citation set or citation to nonexistent article identifier yields FAIL |
| Output authority class | ARCHITECTURAL_DECISION |

### D-002 Finding Derivation

| Field | Value |
|-------|-------|
| Input | Any proposed finding record |
| Rule | Finding statement must map to violated constitution article identifiers and restate the article verification predicate failure condition |
| Verification predicate | Finding without constitution article linkage or without restated failure condition yields FAIL |
| Output authority class | FINDING |

### D-003 Corrective Control Derivation

| Field | Value |
|-------|-------|
| Input | Any proposed corrective control record |
| Rule | Corrective control must restate target behavior that satisfies the linked article principle and define observable state where verification predicate passes |
| Verification predicate | Control lacking principle restatement or lacking pass-state definition yields FAIL |
| Output authority class | CORRECTIVE_CONTROL |

### D-004 Preventive Control Derivation

| Field | Value |
|-------|-------|
| Input | Any proposed preventive control record |
| Rule | Preventive control must restate article verification predicate as blocking recurrence gate with explicit FAIL semantics |
| Verification predicate | Preventive control described as non-blocking or without FAIL semantics yields FAIL |
| Output authority class | PREVENTIVE_CONTROL |

### D-005 Implementation Contract Derivation

| Field | Value |
|-------|-------|
| Input | Any proposed implementation contract record |
| Rule | Contract may be created only from linked corrective or preventive control records that already satisfy D-003 or D-004 |
| Verification predicate | Contract with direct manual requirement text not traceable to control record yields FAIL |
| Output authority class | IMPLEMENTATION_CONTRACT |

### D-006 Test Derivation

| Field | Value |
|-------|-------|
| Input | Any proposed test record |
| Rule | Test must assert the verification predicate of the linked constitution article or derived control verbatim as pass-fail condition |
| Verification predicate | Test without linked article or control predicate citation yields FAIL |
| Output authority class | TEST |

### D-007 Manual Creation Prohibition

| Field | Value |
|-------|-------|
| Input | Any downstream artifact in classes D-001 through D-006 |
| Rule | Manual creation without constitution derivation chain is forbidden |
| Verification predicate | Artifact metadata missing derivation chain hash yields FAIL |
| Output authority class | DERIVATION_ENFORCEMENT |

---

## Article Index by Authority Domain

| Authority domain | Constitution document | Article prefix | Article count |
|------------------|----------------------|----------------|---------------|
| Engineering process | ENGINEERING_CONSTITUTION.md | ART-ENG | 10 |
| Structure and topology | ARCHITECTURE_CONSTITUTION.md | ART-ARCH | 10 |
| Monetary precision | FINANCIAL_CONSTITUTION.md | ART-FIN | 6 |
| Execution authorization and isolation | SECURITY_CONSTITUTION.md | ART-SEC | 11 |
| Inference and machine learning | AI_CONSTITUTION.md | ART-AI | 6 |
| Price and data authority | DATA_CONSTITUTION.md | ART-DATA | 6 |
| Platform boundary | PLATFORM_CONSTITUTION.md | ART-PLAT | 7 |
| Enumeration and supremacy | GOVERNANCE_CONSTITUTION.md | ART-GOV | 13 |
| Evidence and institutional quality | QUALITY_CONSTITUTION.md | ART-QUAL | 10 |

---

## Cross-Document Complementarity Map

| Primary article | Complement article | Relationship |
|-----------------|-------------------|--------------|
| ART-GOV-000 | ART-GOV-012 | Supremacy and superseded reference class |
| ART-GOV-001 | ART-GOV-002 | Attested authority versus non-authoritative grid |
| ART-GOV-001 | ART-GOV-003 | Enumeration versus crosswalk cardinality |
| ART-GOV-001 | ART-GOV-007 | Attestation versus marketing narrative |
| ART-GOV-001 | ART-GOV-008 | Attestation integrity versus publication |
| ART-DATA-001 | ART-DATA-002 | Canonical API versus substrate prohibition |
| ART-DATA-001 | ART-DATA-003 | Public canonical versus internal aggregation |
| ART-DATA-004 | ART-DATA-005 | Execution freshness versus scan freshness |
| ART-SEC-001 | ART-SEC-002 | Master switch versus deny semantics |
| ART-SEC-001 | ART-SEC-003 | Authorization versus connector gate |
| ART-SEC-006 | ART-SEC-007 | Route exclusion versus manifest proof |
| ART-ARCH-001 | ART-ARCH-002 | Platform count versus replica profile |
| ART-ARCH-004 | ART-ARCH-005 | Profile contract versus mixed boot prohibition |
| ART-ENG-003 | ART-ENG-004 | Full collection versus subset prohibition |
| ART-ENG-008 | ART-ENG-009 | Readiness contract versus launch parity |
| ART-QUAL-001 | ART-QUAL-007 | Schema validation versus version policy |
| ART-QUAL-002 | ART-QUAL-003 | Scope enum versus hourly integrity veto |
| ART-FIN-001 | ART-FIN-002 | Storage decimal versus new column prohibition |
| ART-FIN-003 | ART-FIN-004 | Decimal path versus boundary invariant |
| ART-AI-001 | ART-AI-005 | Inference entry versus import allow list |
| ART-AI-002 | ART-AI-006 | Separation versus saturation guard boundary |
| ART-PLAT-001 | ART-PLAT-003 | Facade imports versus route owner sync |
| ART-SEC-009 | ART-PLAT-002 | Access facade platform and security views |

---

## Total Article Count

| Metric | Value |
|--------|-------|
| Total constitution articles | 79 |
| Derivation rules | 7 |
| Constitution documents | 10 |

---

## Acceptance Predicate Summary

| Criterion | Verification predicate |
|-----------|------------------------|
| Exactly one governing authority | ART-GOV-000 present; zero competing supremacy declarations |
| Exactly one document per authority domain | Ten files exist under BIEC with distinct roles in index table |
| Zero duplicated principles | Pairwise principle text equality count equals zero |
| Zero contradictory principles | No pair of principles with mutually exclusive pass conditions under same scope |
| Zero implementation content | Constitution corpus contains zero file path literals and zero module identifiers |
| Zero superseded execution authority | ART-GOV-012 verification predicate pass |
