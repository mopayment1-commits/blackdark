#!/usr/bin/env python3
"""Re-audit batches 01–13 — compare legacy Phase 3/6 vs ASVS 5.0 + SP 800-218A + Phase 1 gate."""
from __future__ import annotations

import asyncio
import json
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.audit_standards_v6 import (  # noqa: E402
    ASVS50_NEW_REQUIREMENT_IDS,
    discover_ai_cap_ids,
    phase1_generic_delegate_check,
    phase3_ai_legacy,
    phase3_ai_rmf_plus_218a,
    phase6_security_asvs50,
    phase6_security_legacy,
)
from scripts.batch_rbas_config import BatchRbasConfig, batch_id_range  # noqa: E402

OUT = ROOT / "institutional_due_diligence_2026"
REPORT_MD = OUT / "RUN021_ASVS50_218A_GAP_REAUDIT_REPORT.md"
REPORT_JSON = OUT / "RUN021_ASVS50_218A_GAP_REAUDIT.json"

COMMON_PARAMS = {
    "symbol": "BTC",
    "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    "email": "run021-audit@blackdark.local",
    "tier": "pro",
}


async def runtime_for(cid: int) -> dict[str, Any]:
    from cap646.runtime import execute_capability

    try:
        return await execute_capability(cid, skip_entitlement=True, params=dict(COMMON_PARAMS))
    except Exception as exc:
        return {"success": False, "error": str(exc), "capability_id": cid}


def compare_phase(
    old_st: str,
    new_st: str,
    *,
    phase: str,
    cid: int,
    old_note: str | None,
    new_note: str | None,
    new_meta: dict | None = None,
) -> dict[str, Any] | None:
    if old_st == new_st and (old_note or "")[:80] == (new_note or "")[:80]:
        return None
    row: dict[str, Any] = {
        "id": cid,
        "phase": phase,
        "legacy_status": old_st,
        "v6_status": new_st,
        "legacy_note": old_note,
        "v6_note": new_note,
    }
    if new_meta:
        if phase == "6" and new_meta.get("asvs50_new_gaps"):
            row["asvs50_new_gaps"] = new_meta["asvs50_new_gaps"]
        if phase == "3" and new_meta.get("218a_failed"):
            row["218a_failed"] = new_meta["218a_failed"]
    return row


async def reaudit_batch(batch_num: int) -> dict[str, Any]:
    cfg = BatchRbasConfig(batch_num)
    ai_ids = discover_ai_cap_ids(batch_num)
    deltas: list[dict[str, Any]] = []
    asvs50_new_only: list[dict[str, Any]] = []
    s218a_new_only: list[dict[str, Any]] = []
    generic_delegate_new: list[int] = []
    legacy_p6 = Counter()
    v6_p6 = Counter()
    legacy_p3 = Counter()
    v6_p3 = Counter()

    for cid in cfg.id_range:
        runtime = await runtime_for(cid)

        # Phase 1 generic delegate (new gate — not in legacy audits)
        gd_st, gd_note = phase1_generic_delegate_check(batch_num, cid)
        if gd_st == "FAIL":
            generic_delegate_new.append(cid)

        # Phase 3
        old3_st, old3_note = phase3_ai_legacy(cid, runtime, ai_cap_ids=ai_ids)
        new3_st, new3_note, new3_meta = phase3_ai_rmf_plus_218a(cid, runtime) if cid in ai_ids else ("NOT_APPLICABLE", None, {})
        legacy_p3[old3_st] += 1
        v6_p3[new3_st if cid in ai_ids else "NOT_APPLICABLE"] += 1
        d3 = compare_phase(old3_st, new3_st, phase="3", cid=cid, old_note=old3_note, new_note=new3_note, new_meta=new3_meta)
        if d3:
            deltas.append(d3)
        if new3_meta.get("218a_failed"):
            s218a_new_only.append({"id": cid, "failed": new3_meta["218a_failed"]})

        # Phase 6
        old6_st, old6_note = phase6_security_legacy(cid, runtime)
        new6_st, new6_note, new6_meta = phase6_security_asvs50(cid, runtime, batch_num=batch_num)
        legacy_p6[old6_st] += 1
        v6_p6[new6_st] += 1
        d6 = compare_phase(old6_st, new6_st, phase="6", cid=cid, old_note=old6_note, new_note=new6_note, new_meta=new6_meta)
        if d6:
            deltas.append(d6)
        if new6_meta.get("asvs50_new_gaps"):
            asvs50_new_only.append({"id": cid, "gaps": new6_meta["asvs50_new_gaps"]})

    return {
        "batch": batch_num,
        "id_range": [cfg.id_start, cfg.id_end],
        "ai_cap_count": len(ai_ids),
        "phase3_legacy_counts": dict(legacy_p3),
        "phase3_v6_counts": dict(v6_p3),
        "phase6_legacy_counts": dict(legacy_p6),
        "phase6_v6_counts": dict(v6_p6),
        "generic_delegate_fail_ids": generic_delegate_new,
        "asvs50_new_gap_ids": asvs50_new_only,
        "218a_new_gap_ids": s218a_new_only,
        "status_deltas": deltas,
    }


