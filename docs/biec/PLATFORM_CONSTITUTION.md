# Platform Constitution

**Program:** BLACKDARK INSTITUTIONAL ENGINEERING CONSTITUTION (BIEC)  
**Document role:** Sole platform boundary and API ownership authority  
**Article schema:** Atomic principle with machine-verifiable predicate

---

### ART-PLAT-001

| Field | Value |
|-------|-------|
| Principle | HTTP API layer imports platform internals only through declared facade modules. |
| Verification predicate | Prohibited-import lint from API layer to internal platform modules yields zero violations. |
| Independence | Does not delegate to any other constitution article. |

### ART-PLAT-002

| Field | Value |
|-------|-------|
| Principle | Platform action authorization uses one access facade for all tier-gated routes. |
| Verification predicate | Route dependency scan shows zero tier checks outside access facade. |
| Independence | Complements ART-SEC-009 without restating security profile rules. |

### ART-PLAT-003

| Field | Value |
|-------|-------|
| Principle | Platform route count increases require synchronized owner map update. |
| Verification predicate | Route inventory diff without owner map update yields merge FAIL. |
| Independence | Complements ART-ARCH-006 without restating platform count. |

### ART-PLAT-004

| Field | Value |
|-------|-------|
| Principle | Platform facade import graph remains acyclic toward internal implementation modules. |
| Verification predicate | Facade import cycle detection reports zero cycles. |
| Independence | Complements ART-PLAT-001 without restating prohibited-import scope. |

### ART-PLAT-005

| Field | Value |
|-------|-------|
| Principle | Production guard evaluates route mount filter not merely infrastructure checklist. |
| Verification predicate | Production profile with demonstration route mounted yields guard FAIL. |
| Independence | Complements ART-SEC-006 without restating allow list mechanics. |

### ART-PLAT-006

| Field | Value |
|-------|-------|
| Principle | Server-sent event streaming contracts are validated by blocking continuous integration class. |
| Verification predicate | Streaming module change without streaming end-to-end job trigger yields path gate FAIL. |
| Independence | Complements ART-QUAL-005 without restating test taxonomy. |

### ART-PLAT-007

| Field | Value |
|-------|-------|
| Principle | Per-platform infrastructure metrics emission completeness meets declared minimum coverage ratio. |
| Verification predicate | Metrics completeness score below declared threshold yields soak assessor FAIL. |
| Independence | Complements ART-QUAL-004 without restating evidence schema. |
