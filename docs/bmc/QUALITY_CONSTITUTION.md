# Quality Constitution

**System:** BLACKDARK META CONSTITUTION (BMC)  
**Level:** 4  
**Domain:** Quality  
**Document role:** Evidence and verification law derived exclusively from Levels 0 through 3  
**Article schema:** Principle with machine-verifiable predicate

---

### ART-QUAL-001

| Field | Value |
|-------|-------|
| Principle | Institutional evidence artifacts validate against declared schema with version field per ART-ID-007. |
| Verification predicate | Evidence missing schema version or failing schema rules yields FAIL. |
| Derives from | ART-ID-007, ART-DER-007 |
| Independence | Does not restate evidence identity schema fields. |

### ART-QUAL-002

| Field | Value |
|-------|-------|
| Principle | Long-duration soak artifacts declare machine-readable gate scope enum distinct from pilot scope. |
| Verification predicate | Institutional scope claim with non-institutional scope enum value yields FAIL. |
| Derives from | ART-DER-007, ART-AUTH-003 |
| Independence | Does not restate schema validation rules. |

### ART-QUAL-003

| Field | Value |
|-------|-------|
| Principle | Soak assessor fails when any hourly integrity interval exceeds declared stale threshold. |
| Verification predicate | Injected stale interval producing pass verdict yields FAIL. |
| Derives from | ART-DER-012, ART-AUTH-003 |
| Independence | Does not restate scope enum rules. |

### ART-QUAL-004

| Field | Value |
|-------|-------|
| Principle | Institutional gate evidence bundle includes integrity signature and schema version per ART-ID-007. |
| Verification predicate | Gate evidence bundle missing integrity signature or schema version yields FAIL. |
| Derives from | ART-ID-007, ART-DER-007 |
| Independence | Does not restate partial-versus-full verification binding owned by engineering domain. |

### ART-QUAL-005

| Field | Value |
|-------|-------|
| Principle | Institutional test corpus includes blocking classes for collection, streaming end-to-end, execution concurrency, backup restore, and execution bypass negatives. |
| Verification predicate | Absence of any declared institutional test class yields FAIL. |
| Derives from | ART-DER-012, ART-AUTH-003 |
| Independence | Does not enumerate test instances. |

### ART-QUAL-006

| Field | Value |
|-------|-------|
| Principle | Test collection baseline count monotonicity is enforced under verification authority record. |
| Verification predicate | Baseline count decrease without regeneration evidence yields FAIL. |
| Derives from | ART-DER-012, ART-AUTH-004 |
| Independence | Does not restate institutional test class list. |

### ART-QUAL-007

| Field | Value |
|-------|-------|
| Principle | Evidence harness output shape change requires schema version increment per ART-ID-007. |
| Verification predicate | Harness shape change without version increment yields FAIL. |
| Derives from | ART-ID-007, ART-META-005 |
| Independence | Does not restate baseline monotonicity. |

### ART-QUAL-008

| Field | Value |
|-------|-------|
| Principle | Restore drill produces signed operability evidence with success flag and duration metric on declared schedule class. |
| Verification predicate | Missing scheduled restore evidence inside retention window yields FAIL. |
| Derives from | ART-DER-007, ART-ID-007 |
| Independence | Does not restate schema version policy. |

### ART-QUAL-009

| Field | Value |
|-------|-------|
| Principle | Execution engine changes trigger blocking concurrency verification class under institutional test authority record. |
| Verification predicate | Engine change without concurrency verification class trigger yields FAIL. |
| Derives from | ART-DER-012, ART-AUTH-003 |
| Independence | Does not restate restore drill rules. |

### ART-QUAL-010

| Field | Value |
|-------|-------|
| Principle | Topology contract validation runs as blocking gate on activation-path changes across declared profile matrix. |
| Verification predicate | Activation-path change without topology validation trigger yields FAIL. |
| Derives from | ART-DER-012, ART-AUTH-003 |
| Independence | Does not restate concurrency trigger rules. |
