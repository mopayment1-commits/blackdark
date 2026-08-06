# Identity Constitution

**System:** BLACKDARK META CONSTITUTION (BMC)  
**Level:** 2  
**Document role:** Sole identity class definition authority  
**Article schema:** Principle with machine-verifiable predicate

---

### ART-ID-001

| Field | Value |
|-------|-------|
| Principle | Feature identity is a stable attested identifier with owner binding, lifecycle state, and attestation signature. |
| Verification predicate | Feature identity record missing identifier, owner binding, lifecycle state, or attestation signature yields FAIL. |
| Derives from | ART-META-003 |
| Independence | Does not enumerate features. |

### ART-ID-002

| Field | Value |
|-------|-------|
| Principle | Capability identity is a stable identifier denoting one institutional ability with declared scope boundary. |
| Verification predicate | Capability identity record missing identifier or scope boundary yields FAIL. |
| Derives from | ART-META-003 |
| Independence | Does not enumerate capabilities. |

### ART-ID-003

| Field | Value |
|-------|-------|
| Principle | Platform identity is a stable identifier denoting one bounded institutional surface with declared ownership binding. |
| Verification predicate | Platform identity record missing identifier or ownership binding yields FAIL. |
| Derives from | ART-META-003 |
| Independence | Does not enumerate platforms. |

### ART-ID-004

| Field | Value |
|-------|-------|
| Principle | Service identity is a stable identifier denoting one operational service unit with declared availability class. |
| Verification predicate | Service identity record missing identifier or availability class yields FAIL. |
| Derives from | ART-META-003 |
| Independence | Does not enumerate services. |

### ART-ID-005

| Field | Value |
|-------|-------|
| Principle | Artifact identity is a stable identifier denoting one derived institutional object with derivation chain binding. |
| Verification predicate | Artifact identity record missing identifier or derivation chain binding yields FAIL. |
| Derives from | ART-META-003, ART-META-004 |
| Independence | Does not enumerate artifact instances. |

### ART-ID-006

| Field | Value |
|-------|-------|
| Principle | Decision identity is a stable identifier denoting one governance or architectural decision with constitution citation set. |
| Verification predicate | Decision identity record missing identifier or constitution citation set yields FAIL. |
| Derives from | ART-META-003 |
| Independence | Does not enumerate decisions. |

### ART-ID-007

| Field | Value |
|-------|-------|
| Principle | Evidence identity is a stable identifier denoting one verifiable proof object with schema version and integrity signature. |
| Verification predicate | Evidence identity record missing identifier, schema version, or integrity signature yields FAIL. |
| Derives from | ART-META-003 |
| Independence | Does not enumerate evidence instances. |

### ART-ID-008

| Field | Value |
|-------|-------|
| Principle | Dataset identity is a stable identifier denoting one data corpus with lineage binding and freshness class. |
| Verification predicate | Dataset identity record missing identifier, lineage binding, or freshness class yields FAIL. |
| Derives from | ART-META-003 |
| Independence | Does not enumerate datasets. |

### ART-ID-009

| Field | Value |
|-------|-------|
| Principle | Model identity is a stable identifier denoting one learned or rule-based model with provenance binding and serving class. |
| Verification predicate | Model identity record missing identifier, provenance binding, or serving class yields FAIL. |
| Derives from | ART-META-003 |
| Independence | Does not enumerate models. |

### ART-ID-010

| Field | Value |
|-------|-------|
| Principle | User identity is a stable identifier denoting one authenticated subject with role binding set. |
| Verification predicate | User identity record missing identifier or role binding set yields FAIL. |
| Derives from | ART-META-003 |
| Independence | Does not enumerate users. |

### ART-ID-011

| Field | Value |
|-------|-------|
| Principle | Tenant identity is a stable identifier denoting one isolation boundary with subject membership policy. |
| Verification predicate | Tenant identity record missing identifier or subject membership policy yields FAIL. |
| Derives from | ART-META-003 |
| Independence | Does not enumerate tenants. |
