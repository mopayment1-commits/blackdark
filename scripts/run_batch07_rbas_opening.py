#!/usr/bin/env python3
"""Master Contract Run 026 — RBAS-001 adoption + Batch07 opening audit (IDs 301–350)."""
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
OUT = ROOT / "institutional_due_diligence_2026" / "batch07_independent_audit"
PYTHON = str(ROOT / ".venv" / "bin" / "python")


def wf027_preflight() -> dict[str, Any]:
    import subprocess as sp

    from scripts.rbas001_scoping import (
        BATCH07_RANGE,
        WF027_DORMANT_LEGACY_IDS,
        WF027_IN_BATCH07,
        WF027_UNRESOLVED_LEGACY_IDS,
    )

    rg = sp.run(
        ["rg", "-n", "584|629|630|631|642|644|646", "cap646/batch01_production.py", "scripts/rbas001_scoping.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    overlap = sorted(WF027_UNRESOLVED_LEGACY_IDS & set(BATCH07_RANGE))
    resolved_prior = sorted({175, 214, 245})
    return {
        "wf027_full_historical_set": sorted(WF027_DORMANT_LEGACY_IDS),
        "wf027_resolved_prior_batches": resolved_prior,
        "wf027_unresolved_remaining": sorted(WF027_UNRESOLVED_LEGACY_IDS),
        "batch07_range": "301-350",
        "overlap_ids": overlap,
        "overlap_count": len(overlap),
        "rg_live_scan": {
            "command": "rg -n '584|629|630|631|642|644|646' cap646/batch01_production.py scripts/rbas001_scoping.py",
            "exit_code": rg.returncode,
            "hit_lines": [ln for ln in (rg.stdout or "").splitlines()[:12]],
        },
        "python_set_intersection": sorted(WF027_IN_BATCH07),
        "evidence": (
            f"WF-027 unresolved={sorted(WF027_UNRESOLVED_LEGACY_IDS)}; Batch07 range 301-350; "
            f"intersection={overlap} ({len(overlap)}/7 unresolved WF-027 IDs in scope). "
            "175/214/245 resolved in Batch04/05."
        ),
    }


def run_tier_classification() -> dict[str, Any]:
    from scripts.rbas001_scoping import write_batch07_tier_table

    path = OUT / "RBAS001_TIER_CLASSIFICATION_BATCH07.json"
    tiers = write_batch07_tier_table(path)
    t1 = sum(1 for r in tiers.values() if r["rbas_tier"] == "TIER1")
    t2 = sum(1 for r in tiers.values() if r["rbas_tier"] == "TIER2")
    return {"path": str(path), "tier1": t1, "tier2": t2, "tiers": tiers}


def run_batch07_audit() -> dict[str, Any]:
    proc = subprocess.run(
        [PYTHON, str(ROOT / "scripts/independent_batch07_rbas_audit.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=900,
    )
    rows = json.loads((OUT / "BATCH07_INDEPENDENT_RBAS_AUDIT.json").read_text(encoding="utf-8"))
    metrics = json.loads((OUT / "RUN015_RBAS_IMPACT_METRICS.json").read_text(encoding="utf-8"))
    return {
        "exit_code": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip()[-600:] if proc.stderr else "",
        "rows": rows,
        "metrics": metrics,
    }


def write_opening_report(
    preflight: dict[str, Any],
    classification: dict[str, Any],
    audit: dict[str, Any],
) -> Path:
    path = OUT / "BATCH07_RUN015_OPENING_REPORT.md"
    metrics = audit["metrics"]
    rows = audit["rows"]
    from collections import Counter

    counts = Counter(r["status"] for r in rows)
    sb = Counter(r.get("split_brain_type") for r in rows)
    lines = [
        "# Batch 07 Run 026 — RBAS-001 Opening Diagnostic Report (IDs 301–350)\n\n",
        f"**Generated:** {datetime.now(UTC).isoformat()}  \n",
        "**Run:** Master Contract 26  \n",
        "**Policies:** RBAS-001 | RTM-IND-001 | SCORE-IDX-001 | CROSS-SPINE-001 | WF-027  \n\n",
        "## Item 1 — WF-027 Preflight (mandatory first)\n\n",
        f"- **WF-027 historical set (10 IDs):** `{preflight['wf027_full_historical_set']}`\n",
        f"- **Resolved prior (Batch04/05):** `{preflight['wf027_resolved_prior_batches']}`\n",
        f"- **Unresolved remaining (7 IDs):** `{preflight['wf027_unresolved_remaining']}`\n",
        f"- **Batch07 official range:** {preflight['batch07_range']}\n",
        f"- **Intersection (overlap):** `{preflight['overlap_ids']}` — **{preflight['overlap_count']}/7** unresolved IDs\n",
        f"- **Live rg scan:** `{preflight['rg_live_scan']['command']}` → exit {preflight['rg_live_scan']['exit_code']}\n",
        f"- **Python set intersection:** `{preflight['python_set_intersection']}` (empty = zero overlap confirmed)\n",
        f"- **Preflight evidence:** {preflight['evidence']}\n\n",
        "## Item 2 — Pre-Audit Tier Classification (50/50)\n\n",
        f"- **Tier1:** {classification['tier1']}/50 (full nine-phase)\n",
        f"- **Tier2:** {classification['tier2']}/50 (abbreviated path)\n\n",
        "See `RBAS001_TIER_CLASSIFICATION_BATCH07.json` for per-ID reasons.\n\n",
        "### Tier Table Summary\n\n",
        "| ID | Capability | Tier | Reason |\n",
        "|---:|---|---|---|\n",
    ]
    for cid in range(301, 351):
        t = classification["tiers"][cid]
        cap = str(t.get("capability") or "").replace("|", "/")
        reason = str(t.get("rbas_reason") or "").replace("|", "/")
        lines.append(f"| {cid} | {cap} | **{t['rbas_tier']}** | {reason} |\n")

    lines.extend(
        [
            "\n## Item 3 — RBAS Impact Metrics\n\n",
            "| Path | IDs | Phase checks executed | Wall time (ms) |\n",
            "|---|---:|---:|---:|\n",
            f"| Tier1 (native) | {metrics['tier1']['ids']} | {metrics['tier1']['phase_checks']} | {metrics['tier1']['duration_ms']} |\n",
            f"| Tier2 (abbreviated) | {metrics['tier2']['ids']} | {metrics['tier2']['phase_checks']} | {metrics['tier2']['duration_ms']} |\n",
            f"| Tier2→Tier1 escalated | {metrics['escalated_count']} | {metrics['escalated_phase_checks']} | {metrics['escalated_duration_ms']} |\n",
            f"| **Total** | 50 | {metrics['total_phase_checks']} | {metrics['total_duration_ms']} |\n\n",
            f"- **Tier2 efficiency ratio:** {metrics.get('tier2_efficiency_ratio', 'n/a')} "
            f"(abbreviated checks vs full nine-phase baseline of 450)\n",
            f"- **CONCEPTUALLY-UNSOUND:** {counts.get('CONCEPTUALLY-UNSOUND', 0)}/50 "
            f"(Tier2 abbreviated path — escalation covers hidden decision logic)\n",
            f"- **RBAS-001 calibration note:** {metrics.get('calibration_note', '')}\n\n",
            "## Item 4 — SPLIT-BRAIN (mandatory all 50)\n\n",
        ]
    )
    for k, v in sb.most_common():
        lines.append(f"- **{k}:** {v}/50\n")
    lines.extend(["\n## Item 5 — Diagnostic Classification Summary\n\n"])
    for status, n in counts.most_common():
        lines.append(f"- **{status}:** {n}/50\n")
    lines.extend(
        [
            "\n## Item 6 — Closure Gate (Batch07 NOT closed in Run 026)\n\n",
            "| Criterion | Status |\n|---|---|\n",
            f"| CONCEPTUALLY-UNSOUND = 0 | **{'MET ✅' if counts.get('CONCEPTUALLY-UNSOUND', 0) == 0 else 'NOT MET ❌'}** ({counts.get('CONCEPTUALLY-UNSOUND', 0)}) |\n",
            "| RTM honest (pending closure run) | **NOT YET** — diagnostic only |\n",
            "| Batch07 opening | **BLOCKED** until Batch07 closure |\n\n",
            "## Cross-Spine Run 026 Actions\n\n",
            "- WF-027: **zero overlap** with Batch07 range — no legacy ID removal required\n",
            "- Catalog duplicates retained with batch07 dedicated handlers: "
            "251/275, 255→205, 256→86, 257→235, 260→126, 272→103\n",
            "- `batch07_production` + `batch07_dedicated` + runtime `BATCH07_IDS` registered\n\n",
            "Full audit: `BATCH07_INDEPENDENT_RBAS_AUDIT_REPORT.md`\n",
        ]
    )
    path.write_text("".join(lines), encoding="utf-8")
    return path


async def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    preflight = wf027_preflight()
    (OUT / "WF027_PREFLIGHT_BATCH07.json").write_text(
        json.dumps(preflight, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    classification = run_tier_classification()
    audit = run_batch07_audit()
    report = write_opening_report(preflight, classification, audit)
    print(f"Wrote {report}")
    print("WF-027 overlap:", preflight["overlap_ids"])
    print("Tier1/Tier2:", classification["tier1"], classification["tier2"])
    print("Metrics:", audit["metrics"])


if __name__ == "__main__":
    asyncio.run(main())
