# AI Constitution

**System:** BLACKDARK META CONSTITUTION (BMC)  
**Level:** 4  
**Domain:** AI  
**Document role:** Inference and model law derived exclusively from Levels 0 through 3  
**Article schema:** Principle with machine-verifiable predicate

---

### ART-AI-001

| Field | Value |
|-------|-------|
| Principle | Production inference mutations and reads use exactly one declared inference authority entry under exclusivity per ART-AUTH-004. |
| Verification predicate | Production inference path outside declared inference authority entry yields FAIL. |
| Derives from | ART-DER-009, ART-AUTH-004, ART-ID-009 |
| Independence | Does not restate model identity schema. |

### ART-AI-002

| Field | Value |
|-------|-------|
| Principle | Training artifact class is inaccessible to serving loader configuration under model authority record. |
| Verification predicate | Overlap between training export class and serving allow class yields FAIL. |
| Derives from | ART-DER-009, ART-AUTH-003 |
| Independence | Does not restate inference entry singularity. |

### ART-AI-003

| Field | Value |
|-------|-------|
| Principle | Every inference mutation emits provenance fields binding source class and lineage identifier. |
| Verification predicate | Inference mutation without provenance fields yields FAIL. |
| Derives from | ART-ID-009, ART-DER-007 |
| Independence | Does not restate training-serving separation. |

### ART-AI-004

| Field | Value |
|-------|-------|
| Principle | Synthetic and live prediction source classes are mutually exclusive in authoritative audit export. |
| Verification predicate | Audit export with undeclared synthetic inclusion yields FAIL. |
| Derives from | ART-DER-007, ART-AUTH-004 |
| Independence | Does not restate provenance emission rules. |

### ART-AI-005

| Field | Value |
|-------|-------|
| Principle | Inference consumer bindings conform to versioned allow list under model authority record with zero violations. |
| Verification predicate | Allow list violation count greater than zero yields FAIL. |
| Derives from | ART-AUTH-003, ART-ID-009 |
| Independence | Does not restate inference entry singularity. |

### ART-AI-006

| Field | Value |
|-------|-------|
| Principle | Economic saturation guard does not substitute for training-serving separation enforcement. |
| Verification predicate | Separation invariant failure waived by saturation guard pass alone yields FAIL. |
| Derives from | ART-AUTH-005, ART-DER-009 |
| Independence | Does not restate allow list rules. |
