# Finding Remediation Traceability Matrix — Stage 2 Baseline

**Version:** 5.0 (Stage 2 — controls linked)  
**Validation branch:** `cursor/g2-g3-quality-gates-soak`  
**Validation commit:** `14112859677b68932c79b31d09a8aed49272794a`  
**Control register:** `CORRECTIVE_PREVENTIVE_CONTROL_REGISTER.md` v5.0

## Scope

This matrix links findings to registers, sub-findings, and Stage 2 corrective/preventive controls. **Implementation steps, test matrix cells, and migrations remain SEMANTICALLY_INVALID — DO NOT EXECUTE** in v3.0 sibling artifacts until Stages 3–5 pass IVV.

---

## Parent Finding Index

| ID | Severity | Category | Registers | Sub-findings | CC | PCtrl | Feature Reg block | CAP block | Impl block | Status |
|----|----------|----------|-----------|--------------|-----|-------|-------------------|-----------|------------|--------|
| PC-001 | CRITICAL | Reproducibility | H | PC-021.a | CC-001 | PCtrl-001 | No | No | Yes | OPEN |
| PC-002 | CRITICAL | Test/Evidence | F | PC-022.a | CC-002 | PCtrl-002 | No | No | Yes | OPEN |
| PC-003 | CRITICAL | Feature Authority | A, K | PC-009.b, PC-015.b | CC-003 | PCtrl-003 | Yes | Yes | Yes | OPEN |
| PC-004 | CRITICAL | Data Authority | C | — | CC-004 | PCtrl-004 | No | Yes | Yes | OPEN |
| PC-005 | CRITICAL | Execution Safety | D | PC-010.a, PC-022.e | CC-005 | PCtrl-005 | No | No | Yes | OPEN |
| PC-006 | CRITICAL | Financial Safety | J | PC-009.c | CC-006 | PCtrl-006 | No | No | Yes | OPEN |
| PC-007 | HIGH | Runtime Topology | H, B | PC-008.a | CC-007 | PCtrl-007 | No | No | Yes | OPEN |
| PC-008 | HIGH | Hidden Coupling | B | PC-008.a–d | CC-008 | PCtrl-008 | No | Yes | Yes | OPEN |
| PC-009 | HIGH | Platform Boundary | B, J | PC-009.a–d | CC-009 | PCtrl-009 | No | Yes | Yes | OPEN |
| PC-010 | HIGH | Execution Gating | D, B | PC-010.a | CC-010 | PCtrl-010 | No | Yes | Yes | OPEN |
| PC-011 | HIGH | G3/Evidence | G | PC-011.a–b | CC-011 | PCtrl-011 | Yes | No | Yes | OPEN |
| PC-012 | HIGH | Oracle Architecture | I | PC-012.a–b | CC-012 | PCtrl-012 | No | Yes | Yes | OPEN |
| PC-013 | HIGH | Tenancy/Security | E, L | PC-013.a–f | CC-013 | PCtrl-013 | No | Yes | Yes | OPEN |
| PC-014 | HIGH | Execution State | D | — | CC-014 | PCtrl-014 | No | No | Yes | OPEN |
| PC-015 | HIGH | Feature Taxonomy | A, K | PC-015.a–b | CC-015 | PCtrl-015 | Yes | Yes | Yes | OPEN |
| PC-016 | MEDIUM | Deploy | H | — | CC-016 | PCtrl-016 | No | No | No | OPEN |
| PC-017 | MEDIUM | Infrastructure | H | — | CC-017 | PCtrl-017 | No | No | Partial | OPEN |
| PC-018 | MEDIUM | Documentation | K | — | CC-018 | PCtrl-018 | Yes | No | Yes | OPEN |
| PC-019 | MEDIUM | ML Safety | I | PC-019.a | CC-019 | PCtrl-019 | No | Yes | Partial | OPEN |
| PC-020 | LOW | Maintainability | B | — | CC-020 | PCtrl-020 | No | No | No | OPEN |
| PC-021 | HIGH | Deploy/Repro | H | PC-021.a | CC-021 | PCtrl-021 | No | No | Yes | OPEN |
| PC-022 | HIGH | Test Architecture | F | PC-022.a–e | CC-022 | PCtrl-022 | Yes | No | Yes | OPEN |
| PC-023 | HIGH | SSOT/Navigation | K | — | CC-023 | PCtrl-023 | Yes | Yes | Yes | OPEN |
| PC-024 | HIGH | Audit Authority | L | — | CC-024 | PCtrl-024 | No | Yes | Yes | OPEN |
| PC-025 | HIGH | Configuration | H, D | — | CC-025 | PCtrl-025 | No | No | Yes | OPEN |
| PC-026 | MEDIUM | Price Architecture | C | — | CC-026 | PCtrl-026 | No | Yes | Partial | OPEN |
| PC-027 | MEDIUM | Database | J | — | CC-027 | PCtrl-027 | No | No | Yes | OPEN |
| PC-028 | MEDIUM | Oracle Migration | I | — | CC-028 | PCtrl-028 | No | Yes | Yes | OPEN |
| PC-029 | MEDIUM | Evidence Schema | G | PC-011.b | CC-029 | PCtrl-029 | Yes | No | Yes | OPEN |
| PC-030 | MEDIUM | Production Guard | E | PC-013.c, PC-013.e | CC-030 | PCtrl-030 | No | Yes | Partial | OPEN |
| PC-031 | MEDIUM | Microservices | B | — | CC-031 | PCtrl-031 | No | Yes | Partial | OPEN |
| PC-032 | LOW | Documentation | K | — | CC-032 | PCtrl-032 | No | No | No | OPEN |
| PC-033 | LOW | CI Security | F | PC-034.a | CC-033 | PCtrl-033 | No | No | Partial | OPEN |
| PC-034 | MEDIUM | Evidence | F, L | PC-034.a | CC-034 | PCtrl-034 | No | No | Partial | OPEN |
| PC-035 | LOW | Observability | G | — | CC-035 | PCtrl-035 | No | No | Partial | OPEN |
| PC-036 | INFORMATIONAL | Documentation | A, K | PC-015.a | CC-036 | PCtrl-036 | No | No | No | OPEN |
| PC-037 | INFORMATIONAL | Marketing | K | — | CC-037 | PCtrl-037 | No | No | No | OPEN |
| PC-038 | INFORMATIONAL | Legal | L | — | CC-038 | PCtrl-038 | No | No | No | OPEN |
| PC-039 | INFORMATIONAL | Test Data | F | PC-022.a | CC-039 | PCtrl-039 | No | No | Partial | OPEN |
| PC-040 | INFORMATIONAL | Test Data | G | — | CC-040 | PCtrl-040 | No | No | Partial | OPEN |
| PC-041 | MEDIUM | Float Migration | C, J | PC-009.c | CC-041 | PCtrl-041 | No | Yes | Yes | OPEN |
| PC-042 | MEDIUM | Governance | K | PC-015.a | CC-042 | PCtrl-042 | Yes | No | Yes | OPEN |

