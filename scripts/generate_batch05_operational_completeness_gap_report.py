#!/usr/bin/env python3
"""Batch05 operational completeness gap report — per-ID honest assessment.

No cosmetic closure. No counter inflation. Live blockers require live evidence.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cap646.batch05_strangler_spine import STRANGLER_IMPLEMENTED_IDS  # noqa: E402

RESIDUAL_7 = frozenset({212, 206, 214, 226, 228, 232, 245})
TOLERATE_CEILING = "2026-12-31"
ARABIC_PHASE = (
    "هذه المرحلة = بناء spine + قبول مسبق + اختبارات محلية فقط. "
    "لا إعلان اكتمال حوكمة · لا Batch05 complete · لا جاهزية حية 100%."
)

CRITERIA = [
    "iso_25010_local",
    "live_e2e",
    "entitlement_live",
    "performance_live",
    "six_heroes",
    "12207_validation_transition",
    "sre_prr_signoff",
    "residual_disposition",
]

OUT_JSON = ROOT / "docs/BATCH05_OPERATIONAL_COMPLETENESS_GAP_REPORT.json"
OUT_MD = ROOT / "docs/BATCH05_OPERATIONAL_COMPLETENESS_GAP_REPORT.md"
GATE_LIVE = ROOT / "docs/BATCH05_GATE_ZERO_LIVE_EXECUTION.json"
RESIDUAL_DOC = ROOT / "docs/BATCH05_RESIDUAL_7_INSTITUTIONAL_DISPOSITION.json"


def git_commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def live_blocked(gate: dict[str, Any]) -> bool:
    return gate.get("status") != "PASS"


def criteria_for_id(cid: int, gate: dict[str, Any], residual_by_id: dict[int, dict]) -> dict[str, str]:
    live_fail = live_blocked(gate)
    is_strangler = cid in STRANGLER_IMPLEMENTED_IDS
    is_residual = cid in RESIDUAL_7
    res = residual_by_id.get(cid, {})

    iso = "PROVEN_LOCAL" if (is_strangler or is_residual) else "N/A_MANIFEST_ONLY"
    if cid == 212:
        iso = "PROVEN_LOCAL_DUPLICATE_DELEGATION"

    heroes = "N/A_NOT_IN_HERO_INPUTS"
    if cid == 226:
        heroes = "PROVEN_VIA_CANONICAL_69_ONLY"

    residual_status = "N/A"
    if is_residual:
        decision = res.get("institutional_decision", "")
        if decision == "CLOSED_TOLERATE_DUAL_PATH":
            residual_status = f"CLOSED_TOLERATE_CEILING_{TOLERATE_CEILING}"
        else:
            residual_status = decision or "UNKNOWN"

    def live_field(local_ok: str) -> str:
        if live_fail:
            return "BLOCKED_LIVE_DEPLOY_404"
        return local_ok.replace("PROVEN_LOCAL", "PROVEN_LIVE") if local_ok.startswith("PROVEN") else "NOT_RUN"

    return {
        "iso_25010_local": iso,
        "live_e2e": live_field("PROVEN_LOCAL" if is_strangler or is_residual else "NOT_APPLICABLE"),
        "entitlement_live": "PROVEN_LOCAL" if is_strangler or is_residual else "NOT_RUN",
        "entitlement_live_note": "Live blocked — local gateway proof exists" if live_fail else "",
        "performance_live": "PROVEN_LOCAL_CAPS" if is_strangler else ("LOCAL_ONLY" if is_residual else "NOT_RUN"),
        "six_heroes": heroes,
        "12207_validation_transition": "NOT_EXECUTED",
        "sre_prr_signoff": "NOT_EXECUTED",
        "residual_disposition": residual_status,
    }


def operational_complete(criteria: dict[str, str]) -> bool:
    required_live = ["live_e2e", "entitlement_live", "performance_live", "12207_validation_transition", "sre_prr_signoff"]
    for key in required_live:
        val = criteria[key]
        if val in ("BLOCKED_LIVE_DEPLOY_404", "NOT_EXECUTED", "NOT_RUN"):
            return False
    if criteria.get("residual_disposition", "").startswith("CLOSED_TOLERATE"):
        return False
    return True


def build_rows(gate: dict[str, Any], residual_doc: dict[str, Any]) -> list[dict[str, Any]]:
    residual_by_id = {r["capability_id"]: r for r in residual_doc["rows"]}
    acceptance = load_json(ROOT / "docs/BATCH05_ACCEPTANCE_201_250.json")
    rows: list[dict[str, Any]] = []

    for acc in acceptance["rows"]:
        cid = acc["capability_id"]
        crit = criteria_for_id(cid, gate, residual_by_id)
        complete = operational_complete(crit)
        gaps: list[dict[str, str]] = []
        if crit["live_e2e"] == "BLOCKED_LIVE_DEPLOY_404":
            gaps.append({"severity": "P0", "gap": "LIVE_E2E", "closure": "Railway redeploy + re-run Gate Zero"})
        if crit["12207_validation_transition"] == "NOT_EXECUTED":
            gaps.append({"severity": "P0", "gap": "12207_VALIDATION_TRANSITION", "closure": "Owner sign-off after live evidence"})
        if crit["sre_prr_signoff"] == "NOT_EXECUTED":
            gaps.append({"severity": "P0", "gap": "SRE_PRR_SIGNOFF", "closure": "Second-review committee with live probes"})
        if crit["residual_disposition"].startswith("CLOSED_TOLERATE"):
            gaps.append(
                {
                    "severity": "P1",
                    "gap": "DUAL_PATH_TOLERATE",
                    "closure": f"Resolve by {TOLERATE_CEILING} or Gate Zero dual-path proof",
                }
            )

        rows.append(
            {
                "capability_id": cid,
                "capability_name": acc["capability_name"],
                "closure_status": acc.get("status"),
                "operational_complete": complete,
                "committee_ready": False,
                "criteria": crit,
                "gaps": gaps,
                "pa_elevated": False,
                "production_aligned": False,
            }
        )
    return rows


def render_md(doc: dict[str, Any]) -> str:
    lines = [
        "# Batch05 Operational Completeness Gap Report",
        "",
        f"**Generated:** {doc['generated_at']} | **Commit:** `{doc['git_commit'][:12]}`",
        f"**Live Gate Zero:** `{doc['gate_zero_live']['status']}` @ {doc['gate_zero_live']['production_url']}",
        "",
        "## Executive truth (no cosmetic closure)",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| IDs operationally complete | **{doc['summary']['operational_complete_count']}/50** |",
        f"| Committee-ready IDs | **{doc['summary']['committee_ready_count']}** |",
        f"| `pa_elevated_count` | **{doc['pa_elevated_count']}** |",
        f"| `LIVE_READY` claimed | **{doc['live_ready']}** |",
        "",
        "## Universal P0 blockers (live)",
        "",
    ]
    for b in doc["universal_blockers"]:
        lines.append(f"- **{b['id']}** ({b['severity']}): {b['status']} — {b['closure_plan']}")
    lines.extend(["", "## Residual 7 operational status", ""])
    for r in doc["residual_7_operational"]:
        lines.append(
            f"- **#{r['id']}** {r['decision']}: local={r['local_build']} live={r['live_operational']}"
        )
    lines.extend(["", ARABIC_PHASE, ""])
    return "\n".join(lines)


def main() -> None:
    if not GATE_LIVE.is_file():
        raise SystemExit(f"Run scripts/execute_batch05_gate_zero_live.py first — missing {GATE_LIVE}")
    if not RESIDUAL_DOC.is_file():
        raise SystemExit(f"Missing {RESIDUAL_DOC}")

    gate = load_json(GATE_LIVE)
    residual = load_json(RESIDUAL_DOC)
    rows = build_rows(gate, residual)

    op_complete = sum(1 for r in rows if r["operational_complete"])
    assert op_complete == 0, "operational_complete must be 0 until live deploy — no inflation"

    doc = {
        "generated_at": datetime.now(UTC).isoformat(),
        "git_commit": git_commit(),
        "scope": "Batch05 operational completeness — formal review committee intake",
        "build_phase": "OPEN",
        "batch05_independent": 0,
        "progress_826": 179,
        "production_aligned_count": 0,
        "pa_elevated_count": 0,
        "live_ready": False,
        "local_governance_complete": False,
        "committee_submittable": False,
        "phase_statement_ar": ARABIC_PHASE,
        "gate_zero_live": {
            "artifact": str(GATE_LIVE.relative_to(ROOT)),
            "status": gate["status"],
            "production_url": gate["production_url"],
            "diagnosis": gate.get("diagnosis"),
        },
        "residual_7_institutional": {
            "artifact": str(RESIDUAL_DOC.relative_to(ROOT)),
            "deferred": residual["summary"]["deferred"],
            "all_decided": True,
        },
        "universal_blockers": [
            {
                "id": "RAILWAY_DEPLOY",
                "severity": "P0",
                "status": "FAILED",
                "evidence": gate["summary"],
                "closure_plan": "Owner redeploy blackdark-production; re-run execute_batch05_gate_zero_live.py",
            },
            {
                "id": "LIVE_E2E",
                "severity": "P0",
                "status": "BLOCKED",
                "closure_plan": "Gate Zero PASS required before any ID live_e2e=PROVEN_LIVE",
            },
            {
                "id": "12207_VALIDATION_TRANSITION",
                "severity": "P0",
                "status": "NOT_EXECUTED",
                "closure_plan": "Owner validation + transition sign-off with live probe artifacts",
            },
            {
                "id": "SRE_PRR_SIGNOFF",
                "severity": "P0",
                "status": "NOT_EXECUTED",
                "closure_plan": "Committee second review after live Gate Zero green",
            },
        ],
        "mandatory_criteria": CRITERIA,
        "summary": {
            "manifest_ids": 50,
            "operational_complete_count": op_complete,
            "committee_ready_count": 0,
            "local_build_proven_stranglers": len(STRANGLER_IMPLEMENTED_IDS),
            "residual_7_decided": 7,
            "p0_gaps_per_id_minimum": 3,
        },
        "residual_7_operational": [
            {
                "id": r["capability_id"],
                "decision": r["institutional_decision"],
                "local_build": "COMPLETE",
                "live_operational": "BLOCKED",
                "ceiling": r.get("tolerate_ceiling"),
            }
            for r in residual["rows"]
        ],
        "rows": rows,
        "elevation_policy": "PA/independent/production_aligned increment only when all 8 mandatory criteria PROVEN_LIVE per ID",
    }
    OUT_JSON.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    OUT_MD.write_text(render_md(doc), encoding="utf-8")
    print(f"Wrote {OUT_JSON.name} — operational_complete={op_complete}/50 committee_ready=0")


if __name__ == "__main__":
    main()
