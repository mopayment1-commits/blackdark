# Quality Constitution

**Program:** BLACKDARK INSTITUTIONAL ENGINEERING CONSTITUTION (BIEC)  
**Document role:** Sole evidence, soak, and institutional test authority  
**Article schema:** Atomic principle with machine-verifiable predicate

---

### ART-QUAL-001

| Field | Value |
|-------|-------|
| Principle | Institutional evidence artifacts validate against declared schema with version field. |
| Verification predicate | Evidence validator rejects artifact missing schema version or failing schema rules. |
| Independence | Does not delegate to any other constitution article. |

### ART-QUAL-002

| Field | Value |
|-------|-------|
| Principle | Long-duration soak artifacts declare machine-readable gate scope enum distinct from pilot scope. |
| Verification predicate | Institutional scope claim with non-institutional scope enum value yields validator FAIL. |
| Independence | Does not delegate to any other constitution article. |

### ART-QUAL-003

| Field | Value |
|-------|-------|
| Principle | Soak assessor fails when any hourly integrity interval exceeds declared stale threshold. |
| Verification predicate | Injected stale hour fixture produces assessor FAIL verdict. |
| Independence | Complements ART-QUAL-002 without restating scope enum. |

### ART-QUAL-004

| Field | Value |
|-------|-------|
| Principle | Combined quality report binds security subset outcome to full-suite outcome on single run identifier. |
| Verification predicate | Report artifact with security pass and full-suite fail on same run identifier is FAIL. |
| Independence | Complements ART-ENG-006 without restating workflow mechanics. |

### ART-QUAL-005

| Field | Value |
|-------|-------|
| Principle | Institutional test corpus includes blocking classes for collection, streaming end-to-end, execution concurrency, backup restore, and execution bypass negatives. |
| Verification predicate | Meta-test detects absence of any declared institutional test class as merge FAIL. |
| Independence | Does not delegate to any other constitution article. |

### ART-QUAL-006

| Field | Value |
|-------|-------|
| Principle | Test collection baseline count monotonicity is merge-gated. |
| Verification predicate | Baseline count decrease without baseline regeneration artifact yields FAIL. |
| Independence | Complements ART-ENG-003 without restating collection mechanics. |

### ART-QUAL-007

| Field | Value |
|-------|-------|
| Principle | Evidence harness output shape change requires schema version increment. |
| Verification predicate | Harness change without version increment detected by policy test yields FAIL. |
| Independence | Complements ART-QUAL-001 without restating validator location. |

### ART-QUAL-008

| Field | Value |
|-------|-------|
| Principle | Restore drill produces signed operability artifact with success flag and duration metric on declared schedule class. |
| Verification predicate | Missing scheduled restore artifact inside retention window yields alert FAIL. |
| Independence | Does not delegate to any other constitution article. |

### ART-QUAL-009

| Field | Value |
|-------|-------|
| Principle | Execution engine module changes trigger blocking concurrency suite. |
| Verification predicate | Engine path change without concurrency job trigger yields path gate FAIL. |
| Independence | Complements ART-QUAL-005 without restating class list. |

### ART-QUAL-010

| Field | Value |
|-------|-------|
| Principle | Topology contract validation runs as blocking gate on boot-path changes across declared profile matrix. |
| Verification predicate | Boot-path diff without topology validation job yields merge FAIL. |
| Independence | Complements ART-ARCH-004 without restating profile contract fields. |
