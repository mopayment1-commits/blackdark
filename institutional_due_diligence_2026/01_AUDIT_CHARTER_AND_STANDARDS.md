# 01 — AUDIT CHARTER AND STANDARDS

**Audit ID:** `IDA-2026-BLACKDARK-001`  
**Wave:** 0  
**Generated:** 2026-09-10T23:36:00Z  
**Spec Reference:** §0–§15, §113

---

## 1. Audit Charter (Summary)

See `BLACKDARK_AUDIT_SSOT.md` §1 for full charter.

**Mode:** Independent institutional due diligence — diagnosis only.  
**Prohibited during audit:** remediation, refactoring, config/DB changes, deployment, commits, pushes.

---

## 2. Zero-Trust Policy

All prior claims including but not limited to:
- README assertions
- `docs/BATCH07_FINAL_LOCAL_FREEZE.json` (`BATCH07_FINAL_LOCAL_FREEZE=true`, CI PASS)
- RTM / capability matrices
- Prior audit registers (`blackdark-forensics` session)
- Test pass status
- Status registers and feature matrices

are classified **CLAIM REQUIRING REVALIDATION** until supported by Evidence IDs at appropriate hierarchy (E1–E6).

---

## 3. Authoritative Source Policy (§5–§6)

Only recognized institutional/regulatory/standards-body sources may anchor audit methodology. Blogs and marketing content excluded.

**Currentness verification:** Required before each standard is used in findings. At Wave 0, all standards listed with `Currentness: NOT VERIFIED`.

---

## 4. Standards Register (Detailed)

### 4.1 Model Risk

| Field | Value |
|---|---|
| Standard | Federal Reserve / OCC / FDIC Revised Guidance on Model Risk Management |
| Reference | SR 26-2, April 2026 |
| Mapping | INSTITUTIONAL BENCHMARK |
| Legal applicability | APPLICABILITY NOT VERIFIED |
| Use in audit | Model identification, tiering, validation, effective challenge, governance |
| Compliance claim permitted | **NO** without independent proof |

### 4.2 Data Governance

| Field | Value |
|---|---|
| Standard | BCBS 239 — Principles for effective risk data aggregation and risk reporting |
| Mapping | INSTITUTIONAL BENCHMARK |
| Legal applicability | APPLICABILITY NOT VERIFIED |
| Use in audit | Accuracy, integrity, completeness, timeliness, lineage, reconciliation |

### 4.3 Software Quality

| Field | Value |
|---|---|
| Standard | ISO/IEC 25010:2023 |
| Mapping | TECHNICAL BENCHMARK |
| Use in audit | Functional suitability, reliability, security, maintainability, etc. |

### 4.4 Security Benchmarks

| Standard | Mapping |
|---|---|
| NIST Cybersecurity Framework 2.0 | TECHNICAL BENCHMARK |
| NIST SP 800-53 Rev.5 | TECHNICAL BENCHMARK |
| NIST SP 800-218 SSDF | TECHNICAL BENCHMARK |
| CIS Controls v8.1 | TECHNICAL BENCHMARK |
| OWASP ASVS (latest stable) | TECHNICAL BENCHMARK |
| OWASP API Security Top 10 (latest stable) | TECHNICAL BENCHMARK |
| OWASP Top 10 (latest stable) | TECHNICAL BENCHMARK |
| ISO/IEC 27001:2022 | TECHNICAL BENCHMARK |

### 4.5 Operational Resilience

| Standard | Mapping | Legal claim |
|---|---|---|
| Basel Principles for Operational Resilience | INSTITUTIONAL BENCHMARK | NOT VERIFIED |
| DORA | INSTITUTIONAL BENCHMARK | NOT VERIFIED |
| ISO 22301 | TECHNICAL BENCHMARK | NOT VERIFIED |
| NIST SP 800-61r3 | TECHNICAL BENCHMARK | NOT VERIFIED |

### 4.6 AI / ML Governance

| Standard | Mapping |
|---|---|
| NIST AI RMF | TECHNICAL BENCHMARK |
| NIST Generative AI Profile | TECHNICAL BENCHMARK |
| ISO/IEC 42001 | TECHNICAL BENCHMARK |

### 4.7 SOC 2 / Trust Services

| Standard | Mapping | Note |
|---|---|---|
| AICPA Trust Services Criteria | INSTITUTIONAL BENCHMARK (readiness) | No SOC 2 attestation claim permitted |

### 4.8 GIPS Applicability Gate (§15)

**Status at Wave 0:** NOT VERIFIED — Wave 1 must determine whether BLACKDARK presents portfolio/strategy/track-record/backtested performance to users/clients.

If no such presentation: `GIPS = NOT APPLICABLE`  
If yes: classify actual/simulated/hypothetical/backtested before applying CFA/GIPS principles.

---

## 5. Evidence Hierarchy (§101)

| Level | Definition | Acceptable for VERIFIED_OPERATIONAL |
|---|---|---|
| E1 | Reproducible runtime proof | YES |
| E2 | Independent recomputation / E2E | YES |
| E3 | Integration evidence | PARTIAL |
| E4 | Code + strong automated tests | PARTIAL |
| E5 | Code only | NO |
| E6 | Documentation/claim only | NO |

---

## 6. Feature Status Vocabulary (§103)

Permitted statuses only:  
`VERIFIED_OPERATIONAL`, `OPERATIONAL_WITH_LIMITATION`, `PARTIALLY_IMPLEMENTED`, `IMPLEMENTED_NOT_REACHABLE`, `FRONTEND_ONLY`, `BACKEND_ONLY`, `PLACEHOLDER`, `BROKEN`, `DEAD`, `EXTERNALLY_BLOCKED`, `NOT_IMPLEMENTED`, `NOT_VERIFIED`

---

## 7. Finding Severity (§99)

P0 (Critical) → P1 (High) → P2 (Medium) → P3 (Low) → OBSERVATION

P0 override rule applies at final verdict (§119).

---

## 8. Acquisition Decision Gates (§118) — All NOT VERIFIABLE at Wave 0

| Gate | Domain | Status |
|---|---|---|
| A | Technical Integrity | NOT VERIFIABLE |
| B | Financial / Quantitative Integrity | NOT VERIFIABLE |
| C | Model Risk | NOT VERIFIABLE |
| D | Data Integrity | NOT VERIFIABLE |
| E | Security | NOT VERIFIABLE |
| F | Processing Integrity | NOT VERIFIABLE |
| G | Product Completeness | NOT VERIFIABLE |
| H | Operational Resilience | NOT VERIFIABLE |
| I | Scalability | NOT VERIFIABLE |
| J | Maintainability | NOT VERIFIABLE |
| K | AI / ML Risk | NOT VERIFIABLE |
| L | IP / Data / Vendor Risk | NOT VERIFIABLE |
| M | Acquisition Readiness | NOT VERIFIABLE |
| N | Institutional Maturity | NOT VERIFIABLE |

---

## 9. Wave 0 Standards Conclusion

Standards register **initialized**. No standard currentness externally verified at Wave 0. No compliance claims issued.
