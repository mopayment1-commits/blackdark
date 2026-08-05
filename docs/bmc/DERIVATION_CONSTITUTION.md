# Derivation Constitution

**System:** BLACKDARK META CONSTITUTION (BMC)  
**Level:** 3  
**Document role:** Sole artifact derivation authority  
**Article schema:** Derivation rule with machine-verifiable predicate

---

### ART-DER-001

| Field | Value |
|-------|-------|
| Input class | Feature |
| Rule | Feature identity may be created only from attestation authority record satisfying ART-AUTH-004 exclusivity for feature scope class. |
| Verification predicate | Feature identity without attestation authority linkage yields FAIL. |
| Output class | FEATURE_IDENTITY |
| Derives from | ART-META-004, ART-ID-001, ART-AUTH-004 |

### ART-DER-002

| Field | Value |
|-------|-------|
| Input class | Capability |
| Rule | Capability identity may be created only from taxonomy authority record and must bind to exactly one scope boundary predicate. |
| Verification predicate | Capability identity without taxonomy authority linkage or without scope boundary yields FAIL. |
| Output class | CAPABILITY_IDENTITY |
| Derives from | ART-META-004, ART-ID-002, ART-AUTH-004 |

### ART-DER-003

| Field | Value |
|-------|-------|
| Input class | Platform |
| Rule | Platform identity may be created only from platform authority record and must bind to exactly one ownership identity. |
| Verification predicate | Platform identity without platform authority linkage or without ownership binding yields FAIL. |
| Output class | PLATFORM_IDENTITY |
| Derives from | ART-META-004, ART-ID-003, ART-AUTH-004 |

### ART-DER-004

| Field | Value |
|-------|-------|
| Input class | Service |
| Rule | Service identity may be created only from service authority record with declared availability class. |
| Verification predicate | Service identity without service authority linkage or availability class yields FAIL. |
| Output class | SERVICE_IDENTITY |
| Derives from | ART-META-004, ART-ID-004, ART-AUTH-004 |

### ART-DER-005

| Field | Value |
|-------|-------|
| Input class | Artifact |
| Rule | Artifact may be created only when derivation chain cites one Level 3 rule and all upstream identity and authority prerequisites are satisfied. |
| Verification predicate | Artifact with incomplete derivation chain hash yields FAIL. |
| Output class | ARTIFACT |
| Derives from | ART-META-004, ART-ID-005, ART-AUTH-003 |

### ART-DER-006

| Field | Value |
|-------|-------|
| Input class | Decision |
| Rule | Decision may be created only when every decision field cites one or more Level 0 through Level 4 article identifiers as sole justification source. |
| Verification predicate | Decision with empty constitution citation set or invalid article reference yields FAIL. |
| Output class | DECISION |
| Derives from | ART-META-004, ART-ID-006, ART-AUTH-003 |

### ART-DER-007

| Field | Value |
|-------|-------|
| Input class | Evidence |
| Rule | Evidence may be created only to assert a verification predicate from a cited constitution article or derived control. |
| Verification predicate | Evidence without cited predicate source or without integrity signature yields FAIL. |
| Output class | EVIDENCE |
| Derives from | ART-META-004, ART-ID-007, ART-DER-005 |

### ART-DER-008

| Field | Value |
|-------|-------|
| Input class | Dataset |
| Rule | Dataset identity may be created only from data authority record with lineage binding to source class. |
| Verification predicate | Dataset without data authority linkage or lineage binding yields FAIL. |
| Output class | DATASET_IDENTITY |
| Derives from | ART-META-004, ART-ID-008, ART-AUTH-004 |

### ART-DER-009

| Field | Value |
|-------|-------|
| Input class | Model |
| Rule | Model identity may be created only from model authority record with provenance binding separating training class from serving class. |
| Verification predicate | Model without model authority linkage or with undifferentiated training and serving class yields FAIL. |
| Output class | MODEL_IDENTITY |
| Derives from | ART-META-004, ART-ID-009, ART-AUTH-004 |

### ART-DER-010

| Field | Value |
|-------|-------|
| Input class | Finding |
| Rule | Finding may be created only when statement maps to violated article identifiers and restates failed verification predicate condition. |
| Verification predicate | Finding without article linkage or without restated failure condition yields FAIL. |
| Output class | FINDING |
| Derives from | ART-META-004, ART-DER-005, ART-DER-006 |

### ART-DER-011

| Field | Value |
|-------|-------|
| Input class | Control |
| Rule | Corrective control must restate target behavior satisfying cited article principle; preventive control must restate verification predicate as blocking gate with explicit FAIL semantics. |
| Verification predicate | Control lacking principle restatement, lacking pass-state definition, or preventive control without FAIL semantics yields FAIL. |
| Output class | CONTROL |
| Derives from | ART-META-004, ART-DER-010 |

### ART-DER-012

| Field | Value |
|-------|-------|
| Input class | Test |
| Rule | Test may be created only when assert condition matches cited article verification predicate or derived control predicate verbatim. |
| Verification predicate | Test without linked predicate citation yields FAIL. |
| Output class | TEST |
| Derives from | ART-META-004, ART-DER-011 |

### ART-DER-013

| Field | Value |
|-------|-------|
| Input class | Governance decision |
| Rule | Governance decision may be created only from governance authority record and must declare affected identity class and authority scope. |
| Verification predicate | Governance decision without governance authority linkage or without affected scope declaration yields FAIL. |
| Output class | GOVERNANCE_DECISION |
| Derives from | ART-META-004, ART-ID-006, ART-AUTH-004, ART-DER-006 |

### ART-DER-014

| Field | Value |
|-------|-------|
| Input class | Feature-capability binding |
| Rule | Each attested feature identity binds to exactly one primary capability identity through crosswalk authority record. |
| Verification predicate | Feature with zero or multiple primary capability bindings yields FAIL. |
| Output class | FEATURE_CAPABILITY_BINDING |
| Derives from | ART-DER-001, ART-DER-002, ART-AUTH-004 |

### ART-DER-015

| Field | Value |
|-------|-------|
| Input class | Manual creation |
| Rule | Manual creation of any artifact in classes ART-DER-001 through ART-DER-014 without complete derivation chain is forbidden. |
| Verification predicate | Artifact metadata missing derivation chain hash yields FAIL. |
| Output class | DERIVATION_ENFORCEMENT |
| Derives from | ART-META-004, ART-DER-005 |
