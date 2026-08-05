# Engineering Constitution

**System:** BLACKDARK META CONSTITUTION (BMC)  
**Level:** 4  
**Domain:** Engineering  
**Document role:** Engineering process law derived exclusively from Levels 0 through 3  
**Article schema:** Principle with machine-verifiable predicate

---

### ART-ENG-001

| Field | Value |
|-------|-------|
| Principle | Change introduction requires completed artifact derivation chain per ART-DER-005 before live activation. |
| Verification predicate | Live activation without ART-DER-005 derivation chain hash yields FAIL. |
| Derives from | ART-META-004, ART-DER-005, ART-AUTH-003 |
| Independence | Does not restate derivation mechanics. |

### ART-ENG-002

| Field | Value |
|-------|-------|
| Principle | Deploy context authority is singular per deploy context class. |
| Verification predicate | Multiple live deploy authority records for identical deploy context class yields FAIL. |
| Derives from | ART-AUTH-004, ART-AUTH-005 |
| Independence | Does not restate authority type registry. |

### ART-ENG-003

| Field | Value |
|-------|-------|
| Principle | Resolved dependency identity must be identical across all declared deploy context classes under common authority record. |
| Verification predicate | Deploy context parity check detects dependency identity divergence yields FAIL. |
| Derives from | ART-AUTH-003, ART-AUTH-004 |
| Independence | Does not restate deploy authority singularity. |

### ART-ENG-004

| Field | Value |
|-------|-------|
| Principle | Partial verification success cannot substitute for full verification authority on the same run identity. |
| Verification predicate | Partial pass recorded as full pass on identical run identity yields FAIL. |
| Derives from | ART-DER-007, ART-AUTH-003 |
| Independence | Does not restate evidence identity schema. |

### ART-ENG-005

| Field | Value |
|-------|-------|
| Principle | Invalid configuration for active context class aborts activation before accepting external requests. |
| Verification predicate | Activation with invalid context class configuration yields FAIL before request acceptance. |
| Derives from | ART-AUTH-003, ART-ID-004 |
| Independence | Does not restate service availability class definition. |

### ART-ENG-006

| Field | Value |
|-------|-------|
| Principle | Readiness contract is uniform per deploy context class under common authority record. |
| Verification predicate | Deploy context class without exactly one readiness contract binding yields FAIL. |
| Derives from | ART-AUTH-004, ART-ID-004 |
| Independence | Does not restate deploy parity rules. |

### ART-ENG-007

| Field | Value |
|-------|-------|
| Principle | Composition growth beyond declared size boundary requires decomposition decision per ART-DER-006. |
| Verification predicate | Size boundary exceedance without linked decision record yields FAIL. |
| Derives from | ART-DER-006, ART-AUTH-003 |
| Independence | Does not restate change introduction rules. |
