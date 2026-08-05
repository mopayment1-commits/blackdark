# Architecture Constitution

**System:** BLACKDARK META CONSTITUTION (BMC)  
**Level:** 4  
**Domain:** Architecture  
**Document role:** Structural law derived exclusively from Levels 0 through 3  
**Article schema:** Principle with machine-verifiable predicate

---

### ART-ARCH-001

| Field | Value |
|-------|-------|
| Principle | System structure is composed of bounded platform identities each with exclusive ownership under platform authority record. |
| Verification predicate | Structural element lacking platform identity or ownership binding yields FAIL. |
| Derives from | ART-DER-003, ART-ID-003, ART-AUTH-004 |
| Independence | Does not enumerate platforms. |

### ART-ARCH-002

| Field | Value |
|-------|-------|
| Principle | Replication variant is a deploy context class and not an additional platform identity class. |
| Verification predicate | Replication variant registered as platform identity yields FAIL. |
| Derives from | ART-ID-003, ART-AUTH-003 |
| Independence | Does not restate platform identity schema. |

### ART-ARCH-003

| Field | Value |
|-------|-------|
| Principle | Background domain activation requires explicit opt-in per domain under composition authority record. |
| Verification predicate | Undeclared background domain activation yields FAIL. |
| Derives from | ART-AUTH-004, ART-AUTH-003 |
| Independence | Does not restate replication variant rules. |

### ART-ARCH-004

| Field | Value |
|-------|-------|
| Principle | Exactly one canonical deploy profile contract defines supported modes, ownership, startup order, forbidden mixed modes, readiness behavior, and topology identity per deploy context class. |
| Verification predicate | Deploy profile contract divergence across declared deploy context classes under common authority yields FAIL. |
| Derives from | ART-AUTH-004, ART-ID-004 |
| Independence | Does not restate background domain opt-in. |

### ART-ARCH-005

| Field | Value |
|-------|-------|
| Principle | Mixed activation modes without declared profile contract are forbidden. |
| Verification predicate | Undeclared mixed activation mode detected yields FAIL. |
| Derives from | ART-AUTH-003, ART-DER-006 |
| Independence | Does not restate profile contract singularity. |

### ART-ARCH-006

| Field | Value |
|-------|-------|
| Principle | Every external surface element maps to exactly one platform identity owner. |
| Verification predicate | External surface element with zero or multiple platform owners yields FAIL. |
| Derives from | ART-ID-003, ART-AUTH-004 |
| Independence | Does not restate profile contract rules. |

### ART-ARCH-007

| Field | Value |
|-------|-------|
| Principle | Optional infrastructure dependency declares hard or soft class per consumer under profile contract. |
| Verification predicate | Consumer without declared dependency class in profile contract yields FAIL. |
| Derives from | ART-AUTH-003, ART-DER-006 |
| Independence | Does not restate surface ownership rules. |

### ART-ARCH-008

| Field | Value |
|-------|-------|
| Principle | Runtime authority state survives process boundary through durable persistence reload. |
| Verification predicate | Process boundary reset loses authority state when durable persistence is present yields FAIL. |
| Derives from | ART-ID-005, ART-AUTH-003 |
| Independence | Sole durability article; no parallel restatement in other domains. |
