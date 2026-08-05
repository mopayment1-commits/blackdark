"""Shared framework for CORRECTIVE_PREVENTIVE_CONTROL_REGISTER v6.0 generation."""

from __future__ import annotations

HEADER = """# Corrective & Preventive Control Register — Stage 2

**Version:** 6.0 (Stage 2 — full 23-field control schema)  
**Date:** 2026-08-05  
**Validation branch:** `cursor/g2-g3-quality-gates-soak`  
**Validation commit:** `14112859677b68932c79b31d09a8aed49272794a`  
**Upstream baseline:** `ROOT_CAUSE_REGISTER.md` v4.0 (Stage 1 evidence-anchored)  
**Scope:** 142 unique controls (71 CC + 71 PCtrl) — design contracts only; no implementation steps.

## Stage 2 Notice

Each control below maps one-to-one to a Stage 1 finding (42 parents + 29 sub-findings). Template substitution, delegated closures, advisory-only preventive gates, and cross-control "same as" references are forbidden. Implementation (Stage 3), test matrix (Stage 4), and schema migrations (Stage 5) remain **SEMANTICALLY_INVALID — DO NOT EXECUTE** until independently verified.

## Control Field Schema (23 fields — all mandatory)

| # | Field name |
|---|------------|
| 1 | Control ID |
| 2 | Finding ID |
| 3 | Control type |
| 4 | Verified Stage 1 root cause addressed |
| 5 | Exact repository evidence files |
| 6 | Exact symbols/settings/routes/tables/functions |
| 7 | Current defective behavior |
| 8 | Required target behavior |
| 9 | Control mechanism |
| 10 | Enforcement point |
| 11 | Explicit affected files or bounded file families |
| 12 | Authority/owning bounded context |
| 13 | Positive impact |
| 14 | Potential negative impact |
| 15 | Other findings affected |
| 16 | Required downstream revalidation |
| 17 | Shared ownership or NONE |
| 18 | Objective acceptance criteria |
| 19 | Verification mechanism |
| 20 | Failure condition |
| 21 | Evidence output required |
| 22 | Architectural-decision compatibility |
| 23 | Stage-boundary declaration |

---

"""

FIELDS = [
    "Control ID",
    "Finding ID",
    "Control type",
    "Verified Stage 1 root cause addressed",
    "Exact repository evidence files",
    "Exact symbols/settings/routes/tables/functions",
    "Current defective behavior",
    "Required target behavior",
    "Control mechanism",
    "Enforcement point",
    "Explicit affected files or bounded file families",
    "Authority/owning bounded context",
    "Positive impact",
    "Potential negative impact",
    "Other findings affected",
    "Required downstream revalidation",
    "Shared ownership or NONE with justification",
    "Objective acceptance criteria",
    "Verification mechanism",
    "Failure condition",
    "Evidence output required",
    "Architectural-decision compatibility",
    "Stage-boundary declaration",
]

STAGE_BOUNDARY = "DESIGN_ONLY — NOT EXECUTABLE"

