# Security Constitution

**Program:** BLACKDARK INSTITUTIONAL ENGINEERING CONSTITUTION (BIEC)  
**Document role:** Sole execution authorization and isolation authority  
**Article schema:** Atomic principle with machine-verifiable predicate

---

### ART-SEC-001

| Field | Value |
|-------|-------|
| Principle | Exactly one master execution authorization switch governs all live order placement. |
| Verification predicate | Static module audit detects zero direct reads of legacy execution flags outside master switch module. |
| Independence | Does not delegate to any other constitution article. |

### ART-SEC-002

| Field | Value |
|-------|-------|
| Principle | Execution authorization conflict or unknown state yields deny. |
| Verification predicate | Authorization service returns DENY on UNKNOWN and CONFLICT states in negative matrix. |
| Independence | Complements ART-SEC-001 without restating switch count. |

### ART-SEC-003

| Field | Value |
|-------|-------|
| Principle | Venue connector invocation requires successful unified authorization consult before network input-output. |
| Verification predicate | Connector bypass matrix shows zero SUCCESS rows without authorization consult. |
| Independence | Complements ART-SEC-001 without restating master switch location. |

### ART-SEC-004

| Field | Value |
|-------|-------|
| Principle | Execution authority state is durable across process restart. |
| Verification predicate | Restart test reloads authority posture from durable store without relying on environment alone. |
| Independence | Complements ART-ARCH-008 without duplicating repository boundary rules. |

### ART-SEC-005

| Field | Value |
|-------|-------|
| Principle | Multi-subject data access requires mandatory tenant context on all user-scoped repositories. |
| Verification predicate | Cross-subject negative access attempts fail on all declared CRUD paths. |
| Independence | Does not delegate to any other constitution article. |

### ART-SEC-006

| Field | Value |
|-------|-------|
| Principle | Production profile excludes demonstration and development route classes at mount time. |
| Verification predicate | Production OpenAPI route diff against allow list shows zero demonstration routes. |
| Independence | Does not delegate to any other constitution article. |

### ART-SEC-007

| Field | Value |
|-------|-------|
| Principle | Production startup emits signed route manifest matching production allow list. |
| Verification predicate | Manifest hash mismatch against golden allow list yields startup FAIL in production profile. |
| Independence | Complements ART-SEC-006 without restating route class definition. |

### ART-SEC-008

| Field | Value |
|-------|-------|
| Principle | Privileged tier authentication requires multi-factor verification when profile flag demands it. |
| Verification predicate | Single-factor success under mandatory multi-factor profile is FAIL. |
| Independence | Does not delegate to any other constitution article. |

### ART-SEC-009

| Field | Value |
|-------|-------|
| Principle | Tier and role authorization for platform actions routes through one centralized access facade. |
| Verification predicate | Route audit detects zero ad hoc tier checks outside access facade module. |
| Independence | Complements ART-PLAT-002 without restating platform numbering. |

### ART-SEC-010

| Field | Value |
|-------|-------|
| Principle | Live credential validation uses fixture credential mode in automated continuous integration. |
| Verification predicate | Continuous integration success without gitignored live credential tree proves fixture mode. |
| Independence | Does not delegate to any other constitution article. |

### ART-SEC-011

| Field | Value |
|-------|-------|
| Principle | Public regulatory verdict transformation uses one compliance facade entry. |
| Verification predicate | Verdict emitter static scan shows zero routes bypassing compliance facade. |
| Independence | Does not delegate to any other constitution article. |
