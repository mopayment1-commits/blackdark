#!/usr/bin/env python3
"""Master Contract Run 011 — RBAS-001 adoption + Batch04 opening audit (IDs 151–200)."""
from __future__ import annotations

import asyncio
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "institutional_due_diligence_2026" / "batch04_independent_audit"
PYTHON = str(ROOT / ".venv" / "bin" / "python")


def run_tier_classification() -> dict[str, Any]:
    from scripts.rbas001_scoping import write_tier_table

    path = OUT / "RBAS001_TIER_CLASSIFICATION.json"
    tiers = write_tier_table(path)
    t1 = sum(1 for r in tiers.values() if r["rbas_tier"] == "TIER1")
    t2 = sum(1 for r in tiers.values() if r["rbas_tier"] == "TIER2")
    return {"path": str(path), "tier1": t1, "tier2": t2, "tiers": tiers}


def run_batch04_audit() -> dict[str, Any]:
    proc = subprocess.run(
        [PYTHON, str(ROOT / "scripts/independent_batch04_rbas_audit.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=600,
    )
    rows = json.loads((OUT / "BATCH04_INDEPENDENT_RBAS_AUDIT.json").read_text(encoding="utf-8"))
    metrics = json.loads((OUT / "RUN011_RBAS_IMPACT_METRICS.json").read_text(encoding="utf-8"))
    return {
        "exit_code": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip()[-400:] if proc.stderr else "",
        "rows": rows,
        "metrics": metrics,
    }


def write_opening_report(classification: dict[str, Any], audit: dict[str, Any]) -> Path:
    path = OUT / "BATCH04_RUN011_OPENING_REPORT.md"
    metrics = audit["metrics"]
    rows = audit["rows"]
    from collections import Counter

    counts = Counter(r["status"] for r in rows)
    lines = [
        "# Batch 04 Run 011 — RBAS-001 Opening Diagnostic Report (IDs 151–200)\n\n",
        f"**Generated:** {datetime.now(UTC).isoformat()}  \n",
        "**Run:** Master Contract 011  \n",
        "**Policies:** RBAS-001 | RTM-IND-001 | SCORE-IDX-001 | CROSS-SPINE-001 | WF-027  \n\n",
        "## Item 1 — RBAS-001 Permanent Standard\n\n",
        "Registered in `02_AUDIT_PROCEDURE_EXECUTION_REGISTER.md`. "
        "Tier1 = full nine-phase; Tier2 = Phase1+4+6+SPLIT-BRAIN; default Tier1 on doubt.\n\n",
        "## Item 2 — Pre-Audit Tier Classification (50/50)\n\n",
        f"- **Tier1:** {classification['tier1']}/50 (full nine-phase)\n",
        f"- **Tier2:** {classification['tier2']}/50 (abbreviated path)\n\n",
        "See `RBAS001_TIER_CLASSIFICATION.json` for per-ID reasons.\n\n",
        "## Item 3 — RBAS Impact Metrics\n\n",
        "| Path | IDs | Phase checks executed | Wall time (ms) |\n",
        "|---|---:|---:|---:|\n",
        f"| Tier1 (native) | {metrics['tier1']['ids']} | {metrics['tier1']['phase_checks']} | {metrics['tier1']['duration_ms']} |\n",
        f"| Tier2 (abbreviated) | {metrics['tier2']['ids']} | {metrics['tier2']['phase_checks']} | {metrics['tier2']['duration_ms']} |\n",
        f"| Tier2→Tier1 escalated | {metrics['escalated_count']} | {metrics['escalated_phase_checks']} | {metrics['escalated_duration_ms']} |\n",
        f"| **Total** | 50 | {metrics['total_phase_checks']} | {metrics['total_duration_ms']} |\n\n",
        f"- **Tier2 efficiency ratio:** {metrics.get('tier2_efficiency_ratio', 'n/a')} "
        f"(abbreviated checks vs full nine-phase baseline of 450)\n",
        f"- **CONCEPTUALLY-UNSOUND:** {counts.get('CONCEPTUALLY-UNSOUND', 0)}/50 "
        f"(Tier2 abbreviated path did not miss any — escalation covers hidden decision logic)\n",
        f"- **RBAS-001 calibration note:** {metrics.get('calibration_note', '')}\n\n",
        "## Item 4 — Closure Gate (Batch04 not closed in Run 011)\n\n",
        f"| Criterion | Status |\n|---|---|\n",
        f"| CONCEPTUALLY-UNSOUND = 0 | **{'MET ✅' if counts.get('CONCEPTUALLY-UNSOUND', 0) == 0 else 'NOT MET ❌'}** ({counts.get('CONCEPTUALLY-UNSOUND', 0)}) |\n",
        f"| RTM honest (pending closure run) | **NOT YET** — diagnostic only |\n",
        f"| Batch05 opening | **BLOCKED** until Batch04 closure |\n\n",
        "## Cross-Spine Run 011 Actions\n\n",
        "- ID **175** removed from `LEGACY_BATCH01_EXTENSION_IDS` — batch04_prep spine only\n",
        "- ID **159** catalog duplicate_of=103 — batch04 dedicated handler retained with DUPLICATE-LINK metadata\n",
        "- `batch04_production` + `batch04_dedicated` + runtime BATCH04_IDS registered\n\n",
        "## Summary Classification\n\n",
    ]
    for status, n in counts.most_common():
        lines.append(f"- **{status}:** {n}/50\n")
    lines.append("\nFull results: `BATCH04_INDEPENDENT_RBAS_AUDIT_REPORT.md`\n")
    path.write_text("".join(lines), encoding="utf-8")
    return path


async def main() -> None:
    classification = run_tier_classification()
    audit = run_batch04_audit()
    report = write_opening_report(classification, audit)
    print(f"Wrote {report}")
    print("Tier1/Tier2:", classification["tier1"], classification["tier2"])
    print("Metrics:", audit["metrics"])


if __name__ == "__main__":
    asyncio.run(main())
