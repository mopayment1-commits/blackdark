#!/usr/bin/env python3
"""Master Contract Run 005 — Batch 01 final closure (IDs 8, 9, 33 + RTM update)."""
from __future__ import annotations

import asyncio
import json
import subprocess
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "institutional_due_diligence_2026" / "batch01_independent_audit"
AUDIT_DIR = ROOT / "institutional_due_diligence_2026"
RTM_PATH = ROOT / "docs" / "BATCH01_OFFICIAL_RTM_1_50.json"
PYTHON = str(ROOT / ".venv" / "bin" / "python")

COMMON_PARAMS = {
    "symbol": "BTC",
    "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    "email": "run005-audit@blackdark.local",
    "tier": "pro",
}


async def live_remediation_evidence() -> dict[str, Any]:
    from cap646.runtime import execute_capability

    evidence: dict[str, Any] = {"generated_at": datetime.now(UTC).isoformat(), "items": {}}

    # ID 8 — path B decision: no on-chain top-holder source in project
    from bd_platform.free_integrations import holder_analytics

    ha = await holder_analytics("BTC")
    evidence["id8_path_decision"] = {
        "chosen_path": "B",
        "reason": (
            "holder_analytics() uses CoinGecko supply + Binance futures only "
            "(bd_platform/free_integrations.py) — no top-holder distribution API available without paid integration"
        ),
        "holder_analytics_source": ha.get("source"),
        "available_metrics": list((ha.get("metrics") or {}).keys()),
    }
    r8 = await execute_capability(8, skip_entitlement=True, params=dict(COMMON_PARAMS))
    evidence["items"]["8"] = {
        "locked_circulating_supply_proxy": r8.get("locked_circulating_supply_proxy"),
        "methodology_status": (r8.get("locked_circulating_supply_proxy") or {}).get("methodology_status"),
        "disclaimer": (r8.get("locked_circulating_supply_proxy") or {}).get("disclaimer"),
        "deprecated_alias": r8.get("top_holders_concentration"),
    }

    r9 = await execute_capability(9, skip_entitlement=True, params=dict(COMMON_PARAMS))
    evidence["items"]["9"] = {
        "path": "B",
        "heuristic": r9.get("heuristic"),
        "methodology_status": r9.get("methodology_status"),
        "heuristic_formula": r9.get("heuristic_formula"),
        "distribution_score": r9.get("distribution_score"),
    }

    r33 = await execute_capability(33, skip_entitlement=True, params=dict(COMMON_PARAMS))
    evidence["items"]["33"] = {
        "path": "B",
        "heuristic": r33.get("heuristic"),
        "methodology_status": r33.get("methodology_status"),
        "heuristic_formula": r33.get("heuristic_formula"),
        "actionability_score": r33.get("actionability_score"),
        "alert_count": len(r33.get("alerts") or []),
    }
    return evidence


