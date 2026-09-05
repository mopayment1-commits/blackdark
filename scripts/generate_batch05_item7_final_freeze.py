#!/usr/bin/env python3
"""Item 7 — Final institutional freeze stamp for Batch05 (IDs 201-250).

Stamps RTM / Acceptance / Pentagonal with Items 1-6 snapshot.
Produces blockers matrix and master freeze artifact.
Does NOT elevate independent, production_aligned, or pa_elevated.
"""

from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

ARABIC_PHASE = (
    "هذه المرحلة = بناء spine + قبول مسبق + اختبارات محلية فقط. "
    "لا إعلان اكتمال حوكمة · لا Batch05 complete · لا جاهزية حية 100%."
)

ACCEPTANCE = ROOT / "docs/BATCH05_ACCEPTANCE_201_250.json"
RTM = ROOT / "docs/BATCH05_RTM_201_250.json"
PENTAGONAL = ROOT / "docs/BATCH05_PENTAGONAL_TEMPLATE_201_250.json"
PROGRESS_MD = ROOT / "docs/BATCH05_INSTITUTIONAL_PROGRESS_REPORT.md"
OUT_FREEZE = ROOT / "docs/BATCH05_ITEM7_FINAL_INSTITUTIONAL_FREEZE.json"
OUT_MATRIX_JSON = ROOT / "docs/BATCH05_REMAINING_BLOCKERS_MATRIX.json"
OUT_MATRIX_MD = ROOT / "docs/BATCH05_REMAINING_BLOCKERS_MATRIX.md"

ITEM_ARTIFACTS = {
    "item_1_pa_sweep": "docs/BATCH05_PA_CLOSURE_SWEEP_43.json",
    "item_2_reused_link": "docs/BATCH05_REUSED_LINK_PARTIAL_DISPOSITION.json",
    "item_3_entitlement": "docs/BATCH05_ENTITLEMENT_GATEWAY_PROOF.json",
    "item_4_heroes": "docs/BATCH05_HERO_SIX_FINAL_FREEZE.json",
    "item_5_gate_zero": "docs/BATCH05_GATE_ZERO_CHECKLIST.md",
    "item_6_sre_prr": "docs/BATCH05_SRE_PRR_READINESS_PACKAGE.json",
}

HARD_BLOCKERS = [
    {
        "id": "LIVE_E2E",
        "status": "AWAITING_DEPLOY",
        "description": "Live E2E probes on deployed Railway/production environment",
        "artifact": "docs/BATCH05_GATE_ZERO_CHECKLIST.md",
    },
    {
        "id": "GATE_ZERO_RUN",
        "status": "AWAITING_DEPLOY",
        "description": "Gate Zero checklist rows G1–G7 not executed on live",
        "artifact": "docs/BATCH05_GATE_ZERO_CHECKLIST.md",
    },
    {
        "id": "12207_VALIDATION_SIGNOFF",
        "status": "IN_PROGRESS_LOCAL",
        "description": "Owner Validation sign-off after live evidence — not Transition yet",
        "artifact": "docs/BATCH05_SRE_PRR_READINESS_PACKAGE.json",
    },
    {
        "id": "12207_TRANSITION_SIGNOFF",
        "status": "NOT_STARTED",
        "description": "Transition sign-off blocked until Validation complete on live",
        "artifact": "docs/BATCH05_SRE_PRR_READINESS_PACKAGE.json",
    },
    {
        "id": "12207_OPERATION",
        "status": "NOT_STARTED",
        "description": "Operation claim forbidden until Transition complete",
        "artifact": "docs/BATCH05_SRE_PRR_READINESS_PACKAGE.json",
    },
    {
        "id": "SRE_PRR_SECOND_REVIEW",
        "status": "NOT_STARTED",
        "description": "SRE PRR second-review sign-off — intake ready locally only",
        "artifact": "docs/BATCH05_SRE_PRR_READINESS_PACKAGE.json",
    },
    {
        "id": "PENTAGONAL_COL10",
        "status": "NOT_STARTED",
        "description": "Per-ID pentagonal column 10 institutional second review",
        "artifact": "docs/BATCH05_PENTAGONAL_TEMPLATE_201_250.json",
    },
    {
        "id": "PER_ID_PA_ELEVATION",
        "status": "NOT_STARTED",
        "description": "Each strangler ID requires all blockers cleared before PRODUCTION-ALIGNED",
        "artifact": "docs/BATCH05_PA_CLOSURE_SWEEP_43.json",
    },
]

