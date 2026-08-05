# Authority Constitution

**System:** BLACKDARK META CONSTITUTION (BMC)  
**Level:** 1  
**Document role:** Sole authority type, ownership, scope, exclusivity, and resolution authority  
**Article schema:** Principle with machine-verifiable predicate

---

### ART-AUTH-001

| Field | Value |
|-------|-------|
| Principle | Exactly one closed authority-type registry defines all authority types; each type declares a distinct scope class. |
| Verification predicate | Authority record referencing undeclared authority type or undeclared scope class yields FAIL. |
| Derives from | ART-META-002 |
| Independence | Does not define identity classes. |

### ART-AUTH-002

| Field | Value |
|-------|-------|
| Principle | Every authority record has exactly one owner identity bound at creation. |
| Verification predicate | Authority record with zero or multiple owner bindings yields FAIL. |
| Derives from | ART-META-002, ART-META-003 |
| Independence | Defers owner identity schema to Level 2 User and Tenant classes. |

### ART-AUTH-003

| Field | Value |
|-------|-------|
| Principle | Every authority record declares bounded scope with explicit subject class and boundary predicate. |
| Verification predicate | Authority exercise outside declared scope boundary yields FAIL. |
| Derives from | ART-AUTH-001 |
| Independence | Does not restate authority type registry rules. |

### ART-AUTH-004

| Field | Value |
|-------|-------|
| Principle | At most one live authority record may hold exclusivity for a given scope class and subject class pair. |
| Verification predicate | Duplicate live exclusivity for identical scope class and subject class pair yields FAIL. |
| Derives from | ART-AUTH-001, ART-AUTH-003 |
| Independence | Does not restate ownership rules. |

### ART-AUTH-005

| Field | Value |
|-------|-------|
| Principle | Conflicting authority claims resolve by level precedence META then AUTHORITY then IDENTITY then DERIVATION then domain; unresolved conflict yields DENY. |
| Verification predicate | Conflict resolution producing GRANT without precedence basis or without DENY on tie yields FAIL. |
| Derives from | ART-META-001, ART-AUTH-004 |
| Independence | Does not restate exclusivity declaration rules. |