---

## Sub-Finding Traceability

| Sub-ID | Parent | Register | Severity | CC | PCtrl | Independent closure required |
|--------|--------|----------|----------|-----|-------|------------------------------|
| PC-008.a | PC-008 | B | HIGH | CC-008.a | PCtrl-008.a | Yes — auto-exec default parity |
| PC-008.b | PC-008 | B | HIGH | CC-008.b | PCtrl-008.b | Yes — route inventory |
| PC-008.c | PC-008 | B, I | HIGH | CC-008.c | PCtrl-008.c | Yes — pipeline scope decision |
| PC-008.d | PC-008 | L | HIGH | CC-008.d | PCtrl-008.d | Yes — compliance single entry |
| PC-009.a | PC-009 | B | HIGH | CC-009.a | PCtrl-009.a | Yes — import lint zero violations |
| PC-009.b | PC-009 | A | HIGH | CC-009.b | PCtrl-009.b | Yes — grid non-authoritative |
| PC-009.c | PC-009 | J, C | HIGH | CC-009.c | PCtrl-009.c | Yes — decimal compute path |
| PC-009.d | PC-009 | B, C | HIGH | CC-009.d | PCtrl-009.d | Yes — single portfolio read model |
| PC-010.a | PC-010 | D | HIGH | CC-010.a | PCtrl-010.a | Yes — connector auth DENY tests |
| PC-011.a | PC-011 | G | HIGH | CC-011.a | PCtrl-011.a | Yes — stale hour veto artifact |
| PC-011.b | PC-011 | G | HIGH | CC-011.b | PCtrl-011.b | Yes — gate_scope schema |
| PC-012.a | PC-012 | I | HIGH | CC-012.a | PCtrl-012.a | Yes — single inference entry |
| PC-012.b | PC-012 | I | HIGH | CC-012.b | PCtrl-012.b | Yes — CAP-053 E2E lineage |
| PC-013.a | PC-013 | E, H | HIGH | CC-013.a | PCtrl-013.a | Yes — fixture validation CI |
| PC-013.b | PC-013 | E | HIGH | CC-013.b | PCtrl-013.b | Yes — cross-tenant negatives |
| PC-013.c | PC-013 | E | HIGH | CC-013.c | PCtrl-013.c | Yes — prod demo deny audit |
| PC-013.d | PC-013 | E, L | HIGH | CC-013.d | PCtrl-013.d | Yes — MFA policy + gate |
| PC-013.e | PC-013 | E, L | HIGH | CC-013.e | PCtrl-013.e | Yes — prod route manifest |
| PC-013.f | PC-013 | E, B | HIGH | CC-013.f | PCtrl-013.f | Yes — P09 RBAC facade proof |
| PC-015.a | PC-015 | A, K | HIGH | CC-015.a | PCtrl-015.a | Yes — matrix absent/archived status |
| PC-015.b | PC-015 | A | HIGH | CC-015.b | PCtrl-015.b | Yes — grid vs CAP disclaimer |
| PC-019.a | PC-019 | I | MEDIUM | CC-019.a | PCtrl-019.a | Yes — training/serving leakage test |
| PC-021.a | PC-021 | H | HIGH | CC-021.a | PCtrl-021.a | Yes — manifest tree diff zero |
| PC-022.a | PC-022 | F | HIGH | CC-022.a | PCtrl-022.a | Yes — blocking collection job |
| PC-022.b | PC-022 | F | HIGH | CC-022.b | PCtrl-022.b | Yes — SSE E2E CI job |
| PC-022.c | PC-022 | F, D | HIGH | CC-022.c | PCtrl-022.c | Yes — concurrency suite |
| PC-022.d | PC-022 | F, G | HIGH | CC-022.d | PCtrl-022.d | Yes — restore drill artifact |
| PC-022.e | PC-022 | F, D | HIGH | CC-022.e | PCtrl-022.e | Yes — bypass DENY matrix |
| PC-034.a | PC-034 | F | MEDIUM | CC-034.a | PCtrl-034.a | Yes — workflow coupling |

---

## Closure Chain Progress

| Stage | Artifact | Status |
|-------|----------|--------|
| Diagnosis + Root Cause | ROOT_CAUSE_REGISTER.md v4.0 | VERIFIED_CLOSED |
| Corrective + Preventive Controls | CORRECTIVE_PREVENTIVE_CONTROL_REGISTER.md v5.0 | REMEDIATED_PENDING_IVV |
| Implementation Contract | ROOT_REMEDIATION_MASTER_PLAN.md v3.0 | SEMANTICALLY_INVALID — DO NOT EXECUTE |
| Tests | MASTER_PLAN test matrix (2286 cells) | SEMANTICALLY_INVALID — DO NOT EXECUTE |
| IVV | Per-stage signoff | Stage 2 pending |
| LOCK | 42/42 + 29/29 VERIFIED_CLOSED | NOT REACHED |

---

## Stage 2 Exclusions (explicit)

| Artifact section | Status |
|------------------|--------|
| Implementation steps R0–R8 | Stage 3 blocked — see MASTER_PLAN v3.0 INVALID |
| Test matrix 2286 cells | Stage 4 blocked |
| Migrations MIG-01–07 | Stage 5 blocked |
| Production code changes | NOT AUTHORIZED — design only |
