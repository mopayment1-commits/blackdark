#!/usr/bin/env python3
"""Master Contract Run 007 — Batch 02 final closure (IDs 52/53/54/81 + cross-spine + RTM)."""
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
OUT = ROOT / "institutional_due_diligence_2026" / "batch02_independent_audit"
AUDIT_DIR = ROOT / "institutional_due_diligence_2026"
RTM_PATH = ROOT / "docs" / "BATCH02_OFFICIAL_RTM_51_100.json"
PYTHON = str(ROOT / ".venv" / "bin" / "python")

COMMON_PARAMS = {
    "symbol": "BTC",
    "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    "email": "run007-audit@blackdark.local",
    "tier": "pro",
}

PERFORMANCE_UNVERIFIABLE_IDS = {66, 69, 90, 97, 98}
CROSS_SPINE_FIXED_IDS = {55, 56, 59, 60}


def scan_batch_id_overlaps() -> dict[str, Any]:
    """CROSS-SPINE-001 — detect capability IDs in more than one BATCH0X_IDS routing list."""
    from cap646.batch01_production import BATCH01_IDS, LEGACY_BATCH01_EXTENSION_IDS, OFFICIAL_BATCH01_IDS
    from cap646.batch02_production import BATCH02_IDS, OFFICIAL_BATCH02_IDS
    from cap646.batch03_production import BATCH03_IDS

    lists = {
        "BATCH01_IDS": BATCH01_IDS,
        "BATCH02_IDS": BATCH02_IDS,
        "BATCH03_IDS": BATCH03_IDS,
    }
    id_to_lists: dict[int, list[str]] = {}
    for name, id_set in lists.items():
        for cid in id_set:
            id_to_lists.setdefault(cid, []).append(name)

    overlaps: list[dict[str, Any]] = []
    for cid, names in sorted(id_to_lists.items()):
        unique_routing = [n for n in names if n.endswith("_IDS")]
        if len(unique_routing) > 1:
            overlaps.append({"id": cid, "lists": unique_routing, "all_lists": names})

    batch01_batch02 = [
        o for o in overlaps if "BATCH01_IDS" in o["lists"] and "BATCH02_IDS" in o["lists"]
    ]
    batch01_batch03 = [
        o for o in overlaps if "BATCH01_IDS" in o["lists"] and "BATCH03_IDS" in o["lists"]
    ]
    batch02_batch03 = [
        o for o in overlaps if "BATCH02_IDS" in o["lists"] and "BATCH03_IDS" in o["lists"]
    ]

    return {
        "scan_at": datetime.now(UTC).isoformat(),
        "rule": "CROSS-SPINE-001",
        "total_overlapping_ids": len(overlaps),
        "overlaps": overlaps,
        "batch01_batch02": batch01_batch02,
        "batch01_batch03": batch01_batch03,
        "batch02_batch03": batch02_batch03,
        "literal_definitions": {
            "OFFICIAL_BATCH01_IDS": sorted(OFFICIAL_BATCH01_IDS),
            "LEGACY_BATCH01_EXTENSION_IDS": sorted(LEGACY_BATCH01_EXTENSION_IDS),
            "BATCH01_IDS": sorted(BATCH01_IDS),
            "BATCH02_IDS": sorted(BATCH02_IDS),
            "BATCH03_IDS": sorted(BATCH03_IDS),
            "runtime_check_order": ["BATCH01_IDS", "BATCH02_IDS", "BATCH03_IDS"],
        },
        "run007_batch02_cross_spine_fixed": sorted(CROSS_SPINE_FIXED_IDS),
        "remaining_findings_outside_batch02": [
            o for o in overlaps if o["id"] not in CROSS_SPINE_FIXED_IDS
        ],
    }


