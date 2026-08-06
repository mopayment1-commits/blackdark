# Data Constitution

**System:** BLACKDARK META CONSTITUTION (BMC)  
**Level:** 4  
**Domain:** Data  
**Document role:** Data authority law derived exclusively from Levels 0 through 3  
**Article schema:** Principle with machine-verifiable predicate

---

### ART-DATA-001

| Field | Value |
|-------|-------|
| Principle | Exactly one canonical public price authority serves execution-grade reads under data authority exclusivity per ART-AUTH-004. |
| Verification predicate | Execution-grade read using non-canonical price authority identifier yields FAIL. |
| Derives from | ART-DER-008, ART-AUTH-004, ART-ID-008 |
| Independence | Does not restate dataset identity schema. |

### ART-DATA-002

| Field | Value |
|-------|-------|
| Principle | Direct substrate reads cannot authorize execution without canonical mediation. |
| Verification predicate | Execution authorization using non-canonical substrate path yields FAIL. |
| Derives from | ART-DER-008, ART-AUTH-003 |
| Independence | Does not restate canonical authority singularity. |

### ART-DATA-003

| Field | Value |
|-------|-------|
| Principle | Internal unified price computation exists as sole internal aggregation entry under data authority record. |
| Verification predicate | Multiple internal aggregation entries detected yields FAIL. |
| Derives from | ART-AUTH-004, ART-ID-008 |
| Independence | Does not restate public canonical rule. |

### ART-DATA-004

| Field | Value |
|-------|-------|
| Principle | Execution-grade price reads enforce maximum age threshold declared per context class under data authority record. |
| Verification predicate | Stale price timestamp yielding authorized execution yields FAIL. |
| Derives from | ART-AUTH-003, ART-ID-008 |
| Independence | Does not restate aggregation entry singularity. |

### ART-DATA-005

| Field | Value |
|-------|-------|
| Principle | Scan operations requiring fresh prices reject stale substrate rows at authorization boundary. |
| Verification predicate | Stale substrate row passing scan authorization gate yields FAIL. |
| Derives from | ART-AUTH-005, ART-DER-008 |
| Independence | Does not restate execution freshness rules. |

### ART-DATA-006

| Field | Value |
|-------|-------|
| Principle | Evidence logs for data validation runs carry schema version field per ART-ID-007. |
| Verification predicate | Unversioned data validation evidence yields FAIL. |
| Derives from | ART-ID-007, ART-DER-007 |
| Independence | Does not restate price authority rules. |