PROVEN_LOCAL = [
    {"area": "Strangler spine", "status": "PROVEN_LOCAL", "evidence": "43/43 builders in cap646/batch05_strangler_spine.py"},
    {"area": "PA sweep (Item 1)", "status": "PROVEN_LOCAL", "evidence": "43/43 domain rules pass on local execute_capability probe"},
    {"area": "REUSED-LINK disposition (Item 2)", "status": "PROVEN_LOCAL", "evidence": "#232 CLOSED; #214/#245 TOLERATE until 2026-12-31"},
    {"area": "Entitlement gateway (Item 3)", "status": "PROVEN_LOCAL", "evidence": "43 strangler + 5 REUSED-LINK gateway proofs; all_verified=true"},
    {"area": "Six Heroes freeze (Item 4)", "status": "PROVEN_LOCAL", "evidence": "FINAL_FREEZE_LOCAL — no strangler in hero inputs"},
    {"area": "Gate Zero checklist (Item 5)", "status": "PROVEN_LOCAL", "evidence": "Checklist prepared — execution NOT done"},
    {"area": "SRE PRR intake (Item 6)", "status": "PROVEN_LOCAL", "evidence": "SECOND_REVIEW_READY_LOCAL — sign-off NOT done"},
    {"area": "MECE+TIME+ADR", "status": "PROVEN_LOCAL", "evidence": "Frozen per BATCH05_MECE_TIME_ADR_INDEX.md"},
]


def git_commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def git_branch() -> str:
    return subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def stamp_doc(doc: dict[str, Any], *, kind: str) -> dict[str, Any]:
    out = dict(doc)
    out["item7_final_freeze"] = {
        "frozen_at": datetime.now(UTC).isoformat(),
        "git_commit": git_commit(),
        "git_branch": git_branch(),
        "pr": 366,
        "sequence_item": 7,
        "build_phase": "OPEN",
        "batch05_independent": 0,
        "progress_826": 179,
        "production_aligned_count": 0,
        "pa_elevated_count": 0,
        "not_claimed": ["LOCAL_GOVERNANCE_COMPLETE", "LIVE_READY", "batch05_complete", "OPERATION"],
        "items_1_6_complete": True,
        "artifact_kind": kind,
        "phase_statement_ar": ARABIC_PHASE,
    }
    out["phase_statement_ar"] = ARABIC_PHASE
    return out


def build_readiness_matrix(pa_sweep: dict, entitlement: dict, disposition: dict) -> dict[str, Any]:
    strangler_count = pa_sweep["summary"]["strangler_count"]
    per_id_blockers = []
    for row in pa_sweep["rows"]:
        per_id_blockers.append(
            {
                "capability_id": row["capability_id"],
                "pa_elevated": False,
                "production_aligned": False,
                "verification_local": row["pa_closure_phase"],
                "validation": "IN_PROGRESS_LOCAL",
                "transition": "NOT_STARTED",
                "operation": "NOT_STARTED",
                "live_e2e": "AWAITING_DEPLOY",
                "gate_zero": "AWAITING_DEPLOY",
                "entitlement_local": "PROVEN_LOCAL",
                "pentagonal_col10": "NOT_STARTED",
                "sre_prr_signoff": "NOT_STARTED",
                "may_elevate_pa": False,
            }
        )

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "git_commit": git_commit(),
        "scope": "Batch05 readiness — proven local vs awaiting deploy / not started",
        "absolute_locks": {
            "batch05_independent": 0,
            "progress_826": 179,
            "production_aligned_count": 0,
            "pa_elevated_count": 0,
            "build_phase": "OPEN",
        },
        "phase_statement_ar": ARABIC_PHASE,
        "12207_lifecycle": {
            "verification": "LOCAL_COMPLETE",
            "validation": "IN_PROGRESS_LOCAL",
            "transition": "NOT_STARTED",
            "operation": "NOT_STARTED",
        },
        "summary": {
            "proven_local_count": len(PROVEN_LOCAL),
            "hard_blockers_count": len(HARD_BLOCKERS),
            "strangler_ids": strangler_count,
            "strangler_pa_eligible_now": 0,
            "entitlement_stranglers_verified": entitlement.get("strangler_test_case_count"),
            "reused_link_closed": disposition["summary"]["closed_count"],
            "reused_link_tolerate": disposition["summary"]["tolerate_count"],
        },
        "proven_local": PROVEN_LOCAL,
        "hard_blockers": HARD_BLOCKERS,
        "per_id_strangler_readiness": per_id_blockers,
        "elevation_policy": (
            "Per-ID PRODUCTION-ALIGNED / batch05_independent increment only when "
            "LIVE_E2E + Gate Zero run + 12207 Validation+Transition + SRE PRR sign-off + Col10 all pass for that ID"
        ),
    }


