# Financial Constitution

**System:** BLACKDARK META CONSTITUTION (BMC)  
**Level:** 4  
**Domain:** Financial  
**Document role:** Monetary law derived exclusively from Levels 0 through 3  
**Article schema:** Principle with machine-verifiable predicate

---

### ART-FIN-001

| Field | Value |
|-------|-------|
| Principle | Authoritative monetary storage uses exact decimal representation with declared scale and precision under financial authority record. |
| Verification predicate | Monetary storage record using inexact representation class yields FAIL. |
| Derives from | ART-AUTH-004, ART-ID-008 |
| Independence | Does not restate data authority rules. |

### ART-FIN-002

| Field | Value |
|-------|-------|
| Principle | New monetary storage fields cannot adopt inexact representation class. |
| Verification predicate | Schema change introducing inexact representation on monetary class yields FAIL. |
| Derives from | ART-AUTH-004, ART-DER-006 |
| Independence | Does not restate storage decimal rule. |

### ART-FIN-003

| Field | Value |
|-------|-------|
| Principle | Authoritative fee and profit comparison paths use exact decimal arithmetic before persist or authorization gate. |
| Verification predicate | Hot-path comparison using inexact arithmetic class yields FAIL. |
| Derives from | ART-AUTH-004, ART-ID-008 |
| Independence | Does not restate storage rules. |

### ART-FIN-004

| Field | Value |
|-------|-------|
| Principle | Threshold boundary comparisons on monetary paths satisfy exact decimal invariants at declared quantum under financial authority record. |
| Verification predicate | Boundary invariant violation at minimum quantum yields FAIL. |
| Derives from | ART-AUTH-003, ART-DER-006 |
| Independence | Does not restate comparison path rules. |

### ART-FIN-005

| Field | Value |
|-------|-------|
| Principle | Portfolio holdings and rebalance preview read from one authoritative read model under financial authority record. |
| Verification predicate | Divergent read model output for identical subject identity yields FAIL. |
| Derives from | ART-AUTH-004, ART-ID-010, ART-ID-011 |
| Independence | Does not restate decimal invariants. |

### ART-FIN-006

| Field | Value |
|-------|-------|
| Principle | Audit export of monetary aggregates preserves exact decimal string representation without silent precision loss. |
| Verification predicate | Export round-trip precision loss beyond declared scale yields FAIL. |
| Derives from | ART-AUTH-004, ART-DER-007 |
| Independence | Does not restate read model singularity. |