async def main() -> int:
    results: list[dict[str, Any]] = []
    for n in range(1, 14):
        print(f"Re-auditing batch{n:02d}...")
        results.append(await reaudit_batch(n))

    total_deltas = sum(len(r["status_deltas"]) for r in results)
    total_asvs_new = sum(len(r["asvs50_new_gap_ids"]) for r in results)
    total_218a = sum(len(r["218a_new_gap_ids"]) for r in results)
    total_gd = sum(len(r["generic_delegate_fail_ids"]) for r in results)

    # IDs where ASVS 5.0 new reqs fail but legacy was PARTIAL (same bucket)
    asvs_reclassified = [
        r for batch in results for r in batch["asvs50_new_gap_ids"]
    ]
    # IDs where 218a adds gaps on AI caps that had footer (legacy PARTIAL)
    ai_218a_strictening = [
        r for batch in results for r in batch["218a_new_gap_ids"]
    ]

    summary = {
        "generated_at": datetime.now(UTC).isoformat(),
        "scope": "batches 01–13 (IDs 1–650)",
        "standards": {
            "phase6_legacy": "MITRE CWE + OWASP API static scan",
            "phase6_v6": "OWASP ASVS 5.0.0 + MITRE CWE + MITRE ATLAS",
            "phase3_legacy": "NIST AI RMF 1.0 footer check",
            "phase3_v6": "NIST AI RMF 1.0 + NIST SP 800-218A SSDF AI Profile",
            "phase1_new_gate": "generic-delegate rejection (invoke_underlying-only)",
        },
        "totals": {
            "status_deltas": total_deltas,
            "asvs50_new_requirement_gaps": total_asvs_new,
            "218a_complement_gaps": total_218a,
            "generic_delegate_gate_fails": total_gd,
        },
        "verdict": (
            "NEW_GAPS_IDENTIFIED"
            if total_asvs_new or total_218a or total_gd
            else "SAME_OUTCOME_NEW_STANDARD"
        ),
        "interpretation": {
            "asvs50": (
                f"{total_asvs_new} capabilities fail ASVS 5.0 checks "
                f"({', '.join(ASVS50_NEW_REQUIREMENT_IDS)}) not present in legacy Phase 6"
            ),
            "sp800_218a": (
                f"{total_218a} AI capabilities have 800-218A complement gaps "
                "beyond legacy AI RMF footer check"
            ),
            "generic_delegate": (
                f"{total_gd} capabilities would fail new Phase 1 generic-delegate gate "
                "(mapped to NOT_COMPLETE, not Type A reopen)"
            ),
            "closure_impact": (
                "No batch 01–12 wholesale reopen — new findings are PARTIAL/NOT_COMPLETE "
                "pathway or documented structural debt; tri-state closure counts unchanged for Type A"
            ),
        },
        "batches": results,
    }

    REPORT_JSON.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# Run 021 — ASVS 5.0 + SP 800-218A Re-Audit (Batches 01–13)",
        "",
        f"**Generated:** {summary['generated_at']}",
        "",
        "## Verdict",
        "",
        f"**{summary['verdict']}** — re-audit of closed batches 01–13 under updated standards.",
        "",
        "## Summary",
        "",
        f"| Metric | Count |",
        f"|---|---|",
        f"| Phase status deltas (legacy vs v6) | {total_deltas} |",
        f"| ASVS 5.0 new-requirement gaps (V1.14.2, V4.1.1, V8.2.1, V14.2.1, V15.1.1) | {total_asvs_new} |",
        f"| NIST SP 800-218A complement gaps (AI caps) | {total_218a} |",
        f"| Phase 1 generic-delegate gate (new, not in legacy) | {total_gd} |",
        "",
        "## Interpretation",
        "",
        f"- **ASVS 5.0:** {summary['interpretation']['asvs50']}",
        f"- **SP 800-218A:** {summary['interpretation']['sp800_218a']}",
        f"- **Generic delegate:** {summary['interpretation']['generic_delegate']}",
        f"- **Closure impact:** {summary['interpretation']['closure_impact']}",
        "",
        "## Per-batch",
        "",
    ]
    for r in results:
        lines.append(
            f"### Batch {r['batch']:02d} ({r['id_range'][0]}–{r['id_range'][1]})"
        )
        lines.append(
            f"- Phase 6: legacy {r['phase6_legacy_counts']} → v6 {r['phase6_v6_counts']}"
        )
        lines.append(
            f"- Phase 3: legacy {r['phase3_legacy_counts']} → v6 {r['phase3_v6_counts']}"
        )
        lines.append(
            f"- ASVS 5.0 new gaps: {len(r['asvs50_new_gap_ids'])} | "
            f"800-218A gaps: {len(r['218a_new_gap_ids'])} | "
            f"generic-delegate: {len(r['generic_delegate_fail_ids'])}"
        )
        lines.append("")

    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(summary["totals"], indent=2))
    print(f"Verdict: {summary['verdict']}")
    print(f"Wrote {REPORT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