def render_matrix_md(matrix: dict[str, Any]) -> str:
    lines = [
        "# Batch05 Remaining Blockers Matrix",
        "",
        f"**Generated:** {matrix['generated_at']} | **Commit:** `{matrix['git_commit'][:12]}`",
        "",
        ARABIC_PHASE,
        "",
        "---",
        "",
        "## Absolute locks",
        "",
        "| Lock | Value |",
        "|------|-------|",
        f"| `batch05_independent` | **{matrix['absolute_locks']['batch05_independent']}** |",
        f"| `progress_826` | **{matrix['absolute_locks']['progress_826']}** |",
        f"| `production_aligned_count` | **{matrix['absolute_locks']['production_aligned_count']}** |",
        f"| `pa_elevated_count` | **{matrix['absolute_locks']['pa_elevated_count']}** |",
        "",
        "## 12207 lifecycle",
        "",
        "| Phase | Status |",
        "|-------|--------|",
    ]
    for phase, status in matrix["12207_lifecycle"].items():
        lines.append(f"| {phase} | **{status}** |")
    lines.extend(["", "## Proven locally (Items 1–6)", "", "| Area | Status | Evidence |", "|------|--------|----------|"])
    for row in matrix["proven_local"]:
        lines.append(f"| {row['area']} | {row['status']} | {row['evidence']} |")
    lines.extend(["", "## Hard blockers (no elevation until cleared)", "", "| ID | Status | Description |", "|----|--------|-------------|"])
    for b in matrix["hard_blockers"]:
        lines.append(f"| `{b['id']}` | **{b['status']}** | {b['description']} |")
    lines.extend(
        [
            "",
            "## Per-ID strangler readiness (43)",
            "",
            "All 43 stranglers: `may_elevate_pa=false` · `live_e2e=AWAITING_DEPLOY` · `gate_zero=AWAITING_DEPLOY`",
            "",
            ARABIC_PHASE,
            "",
        ]
    )
    return "\n".join(lines)


def update_progress_report(commit: str) -> None:
    text = PROGRESS_MD.read_text(encoding="utf-8")
    if "## 13) Item 7" in text:
        return
    item7 = f"""
---

## 13) Item 7 — Final institutional freeze

**Commit:** `{commit[:12]}` · **Master artifact:** `docs/BATCH05_ITEM7_FINAL_INSTITUTIONAL_FREEZE.json`  
**Blockers matrix:** `docs/BATCH05_REMAINING_BLOCKERS_MATRIX.json`

| Stamp | RTM · Acceptance · Pentagonal · Progress |
|-------|------------------------------------------|
| `item7_final_freeze` | Applied to all core artifacts |
| Elevation | **0** — no PA / independent / production_aligned |
| Hard blockers | LIVE_E2E · Gate Zero run · 12207 Transition · SRE PRR sign-off |

{ARABIC_PHASE}
"""
    marker = "## 12) Frozen artifacts"
    if marker in text:
        text = text.replace(
            "\n---\n\nهذه المرحلة = بناء spine",
            item7 + "\n---\n\n## 14) Complete artifact index (Items 1–7)\n\n"
            + "- `BATCH05_ITEM7_FINAL_INSTITUTIONAL_FREEZE.json` (Item 7 master)\n"
            + "- `BATCH05_REMAINING_BLOCKERS_MATRIX.json` (Item 7 blockers)\n"
            + "\n---\n\nهذه المرحلة = بناء spine",
        )
        # Update section 12 header to include item 7 artifacts in list
        text = text.replace(
            "- `BATCH05_POST_STRANGLER_INSTITUTIONAL_FREEZE_REPORT.md`",
            "- `BATCH05_POST_STRANGLER_INSTITUTIONAL_FREEZE_REPORT.md`\n"
            "- `BATCH05_ITEM7_FINAL_INSTITUTIONAL_FREEZE.json` (Item 7)\n"
            "- `BATCH05_REMAINING_BLOCKERS_MATRIX.json` (Item 7)",
        )
    text = text.replace(
        "**Phase:** **BUILD_PHASE OPEN** — Items 1–6 institutional closure (local)",
        "**Phase:** **BUILD_PHASE OPEN** — Items 1–7 final institutional freeze (local)",
    )
    PROGRESS_MD.write_text(text, encoding="utf-8")


