# Engineering Constitution

**Program:** BLACKDARK INSTITUTIONAL ENGINEERING CONSTITUTION (BIEC)  
**Document role:** Sole engineering-process authority  
**Article schema:** Atomic principle with machine-verifiable predicate

---

### ART-ENG-001

| Field | Value |
|-------|-------|
| Principle | Exactly one resolved dependency artifact is the deploy authority for each deploy profile. |
| Verification predicate | Mechanical comparison of resolved dependency identity across clone, continuous integration, and container profile yields zero diff. |
| Independence | Does not delegate to any other constitution article. |

### ART-ENG-002

| Field | Value |
|-------|-------|
| Principle | Range-only dependency manifests cannot be sole deploy authority. |
| Verification predicate | Deploy path absence of exclusive range-only resolution is detected as FAIL. |
| Independence | Complements ART-ENG-001 without restating it. |

### ART-ENG-003

| Field | Value |
|-------|-------|
| Principle | Continuous integration merge authority requires full test collection success against a stored baseline count. |
| Verification predicate | Merge gate FAIL when collected test count is below committed baseline. |
| Independence | Does not delegate to any other constitution article. |

### ART-ENG-004

| Field | Value |
|-------|-------|
| Principle | Subset test success cannot substitute for full collection merge authority. |
| Verification predicate | Workflow configuration audit detects subset-only merge gate as FAIL. |
| Independence | Complements ART-ENG-003 without restating it. |

### ART-ENG-005

| Field | Value |
|-------|-------|
| Principle | Continuous integration and container deploy profiles share identical runtime dependency identity. |
| Verification predicate | Cross-profile import parity check yields zero missing runtime module on either side. |
| Independence | Does not delegate to any other constitution article. |

### ART-ENG-006

| Field | Value |
|-------|-------|
| Principle | Security workflow success is subordinate to full-suite success within one orchestrated pipeline identity. |
| Verification predicate | Security job success without upstream full-suite success on same run identifier is FAIL. |
| Independence | Does not delegate to any other constitution article. |

### ART-ENG-007

| Field | Value |
|-------|-------|
| Principle | Startup configuration invalid for active profile aborts process bind. |
| Verification predicate | Invalid profile configuration yields non-zero exit before HTTP accept. |
| Independence | Does not delegate to any other constitution article. |

### ART-ENG-008

| Field | Value |
|-------|-------|
| Principle | Health readiness semantics are uniform per declared deploy profile. |
| Verification predicate | Profile matrix maps each profile to exactly one readiness probe contract. |
| Independence | Complements ART-ARCH-004 without duplicating topology rules. |

### ART-ENG-009

| Field | Value |
|-------|-------|
| Principle | Operator launch paths validate the same readiness contract as container profile for equivalent profile class. |
| Verification predicate | Launch path probe set mismatch against profile matrix is FAIL. |
| Independence | Complements ART-ENG-008 without restating profile definition. |

### ART-ENG-010

| Field | Value |
|-------|-------|
| Principle | Application composition module size growth without bounded decomposition is merge-blocked. |
| Verification predicate | Composition root module line count increase beyond declared ceiling yields merge FAIL. |
| Independence | Does not delegate to any other constitution article. |
