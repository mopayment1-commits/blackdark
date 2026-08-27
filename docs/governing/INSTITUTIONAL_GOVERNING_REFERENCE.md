# BLACKDARK — Institutional Governing Reference (Adopted)

**Status:** ACTIVE — permanent review & acceptance baseline for this project  
**Adopted:** 2026-08-21  
**Authority:** User directive — do not override without explicit user instruction

## Source document

| Field | Value |
|---|---|
| Title | BLACKDARK Final Institutional Merged Specification (Five-Layer Verified) |
| Role | **Baseline** for requirements, controls, evidence — **not** an implementation certification |
| Review date | 21 August 2026 |
| Source units | 3,142 SRC-IDs (Excel ↔ Word PASS, 100%) |
| Normative controls | **42** (GOV, ARC, QUA, SEC, DAT, REL, QA, AI, FIN, PRV, UX) |
| Five-layer doc integrity | PASS (Source → Standards → Traceability → De-dup → Render QA) |
| Local copy (upload) | `/home/ubuntu/.cursor/projects/workspace/uploads/BLACKDARK_FINAL_INSTITUTIONAL_MERGED_SPECIFICATION_FIVE_LAYER_VERIFIED_3108.pdf` |
| Extracted text (agent use) | `/tmp/blackdark_spec.txt` (regenerate via pdftotext if missing) |
| **Agent context injection (Arabic/EN)** | [`BLACKDARK_CONTEXT.md`](../../BLACKDARK_CONTEXT.md) at repo root — **adopted 2026-08-24**; use `@BLACKDARK_CONTEXT.md` for defects D-01→D-15, roadmap T01–T18, and executive **NOT READY** verdict |

## Adopted understanding (SSOT)

1. **Binary verdict only:** `VERIFIED COMPLETE` or `NOT READY` — no gray “mostly ready”.
2. **Baseline ≠ certification:** The PDF defines *what must be proven*; it does not claim the repo already proves it.
3. **42 controls are normative; capabilities are not.** Feature names (engines, 50ms, 99.9%, etc.) live in capability registry — they close controls only with code + tests + evidence.
4. **Evidence Room rule:** No control is PASS without reproducible evidence (architecture, code refs, commit, tests, results, limitations).
5. **Promotion gates G1–G8** apply to any new normative requirement.
6. **Certification statuses:** PASS | PASS WITH RISK | NOT VERIFIED | FAIL | EXTERNAL EVIDENCE.
7. **Product north star (capability layer):** Cross-Domain Decision Intelligence + Evidence/Confidence/Freshness/Sources/Conflicting Signals — not feature parity or marketing claims.
8. **Fail-closed financial & data truth:** net economics, stale reject, quarantine on disagreement, unknown ≠ 0, no mock/demo as sole production proof (GOV-003, QA-004, FIN-*, DAT-*).

## Priority tiers (reference only — do not reorder user’s active work)

- **P0 deal blockers:** SSO, MFA, multi-tenant, KYC, signed capacity, SOC2/ISO path, pentest, MSA/DPA.
- **P1 procurement:** RBAC, model card, IR, WAF/CDN, HA signed, observability, secrets manager.
- **Product differentiation (after truth path):** Market Regime → Entity metrics → Provenance → Cross-Domain Decision stack.

## Operating rules for future agent turns

### DO

- Use this reference to **review** architecture, security, QA, product/design, and **evidence** when the user assigns a task.
- Apply controls to **actual repo state** (main, open PRs, existing tests/docs) — map what exists vs NOT VERIFIED vs EXTERNAL EVIDENCE.
- Invoke specific control IDs (e.g. SEC-003, QA-004, DAT-003) as **acceptance criteria** when relevant to the task.
- Prefer incremental closure of gaps; reuse existing artifacts (readiness reports, tests, CI) instead of duplicating work.
- State explicitly when something is NOT VERIFIED or requires EXTERNAL EVIDENCE.

### DO NOT (unless user explicitly requests)

- Start new implementation, reprioritize, or open Branch/PR **solely because** this reference was adopted.
- Treat the PDF as a literal build backlog or re-implement controls already verified in repo.
- Convert capability/marketing language into normative PASS without evidence.
- Claim acquisition-ready or VERIFIED COMPLETE without Evidence Room + Zero-Defect Gate alignment.

## 42 controls (quick index)

| Domain | IDs |
|---|---|
| Governance | GOV-001, GOV-002, GOV-003 |
| Architecture | ARC-001, ARC-002 |
| Quality | QUA-001 |
| Security | SEC-001 … SEC-009 |
| Data | DAT-001 … DAT-004 |
| Reliability | REL-001 … REL-005 |
| QA & Evidence | QA-001 … QA-004 |
| AI | AI-001 … AI-005 |
| Financial | FIN-001 … FIN-004 |
| Privacy | PRV-001, PRV-002 |
| UX & Design | UX-001 … UX-003 |

## Repo context snapshot (2026-08-21)

- **Branch at adoption:** `main` (clean), production hardening merges present.
- **Known autonomous posture (docs):** institutional/launch code gates largely complete; **acquisition NOT COMPLETE** (founder/external items).
- **Open draft PRs exist** (#71 institutional-hardening, #73 decision-api, #75 prod E2E, etc.) — do not spawn parallel tracks without user direction.

## Review checklist (invoke when task touches the area)

- [ ] Maps to a control ID or explicit user scope?
- [ ] Evidence exists or gap labeled NOT VERIFIED / EXTERNAL EVIDENCE?
- [ ] No unsupported claims (G5)?
- [ ] Single ownership / no duplicate authority (GOV-002)?
- [ ] Production path vs mock/demo distinguished (QA-004)?
- [ ] Acceptance criteria stated before merge?

---

*This file is the agent’s persistent governing reference. Update only on explicit user instruction or when repo-verified status materially changes during assigned work.*