def main() -> None:
    commit = git_commit()
    pa_sweep = load_json(ROOT / ITEM_ARTIFACTS["item_1_pa_sweep"])
    entitlement = load_json(ROOT / ITEM_ARTIFACTS["item_3_entitlement"])
    disposition = load_json(ROOT / ITEM_ARTIFACTS["item_2_reused_link"])

    for path in (ACCEPTANCE, RTM, PENTAGONAL):
        if not path.is_file():
            raise SystemExit(f"Missing required artifact: {path}")

    acceptance = stamp_doc(load_json(ACCEPTANCE), kind="acceptance")
    rtm = stamp_doc(load_json(RTM), kind="rtm")
    pentagonal = stamp_doc(load_json(PENTAGONAL), kind="pentagonal")

    acceptance["production_aligned"] = False
    acceptance["batch05_independent"] = 0
    acceptance["progress_826"] = 179
    rtm["batch05_independent"] = 0
    rtm["progress_826"] = 179
    pentagonal["batch05_independent"] = 0
    pentagonal["progress_826"] = 179
    pentagonal["production_aligned_count"] = 0
    pentagonal["pa_elevated_count"] = 0

    ACCEPTANCE.write_text(json.dumps(acceptance, indent=2) + "\n", encoding="utf-8")
    RTM.write_text(json.dumps(rtm, indent=2) + "\n", encoding="utf-8")
    PENTAGONAL.write_text(json.dumps(pentagonal, indent=2) + "\n", encoding="utf-8")

    matrix = build_readiness_matrix(pa_sweep, entitlement, disposition)
    OUT_MATRIX_JSON.write_text(json.dumps(matrix, indent=2) + "\n", encoding="utf-8")
    OUT_MATRIX_MD.write_text(render_matrix_md(matrix), encoding="utf-8")

    freeze = {
        "generated_at": datetime.now(UTC).isoformat(),
        "git_commit": commit,
        "git_branch": git_branch(),
        "pr": 366,
        "sequence_item": 7,
        "title": "Batch05 final institutional freeze — Items 1–7 complete (local only)",
        "build_phase": "OPEN",
        "batch05_independent": 0,
        "progress_826": 179,
        "production_aligned_count": 0,
        "pa_elevated_count": 0,
        "not_claimed": [
            "LOCAL_GOVERNANCE_COMPLETE",
            "LIVE_READY",
            "batch05_complete",
            "OPERATION",
        ],
        "phase_statement_ar": ARABIC_PHASE,
        "12207_lifecycle": matrix["12207_lifecycle"],
        "items_1_6_snapshot": {
            "item_1": {
                "artifact": ITEM_ARTIFACTS["item_1_pa_sweep"],
                "strangler_swept": pa_sweep["summary"]["strangler_count"],
                "domain_all_pass": pa_sweep["summary"]["domain_all_pass_count"],
                "pa_elevated": 0,
            },
            "item_2": {
                "artifact": ITEM_ARTIFACTS["item_2_reused_link"],
                "closed": disposition["summary"]["closed_count"],
                "tolerate": disposition["summary"]["tolerate_count"],
            },
            "item_3": {
                "artifact": ITEM_ARTIFACTS["item_3_entitlement"],
                "strangler_proofs": entitlement.get("strangler_test_case_count"),
                "all_verified": entitlement.get("all_verified"),
            },
            "item_4": {"artifact": ITEM_ARTIFACTS["item_4_heroes"], "status": "FINAL_FREEZE_LOCAL"},
            "item_5": {"artifact": ITEM_ARTIFACTS["item_5_gate_zero"], "status": "AWAITING_DEPLOY"},
            "item_6": {
                "artifact": ITEM_ARTIFACTS["item_6_sre_prr"],
                "prr_status": "SECOND_REVIEW_READY_LOCAL",
            },
        },
        "stamped_artifacts": {
            "acceptance": str(ACCEPTANCE.relative_to(ROOT)),
            "rtm": str(RTM.relative_to(ROOT)),
            "pentagonal": str(PENTAGONAL.relative_to(ROOT)),
            "progress_report": str(PROGRESS_MD.relative_to(ROOT)),
        },
        "blockers_matrix": str(OUT_MATRIX_JSON.relative_to(ROOT)),
        "hard_blockers": HARD_BLOCKERS,
        "elevation_log": [],
    }
    OUT_FREEZE.write_text(json.dumps(freeze, indent=2) + "\n", encoding="utf-8")
    update_progress_report(commit)

    assert freeze["pa_elevated_count"] == 0
    assert freeze["production_aligned_count"] == 0
    assert matrix["summary"]["strangler_pa_eligible_now"] == 0
    print(f"Item 7 freeze @ {commit[:12]} — stamped acceptance/rtm/pentagonal; matrix written")


if __name__ == "__main__":
    main()