async def live_remediation_evidence() -> dict[str, Any]:
    from cap646.runtime import execute_capability

    evidence: dict[str, Any] = {
        "generated_at": datetime.now(UTC).isoformat(),
        "conceptual_unsound_remediation": {},
        "cross_spine": {},
        "performance_unverifiable": {},
    }

    for cid in (52, 53, 54, 81):
        result = await execute_capability(cid, skip_entitlement=True, params=dict(COMMON_PARAMS))
        payload_key = {
            52: "cross_asset_breadth",
            53: "btc_macro_coupling",
            54: "global_liquidity",
            81: "whale_accumulation_distribution",
        }[cid]
        inner = result.get(payload_key) or {}
        evidence["conceptual_unsound_remediation"][str(cid)] = {
            "path": "A",
            "production_spine": result.get("production_spine"),
            "surface": result.get("surface"),
            "success": result.get("success"),
            "payload_sample": {
                k: inner.get(k)
                for k in list(inner.keys())[:12]
                if k not in ("macro_context", "whale_alerts", "asset_details", "asset_volumes")
            },
        }

    for cid in sorted(CROSS_SPINE_FIXED_IDS):
        result = await execute_capability(cid, skip_entitlement=True, params=dict(COMMON_PARAMS))
        evidence["cross_spine"][str(cid)] = {
            "production_spine": result.get("production_spine"),
            "backend_module": result.get("backend_module"),
            "surface": result.get("surface"),
            "success": result.get("success"),
            "routing_correct": result.get("production_spine") == "batch02",
        }

    gips_path = ROOT / "data" / "decision_ledger.jsonl"
    gips_stats: dict[str, Any] = {"exists": gips_path.is_file(), "unique_decisions": 0, "simulated_only": True}
    if gips_path.is_file():
        seen: set[str] = set()
        with gips_path.open(encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                row = json.loads(line)
                did = str(row.get("decision_id") or "")
                if did:
                    seen.add(did)
                if str(row.get("evidence_class") or "") not in ("SIMULATED", "SHADOW_LIVE_FORWARD"):
                    gips_stats["simulated_only"] = False
        gips_stats["unique_decisions"] = len(seen)

    for cid in sorted(PERFORMANCE_UNVERIFIABLE_IDS):
        result = await execute_capability(cid, skip_entitlement=True, params=dict(COMMON_PARAMS))
        evidence["performance_unverifiable"][str(cid)] = {
            "status": "PERFORMANCE-UNVERIFIABLE",
            "reason": "GIPS: shadow-only decision ledger (Run 004 rationale preserved)",
            "ledger_unique_decisions": gips_stats["unique_decisions"],
            "ledger_simulated_only": gips_stats["simulated_only"],
            "runtime_success": result.get("success"),
        }

    evidence["cross_spine_scan"] = scan_batch_id_overlaps()
    return evidence


def run_independent_audit() -> dict[str, Any]:
    proc = subprocess.run(
        [PYTHON, str(ROOT / "scripts/independent_batch02_nine_phase_audit.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=300,
    )
    rows = json.loads((OUT / "BATCH02_INDEPENDENT_NINE_PHASE.json").read_text(encoding="utf-8"))
    counts = Counter(r["status"] for r in rows)
    return {
        "exit_code": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip()[-500:] if proc.stderr else "",
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
            "official_batch": "batch02",
            "status": r["status"],
            "production_spine": "batch02",
            "audit_method": "Independent Third-Line Nine-Phase (Run 007)",
            "failed_phase": r.get("failed_phase"),
            "failed_standard": r.get("failed_standard"),
            "evidence": r.get("evidence"),
            "remediated_run007": cid in {52, 53, 54, 81, 55, 56, 59, 60},
        }
    doc = {
        "generated_at": datetime.now(UTC).isoformat(),
        "scope": "Official Batch 02 — IDs 51–100",
        "supersedes": "self-assessment / Run 006 diagnostic (50/50 PRODUCTION-ALIGNED — invalidated WF-026)",
        "audit_method": "Independent Third-Line Nine-Phase Due Diligence — Run 007",
        "wf026_policy": "Self-assessment RTM prohibited; nine-phase independent audit only",
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
            "batch02_closed": counts.get("CONCEPTUALLY-UNSOUND", 0) == 0,
        },
        "per_id": per_id,
    }
    RTM_PATH.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return doc


def write_final_closure_report(
    remediation: dict[str, Any], audit: dict[str, Any], rtm: dict[str, Any]
) -> Path:
    path = OUT / "BATCH02_FINAL_CLOSURE_REPORT.md"
    counts = audit["counts"]
    gate_met = rtm["closure_gate"]["met"]
    scan = remediation.get("cross_spine_scan") or {}
    lines = [
        "# Batch 02 Final Closure Report (Run 007)\n\n",
        f"**Generated:** {datetime.now(UTC).isoformat()}  \n",
        "**Run:** Master Contract 007  \n",
        "**Scope:** IDs 51–100  \n\n",
        "## Closure Gate\n\n",
        f"| Criterion | Status |\n|---|---|\n",
        f"| CONCEPTUALLY-UNSOUND = 0 | **{'MET ✅' if gate_met else 'NOT MET ❌'}** ({counts.get('CONCEPTUALLY-UNSOUND', 0)}) |\n",
        f"| RTM updated (no fake 50/50) | **MET ✅** (`docs/BATCH02_OFFICIAL_RTM_51_100.json`) |\n",
        f"| Batch 02 officially closed | **{'YES' if gate_met else 'NO'}** |\n\n",
        "## Item 1 — CONCEPTUALLY-UNSOUND Remediation (Path A)\n\n",
        "| ID | Fix |\n|---:|---|\n",
        "| 52 | Real breadth = % reference basket same direction as primary (24h) |\n",
        "| 53 | Pearson BTC/SPX daily-return coupling coefficient (30d window) |\n",
        "| 54 | Removed `global_liquidity_proxy=len(sources)`; aggregated 24h quote volume |\n",
        "| 81 | Accum/dist via notional USD + direction fields, not substring match |\n\n",
        "## Item 2 — Cross-Spine (55, 56, 59, 60)\n\n",
        "**Root cause:** `LEGACY_BATCH01_EXTENSION_IDS` contained {55,56,59,60}; `BATCH01_IDS` checked before `BATCH02_IDS` in `runtime.py`.\n\n",
        "**Fix:** Removed overlap IDs from `LEGACY_BATCH01_EXTENSION_IDS`; batch02 dedicated handlers added; routing now `production_spine=batch02`.\n\n",
        "| ID | production_spine | routing_correct |\n|---:|---|---|\n",
    ]
    for cid in sorted(CROSS_SPINE_FIXED_IDS):
        row = remediation["cross_spine"][str(cid)]
        lines.append(
            f"| {cid} | {row.get('production_spine')} | {row.get('routing_correct')} |\n"
        )
    lines.extend(
        [
            "\n## Item 3 — CROSS-SPINE-001 Scan\n\n",
            f"- **Overlapping routing IDs remaining:** {scan.get('total_overlapping_ids', '?')}\n",
            f"- **batch01∩batch02 (post-fix):** {[o['id'] for o in scan.get('batch01_batch02', [])]}\n",
            f"- **batch01∩batch03 (separate finding):** {[o['id'] for o in scan.get('batch01_batch03', [])]}\n",
            f"- **batch02∩batch03:** {[o['id'] for o in scan.get('batch02_batch03', [])]}\n\n",
            "## Item 4 — PERFORMANCE-UNVERIFIABLE (unchanged)\n\n",
            "IDs 66, 69, 90, 97, 98 remain PERFORMANCE-UNVERIFIABLE per GIPS shadow-only ledger (Run 004).\n\n",
            "## Final Classification Summary\n\n",
        ]
    )
    for status, n in sorted(counts.items(), key=lambda x: -x[1]):
        lines.append(f"- **{status}:** {n}/50\n")
    lines.append("\n## Final Status Table (50/50)\n\n")
    lines.append("| ID | Name | Status | Phase | Standard |\n|---:|---|---|---|---|\n")
    for r in audit["rows"]:
        lines.append(
            f"| {r['id']} | {r['name']} | **{r['status']}** | {r.get('failed_phase','—')} | "
            f"{r.get('failed_standard','—')[:60]} |\n"
        )
    path.write_text("".join(lines), encoding="utf-8")
    evidence_path = OUT / "RUN007_BATCH02_CLOSURE_EVIDENCE.json"
    evidence_path.write_text(
        json.dumps(
            {
                "remediation": remediation,
                "audit_counts": counts,
                "rtm_summary": rtm["summary"],
                "closure_gate_met": gate_met,
            },
            indent=2,
            default=str,
        ),
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
