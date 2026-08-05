# Finding Remediation Traceability Matrix — Stage 2 Repair Baseline

**Version:** 6.0 (Stage 2 — 23-field controls linked)  
**Validation branch:** `cursor/g2-g3-quality-gates-soak`  
**Validation commit:** `14112859677b68932c79b31d09a8aed49272794a`  
**Control register:** `CORRECTIVE_PREVENTIVE_CONTROL_REGISTER.md` v6.0

## Scope

Links findings to registers, sub-findings, and Stage 2 corrective/preventive controls (23-field schema). Implementation steps, test matrix cells, and migrations remain **SEMANTICALLY_INVALID — DO NOT EXECUTE** in v3.0 sibling artifacts.

---

## Parent Finding Index

| ID | Severity | Registers | CC | PCtrl | Status |
|----|----------|-----------|-----|-------|--------|
| PC-001 | CRITICAL | H | CC-001 | PCtrl-001 | OPEN |
| PC-002 | CRITICAL | F | CC-002 | PCtrl-002 | OPEN |
| PC-003 | CRITICAL | A, K | CC-003 | PCtrl-003 | OPEN |
| PC-004 | CRITICAL | C | CC-004 | PCtrl-004 | OPEN |
| PC-005 | CRITICAL | D | CC-005 | PCtrl-005 | OPEN |
| PC-006 | CRITICAL | J | CC-006 | PCtrl-006 | OPEN |
| PC-007 | HIGH | H, B | CC-007 | PCtrl-007 | OPEN |
| PC-008 | HIGH | B | CC-008 | PCtrl-008 | OPEN |
| PC-009 | HIGH | B, J | CC-009 | PCtrl-009 | OPEN |
| PC-010 | HIGH | D, B | CC-010 | PCtrl-010 | OPEN |
| PC-011 | HIGH | G | CC-011 | PCtrl-011 | OPEN |
| PC-012 | HIGH | I | CC-012 | PCtrl-012 | OPEN |
| PC-013 | HIGH | E, L | CC-013 | PCtrl-013 | OPEN |
| PC-014 | HIGH | D | CC-014 | PCtrl-014 | OPEN |
| PC-015 | HIGH | A, K | CC-015 | PCtrl-015 | OPEN |
| PC-016 | MEDIUM | H | CC-016 | PCtrl-016 | OPEN |
| PC-017 | MEDIUM | H | CC-017 | PCtrl-017 | OPEN |
| PC-018 | MEDIUM | K | CC-018 | PCtrl-018 | OPEN |
| PC-019 | MEDIUM | I | CC-019 | PCtrl-019 | OPEN |
| PC-020 | LOW | B | CC-020 | PCtrl-020 | OPEN |
| PC-021 | HIGH | H | CC-021 | PCtrl-021 | OPEN |
| PC-022 | HIGH | F | CC-022 | PCtrl-022 | OPEN |
| PC-023 | HIGH | K | CC-023 | PCtrl-023 | OPEN |
| PC-024 | HIGH | L | CC-024 | PCtrl-024 | OPEN |
| PC-025 | HIGH | H, D | CC-025 | PCtrl-025 | OPEN |
| PC-026 | MEDIUM | C | CC-026 | PCtrl-026 | OPEN |
| PC-027 | MEDIUM | J | CC-027 | PCtrl-027 | OPEN |
| PC-028 | MEDIUM | I | CC-028 | PCtrl-028 | OPEN |
| PC-029 | MEDIUM | G | CC-029 | PCtrl-029 | OPEN |
| PC-030 | MEDIUM | E | CC-030 | PCtrl-030 | OPEN |
| PC-031 | MEDIUM | B | CC-031 | PCtrl-031 | OPEN |
| PC-032 | LOW | K | CC-032 | PCtrl-032 | OPEN |
| PC-033 | LOW | F | CC-033 | PCtrl-033 | OPEN |
| PC-034 | MEDIUM | F, L | CC-034 | PCtrl-034 | OPEN |
| PC-035 | LOW | G | CC-035 | PCtrl-035 | OPEN |
| PC-036 | INFORMATIONAL | A, K | CC-036 | PCtrl-036 | OPEN |
| PC-037 | INFORMATIONAL | K | CC-037 | PCtrl-037 | OPEN |
| PC-038 | INFORMATIONAL | L | CC-038 | PCtrl-038 | OPEN |
| PC-039 | INFORMATIONAL | F | CC-039 | PCtrl-039 | OPEN |
| PC-040 | INFORMATIONAL | G | PC-040 | PCtrl-040 | OPEN |
| PC-041 | MEDIUM | C, J | CC-041 | PCtrl-041 | OPEN |
| PC-042 | MEDIUM | K | CC-042 | PCtrl-042 | OPEN |

