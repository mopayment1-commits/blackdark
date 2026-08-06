# Architecture Constitution

**Program:** BLACKDARK INSTITUTIONAL ENGINEERING CONSTITUTION (BIEC)  
**Document role:** Sole structural and topology authority  
**Article schema:** Atomic principle with machine-verifiable predicate

---

### ART-ARCH-001

| Field | Value |
|-------|-------|
| Principle | Logical system structure is a modular monolith of exactly sixteen bounded platforms numbered P01 through P16. |
| Verification predicate | Platform registry count equals sixteen and excludes any P17 or higher identifier. |
| Independence | Does not delegate to any other constitution article. |

### ART-ARCH-002

| Field | Value |
|-------|-------|
| Principle | Physical worker replication is a deploy profile variant and not a seventeenth platform. |
| Verification predicate | Worker mode declaration maps to profile class DEPLOY_REPLICA only, never PLATFORM_ID. |
| Independence | Complements ART-ARCH-001 without restating platform count. |

### ART-ARCH-003

| Field | Value |
|-------|-------|
| Principle | Composition root activation of background domains requires explicit opt-in per domain. |
| Verification predicate | Default profile startup manifest excludes undeclared background domains. |
| Independence | Does not delegate to any other constitution article. |

### ART-ARCH-004

| Field | Value |
|-------|-------|
| Principle | Exactly one canonical deploy profile contract defines supported modes, component ownership, startup sequence, forbidden mixed modes, readiness behavior, deployment parity, and runtime topology identity. |
| Verification predicate | Profile contract hash mismatch across local, container, compose, hosted, and continuous-integration simulation is FAIL. |
| Independence | Does not delegate to any other constitution article. |

### ART-ARCH-005

| Field | Value |
|-------|-------|
| Principle | Mixed monolith and worker boot without declared profile is forbidden. |
| Verification predicate | Undeclared dual boot graph detection yields FAIL. |
| Independence | Complements ART-ARCH-004 without restating profile fields. |

### ART-ARCH-006

| Field | Value |
|-------|-------|
| Principle | HTTP route surface maps one-to-one to a single P01–P16 owner per route. |
| Verification predicate | Route inventory contains zero routes without owner field in platform registry. |
| Independence | Complements ART-PLAT-001 without restating facade rules. |

### ART-ARCH-007

| Field | Value |
|-------|-------|
| Principle | Infrastructure optional services declare minimal versus full profile contract with explicit hard or soft dependency class per consumer. |
| Verification predicate | Consumer without declared dependency class in profile matrix is FAIL. |
| Independence | Does not delegate to any other constitution article. |

### ART-ARCH-008

| Field | Value |
|-------|-------|
| Principle | Execution and runtime authority state survives process restart through durable store reload. |
| Verification predicate | Restart simulation loses neither freeze posture nor loop authority when durable store present. |
| Independence | Complements ART-SEC-004 without restating authorization semantics. |

### ART-ARCH-009

| Field | Value |
|-------|-------|
| Principle | Database persistence access uses domain-bounded repositories behind a stable facade. |
| Verification predicate | Financial schema mutation occurs only within financial repository boundary artifact. |
| Independence | Does not delegate to any other constitution article. |

### ART-ARCH-010

| Field | Value |
|-------|-------|
| Principle | Oracle and research mutation paths expose a single public inference entry. |
| Verification predicate | Static caller inventory shows zero production callers outside declared inference entry. |
| Independence | Complements ART-AI-001 without restating inference rules. |