FOOTER = """
---

## Control Coverage Index

| Category | Count | IDs |
|----------|-------|-----|
| Parent corrective | 42 | CC-001–CC-042 |
| Parent preventive | 42 | PCtrl-001–PCtrl-042 |
| Sub corrective | 29 | CC-008.a–CC-034.a (see Sub-Finding sections) |
| Sub preventive | 29 | PCtrl-008.a–PCtrl-034.a (see Sub-Finding sections) |
| **Total controls** | **142** | |

Every parent PC-001–PC-042 and sub-finding PC-008.a–PC-034.a (29 subs) has exactly one CC and one PCtrl. Sub-finding controls address independent closure evidence from Stage 1 with scope narrower than their parent.

---

## Register Cross-Reference

| Register | Primary control themes |
|----------|------------------------|
| A | CC-003, CC-015, CC-036, CC-037, CC-009.b, CC-015.a/b, PCtrl-003, PCtrl-015, PCtrl-036, PCtrl-037 |
| B | CC-007–009, CC-031, CC-008.a–d, CC-009.a/d, CC-020, platform route/import/topology controls |
| C | CC-004, CC-026, CC-009.c, CC-009.d, PCtrl-004, PCtrl-026, PCtrl-009.c |
| D | CC-005, CC-010, CC-014, CC-010.a, CC-022.c/e, PCtrl-005, PCtrl-010 |
| E | CC-013, CC-030, CC-013.a–f, PCtrl-013, PCtrl-030, PCtrl-013.b |
| F | CC-002, CC-022, CC-033, CC-034, CC-039, CC-022.a–e, CC-034.a, PCtrl-002, PCtrl-022 |
| G | CC-011, CC-029, CC-035, CC-040, CC-011.a/b, PCtrl-011, PCtrl-029, PCtrl-035 |
| H | CC-001, CC-007, CC-016, CC-017, CC-021, CC-025, CC-021.a, PCtrl-001, PCtrl-007, PCtrl-021 |
| I | CC-012, CC-019, CC-028, CC-012.a/b, CC-019.a, PCtrl-012, PCtrl-019 |
| J | CC-006, CC-027, CC-041, CC-009.c, PCtrl-006, PCtrl-027, PCtrl-041 |
| K | CC-023, CC-032, CC-036, CC-037, CC-042, CC-015.a, PCtrl-023, PCtrl-032, PCtrl-042 |
| L | CC-024, CC-038, CC-008.d, CC-013.d/e, PCtrl-024, PCtrl-008.d |

---

## Stage 2 IVV Checklist (design-level)

1. 42/42 parent CC + 42/42 parent PCtrl present with unique statements and all 23 fields populated
2. 29/29 sub CC + 29/29 sub PCtrl present with distinct scope from parent
3. Zero controls use parameter-substituted boilerplate or delegated "see parent" closures
4. Every control references concrete files, jobs, or modules from ROOT_CAUSE_REGISTER v4.0 evidence
5. All PCtrl controls specify blocking CI, runtime, schema, or static-analysis enforcement (no advisory-only)
6. Special repairs verified: PC-031 topology contract, PC-036 taxonomy authority, PC-037 attestation binding, PCtrl-020 blocking composition invariant, CC-009.c independent scan decimal path, CC-022.a independent collection gate, PCtrl-013.b independent tenant repository gate
7. No MIG-01–MIG-07 references; no R0-Sxx step references in control bodies
8. Proposed new artifacts marked PROPOSED_ARTIFACT — STAGE 3 MUST DECIDE LOCATION
9. Stage-boundary declaration on every control: DESIGN_ONLY — NOT EXECUTABLE

**Stage 2 status:** REMEDIATED_PENDING_IVV
"""


def dec(*pairs: tuple[str, str, str]) -> str:
    order = ["DEC-A", "DEC-B", "DEC-C", "DEC-D", "DEC-E"]
    m = {k: f"{k}: {status} — {reason}" for k, status, reason in pairs}
    for k in order:
        if k not in m:
            m[k] = f"{k}: NOT_APPLICABLE — control scope does not intersect this decision binding"
    return "; ".join(m[k] for k in order)


def esc(val: str) -> str:
    return val.replace("|", "\\|")


def render_control(cid: str, title: str, data: dict[str, str]) -> str:
    lines = [f"### {cid} — {title}", "", "| # | Field | Value |", "|---:|---|---|"]
    for i, field in enumerate(FIELDS, 1):
        val = data.get(field, STAGE_BOUNDARY if field == "Stage-boundary declaration" else "")
        lines.append(f"| {i} | {field} | {esc(val)} |")
    lines.append("")
    return "\n".join(lines)


def cc(fid: str, num: str, title: str, **kw: str) -> tuple[str, str, dict]:
    d = {
        "Control ID": f"CC-{num}",
        "Finding ID": fid,
        "Control type": "CORRECTIVE",
        "Stage-boundary declaration": STAGE_BOUNDARY,
        **kw,
    }
    return (f"CC-{num}", title, d)


def pc(fid: str, num: str, title: str, **kw: str) -> tuple[str, str, dict]:
    d = {
        "Control ID": f"PCtrl-{num}",
        "Finding ID": fid,
        "Control type": "PREVENTIVE",
        "Stage-boundary declaration": STAGE_BOUNDARY,
        **kw,
    }
    return (f"PCtrl-{num}", title, d)