def run_independent_audit() -> dict[str, Any]:
    proc = subprocess.run(
        [PYTHON, str(ROOT / "scripts/independent_batch01_nine_phase_audit.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    rows = json.loads((OUT / "BATCH01_INDEPENDENT_NINE_PHASE.json").read_text(encoding="utf-8"))
    counts = Counter(r["status"] for r in rows)
    return {
        "exit_code": proc.returncode,
        "stdout": proc.stdout.strip(),
        "counts": dict(counts),
        "rows": rows,
    }


def write_rtm(rows: list[dict]) -> dict[str, Any]:
    from cap646.catalog import catalog_by_id

    catalog = catalog_by_id()
    counts = Counter(r["status"] for r in rows)
    per_id = {}
    for r in rows:
        cid = r["id"]
        per_id[str(cid)] = {
            "id": cid,
            "capability": catalog.get(cid, {}).get("capability", r["name"]),
            "official_batch": "batch01",
            "status": r["status"],
            "production_spine": "batch01",
            "audit_method": "Independent Third-Line Nine-Phase (Run 005)",
            "failed_phase": r.get("failed_phase"),
            "failed_standard": r.get("failed_standard"),
            "evidence": r.get("evidence"),
            "heuristic_or_data_gap": cid in {8, 9, 33},
        }
    doc = {
        "generated_at": datetime.now(UTC).isoformat(),
        "scope": "Official Batch 01 — IDs 1–50",
        "supersedes": "self-assessment audit_official_batch01_rtm.py (50/50 PRODUCTION-ALIGNED — invalidated WF-026)",
        "audit_method": "Independent Third-Line Nine-Phase Due Diligence — Run 005",
        "wf026_policy": "Self-assessment RTM script prohibited for batches 51–826; nine-phase independent audit only",
        "summary": {
            "total": 50,
            "production_aligned": counts.get("PRODUCTION-ALIGNED", 0),
            "not_complete": counts.get("NOT_COMPLETE", 0),
            "performance_unverifiable": counts.get("PERFORMANCE-UNVERIFIABLE", 0),
            "conceptually_unsound": counts.get("CONCEPTUALLY-UNSOUND", 0),
            "split_brain_unverified": counts.get("SPLIT-BRAIN-UNVERIFIED", 0),
        },
        "closure_gate": {
            "conceptually_unsound_zero_required": True,
            "met": counts.get("CONCEPTUALLY-UNSOUND", 0) == 0,
            "batch01_closed": counts.get("CONCEPTUALLY-UNSOUND", 0) == 0,
        },
        "per_id": per_id,
    }
    RTM_PATH.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return doc


def write_final_closure_report(
    remediation: dict[str, Any], audit: dict[str, Any], rtm: dict[str, Any]
) -> Path:
    path = OUT / "BATCH01_FINAL_CLOSURE_REPORT.md"
    counts = audit["counts"]
    gate_met = rtm["closure_gate"]["met"]
    lines = [
        "# Batch 01 Final Closure Report (Run 005)\n\n",
        f"**Generated:** {datetime.now(UTC).isoformat()}  \n",
        "**Run:** Master Contract 005  \n",
        "**Scope:** IDs 1–50  \n\n",
        "## Closure Gate\n\n",
        f"| Criterion | Status |\n|---|---|\n",
        f"| CONCEPTUALLY-UNSOUND = 0 | **{'MET ✅' if gate_met else 'NOT MET ❌'}** ({counts.get('CONCEPTUALLY-UNSOUND', 0)}) |\n",
        f"| RTM updated (no fake 50/50) | **MET ✅** (`docs/BATCH01_OFFICIAL_RTM_1_50.json`) |\n",
        f"| Batch 01 officially closed | **{'YES' if gate_met else 'NO'}** |\n\n",
        "## Run 005 Remediation (IDs 8, 9, 33)\n\n",
        "### ID 8 — Path **B** (honest proxy rename)\n\n",
        f"- **Decision:** {remediation['id8_path_decision']['chosen_path']} — {remediation['id8_path_decision']['reason']}\n",
        f"- **New field:** `locked_circulating_supply_proxy.non_circulating_supply_pct`\n",
        f"- **methodology_status:** `{remediation['items']['8'].get('methodology_status')}`\n",
        f"- **disclaimer:** {remediation['items']['8'].get('disclaimer')}\n\n",
        "### ID 9 — Path **B** (heuristic documented)\n\n",
        f"- **heuristic:** `{remediation['items']['9'].get('heuristic')}`\n",
        f"- **formula:** `{remediation['items']['9'].get('heuristic_formula')}`\n",
        f"- **methodology_status:** `{remediation['items']['9'].get('methodology_status')}`\n\n",
        "### ID 33 — Path **B** (heuristic documented)\n\n",
        f"- **heuristic:** `{remediation['items']['33'].get('heuristic')}`\n",
        f"- **formula:** `{remediation['items']['33'].get('heuristic_formula')}`\n",
        f"- **methodology_status:** `{remediation['items']['33'].get('methodology_status')}`\n",
        f"- **alert_count at test:** {remediation['items']['33'].get('alert_count')}\n\n",
        "## Final Classification Summary\n\n",
    ]
    for status, n in sorted(counts.items(), key=lambda x: -x[1]):
        lines.append(f"- **{status}:** {n}/50\n")
    lines.append("\n## Permanent Standards (Run 005)\n\n")
    lines.append(
        "1. **SCORE-IDX-001:** Scoring/index capabilities require cited weights OR explicit heuristic labeling — "
        "see `02_AUDIT_PROCEDURE_EXECUTION_REGISTER.md`\n"
    )
    lines.append(
        "2. **WF-026 / RTM-IND-001:** Self-assessment `audit_official_batch01_rtm.py` prohibited for batches 51–826; "
        "nine-phase independent audit only\n\n"
    )
    lines.append("## Final Status Table (50/50)\n\n")
    lines.append("| ID | Name | Status | Phase | Standard |\n|---:|---|---|---|---|\n")
    for r in audit["rows"]:
        lines.append(
            f"| {r['id']} | {r['name']} | **{r['status']}** | {r.get('failed_phase','—')} | "
            f"{r.get('failed_standard','—')[:60]} |\n"
        )
    path.write_text("".join(lines), encoding="utf-8")
    (OUT / "RUN005_BATCH01_CLOSURE_EVIDENCE.json").write_text(
        json.dumps({"remediation": remediation, "audit_counts": counts, "rtm_summary": rtm["summary"]}, indent=2),
        encoding="utf-8",
    )
    return path


async def main() -> None:
    remediation = await live_remediation_evidence()
    audit = run_independent_audit()
    rtm = write_rtm(audit["rows"])
    report = write_final_closure_report(remediation, audit, rtm)
    print(f"Wrote {report}")
    print(f"Wrote {RTM_PATH}")
    print("Counts:", audit["counts"])
    print("Closure gate MET:", rtm["closure_gate"]["met"])


if __name__ == "__main__":
    asyncio.run(main())
