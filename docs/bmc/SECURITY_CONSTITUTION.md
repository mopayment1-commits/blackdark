# Security Constitution

**System:** BLACKDARK META CONSTITUTION (BMC)  
**Level:** 4  
**Domain:** Security  
**Document role:** Authorization and isolation law derived exclusively from Levels 0 through 3  
**Article schema:** Principle with machine-verifiable predicate

---

### ART-SEC-001

| Field | Value |
|-------|-------|
| Principle | Exactly one master execution authorization authority governs all live order placement under exclusivity per ART-AUTH-004. |
| Verification predicate | Live order placement without master authorization authority consult yields FAIL. |
| Derives from | ART-AUTH-004, ART-AUTH-005 |
| Independence | Does not restate authority type registry. |

### ART-SEC-002

| Field | Value |
|-------|-------|
| Principle | Execution authorization conflict or unknown state yields DENY. |
| Verification predicate | GRANT on UNKNOWN or CONFLICT state without precedence basis yields FAIL. |
| Derives from | ART-AUTH-005, ART-AUTH-003 |
| Independence | Does not restate master authorization singularity. |

### ART-SEC-003

| Field | Value |
|-------|-------|
| Principle | External connector invocation requires successful unified authorization consult before external input-output. |
| Verification predicate | External input-output success without prior authorization consult yields FAIL. |
| Derives from | ART-AUTH-003, ART-AUTH-004 |
| Independence | Does not restate deny semantics. |

### ART-SEC-004

| Field | Value |
|-------|-------|
| Principle | Multi-subject data access requires mandatory tenant context on all user-scoped operations. |
| Verification predicate | Cross-tenant access attempt succeeding yields FAIL. |
| Derives from | ART-ID-010, ART-ID-011, ART-AUTH-003 |
| Independence | Does not restate execution authorization rules. |

### ART-SEC-005

| Field | Value |
|-------|-------|
| Principle | Production context class excludes demonstration and development surface classes at activation boundary. |
| Verification predicate | Demonstration surface class active in production context yields FAIL. |
| Derives from | ART-AUTH-003, ART-ID-003 |
| Independence | Does not restate tenant isolation. |

### ART-SEC-006

| Field | Value |
|-------|-------|
| Principle | Production activation emits signed surface manifest matching production allow list under security authority record. |
| Verification predicate | Manifest divergence from allow list in production context yields FAIL. |
| Derives from | ART-AUTH-004, ART-DER-007 |
| Independence | Does not restate surface exclusion rule. |

### ART-SEC-007

| Field | Value |
|-------|-------|
| Principle | Privileged tier authentication requires multi-factor verification when authority record demands it. |
| Verification predicate | Single-factor success under mandatory multi-factor authority record yields FAIL. |
| Derives from | ART-AUTH-003, ART-ID-010 |
| Independence | Does not restate production surface rules. |

### ART-SEC-008

| Field | Value |
|-------|-------|
| Principle | Tier and role authorization for platform actions routes through one centralized access authority record under exclusivity per ART-AUTH-004. |
| Verification predicate | Ad hoc tier check outside access authority record yields FAIL. |
| Derives from | ART-AUTH-004, ART-ID-003 |
| Independence | Sole access-authority article; no parallel restatement in other domains. |

### ART-SEC-009

| Field | Value |
|-------|-------|
| Principle | Live credential validation uses fixture credential class in automated verification context. |
| Verification predicate | Automated verification pass depending on non-declared live credential store yields FAIL. |
| Derives from | ART-DER-007, ART-AUTH-003 |
| Independence | Does not restate access authority singularity. |

### ART-SEC-010

| Field | Value |
|-------|-------|
| Principle | Public regulatory verdict transformation uses one compliance authority entry under exclusivity per ART-AUTH-004. |
| Verification predicate | Verdict emission bypassing compliance authority entry yields FAIL. |
| Derives from | ART-AUTH-004, ART-DER-006 |
| Independence | Does not restate credential validation rules. |