---

## Sub-Finding Traceability

| Sub-ID | Parent | CC | PCtrl | Independent closure |
|--------|--------|-----|-------|----------------------|
| PC-008.a | PC-008 | CC-008.a | PCtrl-008.a | Yes |
| PC-008.b | PC-008 | CC-008.b | PCtrl-008.b | Yes |
| PC-008.c | PC-008 | CC-008.c | PCtrl-008.c | Yes |
| PC-008.d | PC-008 | CC-008.d | PCtrl-008.d | Yes |
| PC-009.a | PC-009 | CC-009.a | PCtrl-009.a | Yes |
| PC-009.b | PC-009 | CC-009.b | PCtrl-009.b | Yes |
| PC-009.c | PC-009 | CC-009.c | PCtrl-009.c | Yes |
| PC-009.d | PC-009 | CC-009.d | PCtrl-009.d | Yes |
| PC-010.a | PC-010 | CC-010.a | PCtrl-010.a | Yes |
| PC-011.a | PC-011 | CC-011.a | PCtrl-011.a | Yes |
| PC-011.b | PC-011 | CC-011.b | PCtrl-011.b | Yes |
| PC-012.a | PC-012 | CC-012.a | PCtrl-012.a | Yes |
| PC-012.b | PC-012 | CC-012.b | PCtrl-012.b | Yes |
| PC-013.a | PC-013 | CC-013.a | PCtrl-013.a | Yes |
| PC-013.b | PC-013 | CC-013.b | PCtrl-013.b | Yes |
| PC-013.c | PC-013 | CC-013.c | PCtrl-013.c | Yes |
| PC-013.d | PC-013 | CC-013.d | PCtrl-013.d | Yes |
| PC-013.e | PC-013 | CC-013.e | PCtrl-013.e | Yes |
| PC-013.f | PC-013 | CC-013.f | PCtrl-013.f | Yes |
| PC-015.a | PC-015 | CC-015.a | PCtrl-015.a | Yes |
| PC-015.b | PC-015 | CC-015.b | PCtrl-015.b | Yes |
| PC-019.a | PC-019 | CC-019.a | PCtrl-019.a | Yes |
| PC-021.a | PC-021 | CC-021.a | PCtrl-021.a | Yes |
| PC-022.a | PC-022 | CC-022.a | PCtrl-022.a | Yes |
| PC-022.b | PC-022 | CC-022.b | PCtrl-022.b | Yes |
| PC-022.c | PC-022 | CC-022.c | PCtrl-022.c | Yes |
| PC-022.d | PC-022 | CC-022.d | PCtrl-022.d | Yes |
| PC-022.e | PC-022 | CC-022.e | PCtrl-022.e | Yes |
| PC-034.a | PC-034 | CC-034.a | PCtrl-034.a | Yes |

---

## Closure Chain Progress

| Stage | Artifact | Status |
|-------|----------|--------|
| Diagnosis + Root Cause | ROOT_CAUSE_REGISTER.md v4.0 | VERIFIED_CLOSED |
| Corrective + Preventive Controls | CORRECTIVE_PREVENTIVE_CONTROL_REGISTER.md v6.0 | REMEDIATED_PENDING_IVV |
| Implementation Contract | ROOT_REMEDIATION_MASTER_PLAN.md v3.0 | SEMANTICALLY_INVALID |
| Tests | MASTER_PLAN test matrix | SEMANTICALLY_INVALID |
| IVV | Per-stage signoff | Stage 2 re-IVV required |
| LOCK | 42/42 + 29/29 | NOT REACHED |

---

## Stage 2 Repair Notes

- All 142 controls use mandatory 23-field schema per Stage 2 repair specification.
- PC-031, PC-036, PC-037, PCtrl-020, CC-009.c, CC-022.a, PCtrl-013.b independently reconstructed.
- Stage 1 `ROOT_CAUSE_REGISTER.md` unchanged (hash verified).
