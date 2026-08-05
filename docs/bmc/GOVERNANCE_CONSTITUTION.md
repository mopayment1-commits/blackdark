# Governance Constitution

**System:** BLACKDARK META CONSTITUTION (BMC)  
**Level:** 4  
**Domain:** Governance  
**Document role:** Enumeration and attestation law derived exclusively from Levels 0 through 3  
**Article schema:** Principle with machine-verifiable predicate

---

### ART-GOV-001

| Field | Value |
|-------|-------|
| Principle | Owner-attested feature enumeration is the sole live feature identity authority per ART-DER-001. |
| Verification predicate | Non-attested enumeration source emitting live feature identifiers yields FAIL. |
| Derives from | ART-DER-001, ART-AUTH-004, ART-ID-001 |
| Independence | Does not enumerate features. |

### ART-GOV-002

| Field | Value |
|-------|-------|
| Principle | Roadmap grid enumeration is non-authoritative and cannot emit attested feature identifiers. |
| Verification predicate | Grid-derived output containing attested feature identifiers yields FAIL. |
| Derives from | ART-AUTH-005, ART-ID-001 |
| Independence | Does not restate attestation source. |

### ART-GOV-003

| Field | Value |
|-------|-------|
| Principle | Feature-to-capability binding follows ART-DER-014 exclusivity rule. |
| Verification predicate | Feature with zero or multiple primary capability bindings yields FAIL. |
| Derives from | ART-DER-014, ART-ID-001, ART-ID-002 |
| Independence | Does not restate feature enumeration authority. |

### ART-GOV-004

| Field | Value |
|-------|-------|
| Principle | Each taxonomy abstraction layer has exactly one authority record with machine-readable metadata per ART-AUTH-004. |
| Verification predicate | Taxonomy layer with zero or duplicate authority records yields FAIL. |
| Derives from | ART-AUTH-004, ART-AUTH-001 |
| Independence | Does not enumerate taxonomy layers. |

### ART-GOV-005

| Field | Value |
|-------|-------|
| Principle | Historical or absent artifacts cannot carry live authority markers. |
| Verification predicate | Live authority marker on absent artifact reference yields FAIL. |
| Derives from | ART-AUTH-004, ART-META-005 |
| Independence | Does not restate taxonomy authority singularity. |

### ART-GOV-006

| Field | Value |
|-------|-------|
| Principle | Navigation indexes cannot declare current single-source-of-truth authority. |
| Verification predicate | Navigation document containing current supremacy marker yields FAIL. |
| Derives from | ART-META-001, ART-AUTH-005 |
| Independence | Does not restate absent artifact rule. |

### ART-GOV-007

| Field | Value |
|-------|-------|
| Principle | Marketing narrative documents cannot become canonical enumeration without attestation binding per ART-DER-001. |
| Verification predicate | Marketing-derived identifier published as canonical yields FAIL. |
| Derives from | ART-DER-001, ART-DER-013 |
| Independence | Does not restate navigation index rule. |

### ART-GOV-008

| Field | Value |
|-------|-------|
| Principle | Attestation records require integrity signature verification before canonical publication. |
| Verification predicate | Publication of unsigned attestation yields FAIL. |
| Derives from | ART-DER-001, ART-DER-007 |
| Independence | Does not restate marketing narrative rule. |

### ART-GOV-009

| Field | Value |
|-------|-------|
| Principle | Audit and compliance exports use one audit authority entry under exclusivity per ART-AUTH-004. |
| Verification predicate | Audit export bypassing audit authority entry yields FAIL. |
| Derives from | ART-AUTH-004, ART-DER-007 |
| Independence | Does not restate attestation integrity rules. |

### ART-GOV-010

| Field | Value |
|-------|-------|
| Principle | Legal feature mapping covers every attested live feature identifier under governance authority record. |
| Verification predicate | Attested feature without legal map entry yields FAIL. |
| Derives from | ART-DER-001, ART-DER-013 |
| Independence | Does not restate audit export singularity. |

### ART-GOV-011

| Field | Value |
|-------|-------|
| Principle | Document authority verification runs as blocking gate on governance corpus changes. |
| Verification predicate | Duplicate authority fixture in governance corpus yields FAIL. |
| Derives from | ART-AUTH-004, ART-META-001 |
| Independence | Does not restate legal mapping coverage. |

### ART-GOV-012

| Field | Value |
|-------|-------|
| Principle | Superseded constitutional systems exist as reference evidence only and hold zero execution authority. |
| Verification predicate | Live gate referencing superseded constitutional system as active authority yields FAIL. |
| Derives from | ART-META-001, ART-META-005 |
| Independence | Does not name superseded systems. |
