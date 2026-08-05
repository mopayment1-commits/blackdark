# Platform Constitution

**System:** BLACKDARK META CONSTITUTION (BMC)  
**Level:** 4  
**Domain:** Platform  
**Document role:** Platform boundary law derived exclusively from Levels 0 through 3  
**Article schema:** Principle with machine-verifiable predicate

---

### ART-PLAT-001

| Field | Value |
|-------|-------|
| Principle | External surface layer accesses platform internals only through declared boundary authority records per platform identity. |
| Verification predicate | Direct internal access bypassing boundary authority record yields FAIL. |
| Derives from | ART-DER-003, ART-AUTH-004, ART-ID-003 |
| Independence | Does not restate platform identity schema. |

### ART-PLAT-002

| Field | Value |
|-------|-------|
| Principle | Each platform identity binds to exactly one boundary authority record at issuance under platform authority record. |
| Verification predicate | Platform identity with zero or multiple boundary authority bindings yields FAIL. |
| Derives from | ART-DER-003, ART-AUTH-004 |
| Independence | Does not restate access authorization rules owned by security domain. |

### ART-PLAT-003

| Field | Value |
|-------|-------|
| Principle | External surface expansion requires synchronized owner binding update under platform authority record. |
| Verification predicate | Surface expansion without owner binding update yields FAIL. |
| Derives from | ART-DER-003, ART-AUTH-003 |
| Independence | Does not restate surface ownership singularity owned by architecture domain. |

### ART-PLAT-004

| Field | Value |
|-------|-------|
| Principle | Platform boundary graph remains acyclic toward internal implementation under platform authority record. |
| Verification predicate | Boundary cycle detected yields FAIL. |
| Derives from | ART-AUTH-003, ART-ID-003 |
| Independence | Does not restate boundary access rules. |

### ART-PLAT-005

| Field | Value |
|-------|-------|
| Principle | Platform boundary authority record declares allowed internal access class set before external surface activation. |
| Verification predicate | External surface activation without declared access class set yields FAIL. |
| Derives from | ART-AUTH-003, ART-ID-003 |
| Independence | Does not restate production surface exclusion owned by security domain. |

### ART-PLAT-006

| Field | Value |
|-------|-------|
| Principle | Streaming surface contracts require blocking verification class under institutional test authority record. |
| Verification predicate | Streaming surface change without linked verification class trigger yields FAIL. |
| Derives from | ART-DER-012, ART-AUTH-003 |
| Independence | Does not restate surface ownership sync. |

### ART-PLAT-007

| Field | Value |
|-------|-------|
| Principle | Per-platform observability emission completeness meets declared minimum coverage ratio under platform authority record. |
| Verification predicate | Completeness score below declared threshold yields FAIL. |
| Derives from | ART-DER-007, ART-AUTH-003 |
| Independence | Does not restate acyclic boundary rule. |
