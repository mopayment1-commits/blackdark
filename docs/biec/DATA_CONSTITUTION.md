# Data Constitution

**Program:** BLACKDARK INSTITUTIONAL ENGINEERING CONSTITUTION (BIEC)  
**Document role:** Sole price and data-authority rules  
**Article schema:** Atomic principle with machine-verifiable predicate

---

### ART-DATA-001

| Field | Value |
|-------|-------|
| Principle | Exactly one canonical public price authority API serves execution-grade reads. |
| Verification predicate | Execution authorization path price source identifier equals canonical authority identifier only. |
| Independence | Does not delegate to any other constitution article. |

### ART-DATA-002

| Field | Value |
|-------|-------|
| Principle | Direct hub or REST substrate reads cannot authorize execution without canonical mediation. |
| Verification predicate | Prohibited-import audit from execution modules to non-canonical price substrates yields zero violations. |
| Independence | Complements ART-DATA-001 without restating API count. |

### ART-DATA-003

| Field | Value |
|-------|-------|
| Principle | Internal unified global price computation exists as sole internal aggregation entry. |
| Verification predicate | Internal aggregation caller inventory shows single entry module only. |
| Independence | Complements ART-DATA-001 without restating public API rule. |

### ART-DATA-004

| Field | Value |
|-------|-------|
| Principle | Execution-grade price reads enforce maximum age threshold declared per profile. |
| Verification predicate | Stale timestamp injection yields zero authorized execution opportunities. |
| Independence | Does not delegate to any other constitution article. |

### ART-DATA-005

| Field | Value |
|-------|-------|
| Principle | Scan engines requiring fresh prices reject stale hub rows at authorization boundary. |
| Verification predicate | Stale hub injection produces zero scan outputs passing authorization gate. |
| Independence | Complements ART-DATA-004 without restating execution scope. |

### ART-DATA-006

| Field | Value |
|-------|-------|
| Principle | Evidence logs for data validation runs carry schema version field. |
| Verification predicate | Validator rejects unversioned data validation log artifacts. |
| Independence | Complements ART-QUAL-001 without restating global evidence rules. |
